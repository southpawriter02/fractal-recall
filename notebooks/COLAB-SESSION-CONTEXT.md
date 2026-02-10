# FractalRecall: Colab/Kaggle Session Context

**Purpose:** This document provides the AI assistant (Gemini, or any in-notebook AI) with enough context about the FractalRecall project to effectively assist with runtime debugging, code review, and Python troubleshooting during prototyping notebook sessions.

**Audience:** An AI coding assistant that has never seen the FractalRecall design documents. This briefing should be pasted into the AI assistant's context when asking for help with notebook code.

**Maintained by:** Ryan
**Last Updated:** 2026-02-10

---

## Project Summary (One Paragraph)

FractalRecall is a research project testing the hypothesis that embedding-based retrieval improves when text chunks are enriched with **hierarchical structural context** before embedding. Instead of embedding a chunk of text in isolation, we prepend structured "context layers" that describe *what the chunk is* — which knowledge base it belongs to, what entity it describes, its editorial authority status, its temporal period, its relationships to other entities, and its position within the document. The enriched text is then embedded as a single vector using standard embedding models. We're comparing this multi-layer enrichment approach against (a) standard RAG with no enrichment and (b) single-layer enrichment (similar to Anthropic's Contextual Retrieval technique).

---

## What the Notebooks Are Doing

We're running six experiments in sequence:

| Notebook | Question Being Answered |
|----------|------------------------|
| **NB1: Baseline** | How well does standard RAG (embed chunks with no enrichment) perform on our test corpus? |
| **NB2: Single-Layer** | Does adding a single document-level context prefix (entity type + name + canon status) improve retrieval? |
| **NB3: Multi-Layer** | Does adding all 8 context layers improve retrieval beyond single-layer? **This is the critical experiment.** |
| **NB4: Ablation** | Which individual layers contribute most to retrieval improvement? (Add layers one at a time, measure marginal gain.) |
| **NB5: Strategy** | Is single-vector prefix enrichment better than multi-vector per-layer or hybrid approaches? |
| **NB6: Cross-Domain** | Does the technique generalize to a non-worldbuilding corpus (e.g., technical documentation)? |

### Evaluation Metrics

Every notebook computes the same metrics against a ground-truth query set:

- **Precision@5** — Of the top 5 results, how many are relevant?
- **Recall@10** — Of all relevant documents, how many appear in the top 10 results?
- **NDCG@10** — Normalized Discounted Cumulative Gain at 10 (accounts for ranking position)
- **MRR** — Mean Reciprocal Rank (how high is the first relevant result?)

Statistical significance is tested via Wilcoxon signed-rank test (paired, p < 0.05).

---

## The Test Corpus

The primary corpus is **Aethelgard** — a fantasy worldbuilding project. Each document is a Markdown file with YAML frontmatter:

```yaml
---
type: faction          # Entity type: faction, character, location, event, etc.
name: The Iron Covenant
canon: true            # Authority status: true, false, "apocryphal", "deprecated"
era: [Third Age, Fourth Age]
region: Ashenmoor
relationships:
  - target: "characters/elena-voss.md"
    type: founded_by
  - target: "factions/silver-hand.md"
    type: rivalry
tags: [military, expansionist, fallen]
---

# The Iron Covenant

## Origins

The Iron Covenant was founded in Year 412 of the Third Age...
```

The body text below the YAML frontmatter is standard Markdown with headings.

---

## The 8 Context Layers

When we "enrich" a chunk, we prepend context layers in this order (outermost to innermost):

| Layer | What It Contains | Example |
|-------|-----------------|---------|
| **Corpus** | Which knowledge base | "Aethelgard Worldbuilding Corpus v5.0" |
| **Domain** | Category within the corpus | "Organizations / Factions" |
| **Entity** | Which specific entity | "The Iron Covenant" |
| **Authority** | Editorial/canonical status | "Canonical" or "Draft" or "Apocryphal" |
| **Temporal** | Time period described | "Third Age, Fourth Age" |
| **Relational** | Links to other entities | "Founded by Elena Voss; Rival of Silver Hand" |
| **Section** | Document section heading | "Origins" |
| **Content** | The actual chunk text | *(the raw text)* |

### Rendered Format for Embedding

The enriched text looks like this when fed to the embedding model:

```
Corpus: Aethelgard Worldbuilding Corpus v5.0

Domain: This content is from a faction document in the organizations category.

Entity: This content describes The Iron Covenant.

Authority: This content is canonical and authoritative.

Temporal: The events described span the Third Age and Fourth Age.

Relationships: The Iron Covenant was founded by Elena Voss, is a rival of the Silver Hand, and is located in the Ashenmoor region.

Section: This content is from the Origins section.

The Iron Covenant was founded in Year 412 of the Third Age by Commander Elena Voss...
```

Layers are separated by double newlines. If a layer has no value for a given chunk, it is omitted entirely (not rendered as empty).

---

## Technology Stack

| Component | Package | Version | Notes |
|-----------|---------|---------|-------|
| **Embedding model** | `nomic-embed-text-v2-moe` | Latest | Via sentence-transformers. Requires `trust_remote_code=True`. Uses `prompt_name="passage"` for documents, `"query"` for search queries. |
| **Embedding library** | `sentence-transformers` | 5.2.x | `encode_query()` / `encode_document()` methods available but optional. |
| **Vector database** | `chromadb` | 1.5.x | In-memory for prototyping. Supports metadata filtering. |
| **YAML parsing** | `pyyaml` | Latest | For reading frontmatter from Markdown files. |
| **Math/stats** | `numpy`, `scipy`, `scikit-learn` | Latest | Cosine similarity, Wilcoxon signed-rank test, clustering. |
| **Visualization** | `matplotlib`, `seaborn` | Latest | Evaluation plots, embedding space visualization. |

