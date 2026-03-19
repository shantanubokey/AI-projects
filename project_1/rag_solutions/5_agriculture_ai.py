"""🌾 Agriculture AI — crop recommendations for Indian farmers."""
import streamlit as st
from base_rag import BaseRAG
from utils import sidebar_docs, clear_cache_button, chat_history, handle_question

DOCS = [
    "Wheat grows best in cool dry climate. Ideal temperature: 10-25°C. Sow in October-November in North India.",
    "Rice requires hot and humid climate with heavy rainfall (150-200cm). Best season: Kharif (June-November).",
    "Cotton grows in black soil (Deccan plateau). Requires 6-8 months warm weather. Kharif crop.",
    "Sugarcane needs tropical climate, 21-27°C, and high rainfall. Grows well in UP, Maharashtra, Karnataka.",
    "Tomato grows in 20-27°C. Needs well-drained loamy soil. Can be grown year-round in South India.",
    "Onion prefers cool dry weather during bulb formation. Best grown in Maharashtra, Karnataka, MP.",
    "Soybean is a Kharif crop. Grows in 26-30°C. Requires moderate rainfall. MP is top producer.",
    "Mustard is a Rabi crop. Grows in 10-25°C. Requires dry cool climate. Rajasthan, UP are top states.",
    "Pest control: Neem-based pesticides are organic and effective against aphids and whiteflies.",
    "Soil health: Adding organic compost improves soil fertility and water retention.",
    "Drip irrigation saves 40-60% water compared to flood irrigation. Best for vegetables and fruits.",
    "PM-KISAN scheme provides ₹6000/year to eligible farmers in 3 installments.",
]

EXAMPLES = [
    "Best crop for black soil in Maharashtra this season?",
    "What crop should I grow in October in North India?",
    "How to control aphids organically?",
    "Which crops need less water?",
    "Tell me about PM-KISAN scheme",
]

SYSTEM = """You are an agriculture AI assistant helping Indian farmers.
Give practical, actionable advice about crops, weather, soil, and farming schemes.
Consider Indian seasons: Kharif (June-Nov), Rabi (Nov-Apr), Zaid (Apr-Jun)."""

@st.cache_resource
def load_rag():
    rag = BaseRAG(system_prompt=SYSTEM)
    rag.add_documents(DOCS)
    return rag

st.set_page_config(page_title="Agriculture AI", page_icon="🌾")
st.title("🌾 Agriculture AI")
st.caption("Smart crop recommendations and farming advice for Indian farmers.")

rag = load_rag()
sidebar_docs(DOCS)

with st.sidebar:
    st.subheader("💡 Examples")
    for q in EXAMPLES:
        if st.button(q, use_container_width=True):
            st.session_state.example_q = q

clear_cache_button(load_rag)
chat_history()

question = st.chat_input("Ask about crops, soil, weather, or schemes...") or st.session_state.pop("example_q", None)
if question:
    handle_question(rag, question)
