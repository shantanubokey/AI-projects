"""
Advanced RAG Technique #6: RAG Fusion (Multi-Query + RRF)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHY RAG FUSION?
- Single query retrieval misses docs that use different terminology
- RAG Fusion generates multiple query variations and fuses results
- Reciprocal Rank Fusion (RRF) combines rankings without score normalization
- Consistently outperforms single-query RAG by 10-20%

TECHNIQUE:
1. Fast LLM generates N variations of the original query
2. Each variation retrieves its own ranked list
3. RRF algorithm fuses all ranked lists into one
   RRF score = Σ 1/(k + rank_i) for each doc across all lists
4. Top-k fused results → powerful LLM for answer

MULTI-LLM STRATEGY:
- Fast model (8B) for query generation → cheap, creative variations
- Powerful model (70B) for final answer → best quality

WHEN TO USE:
- When users phrase queries ambiguously
- Large diverse document collections
- Search engines, knowledge bases
- When recall is more important than speed
"""

from advanced_rag.base import embed_texts, build_faiss_index, call_llm
import numpy as np
import json

class RAGFusion:
    def __init__(self, docs: list[str]):
        self.docs = docs
        vecs = embed_texts(docs)
        self.vecs = vecs
        self.index = build_faiss_index(vecs)
    
    def generate_query_variations(self, query: str, n: int = 4) -> list[str]:
        """
        Use fast LLM to generate N variations of the query.
        Different phrasings improve recall across diverse docs.
        """
        prompt = f"""Generate {n} different ways to ask this question.
Use different keywords and phrasings to maximize search coverage.
Return ONLY a JSON array of strings.

Original question: {query}

Variations (JSON array):"""
        
        result = call_llm(prompt, model="fast")
        try:
            variations = json.loads(result["answer"])
            if isinstance(variations, list):
                return [query] + variations[:n-1]  # include original
        except:
            pass
        return [query]  # fallback
    
    def rrf_score(self, rankings: list[list[int]], k: int = 60) -> dict[int, float]:
        """
        Reciprocal Rank Fusion algorithm.
        
        Args:
            rankings: List of ranked doc index lists
            k: RRF constant (60 is standard, reduces impact of top ranks)
        
        Returns:
            Dict of {doc_index: rrf_score}
        """
        scores = {}
        for ranked_list in rankings:
            for rank, doc_idx in enumerate(ranked_list):
                if doc_idx not in scores:
                    scores[doc_idx] = 0
                # RRF formula: 1 / (k + rank)
                scores[doc_idx] += 1 / (k + rank + 1)
        return scores
    
    def ask(self, question: str, n_queries: int = 4, top_k: int = 3) -> dict:
        """
        RAG Fusion: multi-query → RRF → answer.
        """
        # Stage 1: Generate query variations with fast LLM
        variations = self.generate_query_variations(question, n=n_queries)
        
        # Stage 2: Retrieve ranked lists for each variation
        all_rankings = []
        for var in variations:
            q_vec = embed_texts([var]).astype("float32")
            distances, indices = self.index.search(q_vec, len(self.docs))
            all_rankings.append(indices[0].tolist())
        
        # Stage 3: Apply RRF to fuse rankings
        fused_scores = self.rrf_score(all_rankings)
        
        # Sort by RRF score and take top-k
        top_indices = sorted(fused_scores, key=fused_scores.get, reverse=True)[:top_k]
        context = "\n\n".join([self.docs[i] for i in top_indices])
        
        # Stage 4: Generate answer with powerful LLM
        prompt = f"""Answer the question using the retrieved context.

Context:
{context}

Question: {question}
Answer:"""
        
        result = call_llm(prompt, model="powerful")
        result["query_variations"] = variations
        result["fused_scores"] = {self.docs[i][:50]: round(fused_scores[i], 4) for i in top_indices}
        result["technique"] = "RAG Fusion (RRF)"
        return result


# ── Demo ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    docs = [
        "Neural networks are computational models inspired by the brain.",
        "Deep learning uses multi-layer neural networks for complex tasks.",
        "Artificial intelligence enables machines to simulate human intelligence.",
        "Machine learning algorithms learn patterns from training data.",
        "Transformers are neural network architectures using self-attention.",
        "GPT models are large language models based on transformer architecture.",
    ]
    
    rag = RAGFusion(docs)
    result = rag.ask("How do AI models learn?")
    
    print(f"Q: How do AI models learn?\n")
    print("Query variations:")
    for v in result["query_variations"]:
        print(f"  - {v}")
    print(f"\nFused scores:")
    for doc, score in result["fused_scores"].items():
        print(f"  [{score}] {doc}...")
    print(f"\nA: {result['answer']}")
    print(f"\nModel: {result['model']} | Latency: {result['latency']:.2f}s | Cost: ${result['cost_usd']:.6f}")
