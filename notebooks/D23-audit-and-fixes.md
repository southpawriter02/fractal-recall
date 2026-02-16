# D-23 Audit: Multi-Layer Enrichment Notebook

Audit date: 2026-02-16
Auditor: Antigravity (automated)
Reference: D-21 baseline, D-22 single-layer (both previously audited and fixed)

## Summary

22 cells audited. **2 issues already fixed** (dependencies, prompt prefixes). **12 issues remaining** across critical, major, and minor severity.

---

## ✅ Already Fixed

| #   | Issue                                                          | Severity | Fix Applied                                                                             |
| --- | -------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------- |
| F1  | Bare `!pip install` with no version pins                       | Critical | `fix_d23_deps.py` — replaced with versioned subprocess install matching D21             |
| F2  | Stale `search_document`/`search_query` prefixes in ModelConfig | Critical | `fix_d23_deps.py` — updated `task_prefix_doc`/`task_prefix_query` to `document`/`query` |

---

## 🔴 Critical Issues (runtime errors)

### Issue 1: `METRIC_LABELS` never defined

**Cell(s):** 15, 16, 17, 18, 20
**Symptom:** `NameError: name 'METRIC_LABELS' is not defined`
**Detail:** `METRIC_LABELS` is used 12+ times across 5 cells but never defined anywhere. D22 doesn't define it either (D22 uses inline labels). Needs to be added to Cell 03 (configuration).
**Fix:** Add to Cell 03 after `METRICS`:

```python
METRIC_LABELS = ["P@5", "R@10", "NDCG@10", "MRR"]
```

### Issue 2: Cell 15 references undefined variables `all_results` and `QUERIES`

**Cell:** 15 (line 2353)
**Symptom:** `NameError: name 'all_results' is not defined`
**Detail:** Cell 15 calls `compute_all_metrics(all_results, QUERIES)` but:

- The query execution cell (12) stores results in `query_results`, not `all_results`
- The query definitions cell (04) stores queries in `GROUND_TRUTH_QUERIES`, not `QUERIES`
  **Fix:** Change to `compute_all_metrics(query_results, GROUND_TRUTH_QUERIES)`

### Issue 3: Cell 20 references undefined `total_chunks`

**Cell:** 20 (line 3167)
**Symptom:** `NameError: name 'total_chunks' is not defined`
**Detail:** Criterion 1 references `total_chunks` for overflow percentage calculation, but Cell 10 uses `len(enriched_chunks)` — no `total_chunks` variable is ever set.
**Fix:** Replace `total_chunks` with `len(enriched_chunks)`.

### Issue 4: Variable name mismatch `layer_token_audit` vs `layer_token_audits`

**Cell(s):** 19, 21 reference `layer_token_audit` (singular); Cell 10 defines `layer_token_audits` (plural)
**Symptom:** `NameError` or silent data loss
**Detail:** Cell 10 creates `layer_token_audits: List[Dict[str, Any]] = []` (plural). Cells 19 and 21 reference `layer_token_audit` (singular). Also Cell 19 uses lowercase layer names (`corpus`, `domain`...) but Cell 10 stores them as capitalized keys (`Corpus`, `Domain`...) from `build_multi_layer_prefix()`.
**Fix:** Standardize on `layer_token_audits` (plural) throughout. Fix case mismatch in Cell 19 layer names.

### Issue 5: Only 3 queries defined — notebook claims 36

**Cell:** 04 (lines 472-479)
**Symptom:** Only 3 queries execute; metrics computed on 3 instead of 36; comparisons fail.
**Detail:** `GROUND_TRUTH_QUERIES` list only contains `[q01, q13, q25]` with comments "Copy from D-21 Cell 04". The remaining 33 queries (Q-02 through Q-36) are **not defined** — only comments. This is a placeholder that was never filled. All downstream cells (12, 14-20) assume 36 queries.
**Fix:** Must copy full 36-query set from D-21 Cell 04, or make D23 load queries from a shared module/file.

---

## 🟡 Major Issues (wrong results / inconsistency with D21/D22)

### Issue 6: Wrong `prompt_name` for document embedding

**Cell:** 11 (line 1859)
**Symptom:** Embedding quality mismatch vs D21/D22
**Detail:** Cell 11 uses `prompt_name="passage"` for encoding chunks with sentence-transformers. D21 and D22 both use `prompt_name="document"`. The Nomic model's prompt template name for documents is `"document"`, not `"passage"`.
**Fix:** Change `prompt_name="passage"` to `prompt_name="document"`.

### Issue 7: Query taxonomy mismatch (3 types vs 5)

**Cell(s):** 04, 12, 16, 18, 20
**Symptom:** Missing query types in breakdown; comparison with D21/D22 fails on join
**Detail:** D23 uses 3 query types: `"authority"`, `"temporal"`, `"factual"`. D21/D22 use 5 types (uppercase): `"SINGLE_HOP"`, `"MULTI_HOP"`, `"AUTHORITY"`, `"TEMPORAL"`, `"EXPLORATORY"`. All per-type loops in D23 hard-code the 3-type taxonomy. When comparing with D21/D22 results, `query_type` values won't match.
**Fix depends on which direction to align:**

