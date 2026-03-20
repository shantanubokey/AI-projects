"""Re-ranking RAG — importable module (mirrors 1_reranking.py)"""
from advanced_rag.base import embed_texts, build_faiss_index, retrieve_top_k, call_llm

class ReRankingRAG:
    def __init__(self, docs: list[str]):
        self.docs = docs
        self.index = build_faiss_index(embed_texts(docs))

    def rerank(self, query: str, candidates: list[str], top_k: int = 3) -> list[tuple[str, float]]:
        scores = []
        for doc in candidates:
            prompt = f"""Rate relevance 0-10. Only respond with a number.
Query: {query}
Document: {doc}
Score:"""
            result = call_llm(prompt, model="fast")
            try:
                score = float(result["answer"].strip())
            except:
                score = 5.0
            scores.append((doc, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def ask(self, question: str, initial_k: int = 10, final_k: int = 3) -> dict:
        q_vec = embed_texts([question])
        candidates = retrieve_top_k(self.index, q_vec, self.docs, k=initial_k)
        reranked = self.rerank(question, candidates, top_k=final_k)
        context = "\n\n".join([doc for doc, _ in reranked])
        prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        result = call_llm(prompt, model="powerful")
        result["reranked_docs"] = reranked
        result["technique"] = "Re-ranking"
        return result
