# D-23 Findings — Multi-Layer Context Enrichment (Round 2)

> **Project:** FractalRecall — Hierarchical context-aware embedding retrieval  
> **Notebook:** D23_multi_layer_3.ipynb  
> **Run Date:** 2026-02-17  
> **Hardware:** Google Colab — A100 GPU, High-RAM  
> **Metrics:** Precision@5, Recall@10, NDCG@10, MRR  
> **Round:** 2 (re-run after chunk-ID metric bug fix from Round 1)

---

## 1. Objective

Determine whether adding **5 hierarchical context layers** to each chunk before embedding improves retrieval performance over the D-21 baseline and the D-22 single-layer enrichment.

D-23 tests a multi-layer enrichment strategy: Corpus → Domain → Entity → Authority → Section. This is the second run — Round 1 produced all-zero metrics due to a chunk-ID format mismatch in the evaluation code (documented in `round-1/D23-findings.md`). This round fixes that bug and produces valid retrieval metrics.

---

## 2. Experimental Setup

### 2.1 Baselines

| Experiment              | Model                 | Enrichment            | NDCG@10 | P@5    | R@10   | MRR    |
| ----------------------- | --------------------- | --------------------- | ------- | ------ | ------ | ------ |
| **D-21** (baseline)     | nomic-embed-text-v1.5 | None                  | 0.7062  | 0.3829 | 0.7199 | 0.8452 |
| **D-22** (single-layer) | nomic-embed-text-v1.5 | 1 prefix (~24 tokens) | 0.8225  | 0.4167 | 0.9167 | 0.8611 |

### 2.2 Enrichment Strategy — 5-Layer Prefix

D-23 prepends a multi-layer natural language prefix to each chunk, drawn from document metadata:

| Layer         | Content Pattern                                  | Mean Tokens | Max Tokens |
| ------------- | ------------------------------------------------ | ----------- | ---------- |
| **Corpus**    | `"Part of the Aethelgard worldbuilding corpus."` | 6.0         | 6          |
| **Domain**    | `"Domain: {entity_type}, {category}."`           | 16.4        | 20         |
| **Entity**    | `"Entity: {name}. Type: {entity_type}."`         | 16.1        | 24         |
| **Authority** | `"Canon status: {canon}. Source tier: {tier}."`  | 9.5         | 10         |
| **Section**   | `"Section: {heading}."`                          | 14.4        | 26         |
|               | **Total overhead:**                              | **63.8**    | **84**     |

> **Note:** Only 5 of the originally planned 8 layers are populated. Temporal, Relational, and Chunk Sequence layers were absent (likely producing `None` for all documents due to missing metadata fields).

### 2.3 Model & Chunking Configuration

| Parameter                 | D-21/D-22             | D-23                  | Change |
| ------------------------- | --------------------- | --------------------- | ------ |
| Model                     | nomic-embed-text-v1.5 | nomic-embed-text-v1.5 | Same   |
| Embedding dimension       | 768                   | 768                   | Same   |
| **Max chunk tokens**      | 1,024                 | **600**               | -41.4% |
| **Prefix reserve tokens** | 0                     | **150**               | New    |
| **Available for content** | 1,024                 | **~450**              | -56.1% |
| **Overlap tokens**        | 150                   | **50**                | -66.7% |

### 2.4 Corpus

- **77 Markdown documents** from the Aethelgard worldbuilding corpus (same as D-21/D-22)
- **36 ground-truth queries** across 5 types (identical query set)

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

> **Token overflow solved.** The `prefix_reserve_tokens = 150` parameter completely eliminated the 43.1% overflow problem seen in D-22. Actual prefix overhead averages 64 tokens (max 84), well within the 150-token budget.

### 3.3 Layer Presence Rates

| Layer     | Present     | Rate | Notes                  |
| --------- | ----------- | ---- | ---------------------- |
| Corpus    | 1,266/1,266 | 100% | Constant 6 tokens      |
| Domain    | 1,266/1,266 | 100% | 15–20 tokens           |
| Entity    | 1,266/1,266 | 100% | 6–24 tokens (widest)   |
| Authority | 1,266/1,266 | 100% | 9–10 tokens (tightest) |
| Section   | 1,190/1,266 | 94%  | 10–26 tokens           |

