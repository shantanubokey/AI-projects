"""Self-Query RAG — importable module (mirrors 3_self_query.py)"""
from advanced_rag.base import embed_texts, build_faiss_index, call_llm
import json, numpy as np

class SelfQueryRAG:
    def __init__(self, docs: list[dict]):
        self.docs = docs
        self.texts = [d["text"] for d in docs]
        self.vecs = embed_texts(self.texts)
        self.index = build_faiss_index(self.vecs)

    def extract_filters(self, query: str) -> dict:
        prompt = f"""Extract metadata filters from this query as JSON.
Available fields: year, category, price, author, topic
Return {{}} if no filters found.
Query: {query}
Filters:"""
        result = call_llm(prompt, model="fast")
        try:
            filters = json.loads(result["answer"])
            return filters if isinstance(filters, dict) else {}
        except:
            return {}

    def apply_filters(self, filters: dict) -> list[int]:
        if not filters:
            return list(range(len(self.docs)))
        matching = []
        for i, doc in enumerate(self.docs):
            match = True
            for key, value in filters.items():
                if key not in doc:
                    match = False; break
                if isinstance(value, str) and value[0] in ("<", ">"):
                    op, num = value[0], float(value[1:])
                    dv = float(doc[key])
                    if (op == "<" and dv >= num) or (op == ">" and dv <= num):
                        match = False; break
                elif doc[key] != value:
                    match = False; break
            if match:
                matching.append(i)
        return matching

    def ask(self, question: str, top_k: int = 3) -> dict:
        filters = self.extract_filters(question)
        valid_indices = self.apply_filters(filters)
        if not valid_indices:
            return {"answer": "No documents match the filters.", "filters": filters, "technique": "Self-Query"}

        filtered_vecs = self.vecs[valid_indices]
        filtered_texts = [self.texts[i] for i in valid_indices]
        q_vec = embed_texts([question])
        distances = np.linalg.norm(filtered_vecs - q_vec, axis=1)
        top_idx = np.argsort(distances)[:top_k]
        context = "\n\n".join([filtered_texts[i] for i in top_idx])

        prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        result = call_llm(prompt, model="balanced")
        result["filters"] = filters
        result["filtered_count"] = len(valid_indices)
        result["technique"] = "Self-Query"
        return result
