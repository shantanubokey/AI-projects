"""
Advanced RAG Technique #5: Agentic RAG
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHY AGENTIC RAG?
- Static RAG always retrieves, even when not needed
- Agentic RAG lets the LLM DECIDE which tool to use
- Can chain multiple retrievals, calculations, or direct answers
- Mimics how a human researcher would approach a problem

TECHNIQUE:
The LLM acts as an agent with access to tools:
  - search(query): retrieve from vector store
  - calculate(expr): evaluate math expressions
  - answer(text): return final answer

Loop:
1. LLM decides which tool to call
2. Tool executes and returns result
3. LLM uses result to decide next step
4. Repeat until LLM calls answer()

MULTI-LLM STRATEGY:
- Powerful model (70B) for agent reasoning → needs strong instruction following
- Fast model (8B) for tool result summarization → cheap post-processing

WHEN TO USE:
- Multi-step reasoning tasks
- When you need to combine retrieval + computation
- Research assistants
- Complex Q&A that requires multiple lookups
"""

from advanced_rag.base import embed_texts, build_faiss_index, retrieve_top_k, call_llm
import json, re

TOOLS_DESCRIPTION = """You have access to these tools:
- search(query): Search the knowledge base for relevant information
- calculate(expression): Evaluate a math expression
- answer(text): Return the final answer to the user

Respond with a JSON object: {"tool": "tool_name", "input": "input_value"}
"""

class AgenticRAG:
    def __init__(self, docs: list[str]):
        self.docs = docs
        vecs = embed_texts(docs)
        self.index = build_faiss_index(vecs)
        self.max_steps = 5  # prevent infinite loops
    
    def tool_search(self, query: str) -> str:
        """Tool: search knowledge base."""
        q_vec = embed_texts([query])
        results = retrieve_top_k(self.index, q_vec, self.docs, k=3)
        return "\n".join(results)
    
    def tool_calculate(self, expression: str) -> str:
        """Tool: safely evaluate math expression."""
        try:
            # Only allow safe math operations
            allowed = set("0123456789+-*/()., ")
            if all(c in allowed for c in expression):
                return str(eval(expression))
            return "Invalid expression"
        except:
            return "Calculation error"
    
    def parse_tool_call(self, response: str) -> tuple[str, str]:
        """Parse LLM response to extract tool name and input."""
        try:
            # Try JSON parsing
            data = json.loads(response)
            return data.get("tool", "answer"), data.get("input", response)
        except:
            # Fallback: regex
            match = re.search(r'"tool"\s*:\s*"(\w+)".*?"input"\s*:\s*"([^"]+)"', response, re.DOTALL)
            if match:
                return match.group(1), match.group(2)
            return "answer", response
    
    def ask(self, question: str) -> dict:
        """
        Agentic loop: LLM decides tools, executes, repeats until done.
        """
        history = []
        total_cost = 0
        total_tokens = 0
        steps = []
        
        # Initial prompt
        system = f"""{TOOLS_DESCRIPTION}
Think step by step. Use tools to gather information before answering."""
        
        messages = [{"role": "user", "content": question}]
        
        for step in range(self.max_steps):
            # Build context from history
            context = "\n".join([f"Tool: {s['tool']}\nResult: {s['result']}" for s in history])
            
            prompt = f"""Question: {question}

Previous steps:
{context if context else "None yet"}

What tool should I use next? Respond with JSON:"""
            
            result = call_llm(prompt, model="powerful", system=system)
            total_cost += result["cost_usd"]
            total_tokens += result["total_tokens"]
            
            tool_name, tool_input = self.parse_tool_call(result["answer"])
            
            # Execute tool
            if tool_name == "search":
                tool_result = self.tool_search(tool_input)
            elif tool_name == "calculate":
                tool_result = self.tool_calculate(tool_input)
            elif tool_name == "answer":
                # Agent is done
                steps.append({"step": step+1, "tool": "answer", "input": tool_input, "result": "FINAL"})
                return {
                    "answer": tool_input,
                    "steps": steps,
                    "total_cost_usd": total_cost,
                    "total_tokens": total_tokens,
                    "num_steps": step + 1,
                    "technique": "Agentic RAG",
                    "model": result["model"],
                    "latency": result["latency"],
                    "cost_usd": total_cost,
                }
            else:
                tool_result = "Unknown tool"
            
            history.append({"tool": tool_name, "input": tool_input, "result": tool_result})
            steps.append({"step": step+1, "tool": tool_name, "input": tool_input, "result": tool_result})
        
        # Max steps reached — generate answer from accumulated context
        context = "\n".join([f"{s['tool']}: {s['result']}" for s in history])
        final = call_llm(f"Based on this research:\n{context}\n\nAnswer: {question}", model="powerful")
        
        return {
            "answer": final["answer"],
            "steps": steps,
            "total_cost_usd": total_cost + final["cost_usd"],
            "total_tokens": total_tokens + final["total_tokens"],
            "num_steps": self.max_steps,
            "technique": "Agentic RAG",
            "model": final["model"],
            "latency": final["latency"],
            "cost_usd": total_cost + final["cost_usd"],
        }


# ── Demo ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    docs = [
        "iPhone 15 costs $999. Released in 2023.",
        "Samsung Galaxy S24 costs $799. Released in 2024.",
        "MacBook Pro M3 costs $1999.",
        "1 USD = 83 INR (approximate).",
    ]
    
    rag = AgenticRAG(docs)
    result = rag.ask("What is the price difference between iPhone 15 and Galaxy S24 in INR?")
    
    print(f"Q: Price difference between iPhone 15 and Galaxy S24 in INR?\n")
    print("Steps taken:")
    for s in result["steps"]:
        print(f"  Step {s['step']}: {s['tool']}({s['input'][:50]}...)")
    print(f"\nA: {result['answer']}")
    print(f"\nTotal steps: {result['num_steps']}")
    print(f"Total cost: ${result['total_cost_usd']:.6f}")
    print(f"Total tokens: {result['total_tokens']}")
