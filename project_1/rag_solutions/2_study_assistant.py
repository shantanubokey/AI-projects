"""📚 Study Assistant — upload textbooks and ask questions."""
import streamlit as st
from base_rag import BaseRAG
from utils import clear_cache_button, chat_history, handle_question, show_stats

SYSTEM = """You are a study assistant. Explain concepts clearly and simply.
Use analogies where helpful. If the answer is not in the context, say so."""

def chunk_text(text: str, size: int = 500) -> list[str]:
    return [text[i:i+size] for i in range(0, len(text), size) if text[i:i+size].strip()]

@st.cache_resource
def load_rag():
    return BaseRAG(system_prompt=SYSTEM)

st.set_page_config(page_title="Study Assistant", page_icon="📚")
st.title("📚 Study Assistant")
st.caption("Upload a textbook or paste text, then ask questions.")

rag = load_rag()

with st.sidebar:
    st.subheader("📂 Load Content")
    uploaded = st.file_uploader("Upload .txt file", type=["txt"])
    pasted   = st.text_area("Or paste text here", height=200)

    if st.button("📥 Index Content", use_container_width=True):
        text = ""
        if uploaded:
            text = uploaded.read().decode("utf-8")
        elif pasted:
            text = pasted
        if text:
            chunks = chunk_text(text)
            rag.add_documents(chunks)
            st.success(f"Indexed {len(chunks)} chunks.")
        else:
            st.warning("Please upload a file or paste text first.")

    st.subheader("💡 Example Questions")
    examples = [
        "Explain transformers in simple terms",
        "What is gradient descent?",
        "Summarize the key concepts",
        "What is backpropagation?",
    ]
    for q in examples:
        if st.button(q, use_container_width=True):
            st.session_state.example_q = q

    clear_cache_button(load_rag)

chat_history()
question = st.chat_input("Ask about your study material...") or st.session_state.pop("example_q", None)
if question:
    if not rag.docs:
        st.warning("Please index some content first using the sidebar.")
    else:
        handle_question(rag, question)
