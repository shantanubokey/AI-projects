"""
Simple RAG Application
- Embeddings: sentence-transformers (free, local)
- Vector Store: FAISS (free, local)
- LLM: Groq API (free tier)
"""

import os
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from groq import Groq

# ── Config ───────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "gsk_key")
EMBED_MODEL  = "all-MiniLM-L6-v2"
LLM_MODEL    = "llama-3.3-70b-versatile"

embedder = SentenceTransformer(EMBED_MODEL)

class RAG:
    def __init__(self):
        self.docs   = []
        self.index  = None
        self.client = Groq(api_key=GROQ_API_KEY)

    def add_documents(self, documents: list[str]):
        self.docs = documents
        vecs = embedder.encode(documents, convert_to_numpy=True).astype("float32")
        self.index = faiss.IndexFlatL2(vecs.shape[1])
        self.index.add(vecs)
        print(f"Indexed {len(documents)} documents.")

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        q_vec = embedder.encode([query], convert_to_numpy=True).astype("float32")
        _, indices = self.index.search(q_vec, top_k)
        return [self.docs[i] for i in indices[0] if i < len(self.docs)]

    def ask(self, question: str, top_k: int = 3) -> dict:
        import time
        context = "\n\n".join(self.retrieve(question, top_k))
        prompt = f"Use the context to answer. If not in context, say 'I don't know'.\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"

        t0 = time.perf_counter()
        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        latency = time.perf_counter() - t0

        usage = response.usage
        # llama-3.3-70b-versatile pricing: $0.59/1M input, $0.79/1M output
        cost = (usage.prompt_tokens * 0.59 + usage.completion_tokens * 0.79) / 1_000_000

        return {
            "answer": response.choices[0].message.content,
            "latency": latency,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "cost_usd": cost,
        }


if __name__ == "__main__":
    rag = RAG()

    docs = [
        "The Eiffel Tower is located in Paris, France. It was built in 1889.",
        "Python is a high-level programming language known for its readability.",
        "RAG stands for Retrieval-Augmented Generation. It combines search with LLMs.",
        "FAISS is a library by Meta for efficient similarity search on dense vectors.",
        "Groq provides a free API tier for running open-source LLMs at high speed.",
    ]

    rag.add_documents(docs)

    for q in ["What is RAG?", "Where is the Eiffel Tower?"]:
        print(f"\nQ: {q}")
        result = rag.ask(q)
        print(f"A: {result['answer']}")
        print(f"   Latency: {result['latency']:.2f}s | Tokens: {result['total_tokens']} | Cost: ${result['cost_usd']:.6f}")
