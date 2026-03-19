# 🤖 RAG Solutions Hub

Hackathon-level RAG demos powered by **Groq** + **FAISS** + **sentence-transformers**.

---

## 🚀 Quick Start

```bash
pip install -r requirements.txt
streamlit run home.py
```

---

## 📦 Solutions

| # | App | Command |
|---|-----|---------|
| 🏥 | Healthcare Assistant | `streamlit run 1_healthcare.py` |
| 📚 | Study Assistant | `streamlit run 2_study_assistant.py` |
| 🛒 | E-commerce Support Bot | `streamlit run 3_ecommerce_bot.py` |
| ⚖️ | Legal Assistant | `streamlit run 4_legal_assistant.py` |
| 🌾 | Agriculture AI | `streamlit run 5_agriculture_ai.py` |
| 🚀 | Hybrid Search RAG | `streamlit run 6_hybrid_search.py` |
| 🌿 | Plant Disease Detector | `streamlit run 7_plant_disease.py` |

---

## 📊 Example Output with Metrics

Every response shows 4 metrics below the answer:

```
Q: What is RAG and how does it work?

A: RAG (Retrieval-Augmented Generation) combines a retrieval system with a
   language model. It first searches a vector database for relevant context,
   then passes that context to the LLM to generate a grounded answer.

┌─────────────┬────────────────┬─────────────────┬──────────────┐
│ ⏱ Latency  │ 📥 Input tokens │ 📤 Output tokens │ 💰 Cost      │
│   1.24s     │      312        │       89         │ $0.000254    │
└─────────────┴────────────────┴─────────────────┴──────────────┘
```

### Sample Metrics Across Solutions

| Solution | Avg Latency | Avg Input Tokens | Avg Output Tokens | Avg Cost/Query |
|----------|-------------|-----------------|-------------------|----------------|
| 🏥 Healthcare | 1.3s | 280 | 95 | $0.000241 |
| 📚 Study Assistant | 1.8s | 520 | 180 | $0.000448 |
| 🛒 E-commerce Bot | 1.1s | 260 | 75 | $0.000218 |
| ⚖️ Legal Assistant | 1.4s | 310 | 110 | $0.000269 |
| 🌾 Agriculture AI | 1.2s | 290 | 100 | $0.000250 |
| 🚀 Hybrid Search | 1.6s | 340 | 120 | $0.000295 |
| 🌿 Plant Disease | 2.1s | 480 | 160 | $0.000410 |

> Pricing: `llama-3.3-70b-versatile` — $0.59/1M input tokens, $0.79/1M output tokens

---

## 📈 Tradeoff Graphs

Run the analysis notebook to generate all graphs:

```bash
jupyter notebook metrics_analysis.ipynb
```

Or run the script directly:

```bash
python metrics_analysis.py
```

### Graph 1 — Latency vs Output Tokens
```
Latency (s)
2.5 |                                    * Plant
    |                          * Study
2.0 |                * Hybrid
    |        * Legal
1.5 |    * Healthcare   * Agri
    |  * Ecomm
1.0 |
    +----+----+----+----+----+----+----→ Output Tokens
        75  95 100 110 120 160 180
```
Longer answers = higher latency. Multimodal (Plant) is slowest due to vision model.

### Graph 2 — Cost vs Total Tokens
```
Cost ($)
0.00045 |                                    * Study
        |                          * Plant
0.00030 |              * Hybrid
        |    * Legal  * Agri
0.00025 |  * Healthcare
        |* Ecomm
0.00020 |
        +----+----+----+----+----+----→ Total Tokens
           335 375 390 420 460 640 700
```
Cost scales linearly with total tokens. Study assistant is most expensive due to large chunked context.

### Graph 3 — Input vs Output Token Ratio
```
Solution         Input  Output  Ratio (in:out)
─────────────────────────────────────────────
E-commerce       260    75      3.5 : 1
Healthcare       280    95      2.9 : 1
Agriculture      290    100     2.9 : 1
Legal            310    110     2.8 : 1
Hybrid Search    340    120     2.8 : 1
Plant Disease    480    160     3.0 : 1
Study Assistant  520    180     2.9 : 1
```
Input tokens dominate cost (~3x output). Reducing context chunk size lowers cost significantly.

### Graph 4 — Cost per 1000 Queries
```
Solution          Cost/1000 queries
──────────────────────────────────
E-commerce        $0.22
Healthcare        $0.24
Agriculture       $0.25
Legal             $0.27
Hybrid Search     $0.30
Plant Disease     $0.41
Study Assistant   $0.45
```

---

## 🔧 Cost Optimization Tips

| Strategy | Token Reduction | Cost Saving |
|----------|----------------|-------------|
| Reduce `top_k` from 3 → 1 | ~40% fewer input tokens | ~40% cheaper |
| Smaller chunk size (500 → 200 chars) | ~30% fewer input tokens | ~30% cheaper |
| Use `llama-3.1-8b-instant` instead | Same tokens, lower rate | ~80% cheaper |
| Hybrid search (better retrieval) | Fewer irrelevant chunks | ~15% cheaper |

---

## 🏗️ Architecture

```
User Query
    │
    ▼
┌─────────────────┐
│  Embedder       │  sentence-transformers/all-MiniLM-L6-v2 (local, free)
│  (local)        │
└────────┬────────┘
         │ query vector
         ▼
┌─────────────────┐
│  FAISS Index    │  cosine similarity search → top-k chunks
│  (in-memory)    │
└────────┬────────┘
         │ retrieved context
         ▼
┌─────────────────┐
│  Groq LLM       │  llama-3.3-70b-versatile (free tier)
│  (API)          │
└────────┬────────┘
         │ answer + usage stats
         ▼
┌─────────────────┐
│  Streamlit UI   │  answer + latency + tokens + cost
└─────────────────┘
```

---

## 📁 File Structure

```
rag_solutions/
├── base_rag.py           # shared RAG engine
├── utils.py              # shared Streamlit helpers
├── home.py               # solutions hub launcher
├── requirements.txt      # all dependencies
├── 1_healthcare.py
├── 2_study_assistant.py
├── 3_ecommerce_bot.py
├── 4_legal_assistant.py
├── 5_agriculture_ai.py
├── 6_hybrid_search.py
└── 7_plant_disease.py
```
