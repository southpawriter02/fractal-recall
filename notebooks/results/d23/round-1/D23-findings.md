# D-23 Findings — Multi-Layer Context Enrichment

> **Project:** FractalRecall — Hierarchical context-aware embedding retrieval  
> **Notebook:** D23-multi-layer.ipynb  
> **Run Date:** 2026-02-17  
> **Hardware:** Google Colab — A100 GPU, High-RAM  
> **Metrics:** Precision@5, Recall@10, NDCG@10, MRR

---

## 1. Objective

Determine whether adding **8 hierarchical context layers** to each chunk before embedding improves retrieval performance over the D-21 baseline and the D-22 single-layer enrichment.

D-23 tests the full FractalRecall enrichment pipeline: Corpus → Domain → Entity → Authority → Temporal → Relational → Section → (Chunk). This is the most aggressive enrichment strategy in the experiment series.

---

## 2. Experimental Setup

### 2.1 Baselines

| Experiment              | Model                 | Enrichment            | Overall NDCG@10 |
| ----------------------- | --------------------- | --------------------- | --------------- |
| **D-21** (baseline)     | nomic-embed-text-v1.5 | None                  | 0.7062          |
| **D-22** (single-layer) | nomic-embed-text-v1.5 | 1 prefix (~24 tokens) | 0.8225          |

### 2.2 Enrichment Strategy — 8-Layer Prefix

D-23 prepends a multi-layer natural language prefix to every chunk, constructed from document metadata:

| Layer          | Content Pattern                                  | Token Budget        |
| -------------- | ------------------------------------------------ | ------------------- |
| **Corpus**     | `"Part of the Aethelgard worldbuilding corpus."` | ~6 tokens           |
| **Domain**     | `"Domain: {entity_type}, {category}."`           | ~16 tokens          |
| **Entity**     | `"Entity: {name}. Type: {entity_type}."`         | ~16 tokens          |
| **Authority**  | `"Canon status: {canon}. Source tier: {tier}."`  | ~10 tokens          |
| **Section**    | `"Section: {heading}."`                          | ~14 tokens          |
| **Temporal**   | _(if present)_ `"Time period: {era}."`           | variable            |
| **Relational** | _(if present)_ `"Related to: {entities}."`       | variable            |
|                | **Total overhead:**                              | **~64 tokens mean** |

### 2.3 Model Configuration

| Parameter                 | D-21/D-22             | D-23                  | Change |
| ------------------------- | --------------------- | --------------------- | ------ |
| **Max chunk tokens**      | 1,024                 | **600**               | -41.4% |
| **Prefix reserve**        | 0 / 0                 | **150**               | +150   |
| **Available for content** | 1,024 / 1,024         | **450**               | -56.1% |
| **Overlap tokens**        | 150                   | **50**                | -66.7% |
| Model                     | nomic-embed-text-v1.5 | nomic-embed-text-v1.5 | Same   |
| Embedding dimension       | 768                   | 768                   | Same   |

### 2.4 Corpus

- 77 Markdown documents from the Aethelgard worldbuilding corpus (same as D-21/D-22)
- 36 ground-truth queries across 5 types (identical query set)

---

## 3. Chunking & Enrichment

### 3.1 Chunk Statistics

| Metric         | D-21 | D-22      | D-23             | Notes                                  |
| -------------- | ---- | --------- | ---------------- | -------------------------------------- |
| Total chunks   | 218  | 218       | **1,266**        | +481% due to smaller chunk size        |
| Chunks indexed | 218  | 124 (57%) | **1,266 (100%)** | D-23 fixed overflow via prefix reserve |
| Token overflow | 0%   | 43.1%     | **0.0%**         | Pre-reserved 150 tokens for prefix     |

### 3.2 Token Budget

| Metric                | Mean  | Median | Max |
| --------------------- | ----- | ------ | --- |
| Raw chunk tokens      | 131.9 | 102.0  | 449 |
| Enriched chunk tokens | 195.7 | 167.0  | 522 |
| Prefix overhead       | 63.8  | 64.0   | 84  |

