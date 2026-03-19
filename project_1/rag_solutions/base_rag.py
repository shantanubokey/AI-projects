"""Shared RAG base used by all solutions."""
import os, time
from sentence_transformers import SentenceTransformer
import faiss, numpy as np
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your_groq_api_key_here")
LLM_MODEL    = "llama-3.3-70b-versatile"
embedder     = SentenceTransformer("all-MiniLM-L6-v2")

class BaseRAG:
    def __init__(self, system_prompt: str = ""):
        self.docs          = []
        self.index         = None
        self.system_prompt = system_prompt
        self.client        = Groq(api_key=GROQ_API_KEY)

    def add_documents(self, documents: list[str]):
        self.docs = documents
        vecs = embedder.encode(documents, convert_to_numpy=True).astype("float32")
        self.index = faiss.IndexFlatL2(vecs.shape[1])
        self.index.add(vecs)

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        q_vec = embedder.encode([query], convert_to_numpy=True).astype("float32")
        _, idx = self.index.search(q_vec, top_k)
        return [self.docs[i] for i in idx[0] if i < len(self.docs)]

    def ask(self, question: str, top_k: int = 3) -> dict:
        context = "\n\n".join(self.retrieve(question, top_k))
        prompt  = f"{self.system_prompt}\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
        t0 = time.perf_counter()
        resp = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        latency = time.perf_counter() - t0
        usage   = resp.usage
        cost    = (usage.prompt_tokens * 0.59 + usage.completion_tokens * 0.79) / 1_000_000
        return {
            "answer": resp.choices[0].message.content,
            "latency": latency,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "cost_usd": cost,
        }
