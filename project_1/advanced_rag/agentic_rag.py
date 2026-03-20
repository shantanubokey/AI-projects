"""Agentic RAG — importable module (mirrors 5_agentic_rag.py)"""
from advanced_rag.base import embed_texts, build_faiss_index, retrieve_top_k, call_llm
import json, re

TOOLS_DESCRIPTION = """You have access to:
- search(query): Search the knowledge base
- calculate(expression): Evaluate math
- answer(text): Return final answer

Respond with JSON: {"tool": "name", "input": "value"}"""

class AgenticRAG:
    def __init__(self, docs: list[str]):
        self.docs = docs
        self.index = build_faiss_index(embed_texts(docs))
        self.max_steps = 5

    def tool_search(self, query: str) -> str:
        q_vec = embed_texts([query])
        return "\n".join(retrieve_top_k(self.index, q_vec, self.docs, k=3))

    def tool_calculate(self, expression: str) -> str:
        try:
            allowed = set("0123456789+-*/()., ")
            if all(c in allowed for c in expression):
                return str(eval(expression))
            return "Invalid expression"
        except:
            return "Calculation error"

    def parse_tool_call(self, response: str) -> tuple[str, str]:
        try:
            data = json.loads(response)
            return data.get("tool", "answer"), data.get("input", response)
        except:
            match = re.search(r'"tool"\s*:\s*"(\w+)".*?"input"\s*:\s*"([^"]+)"', response, re.DOTALL)
            if match:
                return match.group(1), match.group(2)
            return "answer", response

    def ask(self, question: str) -> dict:
        history, total_cost, total_tokens, steps = [], 0, 0, []

        for step in range(self.max_steps):
            context = "\n".join([f"Tool: {s['tool']}\nResult: {s['result']}" for s in history])
            prompt = f"Question: {question}\n\nPrevious steps:\n{context or 'None'}\n\nNext tool (JSON):"
            result = call_llm(prompt, model="powerful", system=TOOLS_DESCRIPTION)
            total_cost += result["cost_usd"]
            total_tokens += result["total_tokens"]

            tool_name, tool_input = self.parse_tool_call(result["answer"])

            if tool_name == "search":
                tool_result = self.tool_search(tool_input)
            elif tool_name == "calculate":
                tool_result = self.tool_calculate(tool_input)
            elif tool_name == "answer":
                steps.append({"step": step+1, "tool": "answer", "input": tool_input, "result": "FINAL"})
                return {"answer": tool_input, "steps": steps, "total_cost_usd": total_cost,
                        "total_tokens": total_tokens, "num_steps": step+1,
                        "technique": "Agentic RAG", "model": result["model"],
                        "latency": result["latency"], "cost_usd": total_cost}
            else:
                tool_result = "Unknown tool"

            history.append({"tool": tool_name, "input": tool_input, "result": tool_result})
            steps.append({"step": step+1, "tool": tool_name, "input": tool_input, "result": tool_result})

        context = "\n".join([f"{s['tool']}: {s['result']}" for s in history])
        final = call_llm(f"Based on:\n{context}\n\nAnswer: {question}", model="powerful")
        return {"answer": final["answer"], "steps": steps, "total_cost_usd": total_cost + final["cost_usd"],
                "total_tokens": total_tokens + final["total_tokens"], "num_steps": self.max_steps,
                "technique": "Agentic RAG", "model": final["model"],
                "latency": final["latency"], "cost_usd": total_cost + final["cost_usd"]}
