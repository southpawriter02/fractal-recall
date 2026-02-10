# Notebook Context Cell Template

**Usage:** Copy the content below (between the `---` markers) into the first markdown cell of each Colab/Kaggle notebook. Update the `[NOTEBOOK_NUMBER]`, `[NOTEBOOK_TITLE]`, and `[NOTEBOOK_QUESTION]` placeholders for each specific notebook.

---

## Content to paste as the first markdown cell:

```markdown
# FractalRecall Prototyping — Notebook [NOTEBOOK_NUMBER]: [NOTEBOOK_TITLE]

> **Project:** FractalRecall — Hierarchical context-aware embedding retrieval
> **Question this notebook answers:** [NOTEBOOK_QUESTION]
> **Corpus:** Aethelgard worldbuilding (Markdown + YAML frontmatter)
> **Embedding model:** `nomic-embed-text-v2-moe` via sentence-transformers
> **Vector DB:** ChromaDB (in-memory)
> **Metrics:** Precision@5, Recall@10, NDCG@10, MRR
> **Full context for AI assistants:** See `COLAB-SESSION-CONTEXT.md` in this directory

## What is FractalRecall?

FractalRecall tests the hypothesis that embedding retrieval improves when text chunks are enriched with **hierarchical structural context** before embedding. Each chunk carries up to 8 "context layers" (Corpus → Domain → Entity → Authority → Temporal → Relational → Section → Content) prepended as natural language prefixes. The enriched text is embedded as a single vector.

## Notebook Sequence

| # | Notebook | Status |
|---|----------|--------|
| 1 | Baseline (standard RAG, no enrichment) | |
| 2 | Single-Layer Enrichment (document-level context only) | |
| 3 | Multi-Layer Enrichment (**core hypothesis test**) | |
| 4 | Layer Ablation (which layers matter most?) | |
| 5 | Embedding Strategy Comparison (prefix vs. multi-vector vs. hybrid) | |
| 6 | Cross-Domain Validation (non-worldbuilding corpus) | |

Mark the current notebook's row with ✅ and completed ones with ✅.
```

---

## Per-Notebook Placeholder Values

| Notebook | NOTEBOOK_NUMBER | NOTEBOOK_TITLE | NOTEBOOK_QUESTION |
|----------|-----------------|----------------|-------------------|
| NB1 | 1 | Baseline Establishment | How well does standard RAG (no enrichment) perform on the Aethelgard corpus? |
| NB2 | 2 | Single-Layer Enrichment | Does adding a single document-level context prefix improve retrieval quality? |
| NB3 | 3 | Multi-Layer Enrichment | Does full 8-layer context enrichment improve retrieval beyond single-layer? (GO/NO-GO) |
| NB4 | 4 | Layer Ablation Study | Which individual context layers contribute most to retrieval improvement? |
| NB5 | 5 | Embedding Strategy Comparison | Is prefix enrichment better than multi-vector or hybrid approaches? |
| NB6 | 6 | Cross-Domain Validation | Does the technique generalize to non-worldbuilding corpora? |
