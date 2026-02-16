# D-21 Baseline Findings — Model Selection & Embedding Baseline

> **Project:** FractalRecall — Hierarchical context-aware embedding retrieval
> **Notebook:** D21-baseline.ipynb
> **Run Date:** 2026-02-15
> **Hardware:** Google Colab — A100 GPU, High-RAM
> **Metrics:** Precision@5, Recall@10, NDCG@10, MRR

---

## 1. Objective

Establish baseline retrieval performance with **no context enrichment** (standard RAG), against which subsequent experiments (D-22 single-layer, D-23 multi-layer, D-24 full 8-layer) can be measured.

Three embedding models are compared to select the best foundation for the enrichment pipeline.

---

## 2. Experimental Setup

### 2.1 Corpus

- **77 Markdown documents** from the Aethelgard worldbuilding test corpus
- Three document prefix types: `000-codex_` (codex entries), `db02-wb_` (worldbook entries), `db03-dc_` (data captures)
- YAML frontmatter metadata including entity type, authority layer, canon status, cross-references, and temporal markers

### 2.2 Models Under Test

| Parameter               | nomic-embed-text-v2-moe          | nomic-embed-text-v1.5          | BAAI/bge-m3   |
| ----------------------- | -------------------------------- | ------------------------------ | ------------- |
| **Model ID**            | nomic-ai/nomic-embed-text-v2-moe | nomic-ai/nomic-embed-text-v1.5 | BAAI/bge-m3   |
| **Context Window**      | 512 tokens                       | 8,192 tokens                   | 8,192 tokens  |
| **Embedding Dimension** | 768                              | 768                            | 1,024         |
| **Loader**              | sentence_transformers            | sentence_transformers          | FlagEmbedding |
| **Document Prefix**     | `search_document`                | `search_document`              | _(none)_      |

### 2.3 Chunking Strategy

Hybrid Semantic + Fixed-Window (sourced from R-02):

1. Split by Markdown headers (semantic boundaries)
2. If section ≤ `max_chunk_tokens` → keep as one chunk
3. If section > `max_chunk_tokens` → apply sliding window with overlap

| Parameter           | v2-moe | v1.5  | bge-m3 |
| ------------------- | ------ | ----- | ------ |
| Target Chunk Tokens | 350    | 600   | 600    |
| Max Chunk Tokens    | 450    | 1,024 | 1,024  |
| Min Chunk Tokens    | 128    | 128   | 128    |
| Overlap Tokens      | 96     | 150   | 150    |

### 2.4 Ground-Truth Query Set

36 queries across 5 query types:

| Query Type  | Count | Description                                                 |
| ----------- | ----- | ----------------------------------------------------------- |
| SINGLE_HOP  | 11    | Direct fact retrieval from one document                     |
| MULTI_HOP   | 8     | Requires synthesizing information across multiple documents |
| AUTHORITY   | 6     | Hierarchical canon/authority layer questions                |
| TEMPORAL    | 6     | Time-dependent or chronological questions                   |
| EXPLORATORY | 5     | Broad, open-ended survey questions                          |

---

## 3. Results

### 3.1 Chunking

| Model                   | Chunks | Avg Tokens | Min | Max   |
| ----------------------- | ------ | ---------- | --- | ----- |
| nomic-embed-text-v2-moe | 1,257  | 134.0      | 2   | 449   |
| nomic-embed-text-v1.5   | 1,215  | 135.7      | 2   | 1,023 |
| BAAI/bge-m3             | 1,215  | 135.7      | 2   | 1,023 |

**Total chunks across all models:** 3,687

v2-moe produces 3.5% more chunks due to its tighter 450-token max window; however, average chunk size is nearly identical across models because most sections fall well below both thresholds.

### 3.2 Embedding Throughput