### Key Code Patterns

**Loading the embedding model:**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "nomic-ai/nomic-embed-text-v2-moe",
    trust_remote_code=True
)

# Embed documents (passages)
doc_embeddings = model.encode(texts, prompt_name="passage")

# Embed queries
query_embedding = model.encode(query_text, prompt_name="query")
```

**Parsing YAML frontmatter from Markdown:**
```python
import yaml
import re

def parse_lore_file(filepath):
    """Parse a Markdown file with YAML frontmatter."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Split on YAML delimiters
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
    if not match:
        return None, content

    frontmatter = yaml.safe_load(match.group(1))
    body = match.group(2)
    return frontmatter, body
```

**Building enriched text from layers:**
```python
def build_enriched_text(frontmatter, chunk_text, section_heading=None):
    """Construct the multi-layer enriched representation."""
    layers = []

    # Corpus layer (hardcoded for this corpus)
    layers.append("Corpus: Aethelgard Worldbuilding Corpus v5.0")

    # Domain layer
    entity_type = frontmatter.get('type', 'unknown')
    layers.append(f"Domain: This content is from a {entity_type} document.")

    # Entity layer
    name = frontmatter.get('name', 'Unknown Entity')
    layers.append(f"Entity: This content describes {name}.")

    # Authority layer
    canon = frontmatter.get('canon', False)
    if canon is True:
        authority = "canonical and authoritative"
    elif canon == "apocryphal":
        authority = "apocryphal (non-canonical, speculative)"
    elif canon == "deprecated":
        authority = "deprecated and superseded"
    else:
        authority = "draft (not yet canonical)"
    layers.append(f"Authority: This content is {authority}.")

    # Temporal layer
    eras = frontmatter.get('era', [])
    if eras:
        if isinstance(eras, list):
            era_text = " and ".join(str(e) for e in eras)
        else:
            era_text = str(eras)
        layers.append(f"Temporal: The events described span the {era_text}.")

    # Relational layer
    relationships = frontmatter.get('relationships', [])
    if relationships:
        rel_parts = []
        for rel in relationships:
            target_name = rel.get('target', '').split('/')[-1].replace('.md', '').replace('-', ' ').title()
            rel_type = rel.get('type', 'related to').replace('_', ' ')
            rel_parts.append(f"{rel_type} {target_name}")
        layers.append(f"Relationships: {'; '.join(rel_parts)}.")

    # Section layer
    if section_heading:
        layers.append(f"Section: This content is from the {section_heading} section.")

    # Content layer (always last)
    layers.append(chunk_text)

    return "\n\n".join(layers)
```

**ChromaDB setup:**
```python
import chromadb

client = chromadb.Client()  # In-memory
collection = client.create_collection(
    name="experiment",
    metadata={"hnsw:space": "cosine"}
)
```

---

## Common Issues and Debugging Context

### "Why is retrieval quality the same across experiments?"

Most likely cause: the corpus is too small, or the test queries don't exercise the structural differences. Check that the ground-truth query set includes authority-sensitive queries (where canonical vs. apocryphal status matters), temporal-scoped queries (where era matters), and relational queries (where entity connections matter). If all queries are simple factual lookups, the enrichment won't have much to improve.

### "The embedding model is slow / runs out of memory."

The `nomic-embed-text-v2-moe` model is a Mixture-of-Experts architecture (475M total params, 305M active). On a free-tier T4 GPU, batch encoding ~1000 enriched chunks (each up to ~2000 tokens) should take 1-3 minutes. If it's much slower, check that GPU is actually being used (`model.device` should show `cuda`). For memory issues, reduce batch size: `model.encode(texts, batch_size=16)`.

### "ChromaDB metadata filtering isn't working."

ChromaDB filters use a specific syntax:
```python
results = collection.query(
    query_embeddings=[query_vec],
    n_results=10,
    where={"canon": "true"},           # Exact match
    where_document={"$contains": "Iron"}  # Text contains
)
```
Note: ChromaDB metadata values must be strings, ints, floats, or bools. Lists and nested objects are not supported as filter values. Store list-valued metadata as comma-separated strings and use `$contains` for matching.

### "Wilcoxon signed-rank test returns NaN or fails."

This happens when both conditions produce identical results on every query (no differences to test). This usually means either (a) the enrichment had zero effect (check that the enriched text is actually being used, not the raw text), or (b) the evaluation set is too small. Need at least 10-15 query pairs for a meaningful test.

### "Chunking produces too many / too few chunks."

We use heading-based chunking: each Markdown section (under a heading) becomes one chunk. If a section is very long (>1000 tokens), split it further at paragraph boundaries. If a file has no headings, the entire body becomes one chunk. The YAML frontmatter is NOT included in chunks — it's extracted separately and used to construct context layers.

---

## Things This Document Does NOT Cover

- **Why we're doing this** — see the Conceptual Architecture doc for the full problem statement and research foundations.
- **The C# production implementation** — these notebooks are Python prototypes. The production library will be .NET.
- **Chronicle (the CLI tool)** — a separate project that will eventually consume FractalRecall. Not relevant to the Colab notebooks.
- **Design decisions and alternatives considered** — see the Design Proposal and Master Strategy documents.

---

*This document is optimized for pasting into an AI assistant's context window. If you're a human reading this, the full technical specification is in `docs/fractalrecall-conceptual-architectural-design.md`.*
