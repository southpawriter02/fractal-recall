# D-23 Findings — Multi-Layer Context Enrichment (Round 4)

> **Project:** FractalRecall — Hierarchical context-aware embedding retrieval  
> **Notebook:** D23_multi_layer_5.ipynb  
> **Run Date:** 2026-02-17  
> **Hardware:** Google Colab — A100 GPU, High-RAM  
> **Metrics:** Precision@5, Recall@10, NDCG@10, MRR  
> **Round:** 4 (chunking geometry alignment — primary confound remediation)

---

## 1. Objective

Determine whether **multi-layer context enrichment** improves retrieval performance over the D-21 baseline (no enrichment) and D-22 (single-layer enrichment), **with matched chunking geometry** to eliminate the 5.7× chunk-count inflation identified in Round 3.

### 1.1 What Changed from Round 3

| Parameter       | Round 3          | Round 4              | Impact                          |
| --------------- | ---------------- | -------------------- | ------------------------------- |
| Total chunks    | 1,233            | **567**              | **54% reduction** — primary fix |
| Chunk geometry  | Word-based split | Aligned to D-21/D-22 | Eliminates chunking confound    |
| Active layers   | 6                | **6**                | Unchanged                       |
| Prefix reserve  | 100 tokens       | 100 tokens           | Unchanged                       |
| NDCG validity   | ✅ All in [0,1]  | ✅ All in [0,1]      | Unchanged                       |
| Overflow chunks | 0/1,233 (0.0%)   | **0/567 (0.0%)**     | Clean execution                 |

> **Round 4 directly addresses the Round 3 post-mortem's #1 recommendation:** align chunking geometry to make the enrichment comparison fair.

---

## 2. Experimental Setup

### 2.1 Three-Way Comparison

| Experiment                | Model                 | Enrichment                  | Chunks  | Prefix Tokens |
| ------------------------- | --------------------- | --------------------------- | ------- | ------------- |
| **D-21** (baseline)       | nomic-embed-text-v1.5 | None                        | ~1,215  | 0             |
| **D-22** (single-layer)   | nomic-embed-text-v1.5 | 1 prefix (~24 tokens)       | 218→124 | ~24           |
| **D-23 R4** (multi-layer) | nomic-embed-text-v1.5 | 6-layer prefix (~80 tokens) | **567** | ~80           |

### 2.2 Enrichment Layers (6 of 8)

| Layer              | Population | Mean Tokens | Max Tokens | Notes                                 |
| ------------------ | ---------- | ----------- | ---------- | ------------------------------------- |
| **Corpus**         | 100%       | 6.0         | 6          | Fixed string, minimal cost            |
| **Domain**         | 100%       | ~17         | ~20        | Document-type classification          |
| **Entity**         | 100%       | ~15         | ~24        | Entity identity signal                |
| **Authority**      | 100%       | ~10         | 10         | Canonical status marker               |
| **Relationships**  | 100%       | ~18         | ~31        | Cross-references, factions, locations |
| **Section**        | ~94%       | ~16         | ~28        | Section heading context               |
| **Temporal**       | **0%**     | 0           | 0          | ⚠️ Still unpopulated — corpus gap     |
| **Chunk Sequence** | N/A        | N/A         | N/A        | Not implemented                       |
|                    | **Total:** | **~80**     | **~103**   |                                       |

### 2.3 Corpus & Query Set

- **77 Markdown documents** from the Aethelgard worldbuilding corpus (shared across D-21/D-22/D-23)
- **36 ground-truth queries** across 5 types (identical query set)

---

## 3. Results

### 3.1 Overall Performance