| Model                   | Time (s) | Throughput (chunks/sec) |
| ----------------------- | -------- | ----------------------- |
| nomic-embed-text-v2-moe | 8.18     | 153.6                   |
| nomic-embed-text-v1.5   | 5.80     | 209.4                   |
| BAAI/bge-m3             | 2.23     | 543.7                   |

bge-m3 is ~3.5× faster than v2-moe, despite producing 1024-dim embeddings (vs. 768-dim). FP16 acceleration on A100 favours the FlagEmbedding loader.

### 3.3 Overall Metrics (Mean Across All 36 Queries)

| Model                       | Precision@5 | Recall@10  | NDCG@10    | MRR        |
| --------------------------- | ----------- | ---------- | ---------- | ---------- |
| **nomic-embed-text-v2-moe** | **0.4611**  | 0.7083     | 0.6834     | 0.8166     |
| **BAAI/bge-m3**             | 0.4171      | **0.7454** | 0.6973     | 0.7917     |
| **nomic-embed-text-v1.5**   | 0.3894      | 0.7384     | **0.7315** | **0.8611** |

**Best model per metric:**

- **Precision@5:** v2-moe (0.4611) — best at surfacing relevant documents in the top 5
- **Recall@10:** bge-m3 (0.7454) — best coverage in the top 10
- **NDCG@10:** v1.5 (0.7315) — best ranking quality
- **MRR:** v1.5 (0.8611) — fastest time-to-first-relevant-result

No single model dominates across all metrics.

### 3.4 Per-Query-Type Breakdown

#### Precision@5

| Query Type  | bge-m3    | v1.5      | v2-moe    |
| ----------- | --------- | --------- | --------- |
| AUTHORITY   | 0.450     | 0.350     | **0.553** |
| EXPLORATORY | 0.250     | **0.267** | 0.258     |
| MULTI_HOP   | **0.650** | 0.556     | 0.640     |
| SINGLE_HOP  | 0.355     | 0.365     | **0.446** |
| TEMPORAL    | 0.361     | 0.367     | **0.378** |

#### Recall@10

| Query Type  | bge-m3    | v1.5      | v2-moe    |
| ----------- | --------- | --------- | --------- |
| AUTHORITY   | 0.700     | 0.700     | **0.800** |
| EXPLORATORY | **0.500** | 0.486     | 0.389     |
| MULTI_HOP   | **0.917** | 0.875     | 0.833     |
| SINGLE_HOP  | 0.682     | 0.697     | **0.727** |
| TEMPORAL    | **0.917** | **0.917** | 0.750     |

#### NDCG@10

| Query Type  | bge-m3 | v1.5      | v2-moe    |
| ----------- | ------ | --------- | --------- |
| AUTHORITY   | 0.709  | 0.705     | **0.738** |
| EXPLORATORY | 0.400  | **0.490** | 0.357     |
| MULTI_HOP   | 0.894  | **0.898** | 0.859     |
| SINGLE_HOP  | 0.706  | **0.736** | 0.727     |
| TEMPORAL    | 0.706  | **0.767** | 0.650     |

#### MRR

| Query Type  | bge-m3    | v1.5      | v2-moe    |
| ----------- | --------- | --------- | --------- |
| AUTHORITY   | 0.800     | 0.800     | **0.822** |
| EXPLORATORY | 0.528     | **0.750** | 0.557     |
| MULTI_HOP   | **1.000** | **1.000** | **1.000** |
| SINGLE_HOP  | 0.833     | **0.894** | 0.849     |
| TEMPORAL    | 0.694     | **0.778** | 0.769     |

---

## 4. Analysis

### 4.1 Model Profiles

**nomic-embed-text-v2-moe** — The Precision Specialist

- Highest Precision@5 overall (0.4611) and on 3/5 query types (AUTHORITY, SINGLE_HOP, TEMPORAL)
- Smaller 512-token context window forces tighter chunking, which appears to reduce noise in top results
- Trade-off: lowest Recall@10 (0.7083) — the tight window may miss broader contextual signals

**nomic-embed-text-v1.5** — The All-Rounder

