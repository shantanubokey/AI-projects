"""Adaptive RAG — importable module (mirrors 7_adaptive_rag.py)"""
from advanced_rag.base import embed_texts, build_faiss_index, retrieve_top_k, call_llm
import json

class AdaptiveRAG:
    def __init__(self, docs: list[str]):
        self.docs = docs
        self.index = build_faiss_index(embed_texts(docs))

    def classify_query(self, query: str) -> str:
        prompt = f"""Classify this query. Reply with ONE word only:
SIMPLE, COMPLEX, NO_CONTEXT, or CLARIFY.
Query: {query}
Strategy:"""
        result = call_llm(prompt, model="fast")
        verdict = result["answer"].strip().upper()
        for s in ("SIMPLE", "COMPLEX", "NO_CONTEXT", "CLARIFY"):
            if s in verdict:
                return s
        return "SIMPLE"

    def handle_simple(self, question: str) -> dict:
        q_vec = embed_texts([question])
        context = "\n\n".join(retrieve_top_k(self.index, q_vec, self.docs, k=2))
        result = call_llm(f"Context:\n{context}\n\nQuestion: {question}\nAnswer briefly:", model="fast")
        result["strategy"] = "SIMPLE"
        return result

    def handle_complex(self, question: str) -> dict:
        decomp = call_llm(f"Break into 2-3 sub-questions. JSON array only.\nQuestion: {question}", model="fast")
        try:
            sub_qs = json.loads(decomp["answer"])
        except:
            sub_qs = [question]

        contexts = []
        for sq in sub_qs:
            q_vec = embed_texts([sq])
            chunks = retrieve_top_k(self.index, q_vec, self.docs, k=2)
            contexts.append(f"Sub-Q: {sq}\nContext: {' '.join(chunks)}")

        prompt = f"Synthesize a comprehensive answer.\n\n{chr(10).join(contexts)}\n\nMain question: {question}\nAnswer:"
        result = call_llm(prompt, model="powerful")
        result["strategy"] = "COMPLEX"
        result["sub_queries"] = sub_qs
        return result

    def handle_no_context(self, question: str) -> dict:
        result = call_llm(question, model="balanced", system="Answer from your knowledge. Be concise.")
        result["strategy"] = "NO_CONTEXT"
        return result

    def handle_clarify(self, question: str) -> dict:
        result = call_llm(f"Generate 2 clarifying questions. JSON array only.\nQuery: {question}", model="fast")
        try:
            clarifications = json.loads(result["answer"])
        except:
            clarifications = ["Could you be more specific?"]
        return {
            "answer": f"Could you clarify: {' OR '.join(clarifications)}",
            "strategy": "CLARIFY", "clarifications": clarifications,
            "model": result["model"], "latency": result["latency"],
            "cost_usd": result["cost_usd"], "total_tokens": result["total_tokens"],
        }

    def ask(self, question: str) -> dict:
        strategy = self.classify_query(question)
        handlers = {
            "SIMPLE": self.handle_simple,
            "COMPLEX": self.handle_complex,
            "NO_CONTEXT": self.handle_no_context,
            "CLARIFY": self.handle_clarify,
        }
        result = handlers.get(strategy, self.handle_simple)(question)
        result["technique"] = "Adaptive RAG"
        return result