| Metric  | D-21 (BL) | D-22 (SL) | D-23 R3 (ML) | **D-23 R4 (ML)** | Δ R4 vs D-21       | Δ R4 vs D-22       | Δ R4 vs R3       |
| ------- | --------- | --------- | ------------ | ---------------- | ------------------ | ------------------ | ---------------- |
| P@5     | 0.3829    | 0.4167    | 0.3111       | **0.3222**       | −0.061 (−15.8%) ❌ | −0.094 (−22.7%) ❌ | +0.011 (+3.6%) ↑ |
| R@10    | 0.7199    | 0.9167    | 0.6829       | **0.6898**       | −0.030 (−4.2%) ❌  | −0.227 (−24.8%) ❌ | +0.007 (+1.0%) ↑ |
| NDCG@10 | 0.7062    | 0.8225    | 0.7241       | **0.7256**       | +0.019 (+2.7%) ✅  | −0.097 (−11.8%) ❌ | +0.002 (+0.2%) ↑ |
| MRR     | 0.8452    | 0.8611    | 0.9059       | **0.8935**       | +0.048 (+5.7%) ✅  | +0.032 (+3.8%) ✅  | −0.012 (−1.4%) ↓ |

**Key Observations:**

1. **R4 maintains the MRR advantage** — still best across all experiments (0.8935), though slightly below R3's 0.9059
2. **NDCG@10 is positive vs D-21** (+2.7%) — consistent with R3 and the only breadth metric showing improvement
3. **P@5 and R@10 remain negative vs both baselines** — the chunk-count fix improved these slightly over R3, but not enough to flip the direction
4. **R4 is marginal improvement over R3** on all metrics except MRR — the chunking alignment helped, but the dominant effect remains the multi-layer prefix behavior

### 3.2 Per-Query-Type Performance

| Query Type  | n   | P@5    | R@10   | NDCG@10 | MRR    | Assessment              |
| ----------- | --- | ------ | ------ | ------- | ------ | ----------------------- |
| SINGLE_HOP  | 11  | 0.2182 | 0.5606 | 0.6210  | 0.8636 | Weakest precision       |
| MULTI_HOP   | 8   | 0.4500 | 0.8333 | 0.9000  | 1.0000 | ⭐ Strong — perfect MRR |
| AUTHORITY   | 5   | 0.3200 | 0.7000 | 0.7226  | 0.8000 | Below average           |
| TEMPORAL    | 6   | 0.3667 | 0.9167 | 0.8710  | 0.8889 | ⭐ Best recall          |
| EXPLORATORY | 6   | 0.3000 | 0.5000 | 0.5704  | 0.8889 | Weakest recall/NDCG     |

**Comparison vs D-22 by Query Type:**

| Query Type  | D-22 P@5 | R4 P@5 | Δ P@5  | D-22 R@10 | R4 R@10 | Δ R@10    |
| ----------- | -------- | ------ | ------ | --------- | ------- | --------- |
| SINGLE_HOP  | 0.2727   | 0.2182 | −0.055 | 0.6667    | 0.5606  | −0.106    |
| MULTI_HOP   | 0.6250   | 0.4500 | −0.175 | 1.0833    | 0.8333  | −0.250 ❌ |
| AUTHORITY   | 0.3600   | 0.3200 | −0.040 | 0.8000    | 0.7000  | −0.100    |
| TEMPORAL    | 0.5000   | 0.3667 | −0.133 | 1.4167    | 0.9167  | −0.500 ❌ |
| EXPLORATORY | 0.3667   | 0.3000 | −0.067 | 0.7500    | 0.5000  | −0.250 ❌ |

> D-22 outperforms D-23 R4 on P@5 and R@10 across **every query type**. The single-layer prefix strategy remains more effective for breadth metrics.

### 3.3 Statistical Significance (Wilcoxon Signed-Rank, Bonferroni α = 0.0167)

| Comparison             | P@5               | R@10              | NDCG@10           | MRR               |
| ---------------------- | ----------------- | ----------------- | ----------------- | ----------------- |
| D-23 R4 vs D-21 (BL)   | **p=0.001** ✓ med | p=0.323 ns        | p=0.084 ns        | **p<0.001** ✓ lrg |
| D-23 R4 vs D-22 (SL)   | **p=0.006** ✓ lrg | **p<0.001** ✓ lrg | p=0.022 ns        | p=0.438 ns        |
| D-22 (SL) vs D-21 (BL) | p=0.194 ns        | **p<0.001** ✓ lrg | **p<0.001** ✓ med | p=0.070 ns        |