- Best NDCG@10 (0.7315) and MRR (0.8611) — consistently ranks relevant results higher
- Strongest on EXPLORATORY queries (NDCG 0.490, MRR 0.750) where broad understanding matters
- Competitive Recall@10 (0.7384) but weakest Precision@5 (0.3894)

**BAAI/bge-m3** — The Coverage Champion

- Highest Recall@10 (0.7454) — best at finding all relevant documents
- Fastest embedding throughput (543.7 chunks/sec) — practical for production pipelines
- Weakest MRR (0.7917) — finds everything but doesn't always rank the best result first

### 4.2 Query Type Patterns

**MULTI_HOP queries perform best** across all models (NDCG 0.86–0.90, MRR 1.000). All three models achieve perfect MRR, meaning the first returned result is always relevant. These queries require information from multiple documents, and the embedding similarity between multi-document topics creates strong retrieval signals.

**EXPLORATORY queries are the weakest** across all models (Precision@5 ≈ 0.25). Broad, open-ended queries like "Survey of post-Glitch medical conditions" produce diffuse similarity signals that don't sharply distinguish relevant from tangential documents. This is the primary target for context enrichment in D-22/D-23.

**TEMPORAL queries reveal model-specific differences.** bge-m3 and v1.5 both achieve 0.917 Recall@10, but v2-moe drops to 0.750 — its smaller context window may lose temporal phrases that provide ordering signals.

**AUTHORITY queries favour v2-moe** (Precision@5 = 0.553 vs. 0.35–0.45). The tighter chunking appears to better isolate authority-layer signals, avoiding dilution by surrounding context.

### 4.3 Chunking Observations

The average chunk size (134–136 tokens) is well below the target for all models, indicating that the corpus's Markdown structure produces naturally-sized sections. The 2-token minimum suggests some documents have empty or near-empty sections that should be filtered or merged in production.

---

## 5. Implications for Enrichment Pipeline

1. **Primary enrichment target: EXPLORATORY queries.** With Precision@5 ≈ 0.25, there is significant headroom for improvement. Context prefixes that inject document-type and entity-identity signals should help the embedding model discriminate relevant survey-level documents.

2. **Model selection for D-22:** v1.5 is the strongest candidate for enrichment experiments due to its:
   - Best ranking quality (NDCG, MRR) — enrichment should amplify existing ranking strength
   - 8,192-token context window — room for multi-layer prefixes without truncation
   - Competitive recall — enrichment may narrow this gap with v2-moe's precision advantage

3. **v2-moe's precision advantage warrants monitoring.** If enrichment closes the precision gap on v1.5, v2-moe's advantage disappears. If enrichment primarily improves recall and ranking, v2-moe may retain a niche for precision-critical deployments.

4. **Minimum chunk size filter needed.** The 2-token minimum chunks provide no semantic signal and should be merged with adjacent chunks or dropped in future iterations.

---

## 6. Exported Artefacts

| File                                 | Contents                                                         |
| ------------------------------------ | ---------------------------------------------------------------- |
| `d21-output/d21_results.csv`         | 108 rows — per-query, per-model metrics (36 queries × 3 models)  |
| `d21-output/d21_chunk_inventory.csv` | 3,687 rows — full chunk inventory with token counts and metadata |
| `d21-output/d21_model_summary.csv`   | 3 rows — aggregate model performance summary                     |

---

## 7. Next Steps

| Notebook | Experiment                                                        | Expected Impact                                            |
| -------- | ----------------------------------------------------------------- | ---------------------------------------------------------- |
| **D-22** | Single-layer enrichment (document type + entity name prefix)      | Improve EXPLORATORY precision; minor NDCG gains            |
| **D-23** | Multi-layer enrichment (type + authority + temporal + relational) | Broader metric improvements; test prefix budget trade-offs |
| **D-24** | Full 8-layer enrichment (all context layers)                      | Maximum enrichment; quantify diminishing returns           |
