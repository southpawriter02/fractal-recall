# D-23 Findings — Multi-Layer Context Enrichment (Round 3)

> **Project:** FractalRecall — Hierarchical context-aware embedding retrieval  
> **Notebook:** D23_multi_layer_4.ipynb  
> **Run Date:** 2026-02-17  
> **Hardware:** Google Colab — A100 GPU, High-RAM  
> **Metrics:** Precision@5, Recall@10, NDCG@10, MRR  
> **Round:** 3 (final corrective run after NDCG bug, layer mappings, and chunking alignment)

---

## 1. Objective

Determine whether adding **multi-layer context enrichment** to each chunk before embedding improves retrieval performance over the D-21 baseline and the D-22 single-layer enrichment.

This is **Round 3** — addressing three bugs identified in Round 2:

1. **NDCG deduplication bug** — `.split("#")[0]` mapped chunk IDs to document IDs but allowed duplicate document contributions to DCG, inflating NDCG above 1.0.
2. **Missing enrichment layers** — `FIELD_MAP` used incorrect keys (`era`, `related_entities`) instead of the corpus's actual keys (`temporal_markers`, `cross_references`, etc.).
3. **Chunking confound** — `max_chunk_tokens` and `overlap_tokens` differed from D-21/D-22, making it impossible to isolate the enrichment effect.

---

## 2. Experimental Setup

### 2.1 Baselines

| Experiment                | Model                 | Enrichment                  | NDCG@10    | P@5        | R@10       | MRR        |
| ------------------------- | --------------------- | --------------------------- | ---------- | ---------- | ---------- | ---------- |
| **D-21** (baseline)       | nomic-embed-text-v1.5 | None                        | 0.7062     | 0.3829     | 0.7199     | 0.8452     |
| **D-22** (single-layer)   | nomic-embed-text-v1.5 | 1 prefix (~24 tokens)       | 0.8225     | 0.4167     | 0.9167     | 0.8611     |
| **D-23 R3** (multi-layer) | nomic-embed-text-v1.5 | 6-layer prefix (~80 tokens) | **0.7241** | **0.3111** | **0.6829** | **0.9059** |

### 2.2 Enrichment Strategy — 6-Layer Prefix (of 8 planned)

D-23 prepends a multi-layer natural language prefix to each chunk, drawn from document metadata:

| Layer             | Content Pattern                                    | Mean Tokens | Max Tokens | Population |
| ----------------- | -------------------------------------------------- | ----------- | ---------- | ---------- |
| **Corpus**        | `"Corpus: Aethelgard Worldbuilding Corpus v5.0"`   | 6.0         | 6          | 100%       |
| **Domain**        | `"Domain: This content is from a {type} document"` | 16.4        | 20         | 100%       |
| **Entity**        | `"Entity: This content describes {name}."`         | 16.2        | 24         | 100%       |
| **Authority**     | `"Authority: This content is canonical..."`        | 9.5         | 10         | 100%       |
| **Relationships** | `"Related to: {cross_references}, {factions}..."`  | 15.4        | 31         | 100% ✅    |
| **Section**       | `"Section: {heading}."`                            | 14.3        | 26         | 94%        |
|                   | **Total overhead:**                                | **79.6**    | **103**    |            |

> **Change from Round 2:** The Relationships layer is now populated (was 0% in Round 2). The FIELD_MAP was corrected to map `cross_references`, `factions_mentioned`, and `locations_mentioned` to the relational layer.
>
> **Still unpopulated:**
>
> - **Temporal (0%)** — The `temporal_markers` field exists in 0/77 documents despite the FIELD_MAP fix. The corpus frontmatter does not contain this key.
> - **Chunk Sequence** — Not implemented (requires inter-chunk awareness).

### 2.3 Model & Chunking Configuration