---

## 4. Results

### ⚠️ CRITICAL: NDCG Computation Bug (Root Cause Confirmed)

**Before interpreting the results, readers must understand that D-23 Round 2 contains an NDCG@10 computation error.** The NDCG values reported range from 0.0 to **2.786**, with 83.3% of queries producing NDCG > 1.0 and 52.8% exceeding 2.0.

**NDCG is mathematically bounded between 0 and 1.** A value above 1.0 is impossible under a correct implementation.

**Root cause (confirmed):** The Round 2 chunk-ID fix (`.split("#")[0]`) maps all chunk IDs back to document filenames before metric computation. This correctly enables matching against document-level relevance judgments — but it introduces duplicate entries: when 7 chunks from `000-codex_echo-cant.md` appear in the top-10, the DCG formula gives each one a relevance gain of 2, accumulating DCG ≈ 7.9. Meanwhile, the IDCG denominator uses `sorted(relevance_scores.values())`, which only has 2 entries (one per unique relevant doc), giving IDCG ≈ 3.3. Result: NDCG = 7.9 / 3.3 = **2.42**.

**Fix applied in Round 3:** Deduplicate retrieved IDs before DCG computation — only the highest-ranked chunk from each document contributes. See `fix_d23_round3.py`.

**Consequence:** NDCG@10 values in this report are **not valid**. All 3-way comparison data, statistical significance tests, and GO/NO-GO criteria that depend on NDCG are tainted.

**Precision@5, Recall@10, and MRR are valid** — P@5 and R@10 use `set()` operations that naturally deduplicate, and MRR only cares about the first match.

### 4.1 Overall Performance (Mean Across 36 Queries)

| Metric          | D-21 Baseline | D-22 Single-Layer | D-23 Multi-Layer | Δ vs D-21            | Δ vs D-22            |
| --------------- | ------------- | ----------------- | ---------------- | -------------------- | -------------------- |
| **Precision@5** | 0.3829        | 0.4167            | **0.3278**       | -0.0551 (-14.4%)     | -0.0889 (-21.3%)     |
| **Recall@10**   | 0.7199        | 0.9167            | **0.7199**       | ±0.0000 (0.0%)       | -0.1968 (-21.5%)     |
| **NDCG@10**     | 0.7062        | 0.8225            | **1.8871** ⚠️    | _+167.2%_ ⚠️ INVALID | _+129.4%_ ⚠️ INVALID |
| **MRR**         | 0.8452        | 0.8611            | **0.8943**       | +0.0491 (+5.8%)      | +0.0332 (+3.9%)      |

**Key observations (valid metrics only):**

- **Precision@5 regressed** from both baselines: -14.4% vs D-21, -21.3% vs D-22. The multi-layer enrichment makes the top-5 results _less_ precise.
- **Recall@10 is flat** vs D-21 (identical at 0.7199) and **down 21.5%** vs D-22. D-22's Recall gain (+27.3% over D-21) is entirely lost.
- **MRR improved modestly** vs both baselines: +5.8% vs D-21, +3.9% vs D-22. The first relevant result appears slightly earlier.

### 4.2 MRR Analysis

| Metric              | D-21  | D-22  | D-23      |
| ------------------- | ----- | ----- | --------- |
| Perfect MRR (= 1.0) | 29/36 | 30/36 | **31/36** |
| Zero MRR (= 0.0)    | 2/36  | 3/36  | **1/36**  |
| Partial MRR         | 5/36  | 3/36  | **4/36**  |

MRR is the best-performing metric for D-23: 31 of 36 queries have a relevant document as the very first result (+2 over D-21, +1 over D-22). Only 1 query (Q-13 AUTHORITY) has zero MRR.

### 4.3 Per-Query-Type Breakdown (Valid Metrics)

#### Precision@5