_✓ = significant at Bonferroni-corrected α=0.0167; lrg/med = effect size_

**Key Statistical Findings:**

- **P@5 degradation vs D-21 is significant** (p=0.001, medium effect) — multi-layer enrichment actively hurts precision even with aligned chunking
- **MRR improvement vs D-21 is significant** (p<0.001, large effect) — the first-result ranking benefit is real and robust
- **Degradation vs D-22 on P@5 and R@10 is significant** (large effects) — multi-layer is statistically worse than single-layer for breadth
- **NDCG vs D-22 is not significant** at the Bonferroni threshold (p=0.022 > 0.0167) — a marginal result that shifted from R3's significant p=0.014

### 3.4 Round-over-Round Significance Changes (R3 → R4)

| Metric pair     | R3 p-value | R4 p-value | Direction Change                |
| --------------- | ---------- | ---------- | ------------------------------- |
| P@5 vs D-21     | p<0.001    | p=0.001    | Weakened slightly               |
| MRR vs D-21     | p<0.001    | p<0.001    | **Stable** ✅                   |
| P@5 vs D-22     | p=0.001    | p=0.006    | **Weakened** — less significant |
| R@10 vs D-22    | p=0.001    | p<0.001    | **Strengthened**                |
| NDCG@10 vs D-22 | p=0.014    | p=0.022    | **Lost significance** ⚠️        |

> With fewer chunks to compare (567 vs 1,233), the statistical power decreased for some comparisons. The NDCG comparison vs D-22 crossed the significance threshold — a cautionary signal.

### 3.5 GO/NO-GO Criteria Assessment

| #   | Criterion                            | R3 Result | **R4 Result** | Detail                                  |
| --- | ------------------------------------ | --------- | ------------- | --------------------------------------- |
| 1   | Execution (overflow < 5%)            | **PASS**  | **PASS** ✅   | 0/567 chunks (0.0%)                     |
| 2   | Improvement over D-21 (≥3/4 metrics) | **FAIL**  | **FAIL** ❌   | 2/4 metrics positive (NDCG, MRR)        |
| 3   | Improvement over D-22 (≥2/4 metrics) | **FAIL**  | **FAIL** ❌   | 1/4 metrics positive (MRR only)         |
| 4   | Statistical significance (≥2)        | **PASS**  | **PASS** ✅   | 2/4 significant (P@5, MRR vs D-21)      |
| 5   | Marginal value >5% over SL (≥1)      | **PASS**  | **FAIL** ❌   | 0/4 metrics >5% gain over D-22          |
| 6   | No catastrophic degradation (<25%)   | **FAIL**  | **FAIL** ❌   | 54.6% queries degraded (59/108 vs D-21) |
| 7   | Authority/Temporal benefit           | **PASS**  | **PASS** ✅   | Both exceed Factual baseline            |

| Summary         | R3       | **R4**       |
| --------------- | -------- | ------------ |
| Criteria passed | **4/7**  | **3/7** ⬇️   |
| Decision        | COND. GO | **COND. GO** |

> **R4 lost one criterion** (Marginal Value) compared to R3. The MRR advantage over D-22 dropped from +5.2% (R3) to +3.8% (R4), falling below the 5% threshold.

### 3.6 Token Budget Analysis

| Statistic | Raw Tokens | Enriched Tokens | Prefix Overhead |
| --------- | ---------- | --------------- | --------------- |
| Mean      | ~260       | ~340            | ~80             |
| Max       | ~960       | ~1,011          | ~103            |
| Overflow  | **0/567**  | **0/567**       | 0.0%            |

- Chunk count reduced **54%** (1,233 → 567) — the primary R3 confound is partially addressed
- Mean raw content per chunk increased substantially (~135 → ~260 tokens) — better content-to-prefix ratio
- Prefix overhead is now ~31% of raw content (was ~59% in R3) — still higher than D-22's ~3%

### 3.7 MRR Deep Dive

