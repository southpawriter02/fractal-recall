# D-22 Audit & Alignment Fixes

**Date:** 2026-02-15  
**Scope:** `D22-single-layer.ipynb` — alignment with D-21 baseline  
**Status:** All 11 issues resolved

---

## Background

D-22 (Single-Layer Enrichment) builds on D-21 (Baseline) by adding a document-level context prefix to each chunk before embedding. For the comparison to be valid, D-22 must use identical corpus loading, query definitions, model configurations, and metric computation as D-21. A cell-by-cell audit revealed 11 issues preventing this.

## Issues Found

### Critical — Would Cause Runtime Errors

| #   | Issue                                 | Root Cause                                                                    | Impact                                 |
| --- | ------------------------------------- | ----------------------------------------------------------------------------- | -------------------------------------- |
| 1   | `NameError: name 're' is not defined` | `re.split()` used in chunking (Cell 7) but `import re` appeared late (Cell 9) | Notebook crashes at chunking step      |
| 2   | Zero documents loaded                 | `corpus_path.glob("*.yaml")` but corpus files are `.md`                       | Empty corpus, no chunks, no embeddings |
| 3   | `FileNotFoundError` on corpus         | `CORPUS_DIR = Path("/mnt/0000_concurrent/d20_corpus")` — Colab mount path     | Notebook crashes at corpus loading     |
| 4   | `FileNotFoundError` on D-21 results   | `D21_RESULTS_PATH = Path("/mnt/0000_concurrent/d21_output/...")`              | Comparison with D-21 baseline fails    |

### Major — Would Produce Incorrect Results

| #   | Issue                               | Root Cause                                                                                                                        | Impact                                                          |
| --- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| 5   | Query type taxonomy mismatch        | D-22 used 3 types (`authority`/`temporal`/`factual`); D-21 uses 5 (`SINGLE_HOP`/`MULTI_HOP`/`AUTHORITY`/`TEMPORAL`/`EXPLORATORY`) | Per-type comparison impossible; delta analysis meaningless      |
| 6   | All metrics return 0.0              | `relevant_docs` referenced `.yaml` filenames; corpus files are `.md`                                                              | Precision, Recall, NDCG, MRR all zero — no ground-truth matches |
| 7   | Wrong embedding model loader        | `SentenceTransformer(model_id)` hardcoded for all models; `bge-m3` requires `BGEM3FlagModel` from FlagEmbedding                   | Crash or wrong embeddings when `SELECTED_MODEL = "bge-m3"`      |
| 10  | D-21 CSV filter matches 0 rows      | `d21_df["model"] == "v1.5"` but D-21 CSV column contains `"nomic-embed-text-v1.5"`                                                | Empty D-21 baseline, no comparison possible                     |
| 11  | Comparison loops miss 2 query types | Hardcoded `["authority", "temporal", "factual"]` in 3 cells                                                                       | SINGLE_HOP and MULTI_HOP queries excluded from analysis         |

### Minor — Structural Issues

| #   | Issue                                 | Root Cause                                            | Impact                                                               |
| --- | ------------------------------------- | ----------------------------------------------------- | -------------------------------------------------------------------- |
| 8   | Duplicate `QUERIES` definition        | Cell 3 had 6 truncated queries; Cell 4 had 36 queries | Confusion; first definition shadows second if cells run out of order |
| 9   | `ModelConfig` fields differ from D-21 | Missing `loader`, `doc_prefix`, `query_prefix` fields | Cross-referencing between D-21 and D-22 code is error-prone          |

> Issues 10 and 11 were discovered during the fix planning phase while cross-referencing D-21's actual CSV output format and comparison cell logic.

## Fixes Applied

### Fix 1 — `import re` placement

Added `import re` to the main imports cell (Cell 2). Removed the redundant late `import re` from Cell 9.

### Fix 2 — Corpus glob pattern

```diff
-md_files = sorted(corpus_path.glob("*.yaml"))
+md_files = sorted(corpus_path.glob("*.md"))
```

### Fix 3 — `CORPUS_DIR` path

```diff
-CORPUS_DIR = Path("/mnt/0000_concurrent/d20_corpus")
+CORPUS_DIR = Path("./test-corpus")  # Same as D-21
```

### Fix 4 — `D21_RESULTS_PATH` and `OUTPUT_DIR`

```diff
-OUTPUT_DIR = Path("/mnt/0000_concurrent/d22_output")
-D21_RESULTS_PATH = Path("/mnt/0000_concurrent/d21_output/d21_results.csv")
+OUTPUT_DIR = Path("./d22-output")
+D21_RESULTS_PATH = Path("./d21-output/d21_results.csv")
```

### Fix 5 + 6 — Query set replacement

Replaced the entire D-22 query set with D-21's exact 36 queries, adapted to D-22's dict format:

- **D-21 format:** `GroundTruthQuery` dataclass with `.expected` as `List[Tuple[str, int]]`
- **D-22 format:** Plain dict with `query_id`, `type`, `text`, `relevant_docs` (list of filenames)

All 36 queries now use D-21's 5-type taxonomy and reference `.md` filenames:

