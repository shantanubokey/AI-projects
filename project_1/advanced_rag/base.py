"""
Advanced RAG Base Module
Shared utilities for all advanced RAG techniques.
"""

import os, time
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from groq import Groq

# ── Configuration ─────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your_groq_api_key_here")

# Multiple LLMs for different purposes:
# - Fast model for quick tasks (routing, classification)
# - Powerful model for complex reasoning
# - Balanced model for general use
MODELS = {
    "fast":     "llama-3.1-8b-instant",      # 8B params, ultra-fast, cheap
    "balanced": "llama-3.3-70b-versatile",   # 70B params, good quality/speed
    "powerful": "llama-3.1-70b-versatile",   # 70B params, best reasoning
}

# Pricing per 1M tokens (input, output)
PRICING = {
    "llama-3.1-8b-instant":      (0.05, 0.08),
    "llama-3.3-70b-versatile":   (0.59, 0.79),
    "llama-3.1-70b-versatile":   (0.59, 0.79),
}

# ── Embedder (shared across all techniques) ──────────────────────────────────
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# ── Groq Client ───────────────────────────────────────────────────────────────
client = Groq(api_key=GROQ_API_KEY)

def call_llm(prompt: str, model: str = "balanced", system: str = "") -> dict:
    """
    Call Groq LLM and return answer + metrics.
    
    Args:
        prompt: User prompt
        model: Model key from MODELS dict
        system: System prompt (optional)
    
    Returns:
        dict with answer, latency, tokens, cost
    """
    model_name = MODELS[model]
    messages = [{"role": "user", "content": prompt}]
    if system:
        messages.insert(0, {"role": "system", "content": system})
    
    t0 = time.perf_counter()
    resp = client.chat.completions.create(model=model_name, messages=messages)
    latency = time.perf_counter() - t0
    
    usage = resp.usage
    price_in, price_out = PRICING[model_name]
    cost = (usage.prompt_tokens * price_in + usage.completion_tokens * price_out) / 1_000_000
    
    return {
        "answer": resp.choices[0].message.content,
        "model": model_name,
        "latency": latency,
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
        "cost_usd": cost,
    }

def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed texts using sentence-transformers."""
    return embedder.encode(texts, convert_to_numpy=True).astype("float32")

def build_faiss_index(vectors: np.ndarray) -> faiss.IndexFlatL2:
    """Build FAISS index from vectors."""
    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)
    return index

def retrieve_top_k(index: faiss.IndexFlatL2, query_vec: np.ndarray, docs: list[str], k: int = 3) -> list[str]:
    """Retrieve top-k documents from FAISS index."""
    _, indices = index.search(query_vec.reshape(1, -1), k)
    return [docs[i] for i in indices[0] if i < len(docs)]
