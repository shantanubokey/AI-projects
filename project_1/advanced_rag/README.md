# 🧠 Advanced RAG Techniques

Production-grade RAG patterns using multiple LLMs for accuracy, with full metrics.

---

## 🚀 Quick Start

```bash
pip install -r requirements.txt
jupyter notebook test_advanced_rag.ipynb
```

---

## 🤖 Multi-LLM Strategy

Every technique uses the right model for the right job:

```
┌─────────────────────────────────────────────────────────────┐
│  Model                      Role              Cost/1M tokens │
├─────────────────────────────────────────────────────────────┤
│  llama-3.1-8b-instant       Routing, scoring  $0.05 / $0.08 │
│  llama-3.3-70b-versatile    Synthesis, QA     $0.59 / $0.79 │
│  llama-3.1-70b-versatile    Complex reasoning $0.59 / $0.79 │
└─────────────────────────────────────────────────────────────┘
```

Rule: use the cheapest model that can do the job.

---

## 📐 Architecture Diagrams

---

### 1️⃣ Re-ranking RAG (`1_reranking.py`)

```
User Query
    │
    ▼
┌─────────────────────┐
│  FAISS Vector Search │  top-20 candidates (broad recall)
└──────────┬──────────┘
           │ 20 candidates
           ▼
┌─────────────────────┐
│  Fast LLM (8B)      │  scores each doc 0-10 for relevance
│  Re-ranker          │
└──────────┬──────────┘
           │ top-3 re-ranked docs
           ▼
┌─────────────────────┐
│  Powerful LLM (70B) │  generates final answer
└──────────┬──────────┘
           │
           ▼
        Answer + Metrics
```

WHY: Vector search retrieves semantically similar docs but not always the most relevant.
Re-ranking adds a precision layer that improves accuracy by 15-30%.

BEST FOR: Legal, medical, technical domains where precision is critical.

---

### 2️⃣ Query Decomposition RAG (`2_query_decomposition.py`)

```
Complex User Query
"Compare Python and JS history and use cases"
    │
    ▼
┌─────────────────────┐
│  Fast LLM (8B)      │  breaks into sub-questions
│  Decomposer         │
└──────────┬──────────┘
           │
    ┌──────┴──────┐──────────────┐
    ▼             ▼              ▼
Sub-Q 1       Sub-Q 2        Sub-Q 3
"Python       "JS history"   "Use cases
 history?"                    comparison?"
    │             │              │
    ▼             ▼              ▼
FAISS         FAISS           FAISS
Search        Search          Search
    │             │              │
    └──────┬───────┘──────────────┘
           │ all contexts merged
           ▼
┌─────────────────────┐
│  Balanced LLM (70B) │  synthesizes all contexts
└──────────┬──────────┘
           ▼
     Comprehensive Answer
```

WHY: Single retrieval misses multi-aspect questions. Each sub-query targets
a different part of the knowledge base.

BEST FOR: Comparative questions, research tasks, multi-part analysis.

---

### 3️⃣ Self-Query RAG (`3_self_query.py`)

```
Natural Language Query
"Cheap laptops under $1000 from 2023"
    │
    ▼
┌─────────────────────┐
│  Fast LLM (8B)      │  extracts structured filters
│  Filter Extractor   │  → {"category": "laptop",
└──────────┬──────────┘     "price": "<1000",
           │                 "year": 2023}
           ▼
┌─────────────────────┐
│  Metadata Filter    │  narrows document pool
│  (pre-filter)       │  1000 docs → 45 docs
└──────────┬──────────┘
           │ filtered subset
           ▼
┌─────────────────────┐
│  FAISS Vector Search │  searches only filtered docs
└──────────┬──────────┘
           │ top-3 relevant
           ▼
┌─────────────────────┐
│  Balanced LLM (70B) │  generates answer
└──────────┬──────────┘
           ▼
     Filtered + Relevant Answer
```