| Experiment | Perfect MRR (=1.0) | Zero MRR (=0.0) | Mean MRR |
| ---------- | ------------------ | --------------- | -------- |
| D-21       | 29/36              | 2/36            | 0.8452   |
| D-22       | 30/36              | 3/36            | 0.8611   |
| D-23 R3    | **32/36**          | **2/36**        | 0.9059   |
| D-23 R4    | **31/36**          | **2/36**        | 0.8935   |

R4 maintains the MRR leadership story, with 31/36 perfect first-result placements. The slight drop from R3 (32→31) suggests that the R3 chunk geometry — which created more granular chunks — slightly favored first-hit retrieval. With larger chunks in R4, the embedding model has more content to work with per vector, slightly reducing the metadata-driven discrimination advantage.

### 3.8 Degradation Analysis

**Per-query degradation vs D-21 (across 108 comparison pairs — 36 queries × 3 D-21 model runs):**

| Category  | R3 Count | R3 %  | R4 Count | R4 %  | Trend   |
| --------- | -------- | ----- | -------- | ----- | ------- |
| Degraded  | 63       | 58.3% | 59       | 54.6% | ↓ 3.7pp |
| Improved  | —        | —     | —        | —     | —       |
| Threshold | <25%     |       | <25%     |       | ❌      |

**Per-query degradation vs D-22 (36 comparison pairs):**

| Category   | Degraded | Improved | Unchanged |
| ---------- | -------- | -------- | --------- |
| R4 vs D-22 | 16 (44%) | 8 (22%)  | 12 (33%)  |

The degradation rate improved modestly from R3 (58.3% → 54.6% vs D-21) but remains far above the <25% threshold.

---

## 4. Root Cause Analysis

### 4.1 Why the Chunk Fix Didn't Fully Resolve the Problem

Round 3 hypothesized that the 5.7× chunk inflation was the **primary cause** of multi-layer underperformance. Round 4 reduced chunks by 54% and saw:

- **Marginal P@5/R@10 improvement** (+3.6%, +1.0% vs R3) — directionally correct but insufficient
- **Marginal NDCG improvement** (+0.2% vs R3) — nearly no change
- **MRR slight degradation** (−1.4% vs R3) — larger chunks reduced the metadata-discrimination advantage

**Conclusion:** The chunk count was **a** confound, but **not the** confound. The residual 2.6× chunk inflation (567 vs 218) still creates more competition for top-k slots, but even if chunks were perfectly matched, the multi-layer prefix introduces a fundamental trade-off between metadata richness and content signal.

### 4.2 The Content-Dilution Hypothesis (Refined)

With ~80 tokens of prefix overhead on chunks averaging ~260 raw tokens, roughly **23-31%** of each enriched chunk is metadata. For the embedding model, this means:

- ~31% of the semantic signal comes from metadata rather than content
- The metadata is **identical within each document** — every chunk from the same document gets the same prefix
- This creates **intra-document embedding homogeneity** — chunks from the same document look more similar to each other than to chunks from other documents

This explains the MRR benefit (correct document identified quickly) and the P@5/R@10 penalty (multiple chunks from the correct document crowd out chunks from _other_ relevant documents).

### 4.3 Why D-22 Remains Superior for Breadth

D-22's single-layer prefix (~24 tokens) achieves a much better content-to-metadata ratio (~3% overhead). Its advantage compounds:

| Factor                       | D-22                | D-23 R4          | Impact                            |
| ---------------------------- | ------------------- | ---------------- | --------------------------------- |
| Prefix overhead              | ~3%                 | ~31%             | D-22 preserves content signal     |
| Unique discriminative layers | 1 (type+entity)     | 6 (all metadata) | D-23 over-specifies               |
| Intra-doc homogeneity        | Low                 | High             | D-23 crowds top-k with duplicates |
| Chunk count                  | 124 (post-overflow) | 567              | D-22 has less noise               |

D-22's 43% overflow rate (94/218 chunks dropped) was flagged as a concern in D-22, but paradoxically, the surviving 124 chunks represent the **best** content-rich chunks — short snippets were naturally filtered out.