| Query Type  | D-21   | D-22   | D-23       | Δ vs D-21   | Δ vs D-22   |
| ----------- | ------ | ------ | ---------- | ----------- | ----------- |
| SINGLE_HOP  | 0.3045 | 0.2727 | **0.2364** | -0.0682     | -0.0364     |
| MULTI_HOP   | 0.6187 | 0.6250 | **0.4750** | **-0.1437** | **-0.1500** |
| AUTHORITY   | 0.3967 | 0.3600 | **0.3200** | -0.0767     | -0.0400     |
| TEMPORAL    | 0.3500 | 0.5000 | **0.3333** | -0.0167     | **-0.1667** |
| EXPLORATORY | 0.2333 | 0.3667 | **0.3000** | +0.0667     | -0.0667     |

**Key finding:** Precision dropped across _every_ query type vs D-22. Multi-hop queries suffered the largest absolute loss (-0.15 vs D-22). The only category that improved vs D-21 is Exploratory (+0.07).

#### Recall@10

| Query Type  | D-21   | D-22   | D-23       | Δ vs D-21 | Δ vs D-22   |
| ----------- | ------ | ------ | ---------- | --------- | ----------- |
| SINGLE_HOP  | 0.6515 | 0.6667 | **0.6364** | -0.0152   | -0.0303     |
| MULTI_HOP   | 0.8750 | 1.0833 | **0.8333** | -0.0417   | **-0.2500** |
| AUTHORITY   | 0.7000 | 0.8000 | **0.7000** | ±0.0000   | -0.1000     |
| TEMPORAL    | 0.9167 | 1.4167 | **0.9167** | ±0.0000   | **-0.5000** |
| EXPLORATORY | 0.4583 | 0.7500 | **0.5417** | +0.0833   | -0.2083     |

**Key finding:** Recall regressed in _every_ category vs D-22. The largest losses are in Temporal (-0.50) and Multi-hop (-0.25) — the exact same categories where D-22 showed the biggest _gains_ over D-21. Against D-21, Recall is approximately flat (slight Exploratory gain, slight Multi-hop/Single-hop loss).

#### MRR

| Query Type  | D-21   | D-22   | D-23       | Δ vs D-21 | Δ vs D-22 |
| ----------- | ------ | ------ | ---------- | --------- | --------- |
| SINGLE_HOP  | 0.8030 | 0.8485 | **0.8712** | +0.0682   | +0.0227   |
| MULTI_HOP   | 1.0000 | 1.0000 | **1.0000** | +0.0000   | +0.0000   |
| AUTHORITY   | 0.8000 | 0.8000 | **0.8000** | +0.0000   | +0.0000   |
| TEMPORAL    | 0.8667 | 0.8889 | **1.0000** | +0.1333   | +0.1111   |
| EXPLORATORY | 0.7321 | 0.7222 | **0.7685** | +0.0364   | +0.0463   |

**Key finding:** MRR improved across all categories. The most meaningful gains are in Temporal (+0.13 vs D-21, full perfect MRR) and Single-Hop (+0.07 vs D-21). Multi-layer enrichment reliably surfaces the right document in _position 1_, even when it fails to surface enough relevant documents in the top 5 or 10.

### 4.4 Statistical Significance (Wilcoxon Signed-Rank Test)

#### D-23 vs D-21 (Bonferroni-adjusted α = 0.0167)

| Metric  | Statistic | p-value | Significant  | Effect Size      |
| ------- | --------- | ------- | ------------ | ---------------- |
| P@5     | 538.5     | 0.0021  | **Yes** ✓    | 0.449 (medium)   |
| R@10    | 128.5     | 0.5317  | No           | 0.143 (small)    |
| NDCG@10 | 11.0      | 5.4e-19 | **Yes** ✓ ⚠️ | 0.996 (large) ⚠️ |
| MRR     | 26.5      | 0.00068 | **Yes** ✓    | 0.808 (large)    |

#### D-23 vs D-22 (Bonferroni-adjusted α = 0.0167)

| Metric  | Statistic | p-value | Significant  | Effect Size      |
| ------- | --------- | ------- | ------------ | ---------------- |
| P@5     | 20.0      | 0.0067  | **Yes** ✓    | 0.739 (large)    |
| R@10    | 20.0      | 0.0039  | **Yes** ✓    | 0.766 (large)    |
| NDCG@10 | 0.0       | 2.5e-07 | **Yes** ✓ ⚠️ | 1.000 (large) ⚠️ |
| MRR     | 0.0       | 0.125   | No           | 1.000 (large)    |

