"""
Advanced RAG Technique #3: Self-Query with Metadata Filtering
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHY SELF-QUERY?
- User queries often contain implicit filters: "recent papers", "cheap products", "2023 data"
- Vector search alone ignores these structured constraints
- Self-query extracts filters and applies them BEFORE vector search

TECHNIQUE:
1. Fast LLM extracts structured filters from natural language query
   Example: "cheap laptops" → {"category": "laptop", "price": "<500"}
2. Apply metadata filters to narrow search space
3. Vector search on filtered subset
4. Powerful LLM generates answer

MULTI-LLM STRATEGY:
- Fast model (8B) for filter extraction → structured output, cheap
- Balanced model (70B) for answer generation → quality response

WHEN TO USE:
- E-commerce (price, category, brand filters)
- Research papers (year, author, topic filters)
- Legal docs (jurisdiction, date, case type)
- Any domain with structured metadata
"""

from advanced_rag.base import embed_texts, build_faiss_index, call_llm
import json
import numpy as np

class SelfQueryRAG:
    def __init__(self, docs: list[dict]):
        """
        Args:
            docs: List of dicts with 'text' and metadata fields
                  Example: {"text": "...", "year": 2023, "category": "tech"}
        """
        self.docs = docs
        self.texts = [d["text"] for d in docs]
        vecs = embed_texts(self.texts)
        self.vecs = vecs
        self.index = build_faiss_index(vecs)
    
    def extract_filters(self, query: str) -> dict:
        """
        Use fast LLM to extract metadata filters from query.
        Returns dict of filters or empty dict.
        """
        prompt = f"""Extract structured filters from this query.
Return ONLY a JSON object with filter keys and values. If no filters, return {{}}.

Available filter fields: year, category, price, author, topic

Query: {query}

Filters (JSON):"""
        
        result = call_llm(prompt, model="fast")
        try:
            filters = json.loads(result["answer"])
            return filters if isinstance(filters, dict) else {}
        except:
            return {}
    
    def apply_filters(self, filters: dict) -> list[int]:
        """
        Return indices of docs matching all filters.
        """
        if not filters:
            return list(range(len(self.docs)))
        
        matching = []
        for i, doc in enumerate(self.docs):
            match = True
            for key, value in filters.items():
                if key not in doc:
                    match = False
                    break
                # Handle numeric comparisons
                if isinstance(value, str) and value.startswith(("<", ">")):
                    op = value[0]
                    num = float(value[1:])
                    doc_val = float(doc[key])
                    if op == "<" and doc_val >= num:
                        match = False
                    elif op == ">" and doc_val <= num:
                        match = False
                elif doc[key] != value:
                    match = False
                    break
            if match:
                matching.append(i)
        return matching
    
    def ask(self, question: str, top_k: int = 3) -> dict:
        """
        Self-query: extract filters, apply them, then vector search.
        """
        # Stage 1: Extract filters with fast LLM
        filters = self.extract_filters(question)
        
        # Stage 2: Apply filters
        valid_indices = self.apply_filters(filters)
        
        if not valid_indices:
            return {
                "answer": "No documents match the specified filters.",
                "filters": filters,
                "technique": "Self-Query",
            }
        
        # Stage 3: Vector search on filtered subset
        filtered_vecs = self.vecs[valid_indices]
        filtered_docs = [self.docs[i] for i in valid_indices]
        filtered_texts = [self.texts[i] for i in valid_indices]
        
        q_vec = embed_texts([question])
        # Manual top-k search on filtered vectors
        distances = np.linalg.norm(filtered_vecs - q_vec, axis=1)
        top_indices = np.argsort(distances)[:top_k]
        context = "\n\n".join([filtered_texts[i] for i in top_indices])
        
        # Stage 4: Generate answer with balanced LLM
        prompt = f"""Answer using the filtered and retrieved context.

Context:
{context}

Question: {question}
Answer:"""
        
        result = call_llm(prompt, model="balanced")
        result["filters"] = filters
        result["filtered_count"] = len(valid_indices)
        result["technique"] = "Self-Query"
        return result


# ── Demo ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    docs = [
        {"text": "iPhone 15 Pro - $999, flagship camera", "category": "phone", "price": 999, "year": 2023},
        {"text": "Samsung Galaxy A54 - $449, mid-range", "category": "phone", "price": 449, "year": 2023},
        {"text": "MacBook Pro M3 - $1999, powerful laptop", "category": "laptop", "price": 1999, "year": 2023},
        {"text": "Dell XPS 13 - $899, ultrabook", "category": "laptop", "price": 899, "year": 2023},
        {"text": "iPad Air - $599, tablet with M1 chip", "category": "tablet", "price": 599, "year": 2022},
        {"text": "Lenovo ThinkPad - $699, business laptop", "category": "laptop", "price": 699, "year": 2023},
    ]
    
    rag = SelfQueryRAG(docs)
    result = rag.ask("Show me affordable laptops under $1000")
    
    print(f"Q: Show me affordable laptops under $1000")
    print(f"\nExtracted filters: {result['filters']}")
    print(f"Filtered docs: {result['filtered_count']}")
    print(f"\nA: {result['answer']}\n")
    print(f"Model: {result['model']}")
    print(f"Latency: {result['latency']:.2f}s")
    print(f"Cost: ${result['cost_usd']:.6f}")
