"""⚖️ Legal Document Assistant — query laws and contracts."""
import streamlit as st
from base_rag import BaseRAG
from utils import sidebar_docs, clear_cache_button, chat_history, handle_question

DOCS = [
    "Section 420 IPC: Cheating and dishonestly inducing delivery of property. Punishment: up to 7 years imprisonment.",
    "Section 302 IPC: Punishment for murder. Death or imprisonment for life, and fine.",
    "Right to Information Act 2005: Every citizen has the right to request information from public authorities.",
    "Consumer Protection Act 2019: Consumers can file complaints for defective goods or deficient services within 2 years.",
    "IT Act Section 66A: Sending offensive messages through communication services is punishable.",
    "Contract clause: Either party may terminate this agreement with 30 days written notice.",
    "Contract clause: All disputes shall be resolved through arbitration in Mumbai jurisdiction.",
    "Contract clause: Confidentiality obligations survive termination of this agreement for 2 years.",
    "Labour Law: Employees are entitled to 12 days of earned leave per year.",
    "GDPR Article 17: Right to erasure — individuals can request deletion of their personal data.",
]

EXAMPLES = [
    "What is Section 420 IPC?",
    "How can I file a consumer complaint?",
    "What does the termination clause say?",
    "What are my rights under RTI?",
    "How long does confidentiality last after contract ends?",
]

SYSTEM = """You are a legal assistant AI. Retrieve and explain relevant legal clauses and laws.
Always recommend consulting a qualified lawyer for legal advice. Cite the specific section or clause."""

@st.cache_resource
def load_rag():
    rag = BaseRAG(system_prompt=SYSTEM)
    rag.add_documents(DOCS)
    return rag

st.set_page_config(page_title="Legal Assistant", page_icon="⚖️")
st.title("⚖️ Legal Document Assistant")
st.caption("Query laws, contracts, and legal clauses. Not a substitute for professional legal advice.")

rag = load_rag()
sidebar_docs(DOCS)

with st.sidebar:
    st.subheader("💡 Examples")
    for q in EXAMPLES:
        if st.button(q, use_container_width=True):
            st.session_state.example_q = q

clear_cache_button(load_rag)
chat_history()

question = st.chat_input("Ask about a law or contract clause...") or st.session_state.pop("example_q", None)
if question:
    handle_question(rag, question)