| Type        | Count | Example Query ID                          |
| ----------- | ----- | ----------------------------------------- |
| SINGLE_HOP  | 11    | Q-01 through Q-07, Q-27, Q-28, Q-30, Q-34 |
| MULTI_HOP   | 8     | Q-08 through Q-12, Q-29, Q-31, Q-35       |
| AUTHORITY   | 5     | Q-13 through Q-17                         |
| TEMPORAL    | 6     | Q-18 through Q-23                         |
| EXPLORATORY | 6     | Q-24 through Q-26, Q-32, Q-33, Q-36       |

### Fix 7 — Conditional model loading

```python
# Before: hardcoded for all models
embedding_model = SentenceTransformer(MODEL_CONFIG.model_id)

# After: conditional based on loader type
if MODEL_CONFIG.loader == "flag_embedding":
    from FlagEmbedding import BGEM3FlagModel
    embedding_model = BGEM3FlagModel(MODEL_CONFIG.model_id, use_fp16=True)
else:
    embedding_model = SentenceTransformer(MODEL_CONFIG.model_id, trust_remote_code=True)
```

Same conditional applied to both document embedding and query embedding, including the different return formats (`bge-m3` returns `dict` with `"dense_vecs"` key).

### Fix 8 — Removed duplicate QUERIES cell

Deleted the truncated 6-query cell. Only one `QUERIES = [...]` definition exists now.

### Fix 9 — `ModelConfig` field alignment

Added three new fields with D-21 equivalents documented:

```python
@dataclass
class ModelConfig:
    # ... existing fields ...
    loader: str = "sentence_transformers"  # or "flag_embedding"
    doc_prefix: str = ""   # e.g., "search_document" for nomic
    query_prefix: str = ""  # e.g., "search_query" for nomic
```

### Fix 10 — D-21 CSV model name mapping

```python
# Mapping from SELECTED_MODEL key → D-21 CSV 'model' column value
D21_MODEL_NAMES = {
    "v2-moe": "nomic-embed-text-v2-moe",
    "v1.5": "nomic-embed-text-v1.5",
    "bge-m3": "BAAI/bge-m3",
}

# When loading D-21 CSV:
d21_model_name = D21_MODEL_NAMES.get(SELECTED_MODEL, SELECTED_MODEL)
d21_df = d21_df[d21_df["model"] == d21_model_name].copy()
d21_df["experiment"] = "baseline"  # D-21 CSV has no 'experiment' column
d21_df["model"] = SELECTED_MODEL   # Normalize for merging
```

### Fix 11 — 5-type query loops

```diff
-for query_type in ["authority", "temporal", "factual"]:
+for query_type in ["SINGLE_HOP", "MULTI_HOP", "AUTHORITY", "TEMPORAL", "EXPLORATORY"]:
```

Applied in 3 code cells (comparison table, delta analysis, visualization) and 1 markdown cell.

## Post-Fix Cell Map

| Cell  | Purpose                                           |
| ----- | ------------------------------------------------- |
| 0     | Title & research question                         |
| 1     | Install dependencies                              |
| 2     | **Imports, config, ModelConfig, D21_MODEL_NAMES** |
| 3     | **36 queries (D-21 aligned)**                     |
| 4     | Field mapping & normalization                     |
| 5     | Corpus loading                                    |
| 6     | Methodology (markdown)                            |
| 7     | Hybrid chunking engine                            |
| 8     | Single-layer enrichment builder                   |
| 9     | Chunk & enrich corpus                             |
| 10    | Embedding & ChromaDB indexing                     |
| 11    | Query execution                                   |
| 12    | Results header (markdown)                         |
| 13    | Metric computation functions                      |
| 14    | D-21 comparison                                   |
| 15    | Delta analysis                                    |
| 16    | Statistical significance testing                  |
| 17    | Improvement distribution visualization            |
| 18    | Side-by-side heatmap                              |
| 19    | Export results                                    |
| 20–21 | C# implications & next steps (markdown)           |

## Verification

All 11 checks pass:

```
✓ Fix 1:  import re in imports cell
✓ Fix 2:  glob uses *.md
✓ Fix 3:  CORPUS_DIR → ./test-corpus
✓ Fix 4:  D21_RESULTS_PATH → ./d21-output/d21_results.csv
✓ Fix 5:  5-type taxonomy (SINGLE_HOP/MULTI_HOP/AUTHORITY/TEMPORAL/EXPLORATORY)
✓ Fix 6:  relevant_docs use .md filenames
✓ Fix 7:  Conditional bge-m3 / nomic model loading
✓ Fix 8:  Single QUERIES definition (36 queries)
✓ Fix 9:  ModelConfig has loader/doc_prefix/query_prefix fields
✓ Fix 10: D21_MODEL_NAMES mapping present
✓ Fix 11: All comparison loops use 5-type taxonomy
```

## Fix Scripts

These scripts were used to apply changes programmatically (safe to delete after verification):

- `fix_d22.py` — Main fix script (fixes 1–8, 10–11)
- `fix_d22_phase2.py` — Restored imports/config cell (fixes 7, 9)