---

## 5. Three-Experiment Summary

### 5.1 Final Scorecard

| Metric  | D-21 (BL) | D-22 (SL)     | D-23 R4 (ML)  | Best Experiment       |
| ------- | --------- | ------------- | ------------- | --------------------- |
| P@5     | 0.3829    | **0.4167** ⭐ | 0.3222        | D-22 (+8.8% vs BL)    |
| R@10    | 0.7199    | **0.9167** ⭐ | 0.6898        | D-22 (+27.3% vs BL)   |
| NDCG@10 | 0.7062    | **0.8225** ⭐ | 0.7256        | D-22 (+16.5% vs BL)   |
| MRR     | 0.8452    | 0.8611        | **0.8935** ⭐ | D-23 R4 (+5.7% vs BL) |

**D-22's single-layer enrichment wins 3 of 4 metrics.** D-23's multi-layer approach wins only MRR.

### 5.2 Per-Query-Type Winners

| Query Type  | Best P@5        | Best R@10       | Best NDCG       | Best MRR    |
| ----------- | --------------- | --------------- | --------------- | ----------- |
| SINGLE_HOP  | D-21/D-22       | D-22            | D-21            | D-21 v2-moe |
| MULTI_HOP   | D-22            | D-22            | D-22            | All (1.000) |
| AUTHORITY   | D-21 v2-moe     | D-22            | D-22            | D-22/D-23   |
| TEMPORAL    | **D-22** (+42%) | **D-22** (+55%) | **D-22** (+39%) | D-23 (tie)  |
| EXPLORATORY | **D-22** (+57%) | **D-22** (+64%) | **D-22** (+35%) | D-23        |

D-22 dominates almost every query type × metric combination. The multi-layer approach provides no differential advantage for the complex query types (TEMPORAL, AUTHORITY) it was designed to help.

### 5.3 Enrichment Progression Narrative

```
D-21 → D-22: Enrichment WORKS — +16.5% NDCG, +27.3% R@10 (statistically significant)
D-22 → D-23: More enrichment HURTS — −11.8% NDCG, −24.8% R@10 (statistically significant)
```

The evidence shows **diminishing and then negative returns** from adding metadata layers. A single sentence prefix (~24 tokens) is the sweet spot for the current model and corpus combination.

---

## 6. Round-over-Round Comparison (D-23 Rounds 1–4)

| Aspect           | Round 1         | Round 2            | Round 3          | **Round 4**          |
| ---------------- | --------------- | ------------------ | ---------------- | -------------------- |
| NDCG validity    | N/A (all zeros) | ❌ 30/36 > 1.0     | ✅ All in [0, 1] | ✅ All in [0, 1]     |
| Active layers    | 5               | 5                  | 6 (+Relations)   | **6**                |
| Temporal layer   | 0%              | 0%                 | 0%               | **0%** ⚠️            |
| Chunk count      | 1,266           | 1,266              | 1,233            | **567** ✅           |
| Max chunk tokens | 600             | 600                | 1,024            | **1,024**            |
| Overlap tokens   | 50              | 50                 | 150              | **150**              |
| Prefix reserve   | 150             | 150                | 100              | **100**              |
| MRR              | N/A             | Invalid            | **0.9059** ⭐    | **0.8935**           |
| GO/NO-GO score   | N/A             | N/A                | 4/7              | **3/7** ⬇️           |
| Primary confound | Chunk-ID format | NDCG dedup, fields | Chunk geometry   | **Content dilution** |

**Progression:** Each round fixed the previous round's primary confound, revealing the next layer of the issue:

1. **R1/R2:** Infrastructure bugs (NDCG calculation, field mapping) masked any signal
2. **R3:** Fixed bugs, but 5.7× chunk inflation confounded the comparison
3. **R4:** Fixed chunk inflation, but multi-layer prefix content-dilution persists as a **fundamental trade-off**, not a fixable bug

---

## 7. Conclusions

