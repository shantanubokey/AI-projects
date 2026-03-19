"""🚀 Hybrid Search RAG — vector search + keyword (BM25) search combined."""
import streamlit as st
from base_rag import BaseRAG
from utils import sidebar_docs, clear_cache_button, chat_history, show_stats
import numpy as np, time
from groq import Groq
import os

# BM25 via rank_bm25 (pip install rank-bm25)
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

DOCS = [
    "The Eiffel Tower is located in Paris, France. It was built in 1889 by Gustave Eiffel.",
    "Python is a high-level programming language known for its readability and simplicity.",
    "RAG stands for Retrieval-Augmented Generation. It combines vector search with LLMs.",
    "FAISS is a library by Meta for efficient similarity search on dense vectors.",
    "Groq provides a free API tier for running open-source LLMs at very high speed.",
    "Machine learning is a subset of AI that enables systems to learn from data.",
    "Neural networks are inspired by the human brain and consist of layers of neurons.",
    "Transformers use self-attention mechanisms and are the backbone of modern LLMs.",
]

SYSTEM = "Answer based on the retrieved context. Be precise and cite relevant details."

@st.cache_resource
def load_rag():
    rag = BaseRAG(system_prompt=SYSTEM)
    rag.add_documents(DOCS)
    return rag

def hybrid_retrieve(rag, query: str, top_k: int = 3) -> list[str]:
    """Combine vector + BM25 scores with equal weight."""
    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    # Vector scores
    q_vec = embedder.encode([query], convert_to_numpy=True).astype("float32")
    distances, indices = rag.index.search(q_vec, len(rag.docs))
    vec_scores = np.zeros(len(rag.docs))
    for rank, idx in enumerate(indices[0]):
        vec_scores[idx] = 1 / (1 + distances[0][rank])  # convert distance to score

    # BM25 scores
    tokenized = [d.lower().split() for d in rag.docs]
    bm25 = BM25Okapi(tokenized)
    bm25_scores = bm25.get_scores(query.lower().split())
    bm25_norm = bm25_scores / (bm25_scores.max() + 1e-9)

    # Combine
    combined = 0.5 * vec_scores + 0.5 * bm25_norm
    top_idx = np.argsort(combined)[::-1][:top_k]
    return [rag.docs[i] for i in top_idx]

st.set_page_config(page_title="Hybrid Search RAG", page_icon="🚀")
st.title("🚀 Hybrid Search RAG")
st.caption("Combines vector similarity + BM25 keyword search for better retrieval.")

if not BM25_AVAILABLE:
    st.warning("Install rank-bm25 for full hybrid search: `pip install rank-bm25`\nFalling back to vector-only.")

rag = load_rag()
sidebar_docs(DOCS)

with st.sidebar:
    st.subheader("💡 Examples")
    for q in ["What is RAG?", "Tell me about FAISS", "Who built the Eiffel Tower?"]:
        if st.button(q, use_container_width=True):
            st.session_state.example_q = q

clear_cache_button(load_rag)

if "messages" not in st.session_state:
    st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

question = st.chat_input("Ask anything...") or st.session_state.pop("example_q", None)
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        with st.spinner("Hybrid searching..."):
            if BM25_AVAILABLE:
                chunks = hybrid_retrieve(rag, question)
            else:
                chunks = rag.retrieve(question)
            context = "\n\n".join(chunks)
            prompt  = f"{SYSTEM}\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
            t0 = time.perf_counter()
            client = Groq(api_key=os.getenv("GROQ_API_KEY", rag.client.api_key))
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
            )
            latency = time.perf_counter() - t0
            usage = resp.usage
            result = {
                "answer": resp.choices[0].message.content,
                "latency": latency,
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "cost_usd": (usage.prompt_tokens * 0.59 + usage.completion_tokens * 0.79) / 1_000_000,
            }
        st.write(result["answer"])
        with st.expander("🔍 Retrieved chunks"):
            for i, c in enumerate(chunks, 1):
                st.markdown(f"**{i}.** {c}")
        show_stats(result)
    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