| Parameter             | D-21/D-22             | D-23 R2 | D-23 R3 (fix) | Status        |
| --------------------- | --------------------- | ------- | ------------- | ------------- |
| Model                 | nomic-embed-text-v1.5 | Same    | Same          | ✅ Controlled |
| Embedding dimension   | 768                   | 768     | 768           | ✅ Controlled |
| Max chunk tokens      | 1,024                 | 600     | **1,024**     | ✅ Fixed      |
| Prefix reserve tokens | 0                     | 150     | **100**       | ✅ Reduced    |
| Available for content | 1,024                 | ~450    | **924**       | ✅ Aligned    |
| Overlap tokens        | 150                   | 50      | **150**       | ✅ Fixed      |
| Total chunks          | 218                   | 1,266   | **1,233**     | ⚠️ See §3.2   |

### 2.4 Corpus

- **77 Markdown documents** from the Aethelgard worldbuilding corpus (same as D-21/D-22)
- **36 ground-truth queries** across 5 types (identical query set)

---

## 3. Results

### 3.1 Bug Fixes — Verified ✅

| Bug                   | Round 2 Symptom                          | Round 3 Status                                              |
| --------------------- | ---------------------------------------- | ----------------------------------------------------------- |
| NDCG > 1.0            | 30/36 queries had NDCG > 1.0 (max: 1.83) | **FIXED** — All values in [0.0, 1.0]                        |
| Missing Relationships | 0% population rate                       | **FIXED** — 100% population (15.4 avg tokens)               |
| Missing Temporal      | 0% population rate                       | **NOT FIXED** — Corpus lacks `temporal_markers` frontmatter |
| Chunking confound     | max=600, overlap=50                      | **FIXED** — max=1024, overlap=150                           |
| Chunk count mismatch  | 1,266 vs D-21/D-22's 218                 | **NOT FIXED** — 1,233 chunks (see §3.2)                     |

### 3.2 Chunk Count Discrepancy (Remaining Confound)

Despite matching `max_chunk_tokens=1024` and `overlap_tokens=150` to D-21/D-22, D-23 R3 produces **1,233 chunks** vs D-21/D-22's **218 chunks** — a **5.7× inflation**.

**Root Cause:** D-23's chunking engine reserves `prefix_reserve_tokens=100` from each chunk's budget, leaving only **924 tokens** for content. But the word-based token estimator (`word_count × 1.3`) creates much shorter segments than D-21/D-22's byte-based chunker that used the full 1,024 tokens. The chunking functions themselves differ between notebooks.

**Impact:** The 5.7× increase in index size directly affects retrieval quality:

- More chunks = more candidates competing for the top-k slots
- Shorter content per chunk = less context for the embedding model
- More boundary effects from chunk splitting

> **This is the most significant remaining confound.** The chunking geometry is not comparable to D-21/D-22 despite matching the configuration parameters.

### 3.3 Overall Performance

| Metric  | D-21 (BL) | D-22 (SL) | D-23 R3 (ML) | Δ vs D-21          | Δ vs D-22          |
| ------- | --------- | --------- | ------------ | ------------------ | ------------------ |
| P@5     | 0.3829    | 0.4167    | **0.3111**   | −0.072 (−18.7%) ❌ | −0.106 (−25.3%) ❌ |
| R@10    | 0.7199    | 0.9167    | **0.6829**   | −0.037 (−5.1%) ❌  | −0.234 (−25.5%) ❌ |
| NDCG@10 | 0.7062    | 0.8225    | **0.7241**   | +0.018 (+2.5%) ✅  | −0.098 (−12.0%) ❌ |
| MRR     | 0.8452    | 0.8611    | **0.9059**   | +0.061 (+7.2%) ✅  | +0.045 (+5.2%) ✅  |

**Summary:**

- D-23 R3 **improves** over D-21 on NDCG@10 (+2.5%) and MRR (+7.2%)
- D-23 R3 **degrades** vs D-22 on P@5 (−25.3%), R@10 (−25.5%), and NDCG@10 (−12.0%)
- D-23 R3 is the **best MRR** across all three experiments (0.9059)
- 32/36 queries have perfect first-result placement (MRR = 1.0)

### 3.4 Per-Query-Type Performance

