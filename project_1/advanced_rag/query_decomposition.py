"""Query Decomposition RAG — importable module (mirrors 2_query_decomposition.py)"""
from advanced_rag.base import embed_texts, build_faiss_index, retrieve_top_k, call_llm
import json

class QueryDecompositionRAG:
    def __init__(self, docs: list[str]):
        self.docs = docs
        self.index = build_faiss_index(embed_texts(docs))

    def decompose_query(self, query: str) -> list[str]:
        prompt = f"""Break into 2-4 simpler sub-questions.
Return ONLY a JSON array of strings.
Question: {query}
Sub-questions:"""
        result = call_llm(prompt, model="fast")
        try:
            sub_queries = json.loads(result["answer"])
            if isinstance(sub_queries, list):
                return sub_queries[:4]
        except:
            pass
        return [query]

    def ask(self, question: str, top_k: int = 3) -> dict:
        sub_queries = self.decompose_query(question)
        all_contexts = []
        for sq in sub_queries:
            q_vec = embed_texts([sq])
            chunks = retrieve_top_k(self.index, q_vec, self.docs, k=top_k)
            all_contexts.append({"sub_query": sq, "context": "\n".join(chunks)})

        context_str = "\n\n".join([
            f"Sub-question: {c['sub_query']}\nContext: {c['context']}"
            for c in all_contexts
        ])
        prompt = f"Synthesize an answer.\n\nMain question: {question}\n\n{context_str}\n\nFinal answer:"
        result = call_llm(prompt, model="balanced")
        result["sub_queries"] = sub_queries
        result["contexts"] = all_contexts
        result["technique"] = "Query Decomposition"
        return result
