"""🏥 Healthcare Assistant — context-based diagnosis suggestions."""
import streamlit as st
from base_rag import BaseRAG
from utils import sidebar_docs, clear_cache_button, chat_history, handle_question

DOCS = [
    "Diabetes symptoms include frequent urination, excessive thirst, and unexplained weight loss.",
    "Hypertension (high blood pressure) often has no symptoms but can cause headaches and dizziness.",
    "Asthma causes wheezing, shortness of breath, chest tightness, and coughing.",
    "COVID-19 symptoms: fever, dry cough, fatigue, loss of taste or smell.",
    "Malaria symptoms include fever, chills, headache, nausea, and vomiting.",
    "Tuberculosis (TB) causes persistent cough, weight loss, night sweats, and fever.",
    "Anemia symptoms: fatigue, weakness, pale skin, shortness of breath.",
    "Dengue fever: sudden high fever, severe headache, pain behind eyes, joint pain.",
]

EXAMPLES = [
    "I have frequent urination and excessive thirst. What could it be?",
    "What are the symptoms of malaria?",
    "Patient has fever, chills and headache. Possible diagnosis?",
    "Difference between dengue and malaria symptoms?",
]

SYSTEM = """You are a medical assistant AI. Based on the provided medical context, 
suggest possible conditions and recommend consulting a doctor. 
Always add a disclaimer that this is not professional medical advice."""

@st.cache_resource
def load_rag():
    rag = BaseRAG(system_prompt=SYSTEM)
    rag.add_documents(DOCS)
    return rag

st.set_page_config(page_title="Healthcare Assistant", page_icon="🏥")
st.title("🏥 Healthcare Assistant")
st.caption("Describe symptoms to get context-based suggestions. Not a substitute for professional advice.")

rag = load_rag()
sidebar_docs(DOCS)

with st.sidebar:
    st.subheader("💡 Examples")
    for q in EXAMPLES:
        if st.button(q, use_container_width=True):
            st.session_state.example_q = q

clear_cache_button(load_rag)
chat_history()

question = st.chat_input("Describe symptoms...") or st.session_state.pop("example_q", None)
if question:
    handle_question(rag, question)
