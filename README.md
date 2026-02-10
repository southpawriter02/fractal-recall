# FractalRecall

**Hierarchical context-aware embedding retrieval for .NET**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status: Pre-Implementation](https://img.shields.io/badge/Status-Pre--Implementation-orange.svg)]()
[![.NET 10](https://img.shields.io/badge/.NET-10-purple.svg)]()

---

## What Is FractalRecall?

FractalRecall is a .NET class library that improves embedding-based retrieval by encoding **hierarchical structural context** — called *context layers* — directly into the embedding representation.

Standard RAG (Retrieval-Augmented Generation) systems treat every text chunk as a context-free fragment. Each chunk knows *what it means* semantically, but not *what it is* structurally — where it came from, how authoritative it is, what entity it describes, what time period it covers, or how it relates to other content.

FractalRecall closes this gap. Each chunk carries its full **structural DNA**: a hierarchical set of context layers encoding provenance, authority, entity type, temporal position, relationships, and structural location. The result is retrieval that is both semantically relevant *and* structurally appropriate.

```
Standard RAG:          "The Iron Covenant was founded in Year 412..."
                        ↓ embed → semantic vector only

FractalRecall:         Corpus: Aethelgard Worldbuilding Corpus v5.0
                       Domain: Organizations / Factions
                       Entity: The Iron Covenant
                       Authority: Canonical
                       Temporal: Third Age, Fourth Age
                       Relationships: Founded by Elena Voss; Rival of Silver Hand
                       Section: Origins

                       "The Iron Covenant was founded in Year 412..."
                        ↓ embed → semantic + structural vector
```

## Why Does This Matter?

FractalRecall addresses three documented deficiencies in standard embedding-based retrieval:

**The Semantic Proximity Trap** — A canonical document and a speculative "what if" document about the same topic produce nearly identical embeddings. Standard retrieval can't distinguish between them because the distinction is structural (canonical vs. apocryphal), not semantic.

**Chunking Amnesia** — When documents are broken into chunks for embedding, each chunk loses its structural context — its parent document, its section, its position in the hierarchy. The chunk "forgets where it came from."

**Authority Blindness** — Standard retrieval treats all content as equally authoritative. In any knowledge base with drafts, versions, or approval stages, this produces results that blend authoritative facts with speculative content.

## Design Principles

**Domain-Agnostic:** FractalRecall provides the *mechanism* for defining, composing, and querying context layers. The consuming application provides the *content* of those layers. The same library works for worldbuilding corpora, technical documentation, legal filings, medical records, or any domain where content has meaningful structure.

**Pluggable Architecture:** Embedding models, vector storage backends, and scoring functions are all abstracted behind interfaces. Use local models via Ollama, cloud APIs via OpenAI, or any custom provider.

**Ecosystem-Aligned:** Designed to integrate with `Microsoft.Extensions.AI.Abstractions` and `Microsoft.Extensions.VectorData.Abstractions` — the standard .NET AI interfaces used by Semantic Kernel and the broader ecosystem.

## Research Foundations

FractalRecall synthesizes insights from recent retrieval research:

- **Anthropic's Contextual Retrieval (2024):** Single-layer document-level context enrichment reduced retrieval failures by 49%. FractalRecall generalizes this to N layers of typed, hierarchical context.
- **Microsoft GraphRAG (2024):** Structural relationships between entities are critical for retrieval quality. FractalRecall encodes relationships as a dedicated context layer.
- **RAPTOR (2024):** Hierarchical, multi-level retrieval outperforms flat retrieval. FractalRecall provides a framework for declared (not inferred) hierarchical context.
- **Late Chunking (Jina AI, 2024):** Preserving document-level context through the encoding process improves embedding quality. FractalRecall's architecture is complementary.
- **Matryoshka Representation Learning (2022):** Embeddings can encode information at multiple granularities. FractalRecall applies this principle to structural granularity.

The novel contribution is unifying these into a single, domain-agnostic, developer-friendly .NET library.

## Project Status

FractalRecall is in the **pre-implementation design and validation phase**.

| Phase | Status | Description |
|-------|--------|-------------|
| Conceptual Architecture | ✅ Complete | Full technical specification: problem statement, context layers, embedding strategies, API design, evaluation framework |
| Google Colab Prototyping | 🔲 Starting | Six Python notebooks to empirically validate multi-layer enrichment before C# implementation |
| Documentation (Phase 1) | 🔲 Planned | API Design Spec, Prototyping Findings Document |
| C# Implementation (Phase 2) | 🔲 Planned | Core library, reference implementations, tests |

### Why Prototype in Python?

The ML/embedding ecosystem in Python (sentence-transformers, chromadb, numpy, scikit-learn) is substantially more mature than .NET for rapid experimentation. The Colab notebooks validate the technique empirically before committing to production C# implementation. The notebooks become **permanent research documentation**, not throwaway work.

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────┐
│                  Consuming Application                  │
│           (e.g., Chronicle, API docs tool)              │
│                                                         │
│   Extracts structural metadata from domain-specific     │
│   sources (YAML frontmatter, database records, etc.)    │
└───────────────┬─────────────────────────┬───────────────┘
                │ context layer values    │ queries
                ▼                         ▼
┌───────────────────────────────────────────────────────────┐
│                      FractalRecall                        │
│                                                           │
│  ┌──────────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │ ContextLayer      │  │ Composite   │  │ FractalQuery │ │
│  │ Registry          │  │ Represen-   │  │ Builder      │ │
│  │                   │  │ tation      │  │              │ │
│  │ Defines layer     │  │ Builder     │  │ Constructs   │ │
│  │ types, hierarchy, │  │             │  │ queries with │ │
│  │ schemas           │  │ Assembles   │  │ layer weights│ │
│  │                   │  │ layers into │  │ and metadata │ │
│  │                   │  │ DNA strand  │  │ filters      │ │
│  └──────────────────┘  └──────┬──────┘  └──────┬───────┘ │
│                               │                 │         │
│                    ┌──────────▼─────────────────▼───────┐ │
│                    │       IFractalIndex                 │ │
│                    │   (vector + metadata storage)       │ │
│                    └──────────┬─────────────────────────┘ │
│                               │                           │
│                    ┌──────────▼─────────────────────────┐ │
│                    │     IEmbeddingGenerator             │ │
│                    │  (Microsoft.Extensions.AI)          │ │
│                    └────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
```

## Standard Context Layers

FractalRecall ships with eight standard layer types, ordered from outermost (most general) to innermost (most specific):

| Layer | Hierarchy | Purpose | Example Values |
|-------|-----------|---------|----------------|
| Corpus | 100 | Which knowledge base | "Aethelgard v5.0", "Acme API Docs" |
| Domain | 90 | Categorical area | "Factions", "API Endpoints", "Case Law" |
| Entity | 80 | Specific entity described | "The Iron Covenant", "GET /users/{id}" |
| Authority | 70 | Editorial/canonical status | "Canonical", "Draft", "Binding (Final Rule)" |
| Temporal | 60 | Time period described | "Third Age", "API v3", "Q3 2025" |
| Relational | 50 | Connections to other entities | "Founded by Elena Voss; Rival of Silver Hand" |
| Section | 20 | Document subdivision | "Origins", "Response Schema", "Subpart Da" |
| Content | 0 | The actual text | *(the raw chunk)* |

Custom layer types are first-class citizens — consuming applications can define domain-specific layers beyond the standard set.

## First Integration Target

[Chronicle](https://github.com/your-username/chronicle) — a C# CLI tool that treats worldbuilding lore like a software codebase. Chronicle layers on top of Git to add canon status management, YAML frontmatter validation, cross-reference integrity checking, and semantic search powered by FractalRecall.

## Documentation

| Document | Description |
|----------|-------------|
| [Conceptual Architecture](docs/fractalrecall-conceptual-architectural-design.md) | Full technical specification: problem statement, research foundations, layer specification, embedding strategies, user stories, API design, evaluation framework |
| [Design Proposal](../Chronicle-FractalRecall-Design-Proposal.md) | Unified design proposal covering both FractalRecall and Chronicle |
| [Master Strategy](../Chronicle-FractalRecall-Master-Strategy.md) | Execution strategy: parallel tracks, document manifest, research due diligence |

## Technology Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| Runtime | .NET 10 (LTS) | Current LTS, supported through Nov 2028 |
| Embedding Interface | `Microsoft.Extensions.AI.Abstractions` | Ecosystem-standard `IEmbeddingGenerator` |
| Vector Storage | SQLite-vec (embedded) or Qdrant (dedicated) | Pluggable via `IFractalIndex` interface |
| Local Inference | Ollama via OllamaSharp | Recommended model: `nomic-embed-text-v2-moe` |
| Prototyping | Python / Kaggle Notebooks | sentence-transformers, chromadb |

## License

This project is licensed under the terms of the [MIT License](LICENSE).

---

*FractalRecall is in active development. The conceptual architecture is complete and validated through design review. Empirical validation via Google Colab prototyping is the current focus. See the [Master Strategy](../Chronicle-FractalRecall-Master-Strategy.md) for the full execution plan.*