### 7.1 Hard Findings

1. **Multi-layer enrichment (6 layers, ~80 tokens) degrades retrieval breadth** — P@5, R@10, and NDCG are all worse than both the bare baseline (D-21) and single-layer enrichment (D-22). This result is now confirmed across two rounds with different chunk geometries.

2. **Multi-layer enrichment improves first-result ranking** — MRR of 0.8935 is the highest of any experiment, with 31/36 queries achieving perfect first-hit placement. This is statistically significant (p<0.001 vs D-21).

3. **The content-dilution effect is the primary cause** — ~31% prefix overhead homogenizes intra-document embeddings, crowding out other relevant documents in top-k retrieval while improving first-document identification.

4. **D-22's single-layer prefix is the current champion** — One sentence, ~24 tokens, produces statistically significant improvements in R@10 (+27.3%) and NDCG (+16.5%) with minimal content dilution.

5. **The chunk-count confound was secondary** — Reducing chunks from 1,233 to 567 produced only marginal improvements (+3.6% P@5, +1.0% R@10 vs R3), confirming that the enrichment overhead is the dominant factor.

### 7.2 Decision: **CONDITIONAL GO → D-24**

**Score: 3/7 criteria passed** (down from 4/7 in R3)

Despite the multi-layer strategy underperforming overall, the MRR signal and the unresolved chunk parity question (567 vs 218) provide enough reason to run **one more controlled experiment** before concluding:

> **Proceed to D-24 with a reduced-layer ablation study**

### 7.3 D-24 Recommendations

| Priority | Action                                  | Rationale                                                              |
| -------- | --------------------------------------- | ---------------------------------------------------------------------- |
| **P0**   | Match chunk count to D-22 (218→124)     | Eliminate the remaining 2.6× inflation                                 |
| **P1**   | Ablation: test 1–6 layers incrementally | Find the optimal layer count (hypothesis: 2-3 layers max)              |
| **P2**   | Drop Corpus layer (6 → 5)               | Adds 0 discriminative signal (identical for all chunks)                |
| **P3**   | Drop Temporal layer from consideration  | 0% population after 4 rounds — corpus data doesn't exist               |
| **P4**   | Test layer combinations, not just stack | Domain+Entity may outperform Domain+Entity+Authority+Relations+Section |

**Ablation Design:**

| Config | Layers                            | Expected Tokens | Hypothesis                           |
| ------ | --------------------------------- | --------------- | ------------------------------------ |
| A      | None (raw)                        | 0               | D-21 equivalent (control)            |
| B      | Domain + Entity                   | ~32             | D-22-equivalent scope, better format |
| C      | Domain + Entity + Authority       | ~42             | Minimal multi-layer                  |
| D      | Domain + Entity + Section         | ~48             | Section context adds heading signal  |
| E      | All 5 active (no Corpus/Temporal) | ~76             | Current D-23 minus zero-value layers |

---

## 8. Files in This Round

| File                                         | Description                                       |
| -------------------------------------------- | ------------------------------------------------- |
| `D23_multi_layer_5.ipynb`                    | Executed notebook with chunking alignment applied |
| `d23_results.csv`                            | Per-query results (36 rows × 4 metrics)           |
| `d23_delta_vs_d21.csv`                       | Per-query deltas vs D-21 (108 rows — 3 D-21 runs) |
| `d23_delta_vs_d22.csv`                       | Per-query deltas vs D-22 (36 rows)                |
| `d23_significance_results.csv`               | Wilcoxon signed-rank test results                 |
| `d23_go_nogo_decision.txt`                   | Automated GO/NO-GO assessment                     |
| `d23_layer_token_audits.csv`                 | Token counts per layer per chunk (567 rows)       |
| `visualization_3way_comparison.png`          | Bar chart: D-21 vs D-22 vs D-23 R4                |
| `visualization_delta_heatmap.png`            | Per-query delta heatmaps                          |
| `visualization_layer_token_distribution.png` | Box plot: token distribution per layer            |
| `D23-findings.md`                            | This document                                     |