#### D-22 vs D-21 (Bonferroni-adjusted α = 0.0167)

| Metric  | Statistic | p-value | Significant | Effect Size    |
| ------- | --------- | ------- | ----------- | -------------- |
| P@5     | 1494.0    | 0.1936  | No          | 0.163 (small)  |
| R@10    | 277.0     | 2.1e-06 | **Yes** ✓   | 0.697 (large)  |
| NDCG@10 | 1275.0    | 0.00012 | **Yes** ✓   | 0.452 (medium) |
| MRR     | 56.5      | 0.0696  | No          | 0.462 (medium) |

> **Note on NDCG significance:** The NDCG results are marked ⚠️ because the underlying NDCG values are invalid (>1.0). The significance tests ran on broken data. P@5, R@10, and MRR significance results are valid.

**Interpretation of valid results:**

- D-23's **Precision@5 decrease** vs D-21 is statistically significant (p=0.002, medium effect). The degradation is real, not noise.
- D-23's **Precision@5** and **Recall@10 decreases** vs D-22 are both statistically significant (p=0.007 and p=0.004, large effects). The regression from D-22 is genuine.
- D-23's **MRR improvement** vs D-21 is significant (p=0.0007, large effect), but vs D-22 it does not reach significance (p=0.125).

### 4.5 Per-Query Degradation Analysis

#### D-23 vs D-22

| Status                       | Count | Percentage |
| ---------------------------- | ----- | ---------- |
| Improved (at least 1 metric) | 35/36 | 97.2%      |
| Degraded (at least 1 metric) | 16/36 | 44.4%      |
| Q-13 unchanged (all zero)    | 1/36  | 2.8%       |

**16 of 36 queries (44.4%) degraded on at least one metric vs D-22.** The degradation is concentrated in P@5 and R@10; NDCG shows improvement for nearly all queries (though the NDCG values themselves are invalid).

#### D-23 vs D-21 (across 3 D-21 model variants, 108 comparisons)

| Status   | Count   | Percentage |
| -------- | ------- | ---------- |
| Improved | 104/108 | 96.3%      |
| Degraded | 53/108  | 49.1%      |

The 49.1% degradation rate triggered the **NO-PASS on Criterion 6** (threshold: <25%) in the GO/NO-GO framework. Note: this high rate reflects that many queries improved on _some_ metrics (primarily NDCG, which is buggy) while degrading on others (P@5, R@10).

### 4.6 GO/NO-GO Decision

| #   | Criterion                                     | Result                   | Status     |
| --- | --------------------------------------------- | ------------------------ | ---------- |
| 1   | Execution (<5% overflow)                      | 0/1,266 (0.0%)           | ✅ PASS    |
| 2   | Improvement over D-21 (≥3/4 metrics positive) | 3/4 positive ⚠️          | ✅ PASS ⚠️ |
| 3   | Improvement over D-22 (≥2/4 metrics positive) | 2/4 positive ⚠️          | ✅ PASS ⚠️ |
| 4   | Statistical significance (≥2 metrics at α)    | 3/4 significant ⚠️       | ✅ PASS ⚠️ |
| 5   | Marginal value (>5% gain over D-22, ≥1)       | 1/4 ⚠️                   | ✅ PASS ⚠️ |
| 6   | No catastrophic degradation (<25%)            | 49.1% degraded           | ❌ FAIL    |
| 7   | Authority/Temporal benefit                    | Temporal > Factual: True | ✅ PASS    |

**Framework decision: GO** (6/7 pass, mandatory criteria met)

> **⚠️ CAVEAT:** The GO decision is **unreliable** because 4 of the 6 passing criteria depend on NDCG@10, which is invalid. If NDCG were excluded:
>
> - Criterion 2: Only MRR is positive for valid metrics; P@5 is negative, R@10 is flat → likely FAIL
> - Criterion 3: Only MRR shows improvement in valid metrics → likely FAIL
> - Criterion 4: Would need re-evaluation without NDCG
> - Criterion 5: No valid metric shows >5% gain over D-22 except MRR (+3.9%, below threshold) → likely FAIL
>
> **A conservative reassessment using only valid metrics (P@5, R@10, MRR) would likely produce a NO-GO or at best a borderline decision.**

