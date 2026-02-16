# D-21 Baseline Findings — Model Selection & Embedding Baseline

> **Project:** FractalRecall — Hierarchical context-aware embedding retrieval
> **Notebook:** D21-baseline.ipynb
> **Run Date:** 2026-02-16
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
| AUTHORITY   | 5     | Hierarchical canon/authority layer questions                |
| TEMPORAL    | 6     | Time-dependent or chronological questions                   |
| EXPLORATORY | 6     | Broad, open-ended survey questions                          |

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
| **nomic-embed-text-v2-moe** | **0.4171**  | 0.6736     | 0.6711     | 0.8165     |
| **BAAI/bge-m3**             | 0.3653      | 0.7083     | 0.6802     | 0.7926     |
| **nomic-embed-text-v1.5**   | 0.3829      | **0.7199** | **0.7062** | **0.8452** |

**Best model per metric:**

- **Precision@5:** v2-moe (0.4171) — best at surfacing relevant documents in the top 5
- **Recall@10:** v1.5 (0.7199) — best coverage in the top 10
- **NDCG@10:** v1.5 (0.7062) — best ranking quality
- **MRR:** v1.5 (0.8452) — fastest time-to-first-relevant-result

No single model dominates across all metrics, though v1.5 leads on 3 of 4 metrics.

### 3.4 Per-Query-Type Breakdown

#### Precision@5

| Query Type  | bge-m3 | v1.5      | v2-moe    |
| ----------- | ------ | --------- | --------- |
| SINGLE_HOP  | 0.312  | 0.305     | **0.403** |
| MULTI_HOP   | 0.594  | 0.619     | **0.627** |
| AUTHORITY   | 0.400  | 0.397     | **0.433** |
| TEMPORAL    | 0.278  | **0.350** | 0.350     |
| EXPLORATORY | 0.217  | **0.233** | 0.217     |

#### Recall@10

| Query Type  | bge-m3    | v1.5      | v2-moe    |
| ----------- | --------- | --------- | --------- |
| SINGLE_HOP  | 0.606     | **0.652** | 0.652     |
| MULTI_HOP   | **0.917** | 0.875     | 0.875     |
| AUTHORITY   | 0.700     | 0.700     | **0.800** |
| TEMPORAL    | **0.917** | 0.917     | 0.667     |
| EXPLORATORY | 0.417     | **0.458** | 0.347     |

#### NDCG@10

| Query Type  | bge-m3    | v1.5      | v2-moe    |
| ----------- | --------- | --------- | --------- |
| SINGLE_HOP  | 0.694     | 0.675     | **0.712** |
| MULTI_HOP   | **0.895** | 0.892     | 0.895     |
| AUTHORITY   | 0.691     | 0.686     | **0.743** |
| TEMPORAL    | 0.675     | **0.779** | 0.595     |
| EXPLORATORY | 0.365     | **0.459** | 0.314     |

#### MRR

| Query Type  | bge-m3    | v1.5      | v2-moe    |
| ----------- | --------- | --------- | --------- |
| SINGLE_HOP  | 0.864     | 0.803     | **0.909** |
| MULTI_HOP   | **1.000** | **1.000** | **1.000** |
| AUTHORITY   | 0.800     | 0.800     | **0.833** |
| TEMPORAL    | 0.667     | **0.867** | 0.750     |
| EXPLORATORY | 0.506     | **0.732** | 0.454     |

---

## 4. Analysis

### 4.1 Model Profiles

**nomic-embed-text-v2-moe** — The Precision Specialist

- Highest Precision@5 overall (0.4171) and on 3/5 query types (SINGLE_HOP, MULTI_HOP, AUTHORITY)
- Smaller 512-token context window forces tighter chunking, which appears to reduce noise in top results
- Trade-off: lowest Recall@10 (0.6736) — the tight window may miss broader contextual signals

**nomic-embed-text-v1.5** — The All-Rounder

- Best Recall@10 (0.7199), NDCG@10 (0.7062), and MRR (0.8452) — leads on 3 of 4 metrics
- Strongest on EXPLORATORY queries (NDCG 0.459, MRR 0.732) where broad understanding matters
- Strongest on TEMPORAL queries (NDCG 0.779, MRR 0.867)

**BAAI/bge-m3** — The Coverage Specialist

- Best MULTI_HOP Recall@10 (0.917) and tied for best TEMPORAL Recall@10 (0.917)
- Fastest embedding throughput (543.7 chunks/sec) — practical for production pipelines
- Weakest MRR overall (0.7926) — finds relevant content but doesn't always rank the best result first

### 4.2 Query Type Patterns

**MULTI_HOP queries perform best** across all models (NDCG 0.89–0.90, MRR 1.000). All three models achieve perfect MRR, meaning the first returned result is always relevant. These queries require information from multiple documents, and the embedding similarity between multi-document topics creates strong retrieval signals.

**EXPLORATORY queries are the weakest** across all models (Precision@5 ≈ 0.22). Broad, open-ended queries like "Survey of post-Glitch medical conditions" produce diffuse similarity signals that don't sharply distinguish relevant from tangential documents. This is the primary target for context enrichment in D-22/D-23.

**TEMPORAL queries reveal model-specific differences.** bge-m3 and v1.5 both achieve 0.917 Recall@10, but v2-moe drops to 0.667 — its smaller context window may lose temporal phrases that provide ordering signals. v1.5 dominates TEMPORAL NDCG (0.779 vs 0.675/0.595).

**AUTHORITY queries favour v2-moe** (Precision@5 = 0.433, NDCG = 0.743). The tighter chunking appears to better isolate authority-layer signals, avoiding dilution by surrounding context.

### 4.3 Chunking Observations

The average chunk size (134–136 tokens) is well below the target for all models, indicating that the corpus's Markdown structure produces naturally-sized sections. The 2-token minimum suggests some documents have empty or near-empty sections that should be filtered or merged in production.

---

## 5. Implications for Enrichment Pipeline

1. **Primary enrichment target: EXPLORATORY queries.** With Precision@5 ≈ 0.25, there is significant headroom for improvement. Context prefixes that inject document-type and entity-identity signals should help the embedding model discriminate relevant survey-level documents.

2. **Model selection for D-22:** v1.5 is the strongest candidate for enrichment experiments due to its:
   - Best ranking quality (NDCG 0.7062, MRR 0.8452) — enrichment should amplify existing ranking strength
   - Best Recall@10 (0.7199) — already leads on coverage
   - 8,192-token context window — room for multi-layer prefixes without truncation

3. **v2-moe's precision advantage warrants monitoring.** If enrichment closes the precision gap on v1.5 (0.3829 vs 0.4171), v2-moe's advantage disappears. If enrichment primarily improves recall and ranking, v2-moe may retain a niche for precision-critical deployments.

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
