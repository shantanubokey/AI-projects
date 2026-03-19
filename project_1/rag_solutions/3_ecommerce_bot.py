"""🛒 E-commerce Support Bot — product catalog + FAQ."""
import streamlit as st
from base_rag import BaseRAG
from utils import sidebar_docs, clear_cache_button, chat_history, handle_question

DOCS = [
    "Return policy: Electronics can be returned within 7 days if unused and in original packaging.",
    "Return policy: Clothing items can be returned within 30 days with tags attached.",
    "Shipping: Standard delivery takes 3-5 business days. Express delivery takes 1-2 days.",
    "Shipping: Free shipping on orders above ₹499. Express shipping costs ₹99.",
    "Payment: We accept UPI, credit/debit cards, net banking, and cash on delivery.",
    "Warranty: All electronics come with a 1-year manufacturer warranty.",
    "Cancellation: Orders can be cancelled within 24 hours of placing. After dispatch, cancellation is not possible.",
    "Product: iPhone 15 - Price ₹79,999. Available in Black, White, Pink. 128GB/256GB storage.",
    "Product: Samsung Galaxy S24 - Price ₹74,999. 6.2 inch display, 50MP camera.",
    "Product: Sony WH-1000XM5 headphones - Price ₹29,990. Noise cancelling, 30hr battery.",
    "Damaged goods: If you receive a damaged product, raise a complaint within 48 hours with photos.",
    "EMI: 0% EMI available on orders above ₹3000 on select credit cards.",
]

EXAMPLES = [
    "What is the return policy for electronics?",
    "How long does shipping take?",
    "Can I pay with UPI?",
    "What is the price of iPhone 15?",
    "I received a damaged product, what do I do?",
]

SYSTEM = """You are a helpful e-commerce customer support assistant.
Answer customer queries based on the product catalog and FAQ. Be concise and friendly."""

@st.cache_resource
def load_rag():
    rag = BaseRAG(system_prompt=SYSTEM)
    rag.add_documents(DOCS)
    return rag

st.set_page_config(page_title="E-commerce Support", page_icon="🛒")
st.title("🛒 E-commerce Support Bot")
st.caption("Ask about products, shipping, returns, and more.")

rag = load_rag()
sidebar_docs(DOCS)

with st.sidebar:
    st.subheader("💡 Examples")
    for q in EXAMPLES:
        if st.button(q, use_container_width=True):
            st.session_state.example_q = q

clear_cache_button(load_rag)
chat_history()

question = st.chat_input("Ask about products or policies...") or st.session_state.pop("example_q", None)
if question:
    handle_question(rag, question)