---

## 5. Analysis

### 5.1 The Precision-Recall Paradox

D-23 presents a contradictory picture: **MRR improved** (the right document appears first more often), but **Precision and Recall degraded** (fewer relevant results in the top 5 and top 10).

How is this possible? The most likely explanation is the **chunking change**:

- D-21/D-22 produced 218 large chunks (mean ~782 tokens of content)
- D-23 produced 1,266 small chunks (mean ~132 tokens of content)

With 6× more chunks in the index, the top-10 retrieval window samples a much smaller _fraction_ of each document. A query that previously surfaced 2 large chunks from a relevant document (covering most of its content) now might surface only 1 small chunk (covering one paragraph). That's a win for MRR (the right document still appears at rank 1) but a loss for Recall (fewer total chunks from relevant documents appear).

**The enrichment prefix may simply be a better "first-hit identifier" than a "comprehensive content retriever."** The 5-layer prefix tells the embedding model _what kind of document this is_ — and that's enough to rank the first result correctly. But 132 tokens of actual content isn't enough for the model to assess deeper relevance across multiple chunks from the same document.

### 5.2 Where Multi-Layer Enrichment Helps

**MRR across all types** — the multi-layer prefix makes first-result accuracy better than both D-21 and D-22 in every query category. This is the clearest positive signal from D-23.

**Temporal MRR = 1.0** — Every temporal query now returns a relevant document in position 1. This was 0.87 in D-21 and 0.89 in D-22. The enrichment prefix's authority and domain signals appear to provide strong type-matching for time-referenced queries.

### 5.3 Where Multi-Layer Enrichment Hurts

**Multi-hop queries** suffered the worst Precision and Recall losses vs D-22 (P@5: -0.15, R@10: -0.25). These queries require finding chunks across _multiple_ documents, and the smaller chunks don't provide enough cross-document context. D-22's larger chunks (with single-layer enrichment) were better at this because each chunk contained more text that might reference other entities.

**Temporal Recall** dropped from 1.42 (D-22) to 0.92 (D-23) — a -35% loss. This is especially notable because D-22's Temporal queries were its strongest category. The enrichment helps MRR but the smaller content window costs coverage.

### 5.4 The Confounding Variable Problem

D-23's results are **confounded by two simultaneous changes** from D-21/D-22:

| Variable           | D-21/D-22  | D-23     | Effect                       |
| ------------------ | ---------- | -------- | ---------------------------- |
| Multi-layer prefix | 0–1 layers | 5 layers | Adds contextual signals      |
| Max chunk tokens   | 1,024      | 600      | 6× more, much smaller chunks |
| Overlap tokens     | 150        | 50       | Less boundary continuity     |

It is **impossible to determine** whether the Precision/Recall regressions are caused by:

- (a) Multi-layer enrichment diluting the embedding signal (too much prefix, not enough content)
- (b) Smaller chunks losing sentence-level context that helped D-22
- (c) Reduced overlap fragmenting cross-boundary concepts

**D-24 should isolate the enrichment variable** by matching D-21/D-22's chunk parameters (`max_chunk_tokens = 1024`, `overlap = 150`) while retaining the multi-layer prefix.

### 5.5 Missing Layers (Root Cause Confirmed)

Only 5 of the planned 8 layers are populated:

| Layer          | Status            |
| -------------- | ----------------- |
| Corpus         | ✅ Present (100%) |
| Domain         | ✅ Present (100%) |
| Entity         | ✅ Present (100%) |
| Authority      | ✅ Present (100%) |
| Section        | ✅ Present (94%)  |
| Temporal       | ❌ Missing        |
| Relational     | ❌ Missing        |
| Chunk Sequence | ❌ Missing        |

**Root cause (confirmed):** The `FIELD_MAP` in Cell 5 maps the wrong metadata key names. The corpus YAML frontmatter uses:

