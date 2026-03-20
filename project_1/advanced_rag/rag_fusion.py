"""RAG Fusion — importable module (mirrors 6_rag_fusion.py)"""
from advanced_rag.base import embed_texts, build_faiss_index, call_llm
import numpy as np, json

class RAGFusion:
    def __init__(self, docs: list[str]):
        self.docs = docs
        self.vecs = embed_texts(docs)
        self.index = build_faiss_index(self.vecs)

    def generate_query_variations(self, query: str, n: int = 4) -> list[str]:
        prompt = f"""Generate {n} different phrasings of this question.
Return ONLY a JSON array of strings.
Question: {query}
Variations:"""
        result = call_llm(prompt, model="fast")
        try:
            variations = json.loads(result["answer"])
            if isinstance(variations, list):
                return [query] + variations[:n-1]
        except:
            pass
        return [query]

    def rrf_score(self, rankings: list[list[int]], k: int = 60) -> dict:
        scores = {}
        for ranked_list in rankings:
            for rank, doc_idx in enumerate(ranked_list):
                scores[doc_idx] = scores.get(doc_idx, 0) + 1 / (k + rank + 1)
        return scores

    def ask(self, question: str, n_queries: int = 4, top_k: int = 3) -> dict:
        variations = self.generate_query_variations(question, n=n_queries)
        all_rankings = []
        for var in variations:
            q_vec = embed_texts([var]).astype("float32")
            _, indices = self.index.search(q_vec, len(self.docs))
            all_rankings.append(indices[0].tolist())

        fused_scores = self.rrf_score(all_rankings)
        top_indices = sorted(fused_scores, key=fused_scores.get, reverse=True)[:top_k]
        context = "\n\n".join([self.docs[i] for i in top_indices])

        prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        result = call_llm(prompt, model="powerful")
        result["query_variations"] = variations
        result["fused_scores"] = {self.docs[i][:50]: round(fused_scores[i], 4) for i in top_indices}
        result["technique"] = "RAG Fusion (RRF)"
        return result
