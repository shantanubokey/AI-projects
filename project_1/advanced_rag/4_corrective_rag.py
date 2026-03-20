"""
Advanced RAG Technique #4: Corrective RAG (CRAG)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHY CORRECTIVE RAG?
- Standard RAG blindly uses retrieved docs even if they're irrelevant
- CRAG evaluates retrieval quality and CORRECTS it if poor
- Reduces hallucination by refusing to answer from bad context

TECHNIQUE:
1. Retrieve top-k docs
2. Fast LLM evaluates relevance: CORRECT / AMBIGUOUS / INCORRECT
3. If CORRECT → answer directly
4. If AMBIGUOUS → refine query and re-retrieve
5. If INCORRECT → fallback to LLM knowledge only
6. Powerful LLM generates final answer

MULTI-LLM STRATEGY:
- Fast model (8B) for relevance evaluation → binary decision, cheap
- Balanced model (70B) for query refinement → better reformulation
- Powerful model (70B) for final answer → highest accuracy

WHEN TO USE:
- When document quality is uncertain
- Open-domain QA where some queries may not be in docs
- Production systems where hallucination is costly
- Medical, legal, financial domains
"""

from advanced_rag.base import embed_texts, build_faiss_index, retrieve_top_k, call_llm

class CorrectiveRAG:
    def __init__(self, docs: list[str]):
        self.docs = docs
        vecs = embed_texts(docs)
        self.index = build_faiss_index(vecs)
    
    def evaluate_relevance(self, query: str, docs: list[str]) -> str:
        """
        Use fast LLM to evaluate if retrieved docs are relevant.
        Returns: "CORRECT", "AMBIGUOUS", or "INCORRECT"
        """
        context = "\n".join(docs)
        prompt = f"""Evaluate if the retrieved documents are relevant to answer the query.
Respond with ONLY one word: CORRECT, AMBIGUOUS, or INCORRECT.

- CORRECT: Documents clearly contain the answer
- AMBIGUOUS: Documents partially relate but may not fully answer
- INCORRECT: Documents are irrelevant to the query

Query: {query}
Documents: {context}

Evaluation:"""
        
        result = call_llm(prompt, model="fast")
        verdict = result["answer"].strip().upper()
        
        # Normalize response
        if "CORRECT" in verdict and "IN" not in verdict:
            return "CORRECT"
        elif "INCORRECT" in verdict:
            return "INCORRECT"
        else:
            return "AMBIGUOUS"
    
    def refine_query(self, original_query: str) -> str:
        """
        Use balanced LLM to rephrase query for better retrieval.
        """
        prompt = f"""Rephrase this query to improve document retrieval.
Make it more specific and use different keywords.
Return ONLY the rephrased query, nothing else.

Original query: {original_query}
Rephrased query:"""
        
        result = call_llm(prompt, model="balanced")
        return result["answer"].strip()
    
    def ask(self, question: str, top_k: int = 3) -> dict:
        """
        Corrective RAG: evaluate → correct → answer.
        """
        # Stage 1: Initial retrieval
        q_vec = embed_texts([question])
        retrieved = retrieve_top_k(self.index, q_vec, self.docs, k=top_k)
        
        # Stage 2: Evaluate relevance with fast LLM
        verdict = self.evaluate_relevance(question, retrieved)
        
        refined_query = None
        
        if verdict == "CORRECT":
            # Good retrieval → use as-is
            context = "\n\n".join(retrieved)
            
        elif verdict == "AMBIGUOUS":
            # Partial match → refine query and re-retrieve
            refined_query = self.refine_query(question)
            q_vec2 = embed_texts([refined_query])
            retrieved2 = retrieve_top_k(self.index, q_vec2, self.docs, k=top_k)
            # Combine original + refined results (deduplicated)
            combined = list(dict.fromkeys(retrieved + retrieved2))
            context = "\n\n".join(combined[:top_k])
            
        else:  # INCORRECT
            # Bad retrieval → use LLM knowledge only
            context = "No relevant documents found. Answer from general knowledge."
        
        # Stage 3: Generate answer with powerful LLM
        prompt = f"""Answer the question using the context.
If context says "No relevant documents found", answer from your knowledge.

Context:
{context}

Question: {question}
Answer:"""
        
        result = call_llm(prompt, model="powerful")
        result["verdict"] = verdict
        result["refined_query"] = refined_query
        result["technique"] = "Corrective RAG"
        return result


# ── Demo ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    docs = [
        "The Eiffel Tower is in Paris, France.",
        "Python is a programming language.",
        "FAISS is used for vector search.",
    ]
    
    rag = CorrectiveRAG(docs)
    
    # Test 1: Good retrieval
    r1 = rag.ask("Where is the Eiffel Tower?")
    print(f"Q: Where is the Eiffel Tower?")
    print(f"Verdict: {r1['verdict']}")
    print(f"A: {r1['answer']}\n")
    
    # Test 2: Out-of-domain (should fallback)
    r2 = rag.ask("What is the capital of Japan?")
    print(f"Q: What is the capital of Japan?")
    print(f"Verdict: {r2['verdict']}")
    print(f"A: {r2['answer']}\n")
    
    print(f"Model: {r1['model']} | Latency: {r1['latency']:.2f}s | Cost: ${r1['cost_usd']:.6f}")
