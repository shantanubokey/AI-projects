"""
Advanced RAG Technique #7: Adaptive RAG
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHY ADAPTIVE RAG?
- Different queries need different strategies:
  * Simple factual → direct retrieval
  * Complex analytical → decomposition
  * Out-of-domain → LLM knowledge only
  * Ambiguous → clarification
- One-size-fits-all RAG wastes compute and reduces quality

TECHNIQUE:
1. Fast LLM classifies query into strategy:
   - SIMPLE: single retrieval + answer
   - COMPLEX: decompose → multi-retrieve → synthesize
   - NO_CONTEXT: answer from LLM knowledge
   - CLARIFY: ask for clarification
2. Route to appropriate strategy
3. Execute strategy with right model

MULTI-LLM STRATEGY:
- Fast model (8B) for routing/classification → cheap decision
- Fast model (8B) for simple queries → no need for 70B
- Powerful model (70B) for complex queries → worth the cost
- Balanced model (70B) for synthesis → good quality

WHEN TO USE:
- Production RAG systems with mixed query types
- Cost optimization (don't use 70B for simple queries)
- When latency varies by query complexity
- Customer support, general assistants
"""

from advanced_rag.base import embed_texts, build_faiss_index, retrieve_top_k, call_llm
import json

STRATEGIES = {
    "SIMPLE":     "Single retrieval, fast answer",
    "COMPLEX":    "Decompose query, multi-retrieve, synthesize",
    "NO_CONTEXT": "Answer from LLM knowledge only",
    "CLARIFY":    "Query is ambiguous, needs clarification",
}

class AdaptiveRAG:
    def __init__(self, docs: list[str]):
        self.docs = docs
        vecs = embed_texts(docs)
        self.index = build_faiss_index(vecs)
    
    def classify_query(self, query: str) -> str:
        """
        Use fast LLM to classify query into a strategy.
        This is the routing step — cheap but critical.
        """
        prompt = f"""Classify this query into one of these strategies:
- SIMPLE: straightforward factual question, single retrieval needed
- COMPLEX: multi-part, comparative, or analytical question
- NO_CONTEXT: general knowledge question unlikely to be in documents
- CLARIFY: too vague or ambiguous to answer

Respond with ONLY the strategy name.

Query: {query}
Strategy:"""
        
        result = call_llm(prompt, model="fast")
        strategy = result["answer"].strip().upper()
        
        # Normalize
        for s in STRATEGIES:
            if s in strategy:
                return s
        return "SIMPLE"  # default
    
    def handle_simple(self, question: str) -> dict:
        """Simple: retrieve + fast answer."""
        q_vec = embed_texts([question])
        context = "\n\n".join(retrieve_top_k(self.index, q_vec, self.docs, k=2))
        prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer briefly:"
        result = call_llm(prompt, model="fast")  # fast model for simple queries
        result["strategy"] = "SIMPLE"
        return result
    
    def handle_complex(self, question: str) -> dict:
        """Complex: decompose → multi-retrieve → synthesize."""
        # Decompose
        decomp_prompt = f"""Break into 2-3 sub-questions. Return JSON array only.
Question: {question}"""
        decomp = call_llm(decomp_prompt, model="fast")
        try:
            sub_qs = json.loads(decomp["answer"])
        except:
            sub_qs = [question]
        
        # Multi-retrieve
        contexts = []
        for sq in sub_qs:
            q_vec = embed_texts([sq])
            chunks = retrieve_top_k(self.index, q_vec, self.docs, k=2)
            contexts.append(f"Sub-Q: {sq}\nContext: {' '.join(chunks)}")
        
        # Synthesize with powerful model
        prompt = f"""Synthesize a comprehensive answer.

{chr(10).join(contexts)}

Main question: {question}
Answer:"""
        result = call_llm(prompt, model="powerful")
        result["strategy"] = "COMPLEX"
        result["sub_queries"] = sub_qs
        return result
    
    def handle_no_context(self, question: str) -> dict:
        """No context: answer from LLM knowledge."""
        result = call_llm(question, model="balanced",
                         system="Answer from your knowledge. Be concise and accurate.")
        result["strategy"] = "NO_CONTEXT"
        return result
    
    def handle_clarify(self, question: str) -> dict:
        """Ambiguous: generate clarifying questions."""
        prompt = f"""This query is ambiguous. Generate 2 clarifying questions.
Return JSON array only.
Query: {question}"""
        result = call_llm(prompt, model="fast")
        try:
            clarifications = json.loads(result["answer"])
        except:
            clarifications = ["Could you be more specific?"]
        
        return {
            "answer": f"I need clarification. Could you answer: {' OR '.join(clarifications)}",
            "strategy": "CLARIFY",
            "clarifications": clarifications,
            "model": result["model"],
            "latency": result["latency"],
            "cost_usd": result["cost_usd"],
            "total_tokens": result["total_tokens"],
        }
    
    def ask(self, question: str) -> dict:
        """
        Adaptive routing: classify → execute right strategy.
        """
        # Route with fast LLM
        strategy = self.classify_query(question)
        
        # Execute strategy
        if strategy == "SIMPLE":
            result = self.handle_simple(question)
        elif strategy == "COMPLEX":
            result = self.handle_complex(question)
        elif strategy == "NO_CONTEXT":
            result = self.handle_no_context(question)
        else:  # CLARIFY
            result = self.handle_clarify(question)
        
        result["technique"] = "Adaptive RAG"
        return result


# ── Demo ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    docs = [
        "Python was created in 1991 by Guido van Rossum.",
        "JavaScript was created in 1995 by Brendan Eich.",
        "Python is used for data science and machine learning.",
        "JavaScript is used for web development.",
    ]
    
    rag = AdaptiveRAG(docs)
    
    queries = [
        ("SIMPLE",     "When was Python created?"),
        ("COMPLEX",    "Compare Python and JavaScript history and use cases"),
        ("NO_CONTEXT", "What is the capital of France?"),
    ]
    
    for expected, q in queries:
        result = rag.ask(q)
        print(f"Q: {q}")
        print(f"Strategy: {result['strategy']} (expected: {expected})")
        print(f"A: {result['answer'][:100]}...")
        print(f"Model: {result['model']} | Cost: ${result['cost_usd']:.6f}\n")