WHY: Vector search ignores structured constraints. Self-query combines
structured filtering with semantic search for precise results.

BEST FOR: E-commerce, research papers, legal docs with rich metadata.

---

### 4️⃣ Corrective RAG (`4_corrective_rag.py`)

```
User Query
    │
    ▼
┌─────────────────────┐
│  FAISS Vector Search │  initial retrieval
└──────────┬──────────┘
           │ top-k docs
           ▼
┌─────────────────────┐
│  Fast LLM (8B)      │  evaluates relevance
│  Quality Evaluator  │
└──────────┬──────────┘
           │
    ┌──────┴──────────────┐
    │                     │
CORRECT              AMBIGUOUS / INCORRECT
    │                     │
    │              ┌──────┴──────────────┐
    │           AMBIGUOUS            INCORRECT
    │              │                     │
    │         Balanced LLM (70B)    Skip retrieval
    │         refines query         use LLM knowledge
    │              │                     │
    │         Re-retrieve                │
    │              │                     │
    └──────┬────────┘─────────────────────┘
           │ best available context
           ▼
┌─────────────────────┐
│  Powerful LLM (70B) │  generates final answer
└──────────┬──────────┘
           ▼
     Grounded Answer (no hallucination)
```

WHY: Standard RAG blindly uses retrieved docs even if irrelevant, causing
hallucination. CRAG evaluates and corrects retrieval quality.

BEST FOR: Production systems, medical/legal domains, open-domain QA.

---

### 5️⃣ Agentic RAG (`5_agentic_rag.py`)

```
User Query
"Price difference between iPhone and Galaxy in INR?"
    │
    ▼
┌─────────────────────────────────────────────────┐
│                 Agent Loop                       │
│                                                  │
│  ┌─────────────────────┐                        │
│  │  Powerful LLM (70B) │ ◄── observation        │
│  │  Agent Brain        │                        │
│  └──────────┬──────────┘                        │
│             │ tool call                          │
│      ┌──────┴──────────────┐                    │
│      ▼                     ▼                    │
│  search("iPhone price") calculate("999-799")    │
│      │                     │                    │
│      ▼                     ▼                    │
│  "$999"               "200 USD"                 │
│      │                     │                    │
│      └──────┬──────────────┘                    │
│             │ observation fed back               │
│             ▼                                   │
│  search("USD to INR rate")                      │
│             │                                   │
│             ▼                                   │
│  "1 USD = 83 INR"                               │
│             │                                   │
│             ▼                                   │
│  calculate("200 * 83")                          │
│             │                                   │
│             ▼                                   │
│  answer("Difference is ₹16,600")               │
└─────────────────────────────────────────────────┘
           │
           ▼
     Multi-step Answer + All Step Metrics
```

WHY: Static RAG can't chain multiple lookups or combine retrieval with
computation. Agentic RAG lets the LLM reason about what to do next.

BEST FOR: Multi-step reasoning, math + retrieval, research assistants.

---

### 6️⃣ RAG Fusion (`6_rag_fusion.py`)

```
User Query
"How do AI models learn?"
    │
    ▼
┌─────────────────────┐
│  Fast LLM (8B)      │  generates N query variations
│  Query Generator    │  → "How does machine learning work?"
└──────────┬──────────┘  → "Training process of neural networks?"
           │             → "What is gradient descent?"
    ┌──────┴──────┬──────────────┬──────────────┐
    ▼             ▼              ▼              ▼
Original      Variation 1   Variation 2   Variation 3
    │             │              │              │
    ▼             ▼              ▼              ▼
FAISS         FAISS           FAISS          FAISS
Ranked        Ranked          Ranked         Ranked
List 1        List 2          List 3         List 4
    │             │              │              │
    └──────┬───────┘──────────────┘──────────────┘
           │
           ▼
┌─────────────────────┐
│  RRF Algorithm      │  score = Σ 1/(60 + rank_i)
│  Reciprocal Rank    │  fuses all ranked lists
│  Fusion             │
└──────────┬──────────┘
           │ top-k fused docs
           ▼
┌─────────────────────┐
│  Powerful LLM (70B) │  generates answer
└──────────┬──────────┘
           ▼
     High-Recall Answer
```

