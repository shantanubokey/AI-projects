import streamlit as st
from rag_app import RAG

st.set_page_config(page_title="RAG App", page_icon="🔍")
st.title("🔍 RAG Q&A")
st.caption("Ask questions about the loaded documents.")

# ── Sample documents ──────────────────────────────────────────────────────────
DOCS = [
    "The Eiffel Tower is located in Paris, France. It was built in 1889.",
    "Python is a high-level programming language known for its readability.",
    "RAG stands for Retrieval-Augmented Generation. It combines search with LLMs.",
    "FAISS is a library by Meta for efficient similarity search on dense vectors.",
    "Groq provides a free API tier for running open-source LLMs at high speed.",
]

EXAMPLE_QUESTIONS = [
    "What is RAG and how does it work?",
    "Where is the Eiffel Tower located?",
    "What is FAISS used for?",
    "What is Groq?",
    "What makes Python special?",
]

# ── Init RAG (once per session) ───────────────────────────────────────────────
@st.cache_resource
def load_rag():
    rag = RAG()
    rag.add_documents(DOCS)
    return rag

rag = load_rag()

# ── Sidebar: documents + examples ────────────────────────────────────────────
with st.sidebar:
    st.subheader("📄 Loaded Documents")
    for i, doc in enumerate(DOCS, 1):
        st.markdown(f"**{i}.** {doc}")

    st.divider()
    if st.button("🗑 Clear Cache & Reload", use_container_width=True):
        load_rag.clear()
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.subheader("💡 Example Questions")
    for q in EXAMPLE_QUESTIONS:
        if st.button(q, use_container_width=True):
            st.session_state.example_q = q

# ── Chat history ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ── Input ─────────────────────────────────────────────────────────────────────
prefill = st.session_state.pop("example_q", "")
question = st.chat_input("Ask a question about the documents...")

if not question and prefill:
    question = prefill

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = rag.ask(question)
        st.write(result["answer"])

        # ── Stats ──────────────────────────────────────────────────────────
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("⏱ Latency", f"{result['latency']:.2f}s")
        col2.metric("📥 Input tokens", result["prompt_tokens"])
        col3.metric("📤 Output tokens", result["completion_tokens"])
        col4.metric("💰 Cost", f"${result['cost_usd']:.6f}")

    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