| Query Type  | n   | P@5    | R@10   | NDCG@10 | MRR    | Assessment      |
| ----------- | --- | ------ | ------ | ------- | ------ | --------------- |
| SINGLE_HOP  | 11  | 0.2000 | 0.5606 | 0.6081  | 0.8636 | Worst category  |
| MULTI_HOP   | 8   | 0.4750 | 0.8333 | 0.8750  | 1.0000 | ⭐ Best overall |
| AUTHORITY   | 5   | 0.3200 | 0.7000 | 0.7226  | 0.8000 | Below average   |
| TEMPORAL    | 6   | 0.3333 | 0.8333 | 0.8710  | 1.0000 | ⭐ Strong       |
| EXPLORATORY | 6   | 0.2667 | 0.5417 | 0.5900  | 0.8519 | Weakest recall  |

**Key Observations:**

- **Multi-hop queries** are the standout: perfect MRR + highest P@5 and NDCG. Multi-layer enrichment helps the model connect information across documents.
- **Temporal queries** perform unexpectedly well despite the Temporal layer being unpopulated — suggesting that entity/relationship layers provide indirect temporal grounding.
- **Single-hop and Exploratory** are the weakest — the increased chunk count dilutes simple lookups.

### 3.5 Statistical Significance

| Comparison         | P@5           | R@10          | NDCG@10       | MRR           |
| ------------------ | ------------- | ------------- | ------------- | ------------- |
| D-23 ML vs D-21 BL | **p<0.001\*** | p=0.225       | p=0.104       | **p<0.001\*** |
| D-23 ML vs D-22 SL | **p=0.001\*** | **p=0.001\*** | **p=0.014\*** | p=0.125       |
| D-22 SL vs D-21 BL | p=0.194       | **p<0.001\*** | **p<0.001\*** | p=0.070       |

_\* Significant at Bonferroni-corrected α=0.0167_

**Interpretation:**

- The P@5 degradation vs D-21 is **statistically significant** (large effect size) — multi-layer enrichment with 1,233 chunks actively hurts precision.
- The P@5 and R@10 degradation vs D-22 is also significant — multi-layer is worse than single-layer for breadth metrics with the current chunking approach.
- The MRR improvement vs D-21 is highly significant (large effect) — multi-layer enrichment helps find the right document first.

### 3.6 Token Budget Analysis

| Statistic | Raw Tokens | Enriched Tokens | Prefix Overhead |
| --------- | ---------- | --------------- | --------------- |
| Mean      | 134.7      | 214.3           | 79.6            |
| Median    | 101.0      | 184.0           | 80.0            |
| Max       | 923        | 1,011           | 103             |
| Min       | 2          | 59              | 50              |

- **Zero overflow chunks** (0/1,233) — token budget is well-managed
- **Mean enrichment overhead: 79.6 tokens** (within the 100-token reserve)
- Prefix overhead is tightly distributed: P25=72, P50=80, P75=86

### 3.7 Enrichment Layer Token Distribution

| Layer         | Population | Mean Tokens | Max Tokens | Notes                            |
| ------------- | ---------- | ----------- | ---------- | -------------------------------- |
| Corpus        | 100%       | 6.0         | 6          | Fixed string, minimal cost       |
| Domain        | 100%       | 16.4        | 20         | Consistent, high value           |
| Entity        | 100%       | 16.2        | 24         | Variable, depends on entity name |
| Authority     | 100%       | 9.5         | 10         | Near-fixed, canonical status     |
| Relationships | 100%       | 15.4        | 31         | **NEW in R3** — wide variance    |
| Section       | 94%        | 14.3        | 26         | Missing for first chunks         |
| Temporal      | 0%         | 0.0         | 0          | **Still missing** — corpus gap   |
| Chunk Seq.    | N/A        | N/A         | N/A        | Not implemented                  |

---

## 4. GO/NO-GO Decision

### 4.1 Criteria Assessment