- **Option A:** Change D23 to use D21/D22's 5-type uppercase taxonomy (requires full query set rewrite)
- **Option B:** Ensure D23 matches D21's actual CSV `query_type` column values (check D21 output CSV format)

### Issue 8: Hardcoded paths pointing to `/mnt/0000_concurrent/`

**Cell:** 03 (lines 287-299)
**Symptom:** `FileNotFoundError` on any machine except a specific Colab setup
**Detail:** Five paths hardcoded to `/mnt/0000_concurrent/`:

- `CORPUS_DIR = Path("/mnt/0000_concurrent/d20_corpus")`
- `OUTPUT_DIR = Path("/mnt/0000_concurrent/d23_output")`
- `D21_RESULTS_PATH = Path("/mnt/0000_concurrent/d21_output/d21_results.csv")`
- `D22_RESULTS_PATH = Path("/mnt/0000_concurrent/d22_output/d22_results.csv")`

D21 and D22 (after fixes) use relative paths like `./corpus`, `./d21-output/`, etc.
**Fix:** Align with D21/D22 relative path conventions:

```python
CORPUS_DIR = Path("./corpus")
OUTPUT_DIR = Path("./d23-output")
D21_RESULTS_PATH = Path("./d21-output/d21_results.csv")
D22_RESULTS_PATH = Path("./d22-output/d22_results.csv")
```

---

## 🔵 Minor Issues (technical debt / cosmetic)

### Issue 9: Corpus loads both `.md` and `.yaml` files

**Cell:** 06 (lines 791-795)
**Symptom:** Potential double-counting or wrong-format documents
**Detail:** `load_corpus()` globs `*.md`, `*.yaml`, and `*.yml` — same as D21 before it was fixed. D21/D22 after fixing only load `.md` files since the Aethelgard corpus is all Markdown.
**Fix:** Remove `.yaml`/`.yml` glob patterns.

### Issue 10: Cell 12 docstring says "36 ground-truth queries"

**Cell:** 12 (line 1949)
**Symptom:** Misleading documentation (currently only 3 queries exist)
**Detail:** Just a documentation accuracy issue — docstring claims 36 queries but only 3 are defined.
**Fix:** Will be resolved when Issue 5 is fixed.

### Issue 11: H3 hypothesis references Q-01 to Q-12/ Q-13 to Q-24 / Q-25 to Q-36

**Cell:** Methodology markdown (line 888)
**Symptom:** Misleading research framing
**Detail:** H3 states "Authority-sensitive queries (Q-01 to Q-12) and temporal queries (Q-13 to Q-24) benefit more from multi-layer enrichment than factual queries (Q-25 to Q-36)." This assumes a clean 12/12/12 split across 3 types, but D21/D22 use 5 query types with a different distribution (11/8/5/6/6).
**Fix:** Update H3 to match actual query taxonomy after Issue 7 is resolved.

### Issue 12: `SELECTED_MODEL` used inconsistently in Cell 15

**Cell:** 15 (line 2354)
**Symptom:** Potential KeyError if model column format differs from D21/D22 CSV
**Detail:** Cell 15 sets `d23_df["model"] = SELECTED_MODEL` which produces `"v1.5"`. D21 CSV may use the full HuggingFace model ID (e.g., `"nomic-ai/nomic-embed-text-v1.5"`). If `comparison_df` merges on model column, mismatch will prevent comparison.
**Fix:** Verify D21 CSV model column format and align.

---

## Priority Order for Fixes

| Priority | Issues     | Rationale                                                     |
| -------- | ---------- | ------------------------------------------------------------- |
| **P0**   | 1, 2, 3, 4 | Runtime `NameError` — notebook won't execute past these cells |
| **P1**   | 5          | Incomplete query set makes all results meaningless            |
| **P1**   | 6          | Wrong prompt name produces wrong embeddings                   |
| **P1**   | 7, 8       | Data/path mismatches prevent valid comparison                 |
| **P2**   | 9, 11, 12  | Correctness refinements                                       |
| **P3**   | 10         | Documentation only                                            |

---

## Cross-Reference: D22 Audit Parity

| D22 Issue                         | D23 Equivalent                        | Status |
| --------------------------------- | ------------------------------------- | ------ |
| Wrong corpus path (.yaml vs .md)  | Issue 9                               | Open   |
| Query type mismatch (3 vs 5)      | Issue 7                               | Open   |
| Model loading (trust_remote_code) | ✓ Already correct in D23 Cell 11      | OK     |
| Stale prompt prefixes             | F2                                    | Fixed  |
| ChromaDB client mismatch          | ✓ D23 uses PersistentClient correctly | OK     |
| Missing packages in deps          | F1                                    | Fixed  |