### 3.3 Layer Presence Rates

| Layer     | Present     | Rate | Mean Tokens | Max Tokens |
| --------- | ----------- | ---- | ----------- | ---------- |
| Corpus    | 1,266/1,266 | 100% | 6.0         | 6          |
| Domain    | 1,266/1,266 | 100% | 16.4        | 20         |
| Entity    | 1,266/1,266 | 100% | 16.1        | 24         |
| Authority | 1,266/1,266 | 100% | 9.5         | 10         |
| Section   | 1,190/1,266 | 94%  | 14.4        | 26         |

> **Token overflow solved.** The `prefix_reserve_tokens = 150` parameter, which subtracts the expected prefix budget from the chunk content allocation _before_ splitting, completely eliminated the 43.1% overflow problem seen in D-22.

---

## 4. Results

### 4.1 Overall Performance (Mean Across 36 Queries)

| Metric          | D-21 Baseline | D-22 Single-Layer | D-23 Multi-Layer | Δ vs D-21       | Δ vs D-22       |
| --------------- | ------------- | ----------------- | ---------------- | --------------- | --------------- |
| **Precision@5** | 0.3829        | 0.4167            | **0.0000**       | -0.3829 (-100%) | -0.4167 (-100%) |
| **Recall@10**   | 0.7199        | 0.9167            | **0.0000**       | -0.7199 (-100%) | -0.9167 (-100%) |
| **NDCG@10**     | 0.7062        | 0.8225            | **0.0000**       | -0.7062 (-100%) | -0.8225 (-100%) |
| **MRR**         | 0.8452        | 0.8611            | **0.0000**       | -0.8452 (-100%) | -0.8611 (-100%) |

> [!CAUTION]
> **All 36 queries returned 0.0 across all four metrics.** This is not a real enrichment regression — it is a **metric computation bug** (see §5).

### 4.2 Per-Query Results

Every single query produced identical results:

| Pattern                                                          | Count | Percentage |
| ---------------------------------------------------------------- | ----- | ---------- |
| All 4 metrics = 0.0                                              | 33/36 | 91.7%      |
| All 4 metrics = 0.0 (Q-13, Q-24, Q-28 unchanged from D-21 zeros) | 3/36  | 8.3%       |

### 4.3 Statistical Significance (Wilcoxon Signed-Rank Test)

#### D-23 vs D-21 Baseline

| Metric  | Statistic | p-value | Significant | Effect Size   |
| ------- | --------- | ------- | ----------- | ------------- |
| P@5     | 0.0       | 8.9e-18 | Yes         | 1.000 (large) |
| R@10    | 0.0       | 7.3e-19 | Yes         | 1.000 (large) |
| NDCG@10 | 0.0       | 2.5e-18 | Yes         | 1.000 (large) |
| MRR     | 0.0       | 7.7e-21 | Yes         | 1.000 (large) |

#### D-23 vs D-22 Single-Layer

| Metric  | Statistic | p-value | Significant | Effect Size   |
| ------- | --------- | ------- | ----------- | ------------- |
| P@5     | 0.0       | 4.1e-07 | Yes         | 1.000 (large) |
| R@10    | 0.0       | 4.8e-07 | Yes         | 1.000 (large) |
| NDCG@10 | 0.0       | 5.2e-07 | Yes         | 1.000 (large) |
| MRR     | 0.0       | 3.1e-08 | Yes         | 1.000 (large) |

> **Note:** The "statistically significant" results are an artifact of the bug — every non-zero D-21/D-22 metric paired with a D-23 zero creates a perfectly one-sided sign distribution. The Wilcoxon test correctly identifies this as non-random, but the underlying data is invalid.

### 4.4 GO/NO-GO Decision