| Layer Builder Expects | Corpus Actually Has                                             | Result                                         |
| --------------------- | --------------------------------------------------------------- | ---------------------------------------------- |
| `era`                 | `temporal_markers`                                              | `build_temporal_layer()` → None for all docs   |
| `related_entities`    | `cross_references`, `factions_mentioned`, `locations_mentioned` | `build_relational_layer()` → None for all docs |

Every document has `temporal_markers` (e.g., `["Year 783 PG", "Post-Glitch era"]`) and `cross_references` (e.g., `["Silent Folk", "Echo-Mothers"]`), but the normalization code didn't know to look for them.

**Fix applied in Round 3:** Added `temporal_markers` to the `era` field mapping and `cross_references` to the `related_entities` mapping. Updated `build_temporal_layer()` to handle the marker format and `build_relational_layer()` to handle simple string-list cross-references plus `factions_mentioned` and `locations_mentioned`. See `fix_d23_round3.py`.

The "multi-layer" enrichment was effectively a **5-layer** enrichment. With the fix, Round 3 will run with the full 7 layers (Chunk Sequence remains unimplemented as it requires a different input source).

---

## 6. Token Budget Analysis

### 6.1 Prefix Budget vs. Content Budget

| Metric                     | Value        |
| -------------------------- | ------------ |
| Mean prefix tokens         | 63.8         |
| Mean content tokens        | 131.9        |
| **Prefix : Content ratio** | **0.48 : 1** |
| Max prefix tokens          | 84           |
| Reserved for prefix        | 150          |
| Unused reserve headroom    | ~66          |

The prefix consumes nearly half the total embedding input, on average. For chunks shorter than the mean (and there are many, given the median of 102), the prefix actually outweighs the content. This is a concerning ratio — it means the embedding model is spending significant capacity encoding structural metadata rather than document content.

### 6.2 Per-Layer Token Cost

| Layer     | Mean Tokens | % of Total Prefix |
| --------- | ----------- | ----------------- |
| Corpus    | 6.0         | 9.4%              |
| Domain    | 16.4        | 25.7%             |
| Entity    | 16.1        | 25.2%             |
| Authority | 9.5         | 14.9%             |
| Section   | 14.4        | 22.6%             |

Domain and Entity are the most expensive layers (~16 tokens each). For a layer ablation study (D-24), the priority order for removal testing should be: Corpus (cheapest, most generic) → Authority → Section → Domain/Entity.

### 6.3 Recommendation: Reduce Prefix Reserve

Actual overhead maxes at 84 tokens. The 150-token reserve wastes 66 tokens of potential content space per chunk. Reducing `prefix_reserve_tokens` to 100 would be conservative and safe, reclaiming ~50 tokens per chunk for content.

---

## 7. NDCG Bug Investigation (Confirmed)

### 7.1 Symptom

| Condition       | Count | Percentage |
| --------------- | ----- | ---------- |
| NDCG@10 > 1.0   | 30/36 | 83.3%      |
| NDCG@10 > 2.0   | 19/36 | 52.8%      |
| NDCG@10 maximum | 2.786 | —          |

### 7.2 Confirmed Root Cause

The bug is a **duplicate-counting interaction** between the Round 2 chunk-ID fix and the NDCG formula:

```python
# Round 2 fix in compute_all_metrics():
retrieved = [r["chunk_id"].split("#")[0] for r in qr.results]
# This maps 'doc.md#chunk_001', 'doc.md#chunk_002', ... all to 'doc.md'

# In ndcg_at_k():
# DCG: iterates over ALL retrieved IDs (including duplicates)
for i, chunk_id in enumerate(top_k):      # 7 entries of 'doc.md'
    rel = relevance_scores.get(chunk_id, 0)  # each gets rel=2
    dcg += rel / log2(i + 2)                 # DCG ≈ 7.9

# IDCG: uses only unique relevance_scores values
ideal_rels = sorted(relevance_scores.values())[:k]  # only [2, 2]
# IDCG ≈ 3.3

# Result: NDCG = 7.9 / 3.3 = 2.42 (impossible!)
```

