"""🏠 RAG Solutions Hub — launch any demo."""
import streamlit as st

st.set_page_config(page_title="RAG Solutions Hub", page_icon="🤖", layout="wide")
st.title("🤖 RAG Solutions Hub")
st.caption("Hackathon-level RAG demos powered by Groq + FAISS + sentence-transformers")

solutions = [
    ("🏥", "Healthcare Assistant",   "1_healthcare.py",    "Symptom-based diagnosis suggestions from medical documents."),
    ("📚", "Study Assistant",        "2_study_assistant.py","Upload textbooks and ask questions about the content."),
    ("🛒", "E-commerce Support Bot", "3_ecommerce_bot.py", "Product catalog + FAQ answering for customer support."),
    ("⚖️", "Legal Assistant",        "4_legal_assistant.py","Query laws, contracts, and retrieve exact clauses."),
    ("🌾", "Agriculture AI",         "5_agriculture_ai.py","Crop recommendations and farming advice for Indian farmers."),
    ("🚀", "Hybrid Search RAG",      "6_hybrid_search.py", "Vector + BM25 keyword search combined for better retrieval."),
    ("🌿", "Plant Disease Detector", "7_plant_disease.py", "Upload plant image + get disease diagnosis (multimodal)."),
]

cols = st.columns(3)
for i, (icon, name, file, desc) in enumerate(solutions):
    with cols[i % 3]:
        st.markdown(f"### {icon} {name}")
        st.caption(desc)
        st.code(f"streamlit run {file}", language="bash")
        st.divider()

st.info("Run any solution with: `streamlit run <filename>` from the `rag_solutions/` folder.")
