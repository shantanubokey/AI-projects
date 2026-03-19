"""🌿 Multimodal RAG — upload plant image + get disease diagnosis."""
import streamlit as st
from base_rag import BaseRAG
from utils import clear_cache_button, chat_history, show_stats
import base64, time, os
from groq import Groq

# Text knowledge base for RAG
DOCS = [
    "Leaf blight: Brown or tan spots with yellow halos on leaves. Caused by fungal infection. Treat with copper-based fungicide.",
    "Powdery mildew: White powdery coating on leaves. Caused by fungal spores. Treat with neem oil or sulfur spray.",
    "Root rot: Yellowing leaves, wilting despite watering. Caused by overwatering and poor drainage. Reduce watering, improve drainage.",
    "Aphid infestation: Tiny green/black insects on stems and leaves. Causes curling leaves. Spray neem oil or insecticidal soap.",
    "Mosaic virus: Yellow-green mottled pattern on leaves. Spread by insects. Remove infected plants, control aphids.",
    "Rust disease: Orange-brown pustules on leaf undersides. Fungal disease. Apply fungicide, remove infected leaves.",
    "Nutrient deficiency (Nitrogen): Yellowing of older leaves first. Apply nitrogen-rich fertilizer.",
    "Nutrient deficiency (Iron): Yellowing between leaf veins (chlorosis). Apply iron chelate or acidify soil.",
    "Healthy plant indicators: Deep green leaves, firm stems, no spots or discoloration.",
]

SYSTEM = """You are a plant disease expert. Analyze the plant image and context to:
1. Identify the disease or condition
2. Explain the cause
3. Provide treatment steps
4. Give prevention tips"""

@st.cache_resource
def load_rag():
    rag = BaseRAG(system_prompt=SYSTEM)
    rag.add_documents(DOCS)
    return rag

def analyze_with_vision(image_bytes: bytes, question: str, context: str) -> dict:
    """Use Groq vision model for image + text analysis."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY", "your_groq_api_key_here"))
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    prompt = f"""{SYSTEM}

Knowledge base context:
{context}

User question: {question}

Analyze the plant image and provide diagnosis."""

    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",  # vision model on Groq
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ],
        }],
    )
    latency = time.perf_counter() - t0
    usage = resp.usage
    return {
        "answer": resp.choices[0].message.content,
        "latency": latency,
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
        "cost_usd": (usage.prompt_tokens * 0.59 + usage.completion_tokens * 0.79) / 1_000_000,
    }

st.set_page_config(page_title="Plant Disease AI", page_icon="🌿")
st.title("🌿 Plant Disease Detector")
st.caption("Upload a plant image to get disease diagnosis and treatment advice.")

rag = load_rag()

with st.sidebar:
    st.subheader("📄 Knowledge Base")
    for i, d in enumerate(DOCS, 1):
        st.markdown(f"**{i}.** {d[:100]}...")
    st.subheader("💡 Example Questions")
    examples = [
        "What disease does this plant have?",
        "How do I treat this condition?",
        "Is this plant healthy?",
        "What caused these spots on the leaves?",
    ]
    for q in examples:
        if st.button(q, use_container_width=True):
            st.session_state.example_q = q
    clear_cache_button(load_rag)

uploaded_img = st.file_uploader("📷 Upload plant image", type=["jpg", "jpeg", "png"])
if uploaded_img:
    st.image(uploaded_img, caption="Uploaded plant", use_container_width=True)

question = st.chat_input("Ask about the plant...") or st.session_state.pop("example_q", None)

if question:
    if not uploaded_img:
        st.warning("Please upload a plant image first.")
    else:
        with st.spinner("Analyzing plant..."):
            context = "\n\n".join(rag.retrieve(question))
            result  = analyze_with_vision(uploaded_img.read(), question, context)
        st.subheader("🔬 Diagnosis")
        st.write(result["answer"])
        show_stats(result)