| Criterion                                               | Result                         | Status    |
| ------------------------------------------------------- | ------------------------------ | --------- |
| 1. Execution (< 5% overflow)                            | 0/1,266 (0.0%)                 | ✅ PASS   |
| 2. Improvement over D-21 (≥ 3/4 metrics positive)       | 0/4 positive                   | ❌ FAIL   |
| 3. Improvement over D-22 (≥ 2/4 metrics positive)       | 0/4 positive                   | ❌ FAIL   |
| 4. Statistical significance (≥ 2 metrics at α=0.017)    | 4/4 significant                | ✅ PASS\* |
| 5. Marginal value (> 5% gain over D-22 for ≥ 1 metric)  | -100% all metrics              | ❌ FAIL   |
| 6. No catastrophic degradation (< 25% queries degraded) | 93.5% degraded                 | ❌ FAIL   |
| 7. Authority/Temporal benefit                           | No improvement in any category | ❌ FAIL   |

**Decision: NO-GO** — 2/7 criteria passed (but criterion 4 is a statistical artifact, so effectively 1/7).

---

## 5. Root Cause Analysis — Metric Computation Bug

### 5.1 The Bug

The all-zeros results are caused by an **ID format mismatch** in the `compute_all_metrics()` function:

```python
# What D-23 does (Cell 13):
retrieved = [r["chunk_id"] for r in qr.results]   # → "000-codex_echo-cant.md#chunk_002"
relevant = set(gt.expected_filenames)               # → {"000-codex_echo-cant.md"}

# These will NEVER match:
"000-codex_echo-cant.md#chunk_002" in {"000-codex_echo-cant.md"}  # → False
```

The `retrieved` list contains **chunk-level IDs** (e.g., `000-codex_echo-cant.md#chunk_002`), but the `relevant` set contains **document-level filenames** (e.g., `000-codex_echo-cant.md`). Since no chunk ID is ever an exact string match for a document filename, every precision/recall/NDCG/MRR computation returns 0.

### 5.2 How D-22 Avoided This

D-22 used a different metric function signature:

```python
# D-22 approach (works correctly):
def precision_at_k(retrieved_docs: List[Dict], relevant_docs: List[str], k: int):
    top_k = retrieved_docs[:k]
    return sum(1 for doc in top_k if doc["doc_filename"] in relevant_docs) / k
```

D-22's metric functions received a list of **dicts** with a `doc_filename` field (the document-level filename, e.g., `000-codex_echo-cant.md`), which matched correctly against the ground truth.

D-23 rewrote the metric functions to take `List[str]` (raw chunk IDs) but did not strip the `#chunk_NNN` suffix before comparison.

### 5.3 The Fix

The fix requires one change in `compute_all_metrics()` — strip the chunk suffix to get the document filename:

```python
# Current (broken):
retrieved = [r["chunk_id"] for r in qr.results]

# Fixed:
retrieved = [r["chunk_id"].split("#")[0] for r in qr.results]
```

This would extract `"000-codex_echo-cant.md"` from `"000-codex_echo-cant.md#chunk_002"`, enabling correct matching against `gt.expected_filenames`.

### 5.4 Evidence the Retrieval Itself Works

The query execution output (Cell 11) confirms that retrieval returned relevant results:

```
Q-01 [SINGLE_HOP]: What is the Echo-Cant communication system?
  [1] 000-codex_echo-cant.md#chunk_002 (dist=0.2977)   ← Correct document!
  [2] 000-codex_echo-cant.md#chunk_009 (dist=0.3188)   ← Correct document!
  [3] 000-codex_echo-cant.md#chunk_005 (dist=0.3198)   ← Correct document!
```

The expected relevant document for Q-01 is `000-codex_echo-cant.md`, and the top 3 results are all chunks from that document. The retrieval is working — the metric computation is broken.

---

## 6. Valid Findings (Infrastructure & Enrichment)

While the retrieval metrics are invalid, several aspects of D-23 worked correctly and produced valuable data:

### 6.1 Token Overflow — Solved ✅

D-22's most critical problem (43.1% chunk overflow) is completely resolved:

| Metric         | D-22      | D-23              |
| -------------- | --------- | ----------------- |
| Overflow rate  | 43.1%     | **0.0%**          |
| Chunks indexed | 124 / 218 | **1,266 / 1,266** |
| Coverage       | 56.9%     | **100%**          |

The `prefix_reserve_tokens = 150` strategy works as designed.

### 6.2 Chunking Strategy — Significant Change

D-23 reduced `max_chunk_tokens` from 1,024 to 600, producing dramatically different chunk characteristics:

| Metric                  | D-21/D-22 | D-23              |
| ----------------------- | --------- | ----------------- |
| Mean chunk tokens (raw) | 782.2     | **131.9** (-83%)  |
| Max chunk tokens (raw)  | 974       | **449** (-54%)    |
| Total chunks            | 218       | **1,266** (+481%) |
| Overlap tokens          | 150       | **50** (-67%)     |

The 6× increase in chunk count combined with 6× smaller chunks is a radically different retrieval geometry. Even with the metric bug fixed, this would significantly affect results — more small chunks means the embedding must work harder to rank the right ones, but also means more entry points into each document.

### 6.3 Layer Token Distribution

The layer token audit provides production-relevant data:

| Layer     | Mean     | P25 | P50    | P75 | Max    |
| --------- | -------- | --- | ------ | --- | ------ |
| Corpus    | 6        | 6   | 6      | 6   | 6      |
| Domain    | 16.4     | 16  | 16     | 18  | 20     |
| Entity    | 16.1     | 13  | 16     | 19  | 24     |
| Authority | 9.5      | 9   | 10     | 10  | 10     |
| Section   | 14.4     | 13  | 14     | 16  | 26     |
| **Total** | **63.8** | —   | **64** | —   | **84** |

The actual prefix overhead (mean 64 tokens) is well below the 150-token reserve, leaving ~86 tokens of unused headroom. This suggests `prefix_reserve_tokens = 100` would be sufficient and would allow 50 more tokens per chunk for content.

### 6.4 Missing Layers

The audit reveals that **only 5 of the planned 8 layers** were populated:

| Layer          | Status              |
| -------------- | ------------------- |
| Corpus         | ✅ Present (100%)   |
| Domain         | ✅ Present (100%)   |
| Entity         | ✅ Present (100%)   |
| Authority      | ✅ Present (100%)   |
| Section        | ✅ Present (94%)    |
| Temporal       | ❌ Not in audit CSV |
| Relational     | ❌ Not in audit CSV |
| Chunk Sequence | ❌ Not in audit CSV |

The three missing layers (Temporal, Relational, Chunk Sequence) likely produced `None` for all documents, meaning the metadata didn't contain the expected fields. This should be investigated before re-running.

---

## 7. Visualizations

### 7.1 3-Way Comparison

The bar chart shows D-23 (green bars) at zero for all metrics and query types, while D-21 (blue) and D-22 (orange) show expected non-zero performance. This is a visual confirmation of the metric bug.

### 7.2 Delta Heatmap

Both heatmap panels (D-23 vs D-21 and D-23 vs D-22) are uniformly dark red, indicating -100% degradation across all queries. Three queries (Q-13, Q-24, Q-28) appear as neutral (green) because they were already 0.0 in the baseline — the metric bug didn't change their scores.

### 7.3 Layer Token Distribution

The box plot shows tight distributions for Corpus (constant 6) and Authority (9-10), with more variance in Domain (15-20), Entity (6-24), and Section (10-26). This confirms the prefix is well-behaved and predictable.

---

## 8. Recommendations

### 8.1 Immediate — Fix and Re-Run

1. **Fix the chunk ID → document filename mapping** in `compute_all_metrics()` by adding `.split("#")[0]` to extract the document filename from each chunk ID.
2. **Apply the same fix** to the individual metric functions (`precision_at_k`, `recall_at_k`, `ndcg_at_k`, `mean_reciprocal_rank`) or normalize the IDs before passing them in.
3. **Re-run D-23** to get valid metrics and a legitimate NO-GO/GO decision.

