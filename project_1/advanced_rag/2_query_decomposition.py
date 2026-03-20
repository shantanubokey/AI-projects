"""
Advanced RAG Technique #2: Query Decomposition
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHY QUERY DECOMPOSITION?
- Complex queries like "Compare X and Y" or "What happened between 2010-2020?" 
  are hard to answer with single retrieval
- Breaking into sub-queries improves coverage and accuracy
- Each sub-query retrieves different relevant chunks

TECHNIQUE:
1. Fast LLM decomposes complex query into 2-4 sub-queries
2. Each sub-query retrieves its own context independently
3. Powerful LLM synthesizes all contexts into final answer

MULTI-LLM STRATEGY:
- Fast model (8B) for decomposition → cheap, structured output
- Balanced model (70B) for synthesis → handles long context well

WHEN TO USE:
- Multi-part questions ("Compare A and B")
- Temporal queries ("What changed from X to Y?")
- Aggregation tasks ("Summarize all mentions of...")
- Research/analysis use cases
"""

from advanced_rag.base import embed_texts, build_faiss_index, retrieve_top_k, call_llm
import json

class QueryDecompositionRAG:
    def __init__(self, docs: list[str]):
        self.docs = docs
        vecs = embed_texts(docs)
        self.index = build_faiss_index(vecs)
    
    def decompose_query(self, query: str) -> list[str]:
        """
        Use fast LLM to break complex query into sub-queries.
        Returns list of 2-4 sub-queries.
        """
        prompt = f"""Break this complex question into 2-4 simpler sub-questions.
Return ONLY a JSON array of strings, nothing else.

Question: {query}

Sub-questions (JSON array):"""
        
        result = call_llm(prompt, model="fast")
        try:
            # Parse JSON array
            sub_queries = json.loads(result["answer"])
            if isinstance(sub_queries, list):
                return sub_queries[:4]  # max 4
        except:
            # Fallback: use original query
            return [query]
        
        return [query]
    
    def ask(self, question: str, top_k: int = 3) -> dict:
        """
        Decompose query, retrieve for each sub-query, synthesize answer.
        """
        # Stage 1: Decompose with fast LLM
        sub_queries = self.decompose_query(question)
        
        # Stage 2: Retrieve context for each sub-query
        all_contexts = []
        for sq in sub_queries:
            q_vec = embed_texts([sq])
            chunks = retrieve_top_k(self.index, q_vec, self.docs, k=top_k)
            all_contexts.append({
                "sub_query": sq,
                "context": "\n".join(chunks)
            })
        
        # Stage 3: Synthesize with powerful LLM
        context_str = "\n\n".join([
            f"Sub-question: {c['sub_query']}\nContext: {c['context']}"
            for c in all_contexts
        ])
        
        prompt = f"""Answer the main question by synthesizing information from multiple sub-questions.

Main question: {question}

{context_str}

Final answer:"""
        
        result = call_llm(prompt, model="balanced")
        result["sub_queries"] = sub_queries
        result["contexts"] = all_contexts
        result["technique"] = "Query Decomposition"
        return result


# ── Demo ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    docs = [
        "Python was created in 1991 by Guido van Rossum.",
        "Python 2.0 was released in 2000 with list comprehensions.",
        "Python 3.0 was released in 2008, breaking backward compatibility.",
        "JavaScript was created in 1995 by Brendan Eich at Netscape.",
        "JavaScript ES6 (2015) added arrow functions and classes.",
        "Python is used for data science, ML, web backends.",
        "JavaScript is used for web frontends, Node.js backends.",
        "Python has Django and Flask frameworks.",
        "JavaScript has React, Vue, Angular frameworks.",
    ]
    
    rag = QueryDecompositionRAG(docs)
    result = rag.ask("Compare Python and JavaScript history and use cases")
    
    print(f"Q: Compare Python and JavaScript history and use cases")
    print(f"\nSub-queries:")
    for sq in result['sub_queries']:
        print(f"  - {sq}")
    print(f"\nA: {result['answer']}\n")
    print(f"Model: {result['model']}")
    print(f"Latency: {result['latency']:.2f}s")
    print(f"Cost: ${result['cost_usd']:.6f}")