The DCG numerator counts the same document 7 times (once per chunk), but the IDCG denominator only has 2 entries (one per unique relevant document). This produces NDCG > 1.0 whenever multiple chunks from a relevant document appear in the top-k results — which is the _common_ case when documents are split into many small chunks.

### 7.3 Fix Applied

**Deduplication before DCG computation** (`fix_d23_round3.py`):

```python
# Only keep first occurrence of each document ID
seen = set()
deduped = []
for rid in retrieved_ids[:k]:
    if rid not in seen:
        seen.add(rid)
        deduped.append(rid)
# Compute DCG on deduped list
```

This ensures DCG and IDCG operate on the same cardinality. P@5 and R@10 were already correct because they use `set()` operations that naturally deduplicate.

### 7.4 Impact on Analysis

- **NDCG-dependent conclusions are invalid.** Any comparison involving NDCG@10 (including 4 of 7 GO/NO-GO criteria) cannot be trusted.
- **P@5, R@10, and MRR are unaffected.** These metrics use set-membership checks and are not subject to the normalization bug.
- **The round-1 metric bug (chunk ID format) has been fixed.** The issue is confined to the NDCG scoring formula.
- **Round 3 will produce corrected NDCG values** bounded in [0, 1].

---

## 8. Visualizations

### 8.1 3-Way Comparison Bar Chart

The bar chart shows D-23 (green) compared to D-21 (blue) and D-22 (orange) across all four metrics and query types. The NDCG bars for D-23 are clearly anomalous — exceeding 1.0 across all panels. The P@5 and R@10 bars show D-23 consistently lower than D-22 and approximately equal to or below D-21.

### 8.2 Per-Query Delta Heatmaps

Two heatmaps show per-query deltas. The left panel (D-23 vs D-21) shows mixed results across all rows — unlike Round 1's uniform dark red. The right panel (D-23 vs D-22) shows prominent red cells in P@5 and R@10 columns, with green NDCG columns (reflecting the inflated NDCG values).

### 8.3 Layer Token Distribution

Box plot showing per-layer token distributions across all 1,266 chunks. Corpus is a constant 6 tokens. Authority is the tightest distribution (9–10). Section shows the widest spread with outliers up to 26 tokens. This visualization is valid and informative for D-24 ablation planning.

---

## 9. Comparison with Round 1

| Aspect            | Round 1                       | Round 2                                 |
| ----------------- | ----------------------------- | --------------------------------------- |
| Chunk-ID bug      | ❌ All metrics = 0.0          | ✅ Fixed (non-zero results)             |
| NDCG computation  | N/A (all zero)                | ❌ New bug (values > 1.0)               |
| P@5, R@10, MRR    | Invalid                       | ✅ Valid                                |
| Token overflow    | ✅ 0% (same)                  | ✅ 0% (same)                            |
| Layer token data  | ✅ Valid (same)               | ✅ Valid (same)                         |
| GO/NO-GO decision | NO-GO (1/7 real, 2/7 nominal) | GO (6/7 nominal, ~2/7 if NDCG excluded) |

---

## 10. Exported Artefacts

| File                                         | Contents                               | Valid?                                |
| -------------------------------------------- | -------------------------------------- | ------------------------------------- |
| `d23_results.csv`                            | 36 rows — per-query metrics            | ⚠️ P@5, R@10, MRR valid; NDCG invalid |
| `d23_delta_vs_d21.csv`                       | 108 rows — delta vs 3 D-21 models      | ⚠️ Same caveat                        |
| `d23_delta_vs_d22.csv`                       | 36 rows — delta vs D-22                | ⚠️ Same caveat                        |
| `d23_significance_results.csv`               | 12 rows — Wilcoxon tests (3 pairs × 4) | ⚠️ NDCG rows invalid                  |
| `d23_go_nogo_decision.txt`                   | GO (6/7 pass)                          | ⚠️ Unreliable (see §4.6)              |
| `d23_layer_token_audits.csv`                 | 1,266 rows — per-chunk layer breakdown | ✅ Valid                              |
| `visualization_3way_comparison.png`          | Bar chart — 3-way comparison           | ⚠️ NDCG bars invalid                  |
| `visualization_delta_heatmap.png`            | Per-query delta heatmaps               | ⚠️ NDCG column invalid                |
| `visualization_layer_token_distribution.png` | Box plot — layer token distributions   | ✅ Valid                              |