### 8.2 Before Re-Run — Consider

1. **Investigate missing layers.** Temporal, Relational, and Chunk Sequence layers are absent. If the metadata doesn't support them, remove them from the prefix to reduce overhead.
2. **Reduce prefix reserve.** Actual overhead is ~64 tokens (max 84). `prefix_reserve_tokens = 100` would reclaim 50 tokens per chunk for content.
3. **Re-evaluate chunking parameters.** The combination of `max_chunk_tokens = 600` and `overlap = 50` produces very small chunks (mean 132 tokens of content). Consider `max_chunk_tokens = 800` with `prefix_reserve = 100` for a more balanced content-to-prefix ratio.

### 8.3 Confounding Variables

Even after the metric bug is fixed, the D-23 results will be confounded by two major parameter changes from D-21/D-22:

| Parameter        | D-21/D-22 | D-23 | Impact                                      |
| ---------------- | --------- | ---- | ------------------------------------------- |
| Max chunk tokens | 1,024     | 600  | 6× more chunks, much smaller content window |
| Overlap tokens   | 150       | 50   | Less context continuity between chunks      |

If the re-run shows regression, it will be unclear whether the cause is:

- (a) Multi-layer enrichment diluting embedding signal
- (b) Smaller chunks losing important sentence-level context
- (c) Reduced overlap fragmenting cross-boundary concepts

An ideal D-23 re-run would use `max_chunk_tokens = 1024` (matching D-21/D-22) with `prefix_reserve = 100`, isolating the enrichment effect from the chunking change.

---

## 9. Exported Artefacts

| File                                         | Contents                               | Valid?                   |
| -------------------------------------------- | -------------------------------------- | ------------------------ |
| `d23_results.csv`                            | 36 rows — all zeros                    | ❌ Metric bug            |
| `d23_delta_vs_d21.csv`                       | 108 rows — all negative                | ❌ Metric bug            |
| `d23_delta_vs_d22.csv`                       | 36 rows — all negative                 | ❌ Metric bug            |
| `d23_significance_results.csv`               | 12 rows — all "significant"            | ❌ Artifact of bug       |
| `d23_go_nogo_decision.txt`                   | NO_GO (2/7 pass)                       | ❌ Based on invalid data |
| `d23_layer_token_audits.csv`                 | 1,266 rows — per-chunk layer breakdown | ✅ Valid                 |
| `visualization_3way_comparison.png`          | Bar chart — D-23 at zero               | ❌ Reflects bug          |
| `visualization_delta_heatmap.png`            | Heatmap — all red                      | ❌ Reflects bug          |
| `visualization_layer_token_distribution.png` | Box plot — layer token stats           | ✅ Valid                 |

---

## 10. Summary

**D-23's retrieval results are entirely invalid due to a metric computation bug** that prevents chunk-level IDs from matching document-level ground truth filenames. The retrieval pipeline itself works correctly — queries return relevant chunks with reasonable cosine distances — but the evaluation layer produces all zeros.

**What IS valid from this run:**

- The token overflow solution works perfectly (0% overflow vs D-22's 43.1%)
- Layer token distribution data is production-ready (~64 tokens mean prefix)
- 5 of 8 planned layers are populating correctly
- The GO/NO-GO framework executed correctly (it just operated on bad data)

**Next steps:**

1. Fix the `.split("#")[0]` bug in `compute_all_metrics()`
2. Investigate missing Temporal/Relational/Chunk layers
3. Consider matching D-21/D-22 chunk parameters for a controlled comparison
4. Re-run D-23 for valid results

---

## Appendix: Delta vs D-21 (All 3 D-21 Models)

The `d23_delta_vs_d21.csv` file contains 108 rows (36 queries × 3 D-21 models), reflecting D-23's comparison against all three D-21 model variants. Since all D-23 metrics are 0.0, every delta is simply the negative of the D-21 value. This data should be regenerated after the bug fix.
