"""
Advanced RAG Technique #1: Re-ranking
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHY RE-RANKING?
- Vector search retrieves semantically similar docs, but not always the MOST relevant
- Re-ranking uses a cross-encoder to score query-doc pairs more accurately
- Improves precision by 15-30% compared to vector-only retrieval

TECHNIQUE:
1. Vector search retrieves top-20 candidates (recall-focused)
2. Fast LLM re-ranks them by relevance score (precision-focused)
3. Select top-3 for final context
4. Powerful LLM generates answer

MULTI-LLM STRATEGY:
- Fast model (8B) for re-ranking → cheap, quick
- Powerful model (70B) for final answer → accurate, detailed

WHEN TO USE:
- Large document collections where top-k vector results are noisy
- When precision matters more than speed
- Legal, medical, technical domains
"""

from advanced_rag.base import embed_texts, build_faiss_index, retrieve_top_k, call_llm
import numpy as np

class ReRankingRAG:
    def __init__(self, docs: list[str]):
        self.docs = docs
        vecs = embed_texts(docs)
        self.index = build_faiss_index(vecs)
    
    def rerank(self, query: str, candidates: list[str], top_k: int = 3) -> list[tuple[str, float]]:
        """
        Re-rank candidates using fast LLM.
        Returns list of (doc, score) sorted by relevance.
        """
        # Prompt fast LLM to score each candidate 0-10
        scores = []
        for doc in candidates:
            prompt = f"""Rate how relevant this document is to the query on a scale of 0-10.
Only respond with a single number.

Query: {query}
Document: {doc}

Relevance score (0-10):"""
            result = call_llm(prompt, model="fast")
            try:
                score = float(result["answer"].strip())
            except:
                score = 5.0  # default if parsing fails
            scores.append((doc, score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    def ask(self, question: str, initial_k: int = 20, final_k: int = 3) -> dict:
        """
        Two-stage retrieval with re-ranking.
        
        Args:
            question: User query
            initial_k: Number of candidates from vector search
            final_k: Number of docs after re-ranking
        """
        # Stage 1: Vector search (broad recall)
        q_vec = embed_texts([question])
        candidates = retrieve_top_k(self.index, q_vec, self.docs, k=initial_k)
        
        # Stage 2: Re-rank with fast LLM (precision)
        reranked = self.rerank(question, candidates, top_k=final_k)
        context = "\n\n".join([doc for doc, score in reranked])
        
        # Stage 3: Generate answer with powerful LLM
        prompt = f"""Answer the question using the provided context.

Context:
{context}

Question: {question}
Answer:"""
        
        result = call_llm(prompt, model="powerful")
        result["reranked_docs"] = reranked
        result["technique"] = "Re-ranking"
        return result


# ── Demo ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    docs = [
        "Python is a high-level programming language.",
        "The Eiffel Tower is in Paris, France.",
        "Machine learning is a subset of AI.",
        "Paris is the capital of France.",
        "Python was created by Guido van Rossum.",
        "The Eiffel Tower was built in 1889.",
        "Deep learning uses neural networks.",
        "France is in Western Europe.",
    ]
    
    rag = ReRankingRAG(docs)
    result = rag.ask("Where is the Eiffel Tower?")
    
    print(f"Q: Where is the Eiffel Tower?")
    print(f"A: {result['answer']}\n")
    print(f"Model: {result['model']}")
    print(f"Latency: {result['latency']:.2f}s")
    print(f"Cost: ${result['cost_usd']:.6f}")
    print(f"\nRe-ranked docs:")
    for doc, score in result['reranked_docs']:
        print(f"  [{score:.1f}] {doc}")