WHY: Single query misses docs using different terminology. Multiple query
variations + RRF fusion consistently improves recall by 10-20%.

BEST FOR: Ambiguous queries, large diverse knowledge bases, search engines.

---

### 7️⃣ Adaptive RAG (`7_adaptive_rag.py`)

```
User Query
    │
    ▼
┌─────────────────────┐
│  Fast LLM (8B)      │  classifies query type
│  Router             │
└──────────┬──────────┘
           │
    ┌──────┴──────────────┬──────────────┬──────────────┐
    ▼                     ▼              ▼              ▼
 SIMPLE               COMPLEX       NO_CONTEXT      CLARIFY
    │                     │              │              │
    ▼                     ▼              ▼              ▼
Fast LLM (8B)      Decompose +    Balanced LLM    Fast LLM (8B)
Single retrieval   Multi-retrieve  (knowledge      generates
+ quick answer     + Powerful LLM  only, no RAG)   clarifying
                   synthesis                       questions
    │                     │              │              │
    └──────┬───────────────┘──────────────┘──────────────┘
           │
           ▼
     Right Answer with Right Model
     (optimized cost + quality)
```

WHY: One-size-fits-all RAG wastes compute on simple queries and under-serves
complex ones. Adaptive routing uses the cheapest model that can do the job.

BEST FOR: Production systems with mixed query types, cost optimization.

---

## 📊 Technique Comparison

| Technique | Latency | Token Usage | Cost | Accuracy | Best For |
|-----------|---------|-------------|------|----------|----------|
| Re-ranking | Medium | High | Medium | ⭐⭐⭐⭐⭐ | Precision-critical |
| Query Decomp | High | Very High | High | ⭐⭐⭐⭐⭐ | Multi-part questions |
| Self-Query | Low | Low | Low | ⭐⭐⭐⭐ | Structured data |
| Corrective RAG | Medium | Medium | Medium | ⭐⭐⭐⭐⭐ | Unknown doc quality |
| Agentic RAG | Very High | Very High | High | ⭐⭐⭐⭐⭐ | Multi-step reasoning |
| RAG Fusion | High | High | High | ⭐⭐⭐⭐ | Ambiguous queries |
| Adaptive RAG | Low-High | Low-High | Low-High | ⭐⭐⭐⭐⭐ | Production systems |

---

## 🏆 Decision Guide

```
Is the query simple and factual?
    YES → Adaptive RAG (SIMPLE route) — cheapest
    NO  ↓

Is the query multi-part or comparative?
    YES → Query Decomposition
    NO  ↓

Does the data have structured metadata?
    YES → Self-Query
    NO  ↓

Is document quality uncertain?
    YES → Corrective RAG
    NO  ↓

Does it require multiple lookups or math?
    YES → Agentic RAG
    NO  ↓

Is the query ambiguous or terminology-heavy?
    YES → RAG Fusion
    NO  → Re-ranking (default best choice)
```

---

## 📁 File Structure

```
advanced_rag/
├── base.py                   # shared LLM client, embedder, FAISS utils
├── 1_reranking.py            # two-stage: vector → LLM re-rank
├── 2_query_decomposition.py  # complex query → sub-queries → synthesize
├── 3_self_query.py           # natural language → metadata filters → search
├── 4_corrective_rag.py       # evaluate retrieval → correct or fallback
├── 5_agentic_rag.py          # LLM agent with search + calculate tools
├── 6_rag_fusion.py           # multi-query + Reciprocal Rank Fusion
├── 7_adaptive_rag.py         # route query to best strategy automatically
├── test_advanced_rag.ipynb   # test all techniques + benchmark charts
└── requirements.txt
```