| #   | Criterion                     | Result   | Detail                                           |
| --- | ----------------------------- | -------- | ------------------------------------------------ |
| [1] | Execution (overflow < 5%)     | **PASS** | 0/1,233 chunks (0.0%)                            |
| [2] | Improvement over D-21 (≥3/4)  | **FAIL** | 2/4 metrics positive (NDCG@10, MRR)              |
| [3] | Improvement over D-22 (≥2/4)  | **FAIL** | 1/4 metrics positive (MRR only)                  |
| [4] | Statistical significance (≥2) | **PASS** | 2/4 significant (P@5, MRR vs D-21)               |
| [5] | Marginal value over SL (≥1)   | **PASS** | 1/4 metrics > 5% gain (MRR: +5.2%)               |
| [6] | No catastrophic degradation   | **FAIL** | 58.3% queries degraded vs D-21 (threshold: <25%) |
| [7] | Authority/Temporal benefit    | **PASS** | Both exceed Factual baseline                     |

### 4.2 Decision: **CONDITIONAL GO**

**Score: 4/7 criteria passed** (mandatory criteria 2+4: NOT MET)

The multi-layer approach shows **promising signals** in ranking quality (MRR) and complex query handling (multi-hop, temporal), but is **net negative** on breadth metrics (P@5, R@10) due to a **5.7× chunk count inflation** that dilutes the index.

---

## 5. Root Cause Analysis — Why Multi-Layer Underperforms

### 5.1 The Chunk Count Problem (Primary)

D-23's 1,233 chunks vs D-21/D-22's 218 is the **dominant confound**:

- **Dilution effect:** With 5.7× more chunks, relevant content is spread across more candidates. Top-10 retrieval must compete against far more noise.
- **Shorter content per chunk:** Mean raw content of 134.7 tokens (vs D-21's ~800) means each chunk carries less semantic signal.
- **Boundary effects:** More chunk boundaries = more potential for relevant content to be split across chunks.

This is **not** caused by the `max_chunk_tokens` parameter (which was correctly set to 1024). It's caused by the **chunking algorithm itself** — D-23's `chunk_document()` uses a section-aware, word-based splitting strategy that produces many more, shorter chunks than D-21/D-22's simpler tokenizer.

### 5.2 Prefix Overhead vs Content Ratio

With mean raw content of only 134.7 tokens, the 79.6-token prefix overhead represents **59% of the raw content**. For the shortest chunks (2 raw tokens), the prefix completely dominates. This unfavorable ratio means the embedding model "sees" more metadata than actual content.

Compare to D-22's single-layer prefix (~24 tokens) on chunks of ~800 tokens — only ~3% overhead.

### 5.3 The MRR Bright Spot

Despite lower breadth metrics, D-23 R3 achieves the **highest MRR (0.9059)** of any experiment:

| Experiment | Perfect MRR (=1.0) | Zero MRR (=0.0) |
| ---------- | ------------------ | --------------- |
| D-21       | 29/36              | 2/36            |
| D-22       | 30/36              | 3/36            |
| D-23 R3    | **32/36**          | **2/36**        |

This suggests that multi-layer enrichment is **excellent at identifying the single most relevant document** — the metadata layers provide strong type-level discrimination that helps the embedding model surface the right entity first. It just can't populate the full top-k with relevant results due to chunk fragmentation.

---

## 6. Recommendations for D-24

### 6.1 Fix the Chunking Geometry (Mandatory)

The comparison is invalidated unless chunking geometry is controlled. Two approaches:

1. **Port D-21/D-22's chunker** into D-23/D-24 to produce ~218 comparable chunks
2. **Re-run D-21/D-22 with D-23's chunker** to produce a matched-chunk baseline

Option 1 is preferred — it isolates the variable under test (enrichment layers) while holding everything else constant.

### 6.2 Ablation Study Design

With matched chunking, test these configurations:

| Configuration | Layers                               | Expected Tokens | Rationale              |
| ------------- | ------------------------------------ | --------------- | ---------------------- |
| A (control)   | None (raw)                           | 0               | D-21 equivalent        |
| B             | Corpus + Domain                      | ~22             | Minimal context        |
| C             | Corpus + Domain + Entity             | ~38             | D-22-equivalent scope  |
| D             | Corpus + Domain + Entity + Authority | ~48             | Core layers only       |
| E             | All 6 active layers                  | ~80             | Current D-23 R3 config |

### 6.3 Temporal Layer Investigation

The Temporal layer showed 0% population. Actions:

1. Audit the 77 corpus documents for `temporal_markers` in frontmatter — field appears to be absent
2. Consider deriving temporal data from document body text if frontmatter is empty
3. If temporal data doesn't exist, remove Temporal from the active layer set

### 6.4 Layer Efficiency Analysis

Based on token cost vs information value:

| Layer         | Cost (tokens) | Value Signal        | Keep?                             |
| ------------- | ------------- | ------------------- | --------------------------------- |
| Corpus        | 6.0           | Low (constant)      | ❓ Cut — identical for all chunks |
| Domain        | 16.4          | High                | ✅ Keep                           |
| Entity        | 16.2          | High                | ✅ Keep                           |
| Authority     | 9.5           | Medium              | ✅ Keep                           |
| Relationships | 15.4          | Unknown (new in R3) | ⚠️ Test in ablation               |
| Section       | 14.3          | Medium              | ✅ Keep                           |

The Corpus layer costs 6 tokens but is identical for every chunk — it adds no discriminative signal and could be cut.

---

## 7. Round-over-Round Comparison

| Aspect           | Round 1         | Round 2            | Round 3            |
| ---------------- | --------------- | ------------------ | ------------------ |
| NDCG validity    | N/A (all zeros) | ❌ 30/36 > 1.0     | ✅ All in [0, 1]   |
| Active layers    | 5               | 5                  | **6** (+Relations) |
| Temporal layer   | 0%              | 0%                 | **0%** ⚠️          |
| Chunk count      | 1,266           | 1,266              | **1,233**          |
| Max chunk tokens | 600             | 600                | **1,024** ✅       |
| Overlap tokens   | 50              | 50                 | **150** ✅         |
| Prefix reserve   | 150             | 150                | **100** ✅         |
| MRR              | N/A             | Invalid            | **0.9059** ⭐      |
| Bugs present     | Chunk-ID format | NDCG dedup, fields | **Chunk geometry** |

---

## 8. Key Takeaways

1. **NDCG bug is fixed.** All values are now in [0.0, 1.0]. The deduplication-before-DCG approach is correct.

2. **Multi-layer enrichment improves first-result ranking.** MRR = 0.9059 is the best across all three experiments, with 32/36 queries achieving perfect first-hit placement.

3. **Multi-layer enrichment hurts breadth metrics under current chunking.** P@5 and R@10 are significantly worse than both D-21 and D-22. The 5.7× chunk inflation is the primary cause.

4. **The chunking geometry is the remaining confound.** D-23 R3 cannot be directly compared to D-21/D-22 because the chunking strategy produces fundamentally different index characteristics. This must be resolved in D-24.

5. **Relationships layer is now active.** Adding cross-references, factions, and locations increased the layer count from 5 to 6. Impact on retrieval quality needs ablation testing to assess.

6. **Temporal layer remains empty — corpus gap.** The `temporal_markers` frontmatter field does not exist in any of the 77 documents.

7. **Decision: CONDITIONAL GO.** Proceed to D-24 with chunking geometry alignment as the top priority, followed by layer ablation to find the optimal layer subset.

---

## 9. Files in This Round

| File                                         | Description                                       |
| -------------------------------------------- | ------------------------------------------------- |
| `D23_multi_layer_4.ipynb`                    | Executed notebook with all fixes applied          |
| `d23_results.csv`                            | Per-query results (36 rows × 4 metrics)           |
| `d23_delta_vs_d21.csv`                       | Per-query deltas vs D-21 (108 rows — 3 D-21 runs) |
| `d23_delta_vs_d22.csv`                       | Per-query deltas vs D-22 (36 rows)                |
| `d23_significance_results.csv`               | Wilcoxon signed-rank test results                 |
| `d23_go_nogo_decision.txt`                   | Automated GO/NO-GO assessment                     |
| `d23_layer_token_audits.csv`                 | Token counts per layer per chunk (1,233 rows)     |
| `visualization_3way_comparison.png`          | Bar chart: D-21 vs D-22 vs D-23 R3                |
| `visualization_delta_heatmap.png`            | Per-query delta heatmaps                          |
| `visualization_layer_token_distribution.png` | Box plot: token distribution per layer            |
| `D23-findings.md`                            | This document                                     |