---

## 11. Summary

### What D-23 Round 2 Tells Us

1. **The chunk-ID metric bug from Round 1 is fixed.** Retrieval metrics are now non-zero and the pipeline produces real results.

2. **A new NDCG computation bug was discovered.** NDCG values exceed 1.0 (up to 2.79), invalidating all NDCG-dependent conclusions including the GO/NO-GO decision.

3. **On valid metrics (P@5, R@10, MRR): multi-layer enrichment is a mixed bag.**
   - ✅ MRR improved vs both baselines (+5.8% vs D-21, +3.9% vs D-22). 31/36 queries now have perfect first-result accuracy.
   - ❌ Precision@5 regressed from both baselines (-14.4% vs D-21, -21.3% vs D-22).
   - ❌ Recall@10 is flat vs D-21 and down 21.5% vs D-22.

4. **The results are confounded by chunking changes.** D-23 simultaneously changed enrichment layers (1 → 5), chunk size (1,024 → 600), and overlap (150 → 50). It is impossible to attribute the P@5/R@10 regressions to enrichment vs. chunking.

5. **Token overflow is solved.** 0% overflow (vs D-22's 43.1%). Prefix-reserve budgeting works.

6. **Only 5 of 8 layers are populated.** Temporal, Relational, and Chunk Sequence are missing.

### What D-23 Round 2 Does NOT Tell Us

- Whether multi-layer enrichment improves or harms retrieval when chunking is held constant
- The actual NDCG performance (due to the computation bug)
- The contribution of individual enrichment layers (no ablation)
- The effect of Temporal/Relational layers (unpopulated)

---

## 12. Recommendations & Resolution (Round 3 Fixes Applied)

All three issues identified in Round 2 have been addressed in `fix_d23_round3.py`:

### 12.1 ✅ NDCG Bug — Fixed

**Fix:** Deduplicate retrieved IDs before DCG computation. Only the first occurrence of each document ID contributes to the score. IDCG remains unchanged (already correct).

**Verification:** Synthetic test confirms fix produces NDCG = 1.0 for perfect retrieval (previously 2.42).

### 12.2 ✅ Missing Layers — Fixed

**Fix:** Added `temporal_markers` to FIELD_MAP's `era` mapping and `cross_references` to `related_entities`. Updated `build_temporal_layer()` to handle `["Year 783 PG", "Post-Glitch era"]` format. Updated `build_relational_layer()` to handle simple string-list cross-references and incorporate `factions_mentioned`/`locations_mentioned`.

**Expected impact:** Round 3 will have 7 active layers (up from 5). All 77 corpus documents have both `temporal_markers` and `cross_references`.

### 12.3 ✅ Chunking Parameters — Aligned

**Fix:** Changed `max_chunk_tokens` from 600 → 1024 and `overlap` from 50 → 150 to match D-21/D-22. Reduced `prefix_reserve_tokens` from 150 → 100 (actual max overhead was 84 tokens).

**Expected impact:** Chunk count should be comparable to D-21/D-22 (~218 vs Round 2's 1,266). Effective content window = 924 tokens (vs D-21/D-22's 1024). This isolates the enrichment effect from chunking geometry.

### 12.4 Round 3 Next Steps

1. **Upload patched `D23-multi-layer.ipynb` to Colab and re-run all cells**
2. **Download results to `notebooks/results/d23/round-3/`**
3. **Verify:** NDCG in [0, 1], Temporal/Relational layers in token audit, chunk count ~218
4. **Re-evaluate GO/NO-GO** with corrected data
5. **Write Round 3 findings** with controlled comparison to D-21/D-22

### 12.5 For D-24

1. **Layer ablation study** — test subsets of layers (e.g., Domain-only, Domain+Entity, all-7) to identify which contribute most.
2. **Variable-depth enrichment** — fewer layers for content-rich documents, more for generic/short ones.
3. **Target prefix-to-content ratio ≤ 0.15:1** — Round 2's 0.48:1 was too high.
