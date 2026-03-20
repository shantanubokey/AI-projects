"""Corrective RAG — importable module (mirrors 4_corrective_rag.py)"""
from advanced_rag.base import embed_texts, build_faiss_index, retrieve_top_k, call_llm

class CorrectiveRAG:
    def __init__(self, docs: list[str]):
        self.docs = docs
        self.index = build_faiss_index(embed_texts(docs))

    def evaluate_relevance(self, query: str, docs: list[str]) -> str:
        prompt = f"""Are these documents relevant to answer the query?
Reply with ONE word: CORRECT, AMBIGUOUS, or INCORRECT.
Query: {query}
Documents: {chr(10).join(docs)}
Evaluation:"""
        result = call_llm(prompt, model="fast")
        verdict = result["answer"].strip().upper()
        if "INCORRECT" in verdict: return "INCORRECT"
        if "AMBIGUOUS" in verdict: return "AMBIGUOUS"
        return "CORRECT"

    def refine_query(self, query: str) -> str:
        result = call_llm(
            f"Rephrase for better retrieval. Return only the rephrased query.\nQuery: {query}",
            model="balanced"
        )
        return result["answer"].strip()

    def ask(self, question: str, top_k: int = 3) -> dict:
        q_vec = embed_texts([question])
        retrieved = retrieve_top_k(self.index, q_vec, self.docs, k=top_k)
        verdict = self.evaluate_relevance(question, retrieved)
        refined_query = None

        if verdict == "CORRECT":
            context = "\n\n".join(retrieved)
        elif verdict == "AMBIGUOUS":
            refined_query = self.refine_query(question)
            q_vec2 = embed_texts([refined_query])
            retrieved2 = retrieve_top_k(self.index, q_vec2, self.docs, k=top_k)
            combined = list(dict.fromkeys(retrieved + retrieved2))
            context = "\n\n".join(combined[:top_k])
        else:
            context = "No relevant documents found. Answer from general knowledge."

        prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        result = call_llm(prompt, model="powerful")
        result["verdict"] = verdict
        result["refined_query"] = refined_query
        result["technique"] = "Corrective RAG"
        return result
