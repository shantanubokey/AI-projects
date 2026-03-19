"""Shared Streamlit UI helpers."""
import streamlit as st

def show_stats(result: dict):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("⏱ Latency",       f"{result['latency']:.2f}s")
    c2.metric("📥 Input tokens",  result["prompt_tokens"])
    c3.metric("📤 Output tokens", result["completion_tokens"])
    c4.metric("💰 Cost",          f"${result['cost_usd']:.6f}")

def sidebar_docs(docs: list[str]):
    with st.sidebar:
        st.subheader("📄 Loaded Documents")
        for i, d in enumerate(docs, 1):
            st.markdown(f"**{i}.** {d[:120]}{'...' if len(d)>120 else ''}")

def clear_cache_button(cache_fn):
    with st.sidebar:
        st.divider()
        if st.button("🗑 Clear Cache & Reload", use_container_width=True):
            cache_fn.clear()
            st.session_state.messages = []
            st.rerun()

def chat_history():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

def handle_question(rag, question: str):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = rag.ask(question)
        st.write(result["answer"])
        show_stats(result)
    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
"""
pip install rank-bm25       # for hybrid search
streamlit run rag_solutions/home.py   # hub
streamlit run rag_solutions/1_healthcare.py  # individual



rag_solutions/
├── base_rag.py          # shared RAG engine
├── utils.py             # shared Streamlit helpers
├── home.py              # launcher hub
├── 1_healthcare.py      # 🏥 symptom checker
├── 2_study_assistant.py # 📚 upload + ask textbooks
├── 3_ecommerce_bot.py   # 🛒 product/FAQ bot
├── 4_legal_assistant.py # ⚖️ law & contract queries
├── 5_agriculture_ai.py  # 🌾 Indian crop advisor
├── 6_hybrid_search.py   # 🚀 vector + BM25 hybrid
└── 7_plant_disease.py   # 🌿 image + text multimodal

"""