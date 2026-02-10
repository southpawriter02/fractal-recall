# FractalRecall: Conceptual Architecture Document

**Version:** 0.1.0-draft  
**Status:** Initial Draft — Seeking Feedback  
**Author:** Ryan (with architectural guidance from Claude)  
**Created:** 2026-02-09  
**Last Updated:** 2026-02-09  
**Repository:** TBD  
**License:** TBD (Recommended: MIT or Apache 2.0)

---

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. Problem Statement](#2-problem-statement)
  - [2.1. The Semantic Proximity Trap](#21-the-semantic-proximity-trap)
  - [2.2. The Chunking Amnesia Problem](#22-the-chunking-amnesia-problem)
  - [2.3. The Authority Blindness Problem](#23-the-authority-blindness-problem)
  - [2.4. Summary of Deficiencies](#24-summary-of-deficiencies)
- [3. Research Foundations](#3-research-foundations)
  - [3.1. Anthropic's Contextual Retrieval (2024)](#31-anthropics-contextual-retrieval-2024)
  - [3.2. Matryoshka Representation Learning (2022)](#32-matryoshka-representation-learning-2022)
  - [3.3. Microsoft GraphRAG (2024)](#33-microsoft-graphrag-2024)
  - [3.4. RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval (2024)](#34-raptor-recursive-abstractive-processing-for-tree-organized-retrieval-2024)
  - [3.5. Late Chunking (Jina AI, 2024)](#35-late-chunking-jina-ai-2024)
  - [3.6. Research Synthesis: What FractalRecall Builds On](#36-research-synthesis-what-fractalrecall-builds-on)
- [4. Core Concepts](#4-core-concepts)
  - [4.1. The DNA Metaphor, Formalized](#41-the-dna-metaphor-formalized)
  - [4.2. Context Layers](#42-context-layers)
  - [4.3. Composite Representation](#43-composite-representation)
  - [4.4. Structural Fingerprint](#44-structural-fingerprint)
  - [4.5. Fractal Index](#45-fractal-index)
  - [4.6. Layer-Weighted Retrieval](#46-layer-weighted-retrieval)
- [5. Architecture Overview](#5-architecture-overview)
  - [5.1. System Components](#51-system-components)
  - [5.2. Data Flow: Indexing Pipeline](#52-data-flow-indexing-pipeline)
  - [5.3. Data Flow: Query Pipeline](#53-data-flow-query-pipeline)
  - [5.4. Extension Points](#54-extension-points)
- [6. Layer Specification](#6-layer-specification)
  - [6.1. Layer Anatomy](#61-layer-anatomy)
  - [6.2. Standard Layer Types](#62-standard-layer-types)
  - [6.3. Layer Composition Rules](#63-layer-composition-rules)
  - [6.4. Worked Example: Worldbuilding Domain](#64-worked-example-worldbuilding-domain)
  - [6.5. Worked Example: Technical Documentation Domain](#65-worked-example-technical-documentation-domain)
  - [6.6. Worked Example: Legal Document Domain](#66-worked-example-legal-document-domain)
- [7. Embedding Strategy](#7-embedding-strategy)
  - [7.1. Approach A: Prefix Enrichment (Simplest)](#71-approach-a-prefix-enrichment-simplest)
  - [7.2. Approach B: Multi-Vector Composition](#72-approach-b-multi-vector-composition)
  - [7.3. Approach C: Hybrid Embedding with Metadata Sidecar](#73-approach-c-hybrid-embedding-with-metadata-sidecar)
  - [7.4. Comparative Analysis and Recommended Path](#74-comparative-analysis-and-recommended-path)
- [8. User Stories](#8-user-stories)
  - [8.1. Library Consumer Stories (Developer Audience)](#81-library-consumer-stories-developer-audience)
  - [8.2. End-User Stories via Chronicle Integration](#82-end-user-stories-via-chronicle-integration)
  - [8.3. Researcher and Evaluator Stories](#83-researcher-and-evaluator-stories)
- [9. API Design (Conceptual)](#9-api-design-conceptual)
  - [9.1. Core Interfaces](#91-core-interfaces)
  - [9.2. Builder Pattern for Composite Representations](#92-builder-pattern-for-composite-representations)
  - [9.3. Query Construction](#93-query-construction)
  - [9.4. Index Management](#94-index-management)
- [10. Prototyping Strategy: Google Colab](#10-prototyping-strategy-google-colab)
  - [10.1. Why Python First](#101-why-python-first)
  - [10.2. Notebook Plan](#102-notebook-plan)
  - [10.3. Transition Criteria: Colab to C#](#103-transition-criteria-colab-to-c)
- [11. Evaluation Framework](#11-evaluation-framework)
  - [11.1. Metrics](#111-metrics)
  - [11.2. Baseline Comparisons](#112-baseline-comparisons)
  - [11.3. Test Corpus Requirements](#113-test-corpus-requirements)
  - [11.4. Evaluation Protocol](#114-evaluation-protocol)
- [12. Risk Register](#12-risk-register)
- [13. Glossary](#13-glossary)
- [14. Open Questions](#14-open-questions)
- [15. Document Revision History](#15-document-revision-history)

---

## 1. Executive Summary

FractalRecall is a .NET class library that improves embedding-based retrieval by encoding hierarchical structural context — what we call "context layers" — directly into the embedding representation. Where standard retrieval-augmented generation (RAG) systems treat every text chunk as a context-free fragment, FractalRecall ensures that each chunk carries its full structural identity: where it came from, what kind of content it is, how authoritative it is, what other entities it relates to, and where it sits in the temporal and categorical hierarchy of the knowledge base.

The library is domain-agnostic by design. It provides the *mechanism* for defining, composing, and querying hierarchical context layers, while the consuming application provides the *content* of those layers. The first integration target is Chronicle (a version-controlled worldbuilding system), but the architecture is deliberately general enough to support technical documentation, legal corpora, game design knowledge bases, medical records, and any other domain where content has meaningful structure beyond its raw semantic meaning.

The name "FractalRecall" reflects the core insight: just as a fractal exhibits self-similar structure at every level of magnification, a well-organized knowledge base has meaningful structure at every level of granularity — from the corpus level down to the individual sentence. FractalRecall ensures that retrieval is aware of structure at *every* level, not just the leaf-node level where the actual text lives.

---

## 2. Problem Statement

### 2.1. The Semantic Proximity Trap

Standard embedding-based retrieval works by converting text into high-dimensional vectors and finding the vectors closest to the query vector in that space. This is called "semantic similarity search," and it's remarkably effective at finding content that is *about the same topic* as the query. The problem is that "about the same topic" is not the same as "the right answer."

Consider a worldbuilding corpus with two documents. The first is a canonical faction document that says "The Iron Covenant was founded in Year 412 of the Third Age." The second is an apocryphal "what if" exploration that says "In this alternate timeline, the Iron Covenant was never founded — instead, Elena Voss joined the Silver Hand." Both documents are semantically about the Iron Covenant's founding. Both will score highly on a similarity search for "When was the Iron Covenant founded?" But only one of them is the *right* answer — the one that represents canonical truth in the current state of the world. A standard embedding has no way to distinguish between them because the distinction is *structural* (canonical vs. apocryphal), not *semantic* (both are about the same topic).

This problem is not hypothetical. It has been documented extensively in the RAG literature. Barnett et al. (2024) compiled a taxonomy of failure modes in RAG systems (published as "Seven Failure Points When Engineering a Retrieval Augmented Generation System"), and "wrong context retrieved" is the single most common failure mode, accounting for the majority of incorrect answers in their evaluation. The retrieved chunks are topically relevant but contextually inappropriate — they come from the wrong version, the wrong authority level, the wrong section, or the wrong scope.

### 2.2. The Chunking Amnesia Problem

RAG systems must break documents into chunks because embedding models have limited input windows (typically 512 to 8,192 tokens, depending on the model). The chunking process destroys the document's internal structure. A paragraph that originally appeared under the heading "### Military History > #### Founding Era > The Iron Covenant" becomes, after chunking, just the paragraph text with no trace of its position in the document's hierarchy. The headings — which provided structural context — are either lost entirely or included as dead text that the embedding model treats as just more words rather than as hierarchical markers.

This is the "amnesia" that chunking inflicts: the chunk forgets where it came from. It forgets its parent section, its sibling sections, its document title, its document type, and its position in the broader corpus. When the LLM receives this chunk as context during generation, it has no structural framework for interpreting the information. It cannot assess whether this chunk is a high-level summary or a granular detail, whether it's from an authoritative source or a speculative one, whether it's current or outdated, or how it connects to other chunks that were (or weren't) retrieved alongside it.

Jina AI's research on "Late Chunking" (2024) demonstrated that even the *timing* of when you chunk (before vs. after the initial encoding pass) significantly affects retrieval quality, precisely because chunking destroys contextual information that the encoder would otherwise have access to. Their work showed that preserving document-level context during the encoding step — even if you still chunk afterward — materially improves the quality of the resulting embeddings.

### 2.3. The Authority Blindness Problem

In any knowledge base with multiple versions, multiple contributors, or multiple levels of editorial approval, not all content is created equal. Some content is authoritative (reviewed, approved, canonical). Some is draft (work-in-progress, not yet validated). Some is speculative (exploratory, explicitly non-canonical). Some is deprecated (outdated, superseded by newer content). Some is derived (generated, summarized, or synthesized from primary sources).

Standard embeddings are completely blind to these distinctions. A draft paragraph and a canonical paragraph about the same topic produce nearly identical embeddings because the embedding model is encoding *meaning*, not *authority*. When a retrieval system returns both chunks to an LLM, the LLM has no basis for weighting one over the other. It may synthesize an answer that blends canonical facts with speculative content, producing a response that is *coherent but unfaithful* to the actual state of the knowledge base.

This problem is acute in collaborative environments (where multiple authors may contribute content at different approval stages), in versioned knowledge bases (where old content coexists with new content), and in creative contexts (where speculative or "what if" content is a legitimate part of the corpus but must never be confused with established canon). It is also critical in regulated domains like legal and medical documentation, where the authority status of a document (binding vs. advisory, current vs. superseded) has legal or clinical implications.

### 2.4. Summary of Deficiencies

The three problems above — semantic proximity trap, chunking amnesia, and authority blindness — share a common root cause. **Standard embedding-based retrieval encodes what content *means* but not what content *is*.** The semantic vector captures topic, terminology, and conceptual relationships. It does not capture provenance, authority, hierarchy, version status, entity type, temporal position, or structural relationships. FractalRecall exists to close this gap.

---

## 3. Research Foundations

FractalRecall does not emerge from a vacuum. It builds on and synthesizes several lines of research that have been actively developing since 2022. Understanding these foundations is important because they define the technical landscape that FractalRecall operates in, and they provide both inspiration and cautionary lessons for the library's design. What follows is not an exhaustive literature review, but a focused summary of the most directly relevant prior work.

### 3.1. Anthropic's Contextual Retrieval (2024)

In October 2024, Anthropic published a technical report describing a technique they called "Contextual Retrieval." The core idea is straightforward: before embedding a chunk, prepend it with a short, LLM-generated summary of the document-level context that chunk belongs to. The prepended context typically includes the document title, a brief description of the document's purpose, and any relevant metadata that helps situate the chunk within the larger work.

Anthropic reported that this technique reduced retrieval failure rates by 49% compared to standard chunking, and by 67% when combined with BM25 hybrid search. These are striking improvements from a relatively simple intervention, and they demonstrate that even a modest amount of structural context — just a few sentences prepended to each chunk — can dramatically improve retrieval quality.

**Relevance to FractalRecall:** Contextual Retrieval is essentially a single-layer version of what FractalRecall proposes. It enriches the chunk with *one* level of context (the parent document). FractalRecall extends this principle to *multiple* levels of context, arranged hierarchically, and provides a framework for defining, composing, and weighting those levels. FractalRecall can be understood as "Contextual Retrieval, generalized to N layers of structural context."

**Limitations addressed by FractalRecall:** Anthropic's approach requires an LLM call for every chunk during indexing (to generate the contextual summary), which adds significant cost and latency at scale. It also produces a flat, unstructured context prefix — there's no distinction between different *types* of contextual information (authority status vs. temporal position vs. entity type). FractalRecall introduces a typed, layered context structure that makes these distinctions explicit and queryable.

### 3.2. Matryoshka Representation Learning (2022)

Kusupati et al. (2022) introduced Matryoshka Representation Learning (MRL), a training technique that produces embeddings where the first *d* dimensions of the vector are themselves a valid (lower-resolution) embedding. Named after Russian nesting dolls, this allows a single embedding model to produce vectors that work at multiple granularities: you can use the full 768-dimensional vector for high-fidelity similarity search, or truncate it to 256 dimensions for faster, coarser search, or to 64 dimensions for rapid filtering.

Several modern embedding models support MRL natively, including Nomic's `nomic-embed-text` (which can be run locally) and OpenAI's `text-embedding-3-small` and `text-embedding-3-large`.

**Relevance to FractalRecall:** The Matryoshka concept directly inspires FractalRecall's multi-resolution architecture. If you think of each context layer as corresponding to a "zoom level" — from the corpus level (most zoomed out) to the sentence level (most zoomed in) — then FractalRecall is applying the Matryoshka principle to *structural* granularity, not just vector dimensionality. A fractal embedding should be queryable at any level of structural resolution: "find me anything in this corpus about military factions" (coarse), "find me canonical Third Age faction documents" (medium), or "find me the founding date of the Iron Covenant in authoritative sources" (fine).

### 3.3. Microsoft GraphRAG (2024)

Microsoft Research published GraphRAG in 2024, a system that constructs a knowledge graph from a document corpus and uses graph-based community detection to organize related entities into hierarchical clusters. During retrieval, the system traverses the graph to pull in structurally related context — if you query about a character, the system also retrieves information about their faction, their era, their key relationships, and the events they participated in.

GraphRAG demonstrated significant improvements over standard RAG on complex, multi-hop queries (questions that require synthesizing information from multiple documents), achieving up to 70% improvement on comprehensiveness metrics for global queries that span the entire corpus.

**Relevance to FractalRecall:** GraphRAG validates the core insight that *structural relationships between entities* are as important as *semantic similarity* for retrieval quality. FractalRecall's relationship-aware context layers are directly informed by this finding. However, GraphRAG constructs its graph *automatically* using LLM-based entity extraction, which is expensive and error-prone. FractalRecall takes a different approach in its expected usage: the structural graph is *declared* by the consuming application (e.g., Chronicle's YAML frontmatter relationships), not inferred by the library. This makes FractalRecall cheaper to run, more deterministic, and more accurate in domains where the structure is already known.

**Key distinction:** GraphRAG is a *complete retrieval system*. FractalRecall is a *library that enhances embeddings*. They operate at different levels of abstraction. An application could theoretically use both — GraphRAG for graph traversal and FractalRecall for context-enriched embeddings within each retrieved node.

### 3.4. RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval (2024)

Sarthi et al. (2024) introduced RAPTOR, a system that builds a tree structure over a document corpus by recursively clustering and summarizing chunks. Leaf nodes are the original chunks. Parent nodes are LLM-generated summaries of clusters of related chunks. Grandparent nodes are summaries of summaries. The tree is queried at multiple levels simultaneously: a query might match a specific leaf chunk (granular detail) *and* a high-level summary node (broad context), and both are returned to the LLM.

RAPTOR improved retrieval quality on question-answering benchmarks by 20% compared to standard dense retrieval, with particularly strong improvements on questions that required synthesizing information across multiple passages.

**Relevance to FractalRecall:** RAPTOR's recursive tree structure is conceptually similar to FractalRecall's hierarchical context layers. Both systems recognize that information exists at multiple levels of abstraction and that a good retrieval system should be able to operate at all of them. The key difference is that RAPTOR builds its tree *from the bottom up* (clustering and summarizing), while FractalRecall constructs its hierarchy *from the top down* (using declared structural metadata). RAPTOR's approach is more automated but less precise; FractalRecall's approach requires more upfront structural declaration but produces a hierarchy that exactly reflects the actual organization of the knowledge base.

### 3.5. Late Chunking (Jina AI, 2024)

Jina AI's "Late Chunking" technique (2024) addresses the chunking amnesia problem by changing *when* chunking occurs in the embedding pipeline. In standard RAG, you chunk first and embed each chunk independently. In Late Chunking, you first pass the *entire document* through the embedding model's encoder (which produces token-level representations), and *then* chunk the token-level representations into segment-level embeddings. Because the encoder has already seen the full document when producing each token's representation, each chunk's embedding implicitly carries information about the surrounding context — the attention mechanism in the transformer model has already allowed each token to "look at" the rest of the document.

Jina reported improvements of 15-25% on retrieval benchmarks compared to standard chunking, with the most dramatic improvements on queries where context is critical for disambiguation.

**Relevance to FractalRecall:** Late Chunking addresses the same problem that FractalRecall addresses — preserving context through the chunking process — but at a different level of the stack. Late Chunking operates at the *embedding model level* (changing how the encoder processes the text). FractalRecall operates at the *representation level* (changing what text is presented to the encoder). These approaches are complementary, not competing. An implementation could use Late Chunking *within* each context layer's embedding process, combining both forms of context preservation for maximum benefit.

### 3.6. Research Synthesis: What FractalRecall Builds On

Drawing these threads together, FractalRecall synthesizes the following validated insights from recent research:

**From Anthropic's Contextual Retrieval:** Prepending structural context to chunks before embedding dramatically improves retrieval quality. FractalRecall generalizes this to multiple, typed context layers.

**From Matryoshka Representation Learning:** Embeddings can encode information at multiple granularities simultaneously. FractalRecall applies this principle to structural granularity, not just vector dimensionality.

**From Microsoft GraphRAG:** Structural relationships between entities are critical for retrieval quality, especially for complex queries. FractalRecall encodes relationship information as a dedicated context layer.

**From RAPTOR:** Hierarchical, multi-level retrieval outperforms flat retrieval. FractalRecall provides a framework for hierarchical context that is declared (not inferred), making it cheaper and more precise.

**From Jina AI's Late Chunking:** Preserving document-level context through the encoding process improves embedding quality. FractalRecall's architecture is compatible with Late Chunking as an additional enhancement at the embedding model level.

**The novel contribution of FractalRecall** is the unification of these insights into a single, domain-agnostic, developer-friendly framework. None of the systems above provide a *library* that an application developer can drop into their .NET project and configure for their specific domain. They are either research prototypes, proprietary systems, or complete retrieval pipelines that must be adopted wholesale. FractalRecall is designed to be a composable building block — a library that enhances any embedding-based retrieval system with hierarchical structural awareness.

---

## 4. Core Concepts

### 4.1. The DNA Metaphor, Formalized

The working metaphor throughout this document is that a piece of content in a structured knowledge base is analogous to a gene in a genome. A gene's function depends not only on its own nucleotide sequence (its "semantic content") but also on its position within a chromosome (its "structural address"), its regulatory elements (which control when and how it's expressed — analogous to authority status and versioning), its relationships to other genes in the same pathway (analogous to entity relationships), and its evolutionary history (analogous to version history and deprecation status).

In this metaphor, a standard embedding captures only the nucleotide sequence — the raw content. FractalRecall adds the full "genetic context": the structural address, the regulatory status, the relational network, and the provenance history. A chunk that arrives with its full FractalRecall context is not a bare sequence — it's a fully annotated gene with its chromosomal address, its expression profile, and its pathway membership.

This metaphor is not just illustrative — it suggests specific design decisions. In genetics, the same gene sequence can have dramatically different effects depending on its chromosomal context (this is the basis of position-effect variegation). Similarly, the same text content can have dramatically different significance depending on its structural context. A passage about a city's destruction means something very different in a canonical event document versus an apocryphal "what if" exploration. FractalRecall ensures that the retrieval system can make this distinction.

### 4.2. Context Layers

A **Context Layer** is the fundamental building block of FractalRecall. It represents one level of structural context that can be associated with a piece of content. Each context layer has a defined type, a value, and optional metadata.

Context layers are ordered from most general (outermost) to most specific (innermost), mirroring the fractal nature of hierarchical structure. The outermost layer describes the corpus or domain. The innermost layer is the raw content itself. The layers in between describe progressively more specific structural positions.

A context layer is not necessarily a single scalar value. It can be a composite structure. For example, a "relationships" layer might contain multiple key-value pairs describing how the current entity connects to other entities in the knowledge base. The layer specification (Section 6) defines the anatomy of a layer in full detail.

### 4.3. Composite Representation

A **Composite Representation** is the assembled collection of context layers for a given chunk of content, arranged in hierarchical order from outermost to innermost. This is the "DNA strand" — the full structural identity of the chunk, ready to be embedded.

The composite representation serves two purposes simultaneously. First, when rendered as text and passed to an embedding model, it produces a vector that encodes structural context alongside semantic content. Second, when stored alongside the vector as structured metadata, it enables filtered queries that can constrain retrieval by any combination of context layers. These two mechanisms (enriched embedding and metadata filtering) work together to provide both semantic awareness and structural precision.

### 4.4. Structural Fingerprint

A **Structural Fingerprint** is a compact, deterministic hash derived from the non-content layers of a composite representation. It uniquely identifies a chunk's structural position without reference to its semantic content. Two chunks with the same structural fingerprint occupy the same position in the knowledge base hierarchy (e.g., same document, same section, same authority level, same entity type) even if their semantic content differs.

Structural fingerprints enable efficient operations like "find all chunks that occupy the same structural position across different versions of the corpus" or "detect when a chunk's structural context has changed even though its content hasn't." They are also useful for cache invalidation: when a document's structural metadata changes (e.g., its canon status is updated), the fingerprint changes, signaling that the chunk's embedding needs to be regenerated even though the raw text hasn't changed.

### 4.5. Fractal Index

A **Fractal Index** is the storage and retrieval engine that manages composite representations and their associated embeddings. It combines vector similarity search (for semantic retrieval) with structured metadata filtering (for structural constraint) and optional graph traversal (for relationship-aware retrieval). The Fractal Index is an abstraction — the library defines its interface, but the actual storage backend is pluggable. Implementations could be backed by SQLite with vector extensions, Qdrant, Chroma, FAISS with a metadata sidecar, or any other storage system that supports both vector search and metadata filtering.

### 4.6. Layer-Weighted Retrieval

**Layer-Weighted Retrieval** is the query mechanism that allows consumers to specify which context layers matter most for a given query. Not all queries care about all layers equally. A query like "What happened in the Third Age?" cares primarily about the temporal layer and the content layer, but doesn't care much about the authority layer (canonical and draft content are both relevant). A query like "What is the *official* founding date of the Iron Covenant?" cares intensely about the authority layer (only canonical sources should be retrieved) and the entity layer (only Iron Covenant-related content), but is temporally unbounded.

Layer-Weighted Retrieval allows the consuming application to assign relative weights to each context layer at query time, influencing how the retrieval system ranks results. This is analogous to how a database query might use different indexes for different queries depending on the WHERE clause — the storage is the same, but the access pattern is optimized for the specific question.

---

## 5. Architecture Overview

### 5.1. System Components

The FractalRecall library consists of the following major components. Each component is described at the interface level here; implementation details are deferred to the detailed design specification (a separate document to be written during Phase 2).

**ContextLayerRegistry:** Manages the catalog of context layer types known to the system. Consuming applications register their domain-specific layer types here. The registry enforces that layer types have unique names, defined schemas, and declared positions in the hierarchy (outermost to innermost ordering). The registry is configured once during application startup and is immutable thereafter.

**CompositeRepresentationBuilder:** Constructs composite representations from raw content and context layer values. The builder validates that all required layers are present (according to the registry's schema), assembles them in hierarchical order, and produces both a textual rendering (for embedding) and a structured metadata object (for filtered search). The builder follows the builder pattern, allowing consuming applications to fluently add layer values one at a time.

**EmbeddingProvider (Interface):** An abstraction over the embedding model used to convert textual representations into vectors. FractalRecall does not bundle an embedding model — it expects the consuming application to provide an implementation of this interface. Reference implementations will be provided for common backends: Ollama (for local models like `nomic-embed-text`), OpenAI-compatible APIs, and raw `sentence-transformers` output via an interop bridge.

**FractalIndex (Interface):** An abstraction over the storage and retrieval backend. The index accepts composite representations with their embeddings for storage, and executes queries that combine vector similarity with metadata filtering. Reference implementations will be provided for SQLite (with a vector extension like `sqlite-vec` or `sqlite-vss`), in-memory storage (for testing), and optionally Qdrant or Chroma for production use cases that require dedicated vector database performance.

**QueryBuilder:** Constructs retrieval queries with layer-weighted constraints. The query builder allows the consuming application to specify the query text (which will be embedded), metadata filters (which constrain the structural context of results), layer weights (which influence ranking), and result parameters (top-K count, score thresholds, etc.).

**EvaluationHarness:** A testing and benchmarking component that enables side-by-side comparison of different retrieval strategies (standard RAG, metadata-filtered RAG, and FractalRecall) against a ground-truth evaluation set. This component is essential for validating that FractalRecall actually improves retrieval quality — a claim that must be demonstrated empirically, not assumed.

### 5.2. Data Flow: Indexing Pipeline

The indexing pipeline is the process by which content enters the Fractal Index. The flow proceeds through the following stages.

**Stage 1 — Content Ingestion:** The consuming application reads a source document (e.g., a Markdown file with YAML frontmatter) and extracts the raw text content and the structural metadata. This stage is entirely the consuming application's responsibility — FractalRecall does not know how to parse any specific document format.

**Stage 2 — Chunking:** The consuming application chunks the raw text into segments suitable for embedding. FractalRecall provides optional chunking utilities (sentence-based, paragraph-based, heading-based, and fixed-size window with overlap), but the consuming application can use its own chunking strategy. The critical requirement is that each chunk retains a reference to its source document and its position within that document, because this information is needed to construct the context layers.

**Stage 3 — Layer Construction:** For each chunk, the consuming application constructs context layer values using data from the source document's metadata and the chunk's position within the document. This is where domain-specific knowledge enters the system. A worldbuilding application might set the "entity type" layer to "faction" and the "authority" layer to "canonical." A legal documentation application might set the "document type" layer to "regulatory filing" and the "jurisdiction" layer to "federal."

**Stage 4 — Composite Assembly:** The consuming application passes the chunk text and its context layer values to the CompositeRepresentationBuilder, which assembles the composite representation, validates it against the registry schema, and produces the textual rendering and structured metadata.

**Stage 5 — Embedding:** The textual rendering of the composite representation is passed to the EmbeddingProvider, which returns a vector. Note that the embedded text includes the context layer prefixes, so the resulting vector encodes structural context alongside semantic content.

**Stage 6 — Storage:** The vector, the structured metadata, and the raw chunk text are stored in the FractalIndex. The metadata is indexed for filtered queries. The vector is indexed for similarity search. The raw text is stored for retrieval (so it can be returned to the consuming application and ultimately to the LLM as context).

### 5.3. Data Flow: Query Pipeline

The query pipeline is the process by which a consuming application retrieves relevant content from the Fractal Index. The flow proceeds through the following stages.

**Stage 1 — Query Construction:** The consuming application constructs a query using the QueryBuilder, specifying the query text, any metadata filters, layer weights, and result parameters. The query text is typically the user's natural language question or the LLM's information need.

**Stage 2 — Query Embedding:** The query text is optionally enriched with context layer prefixes (if the consuming application has structural expectations about the kind of content it's looking for) and then embedded via the EmbeddingProvider. This produces the query vector.

**Stage 3 — Retrieval:** The FractalIndex executes the query by combining vector similarity search (using the query vector) with metadata filtering (using the structural constraints from the query). Results are ranked by a composite score that combines semantic similarity with structural alignment (how well the result's context layers match the query's layer weights).

**Stage 4 — Result Assembly:** The top-K results are returned to the consuming application, each containing the raw chunk text, the structured metadata (all context layer values), the composite similarity score, and optionally a breakdown of how much each context layer contributed to the score. This breakdown is important for debugging and evaluation — it lets the consuming application (and ultimately the developer) understand *why* a particular result was ranked where it was.

### 5.4. Extension Points

FractalRecall is designed to be extensible at several key points in the architecture.

**Custom Layer Types:** Consuming applications can define any context layer types they need, beyond the standard types provided by the library. A medical documentation application might define a "clinical trial phase" layer. A software documentation application might define a "API version" layer. Custom layer types are first-class citizens — they participate in embedding enrichment and metadata filtering exactly like standard types.

**Custom Embedding Providers:** Any embedding model can be used, as long as an implementation of the EmbeddingProvider interface is provided. This ensures the library is not locked to any specific model vendor or inference infrastructure.

**Custom Index Backends:** Any storage system can be used, as long as it implements the FractalIndex interface. This allows the library to scale from local SQLite databases (for single-user tools like Chronicle) to cloud-hosted vector databases (for enterprise applications).

**Custom Scoring Functions:** The default ranking algorithm (which combines semantic similarity with structural alignment) can be replaced or extended with custom scoring logic. An application might want to boost results from recently modified documents, or penalize results from a specific author, or apply domain-specific relevance heuristics that the library cannot anticipate.

---

## 6. Layer Specification

### 6.1. Layer Anatomy

Each context layer is defined by the following properties.

**Name:** A unique, human-readable identifier for the layer type (e.g., "corpus," "entity_type," "authority," "temporal," "relational"). Names must be unique within a ContextLayerRegistry.

**Hierarchy Position:** An integer indicating the layer's position in the hierarchy, from outermost (highest number or lowest specificity) to innermost (lowest number or highest specificity). The raw content is always the innermost layer (position 0). The corpus identity is typically the outermost layer. Positions are used to determine the ordering of layers in the composite representation's textual rendering.

**Value Type:** The data type of the layer's value. Supported value types include string (free text), enum (constrained to a set of predefined options), string list (multiple values, e.g., a list of tags or eras), key-value map (for structured data like relationships), and numeric (for quantitative metadata like confidence scores or version numbers).

**Embedding Behavior:** How the layer participates in the composite representation's textual rendering. Options include "prefix" (the layer value is prepended as natural language text), "suffix" (appended after the content), "omit" (the layer is stored as metadata but not included in the embedded text), and "template" (the layer value is inserted into a configurable template string). The default behavior is "prefix."

**Filter Behavior:** How the layer participates in metadata-filtered queries. Options include "exact match" (the query value must exactly equal the stored value), "contains" (for list-typed layers, the stored list must contain the query value), "range" (for numeric layers, the stored value must fall within a query-specified range), and "exists" (any non-null value matches). The default behavior is "exact match."

**Weight Default:** The default relevance weight assigned to this layer when no query-specific weight is provided. A weight of 0 means the layer is ignored during ranking (though it may still participate in filtering). A weight of 1.0 means the layer is considered equally important as the raw content similarity. Weights greater than 1.0 mean the layer is considered more important than content similarity for ranking purposes.

### 6.2. Standard Layer Types

FractalRecall ships with a set of standard layer types that are broadly applicable across domains. Consuming applications can use these as-is, extend them, or ignore them in favor of entirely custom layers.

**Corpus Layer (Hierarchy: 100):** Identifies which knowledge base or collection the content belongs to. Example values: "Aethelgard Worldbuilding Corpus v5.0," "Acme Corp Technical Documentation," "Johnson v. Smith Case Files." Embedding behavior: prefix. This layer is most useful in applications that search across multiple knowledge bases simultaneously.

**Domain Layer (Hierarchy: 90):** Identifies the broad categorical domain of the content within the corpus. Example values: "organizations," "characters," "locations," "events," "game mechanics," "API reference," "legal precedent." Embedding behavior: prefix. This layer helps the retrieval system distinguish between different *kinds* of content that might share similar vocabulary.

**Entity Layer (Hierarchy: 80):** Identifies the specific entity that the content describes. Example values: "The Iron Covenant," "Elena Voss," "Ashenmoor Region," "Third Age Timeline." Embedding behavior: prefix. This layer is critical for entity-specific queries and for ensuring that retrieval results are about the right entity, not just the right topic.

**Authority Layer (Hierarchy: 70):** Indicates the editorial or canonical status of the content. Example values: "canonical," "draft," "apocryphal," "deprecated," "superseded," "generated." Embedding behavior: prefix. This layer enables authority-aware retrieval — the ability to restrict results to only authoritative content, or to include speculative content with appropriate caveats.

**Temporal Layer (Hierarchy: 60):** Indicates the time period that the content describes (not the time the content was written). Example values: "Third Age," "Year 412," "Q3 2025," "Pre-Founding Era." Embedding behavior: prefix. This layer enables time-scoped queries and prevents anachronistic retrieval (returning content from the wrong era).

**Relational Layer (Hierarchy: 50):** Describes the relationships between the current entity and other entities in the knowledge base. Example value: a key-value map like `{"founded_by": "Elena Voss", "rival": "Silver Hand", "region": "Ashenmoor"}`. Embedding behavior: template (rendered as a natural language sentence like "This entity was founded by Elena Voss, is a rival of the Silver Hand, and is located in the Ashenmoor region."). This layer enables relationship-aware retrieval and helps the embedding model understand the entity's position in the knowledge graph.

**Section Layer (Hierarchy: 20):** Identifies the section or structural subdivision of the document that the chunk comes from. Example values: "Origins," "Military History," "Key Members," "Prerequisites," "Return Value." Embedding behavior: prefix. This layer helps disambiguate chunks from different sections of the same document that might have similar content but different purposes.

**Content Layer (Hierarchy: 0):** The raw text content of the chunk itself. This is always the innermost layer and is always present. Embedding behavior: this IS the content that the other layers provide context for.

### 6.3. Layer Composition Rules

The following rules govern how layers are composed into a composite representation.

**Rule 1 — Hierarchical Ordering:** Layers are always rendered in descending hierarchy order (outermost first, innermost last) in the textual representation. This means the embedding model encounters the broadest context first and the most specific content last, which aligns with how transformer attention mechanisms process sequential input (earlier tokens establish context for later tokens).

**Rule 2 — Required vs. Optional Layers:** The ContextLayerRegistry configuration specifies which layers are required and which are optional for a given application. At minimum, the Content Layer is always required. All other layers are optional by default. The consuming application can mark additional layers as required (e.g., "the Authority Layer must always be present in our use case").

**Rule 3 — Null Handling:** If an optional layer has no value for a given chunk, it is omitted from both the textual rendering and the metadata. It does not appear as an empty or null entry. This prevents the embedding model from wasting capacity encoding absence.

**Rule 4 — Rendering Delimiter:** Layers in the textual rendering are separated by a configurable delimiter. The default delimiter is a double newline (`\n\n`), which is sufficient for most embedding models. The delimiter should be distinct enough that the embedding model can implicitly learn to treat it as a boundary between context levels, but not so verbose that it wastes significant token capacity.

**Rule 5 — Total Token Budget:** The composite representation has a configurable maximum token budget (defaulting to the embedding model's maximum input length). If the fully rendered composite exceeds this budget, layers are truncated from the outermost inward — the most general context is sacrificed first, preserving the most specific content and its immediate structural context. This is a graceful degradation strategy that ensures the raw content is always embedded, even if the outermost context layers must be abbreviated.

### 6.4. Worked Example: Worldbuilding Domain

The following example shows how a chunk from a Chronicle worldbuilding repository would be represented as a composite representation using FractalRecall's layer system. The source file is `factions/iron-covenant.md` in the Aethelgard repository.

**Source YAML Frontmatter:**
```yaml
type: faction
name: The Iron Covenant
canon: true
era: [Third Age, Fourth Age]
region: Ashenmoor
relationships:
  - target: "characters/elena-voss.md"
    type: founded_by
  - target: "factions/silver-hand.md"
    type: rivalry
tags: [military, expansionist, fallen]
```

**Source Chunk (from the "Origins" section):**
"The Iron Covenant was founded in Year 412 of the Third Age by Commander Elena Voss, following the Arcane Purges that devastated the Ashenmoor region. Voss, a decorated military officer who had lost her entire regiment to uncontrolled magical detonations, believed that arcane power could only be safely wielded under strict military discipline."

**Constructed Context Layers:**

| Layer | Hierarchy | Value |
|-------|-----------|-------|
| Corpus | 100 | Aethelgard Worldbuilding Corpus v5.0 |
| Domain | 90 | Organizations / Factions |
| Entity | 80 | The Iron Covenant |
| Authority | 70 | Canonical |
| Temporal | 60 | Third Age, Fourth Age |
| Relational | 50 | Founded by Elena Voss; Rival of the Silver Hand; Located in Ashenmoor |
| Section | 20 | Origins |
| Content | 0 | *(the raw chunk text)* |

**Rendered Textual Representation (for embedding):**

```
Corpus: Aethelgard Worldbuilding Corpus v5.0

Domain: This content is from a faction document in the organizations category.

Entity: This content describes The Iron Covenant.

Authority: This content is canonical and authoritative.

Temporal: The events described span the Third Age and Fourth Age.

Relationships: The Iron Covenant was founded by Elena Voss, is a rival of the Silver Hand, and is located in the Ashenmoor region.

Section: This content is from the Origins section.

The Iron Covenant was founded in Year 412 of the Third Age by Commander Elena Voss, following the Arcane Purges that devastated the Ashenmoor region. Voss, a decorated military officer who had lost her entire regiment to uncontrolled magical detonations, believed that arcane power could only be safely wielded under strict military discipline.
```

**Structural Fingerprint:** A hash of `[corpus=aethelgard-v5, domain=factions, entity=iron-covenant, authority=canonical, temporal=third-age+fourth-age, section=origins]`. This fingerprint uniquely identifies this chunk's structural position and will change if any of these metadata values change, triggering re-embedding.

### 6.5. Worked Example: Technical Documentation Domain

The following example demonstrates FractalRecall's domain-agnostic design by showing the same layer system applied to a technical documentation corpus.

**Source File:** `api/v3/endpoints/users/get-user.md` in a REST API documentation repository.

**Constructed Context Layers:**

| Layer | Hierarchy | Value |
|-------|-----------|-------|
| Corpus | 100 | Acme Platform API Documentation |
| Domain | 90 | API Reference / Endpoints |
| Entity | 80 | GET /api/v3/users/{id} |
| Authority | 70 | Released (v3.2.1) |
| Temporal | 60 | API Version 3 |
| Relational | 50 | Related endpoints: POST /users, DELETE /users/{id}; Requires authentication: Bearer token; Rate limit: 100/min |
| Section | 20 | Response Schema |
| Content | 0 | "The response body contains a User object with the following fields: id (string, UUID format), email (string), display_name (string, nullable), created_at (ISO 8601 datetime)..." |

**Rendered Textual Representation (for embedding):**

```
Corpus: Acme Platform API Documentation

Domain: This content is from an API endpoint reference document.

Entity: This content describes the GET /api/v3/users/{id} endpoint.

Authority: This content is from the released API, version 3.2.1.

Temporal: This content applies to API Version 3.

Relationships: Related endpoints include POST /users and DELETE /users/{id}. This endpoint requires Bearer token authentication and has a rate limit of 100 requests per minute.

Section: This content is from the Response Schema section.

The response body contains a User object with the following fields: id (string, UUID format), email (string), display_name (string, nullable), created_at (ISO 8601 datetime)...
```

The layer names and hierarchy positions are identical to the worldbuilding example. The *values* are completely different because they describe a different domain. This is the key design property: the framework is generic, and the domain knowledge lives entirely in the consuming application's layer value construction logic.

### 6.6. Worked Example: Legal Document Domain

One more example to demonstrate versatility, this time in a legal documentation context.

**Source File:** A federal regulatory filing.

**Constructed Context Layers:**

| Layer | Hierarchy | Value |
|-------|-----------|-------|
| Corpus | 100 | US Federal Regulatory Corpus |
| Domain | 90 | Environmental Regulation / Emissions Standards |
| Entity | 80 | 40 CFR Part 60 — Standards of Performance for New Stationary Sources |
| Authority | 70 | Binding (Final Rule, effective 2024-03-01) |
| Temporal | 60 | Effective 2024-03-01; Supersedes 2019 revision |
| Relational | 50 | Implements: Clean Air Act Section 111; Cited by: EPA v. West Virginia (2022); Related: 40 CFR Part 63 |
| Section | 20 | Subpart Da — Electric Utility Steam Generating Units |
| Content | 0 | *(regulatory text)* |

Notice how the Authority layer value "Binding (Final Rule, effective 2024-03-01)" carries different *semantic weight* in a legal context than "Canonical" does in a worldbuilding context, even though both use the same layer type. The layer provides the *structure*; the domain provides the *meaning*. A legal retrieval system would weight the Authority layer very heavily (it matters enormously whether a regulation is binding or proposed), while a casual worldbuilding search might weight it lower.

---

## 7. Embedding Strategy

This section describes three candidate approaches for how context layers are incorporated into the actual embedding process. A primary goal of the Google Colab prototyping phase (Section 10) is to empirically evaluate these approaches and determine which one (or which combination) produces the best retrieval quality.

### 7.1. Approach A: Prefix Enrichment (Simplest)

In this approach, the composite representation is rendered as a single text string (as shown in the worked examples above) and embedded as a single vector. The embedding model receives the full context-enriched text and produces one vector that encodes both the structural context and the semantic content.

**Advantages:** This is the simplest approach to implement and the most compatible with existing embedding models and vector databases. It requires no changes to the embedding model, the vector storage, or the retrieval algorithm. It builds directly on Anthropic's Contextual Retrieval technique, simply extending the context prefix from one layer to multiple layers.

**Disadvantages:** The embedding model is responsible for learning, implicitly, which parts of the input are "structural context" and which parts are "semantic content." It has no explicit mechanism for distinguishing between them — it just sees a sequence of tokens. In practice, embedding models are reasonably good at this (the prefix text is stylistically distinct from the content text), but there's no guarantee that the model is correctly weighting the structural information versus the semantic information. Additionally, all the structural context consumes tokens from the model's input window, leaving less room for the actual content in cases where the content is long.

**Best for:** Prototyping, small-to-medium corpora, and use cases where simplicity is more important than maximum precision.

### 7.2. Approach B: Multi-Vector Composition

In this approach, each context layer is embedded *separately*, producing a set of vectors for each chunk rather than a single vector. The layer vectors are then combined at query time using a weighted combination strategy: the query is compared against each layer's vector independently, and the scores are combined according to the layer weights.

For example, a single chunk might produce seven vectors: one for the corpus layer, one for the domain layer, one for the entity layer, and so on. At query time, the query vector is compared against each of these seven vectors, producing seven similarity scores. The final ranking score is a weighted sum of these individual scores, with weights determined by the query's layer weight specification.

**Advantages:** This approach gives the retrieval system explicit, fine-grained control over how much each layer contributes to the ranking. It doesn't rely on the embedding model to implicitly weight structural information — the weighting is explicit and adjustable at query time. It also avoids the token budget problem, since each layer is embedded independently and can use the full model input window.

**Disadvantages:** This approach multiplies the storage requirements (one vector per layer per chunk, rather than one vector per chunk) and increases query latency (multiple vector comparisons per chunk instead of one). For a corpus with 10,000 chunks and 7 layers, you'd need to store 70,000 vectors. This is manageable with modern hardware and vector databases, but it's a meaningful increase in complexity and cost. The approach also requires a more sophisticated index backend that can efficiently execute multi-vector queries with weighted combination.

**Best for:** High-precision use cases where the retrieval quality improvement justifies the additional storage and query complexity. Production deployments where layer-weighted control is a critical feature.

### 7.3. Approach C: Hybrid Embedding with Metadata Sidecar

In this approach, the content is embedded with a *selected subset* of context layers as a prefix (typically the most impactful layers, such as Authority and Entity), while the remaining layers are stored as structured metadata alongside the vector. During retrieval, the vector similarity search handles semantic and partially-structural matching, while the metadata filters handle the remaining structural constraints.

For example, the embedded text might include only the Authority, Entity, and Content layers. The Corpus, Domain, Temporal, Relational, and Section layers would be stored as metadata and used for pre-filtering or post-filtering.

**Advantages:** This approach balances embedding quality against storage efficiency. The most impactful structural context is baked into the embedding (improving the quality of the semantic search), while less impactful or more easily filterable context is handled via metadata (which is cheap to store and fast to filter on). It requires only one vector per chunk, keeping storage requirements manageable, while still enabling structurally-aware retrieval through the metadata filters.

**Disadvantages:** The developer must decide *which* layers to include in the embedding and which to relegate to metadata. This is a tuning decision that may vary by domain and by query patterns. Making the wrong choice (e.g., including a layer in the embedding that doesn't improve retrieval, or excluding a layer that would have improved it) reduces the effectiveness of the approach.

**Best for:** Production deployments at scale where storage efficiency matters. Use cases where some context layers are better suited to filtering (e.g., Authority = "canonical" is an easy exact-match filter) while others are better suited to embedding enrichment (e.g., Relational context is hard to filter on but easy to embed).

### 7.4. Comparative Analysis and Recommended Path

The three approaches form a progression from simplest to most sophisticated.

| Dimension | Approach A | Approach B | Approach C |
|-----------|-----------|-----------|-----------|
| Implementation Complexity | Low | High | Medium |
| Storage Overhead | None (1 vector/chunk) | High (N vectors/chunk) | None (1 vector/chunk + metadata) |
| Query Latency | Low | High | Low-Medium |
| Layer Weight Control | None (implicit) | Full (explicit per-layer) | Partial (some layers explicit, others implicit) |
| Embedding Model Requirements | Any | Any | Any |
| Index Backend Requirements | Basic vector DB | Multi-vector capable DB | Vector DB with metadata filtering |

**Recommended prototyping strategy:** Begin with Approach A in the Google Colab notebooks, because it's the simplest to implement and the most directly comparable to existing baselines (standard RAG and Anthropic's Contextual Retrieval). If Approach A shows meaningful improvement, proceed to Approach C to evaluate whether selective layer inclusion can further improve results while keeping storage efficient. Approach B should be evaluated only if the other approaches prove insufficient, due to its significantly higher implementation complexity.

The C# library should ultimately support all three approaches via its pluggable architecture, allowing the consuming application to choose the strategy that best fits its requirements.

---

## 8. User Stories

### 8.1. Library Consumer Stories (Developer Audience)

These stories describe the experience of a developer who is using FractalRecall as a NuGet package dependency in their own application.

**US-LIB-001: Basic Integration**
*As a .NET developer building an AI-enhanced application, I want to add FractalRecall as a NuGet dependency and configure it with my domain's context layers, so that I can improve the retrieval quality of my RAG pipeline without building a custom embedding enrichment system from scratch.*

Acceptance Criteria:
- Installing the NuGet package and configuring a basic ContextLayerRegistry with two custom layers takes less than 30 minutes for a developer familiar with .NET dependency injection patterns.
- The library provides a `README.md` with a complete quick-start example that indexes 10 documents and executes a query within a single `Program.cs` file.
- The library does not require any specific embedding model, vector database, or LLM. All external dependencies are abstracted behind interfaces.

**US-LIB-002: Custom Layer Definition**
*As a developer working in a specialized domain (legal, medical, game design, etc.), I want to define custom context layer types specific to my domain, so that the retrieval system understands the structural concepts that matter in my context.*

Acceptance Criteria:
- Custom layer types are defined via a fluent configuration API during application startup.
- Each custom layer type specifies its name, hierarchy position, value type, embedding behavior, and filter behavior.
- Custom layer types are validated at registration time (e.g., duplicate names are rejected, hierarchy positions must be unique).
- Documentation includes at least three worked examples of custom layer definitions for different domains.

**US-LIB-003: Embedding Provider Flexibility**
*As a developer who uses a local LLM inference server (such as Ollama or LM Studio), I want to plug in my own embedding provider, so that I can use FractalRecall with whatever embedding model I have available without being forced into a cloud API dependency.*

Acceptance Criteria:
- The `IEmbeddingProvider` interface has a single method: given a string, return a float array (the vector).
- The library ships with at least two reference implementations: one for Ollama's API (local) and one for OpenAI-compatible APIs (cloud).
- A developer can implement a custom `IEmbeddingProvider` in under 20 lines of code for any HTTP-based embedding API.
- The library includes an `InMemoryEmbeddingProvider` that returns deterministic, fake embeddings for unit testing, so that consuming application tests don't require a running embedding model.

**US-LIB-004: Retrieval Quality Evaluation**
*As a developer integrating FractalRecall, I want to run an evaluation benchmark against my own corpus, so that I can measure whether FractalRecall actually improves retrieval quality compared to standard RAG in my specific domain.*

Acceptance Criteria:
- The EvaluationHarness component accepts a ground-truth dataset (query + expected relevant chunk IDs).
- The harness runs the same queries against configurable retrieval strategies (standard, metadata-filtered, FractalRecall) and produces a comparative report.
- The report includes precision, recall, NDCG, and MRR metrics (defined in Section 11) for each strategy.
- The harness can be invoked programmatically (for CI integration) or via a CLI command (for ad-hoc evaluation).

**US-LIB-005: Incremental Indexing**
*As a developer whose knowledge base changes over time (documents are added, updated, and deprecated), I want FractalRecall to support incremental indexing, so that I don't have to re-embed the entire corpus every time a single document changes.*

Acceptance Criteria:
- The Fractal Index tracks the structural fingerprint of each indexed chunk.
- When a document is re-indexed, only chunks whose structural fingerprint or content has changed are re-embedded.
- Chunks from deleted documents are removed from the index.
- The incremental indexing process produces a log indicating how many chunks were added, updated, unchanged, and removed.

### 8.2. End-User Stories via Chronicle Integration

These stories describe the experience of an end user (a worldbuilder) using Chronicle, which internally uses FractalRecall for its retrieval features. The end user does not directly interact with FractalRecall — they interact with Chronicle's CLI commands. These stories are included because they ground FractalRecall's design in real user needs.

**US-CHR-001: Semantic Lore Search**
*As a worldbuilder working on a large lore corpus, I want to search my worldbuilding documents using natural language questions rather than exact keyword matches, so that I can find relevant information even when I don't remember the exact terminology I used.*

Example: The user types `chronicle search "What factions have a presence in the northern territories?"` and the system returns results from faction documents that describe northern territorial activity, even if none of those documents contain the exact phrase "northern territories" (they might use "Frostmarch provinces," "the upper reaches," or "territories north of the Ashenmoor ridge").

**US-CHR-002: Canon-Aware Search**
*As a worldbuilder who maintains both canonical and apocryphal content in my repository, I want my searches to default to canonical results, with an explicit flag to include non-canonical content, so that I'm never accidentally misled by speculative material when looking for established facts.*

Example: `chronicle search "founding of the Iron Covenant"` returns only results from documents where `canon: true`. Adding the `--include-apocrypha` flag broadens the search to include apocryphal and draft content, clearly labeled as such in the results.

**US-CHR-003: Temporal Scoping**
*As a worldbuilder with a multi-era timeline, I want to scope my searches to a specific era, so that I don't get results from time periods that aren't relevant to what I'm currently working on.*

Example: `chronicle search "major battles" --era "Third Age"` returns only results from documents tagged with the Third Age era, filtering out battles from other eras that would be distracting.

**US-CHR-004: Relationship Traversal**
*As a worldbuilder, when I search for information about a specific entity, I want the results to include contextually relevant information about closely related entities, so that I get a fuller picture without having to run multiple searches.*

Example: Searching for "Elena Voss" returns results from Elena Voss's character document *and* from documents about entities directly related to her (the Iron Covenant, the Arcane Purges, the Ashenmoor region), ranked by a combination of semantic relevance and relationship proximity.

**US-CHR-005: Contradiction Surface**
*As a worldbuilder, I want to be warned when my search results contain information that appears to contradict other established facts in the corpus, so that I can identify and resolve inconsistencies before they propagate.*

Example: A search for "Thornhaven" returns a result describing Thornhaven as a thriving trade hub (from an older document) alongside a result describing Thornhaven's destruction in a siege (from a newer document). Chronicle flags the potential contradiction in the search results, noting the conflicting assertions and the relative dates of the documents.

### 8.3. Researcher and Evaluator Stories

These stories describe the experience of someone (potentially the project author) who is evaluating FractalRecall's effectiveness as a retrieval technique.

**US-RES-001: Baseline Comparison**
*As a researcher evaluating FractalRecall, I want to run identical queries against standard RAG, Contextual Retrieval (Anthropic-style single-layer enrichment), and FractalRecall (multi-layer enrichment), using the same corpus and the same embedding model, so that I can isolate the impact of multi-layer context enrichment on retrieval quality.*

**US-RES-002: Layer Ablation Study**
*As a researcher, I want to run an ablation study that measures retrieval quality as context layers are added one at a time (content only → content + authority → content + authority + entity → ... → all layers), so that I can determine which layers contribute the most to retrieval improvement and which layers are redundant or counterproductive.*

**US-RES-003: Cross-Domain Evaluation**
*As a researcher, I want to evaluate FractalRecall on at least two different domain corpora (e.g., worldbuilding + technical documentation) using the same library configuration, so that I can assess whether the technique generalizes across domains or is only effective in specific contexts.*

---

## 9. API Design (Conceptual)

This section presents a conceptual sketch of FractalRecall's public API surface. This is not a final API specification — it is a starting point for design discussion that will be refined during implementation. Code examples are in C# pseudocode to establish the intended developer experience.

### 9.1. Core Interfaces

```csharp
/// <summary>
/// Converts text into a vector representation (embedding).
/// Implementations connect to specific embedding models/services.
/// </summary>
public interface IEmbeddingProvider
{
    /// <summary>
    /// Generates a vector embedding for the provided text input.
    /// </summary>
    /// <param name="text">The text to embed. May include context layer 
    /// prefixes as part of the composite representation.</param>
    /// <returns>A float array representing the embedding vector.</returns>
    Task<float[]> EmbedAsync(string text);

    /// <summary>
    /// Returns the dimensionality of vectors produced by this provider.
    /// Used by the FractalIndex to validate storage compatibility.
    /// </summary>
    int Dimensions { get; }
}

/// <summary>
/// Stores and retrieves composite representations with their embeddings.
/// Implementations connect to specific storage backends (SQLite, Qdrant, etc.).
/// </summary>
public interface IFractalIndex
{
    /// <summary>
    /// Adds or updates a chunk in the index.
    /// If a chunk with the same ID already exists, it is replaced.
    /// </summary>
    Task UpsertAsync(IndexedChunk chunk);

    /// <summary>
    /// Removes a chunk from the index by its unique identifier.
    /// </summary>
    Task RemoveAsync(string chunkId);

    /// <summary>
    /// Executes a query against the index, combining vector similarity
    /// with metadata filtering and layer-weighted ranking.
    /// </summary>
    Task<IReadOnlyList<RetrievalResult>> QueryAsync(FractalQuery query);

    /// <summary>
    /// Returns the total number of indexed chunks.
    /// Useful for diagnostics and evaluation reporting.
    /// </summary>
    Task<long> CountAsync();
}
```

### 9.2. Builder Pattern for Composite Representations

```csharp
// Example: Constructing a composite representation for a worldbuilding chunk.
// The consuming application (Chronicle) is responsible for extracting the
// layer values from its domain-specific data model (YAML frontmatter, etc.).

var composite = new CompositeRepresentationBuilder(registry)
    .WithCorpus("Aethelgard Worldbuilding Corpus v5.0")
    .WithDomain("Organizations / Factions")
    .WithEntity("The Iron Covenant")
    .WithAuthority(AuthorityLevel.Canonical)
    .WithTemporal("Third Age", "Fourth Age")
    .WithRelationships(new Dictionary<string, string>
    {
        ["founded_by"] = "Elena Voss",
        ["rival"] = "Silver Hand",
        ["region"] = "Ashenmoor"
    })
    .WithSection("Origins")
    .WithContent(chunkText)
    .Build();

// The Build() method returns a CompositeRepresentation object containing:
// - TextualRendering: the full text string ready for embedding
// - Metadata: a structured dictionary of layer values for filtered search
// - StructuralFingerprint: a hash of the non-content layers for change detection
```

### 9.3. Query Construction

```csharp
// Example: Querying for canonical Iron Covenant information from the Third Age.

var query = new FractalQueryBuilder()
    .WithQueryText("When was the Iron Covenant founded?")
    .FilterByAuthority(AuthorityLevel.Canonical)  // Only canonical results
    .FilterByTemporal("Third Age")                 // Only Third Age content
    .WeightLayer("entity", 1.5f)    // Boost results about specific entities
    .WeightLayer("authority", 2.0f) // Heavily weight canonical status
    .WeightLayer("relational", 0.5f) // Lightly consider relationships
    .TopK(5)                         // Return top 5 results
    .Build();

IReadOnlyList<RetrievalResult> results = await index.QueryAsync(query);

// Each RetrievalResult contains:
// - ChunkText: the raw content of the retrieved chunk
// - CompositeMetadata: the full set of context layer values
// - Score: the composite retrieval score
// - LayerScoreBreakdown: how much each layer contributed to the score
//   (e.g., {"semantic": 0.82, "authority": 1.0, "entity": 0.91, "temporal": 0.95})
```

### 9.4. Index Management

```csharp
// Example: Incremental indexing workflow.
// The consuming application detects which files have changed (via Git, 
// filesystem watcher, or manual trigger) and re-indexes only those files.

var indexer = new FractalIndexer(index, embeddingProvider, registry);

// IndexDocumentAsync handles chunking, layer construction, embedding,
// and upserting. It returns a summary of what changed.
IndexingSummary summary = await indexer.IndexDocumentAsync(
    documentId: "factions/iron-covenant",
    chunks: chunkedContent,
    layerValues: extractedLayerValues
);

// summary.Added: 0 (no new chunks)
// summary.Updated: 2 (two chunks had metadata changes)
// summary.Unchanged: 5 (five chunks were identical)
// summary.Removed: 1 (one chunk was deleted from the source)
```

---

## 10. Prototyping Strategy: Google Colab

### 10.1. Why Python First

The machine learning and embedding ecosystem in Python is substantially more mature than its .NET equivalent. The following libraries have no direct C# equivalents of comparable quality and community support.

- **`sentence-transformers`**: The standard library for generating embeddings from text. Provides access to hundreds of pre-trained embedding models with a consistent API. The closest C# equivalent would be calling an embedding model via an HTTP API (e.g., Ollama), which is viable but less convenient for rapid experimentation.

- **`numpy` and `scikit-learn`**: Essential for vector operations, cosine similarity computation, clustering, and statistical evaluation. C# has `MathNet.Numerics`, which is functional but less ergonomic for exploratory work.

- **`chromadb` and `faiss`**: In-memory vector databases for prototyping retrieval pipelines. The C# ecosystem has emerging options but none with the same level of community documentation and tutorial support.

- **`matplotlib` and `seaborn`**: Visualization libraries for plotting evaluation results, embedding distributions, and similarity heatmaps. Invaluable during the exploratory phase for understanding how different layer configurations affect the embedding space.

The strategic approach is: **prototype in Python (Colab), validate the technique empirically, document findings, and then implement the production library in C#.** The Colab notebooks serve as executable documentation — they record the experiments, the results, and the design decisions that inform the C# implementation. They are not throwaway work; they are a permanent part of the project's documentation.

### 10.2. Notebook Plan

The prototyping phase consists of a series of Colab notebooks, each focused on a specific experimental question. The notebooks should be developed in this order, as each one builds on the findings of the previous.

**Notebook 1: Baseline Establishment**
Purpose: Implement standard RAG (chunk → embed → retrieve) on a test corpus and measure baseline retrieval quality. This notebook establishes the "control group" that all subsequent experiments are compared against.
Key activities: Load a test corpus (a subset of the Aethelgard lore files, converted to plain text), chunk it using a standard strategy (e.g., 256-token windows with 50-token overlap), embed each chunk using `nomic-embed-text` (or another locally-runnable model), store embeddings in ChromaDB, run a set of test queries with known ground-truth answers, and measure retrieval precision, recall, and NDCG.

**Notebook 2: Single-Layer Enrichment (Replicating Anthropic)**
Purpose: Implement Anthropic's Contextual Retrieval technique (single-layer document-level context prefix) and measure improvement over the baseline. This validates that context enrichment works on *your specific corpus* before investing in multi-layer extensions.
Key activities: For each chunk, prepend a document-level context summary (generated via LLM or manually written from YAML frontmatter). Embed the enriched chunks. Run the same test queries and compare metrics to Notebook 1.

**Notebook 3: Multi-Layer Enrichment (FractalRecall Core Hypothesis)**
Purpose: Implement the full multi-layer composite representation (as described in Section 6) and measure improvement over both the baseline and single-layer enrichment. This is the core experiment that validates whether FractalRecall's approach works.
Key activities: For each chunk, construct the full composite representation with all context layers derived from YAML frontmatter. Embed the composite representations. Run the same test queries and compare metrics to Notebooks 1 and 2. Analyze which queries improved the most and which (if any) regressed.

**Notebook 4: Layer Ablation Study**
Purpose: Determine which context layers contribute the most to retrieval improvement by systematically adding and removing layers and measuring the impact on retrieval quality.
Key activities: Start with content-only embeddings (baseline). Add layers one at a time, in order of hypothesized impact (Authority → Entity → Temporal → Relational → Domain → Section → Corpus). Measure retrieval quality after each addition. Identify the "diminishing returns" point — the layer configuration that achieves the best quality-to-complexity ratio.

**Notebook 5: Embedding Strategy Comparison**
Purpose: Compare the three embedding strategies (Prefix Enrichment, Multi-Vector Composition, Hybrid with Metadata Sidecar) described in Section 7.
Key activities: Implement all three strategies using the same corpus and queries. Measure retrieval quality, indexing time, storage size, and query latency for each. Produce a comparative analysis that informs which strategy the C# library should default to.

**Notebook 6: Cross-Domain Validation**
Purpose: Apply FractalRecall to a second domain corpus (technical documentation, legal documents, or another structured knowledge base) to test whether the technique generalizes beyond worldbuilding.
Key activities: Prepare a second test corpus with its own frontmatter schema. Define domain-appropriate context layers. Run the same experimental protocol (baseline → single-layer → multi-layer → ablation). Compare results to the worldbuilding experiments.

### 10.3. Transition Criteria: Colab to C#

The transition from Python prototyping to C# production implementation should occur when the following conditions are met.

- **Empirical validation is complete:** At least Notebooks 1-4 have been executed and the results demonstrate a statistically meaningful improvement in retrieval quality from multi-layer enrichment compared to the baseline and single-layer enrichment.
- **Layer configuration is stabilized:** The ablation study (Notebook 4) has identified a recommended default layer configuration that provides strong results without unnecessary complexity.
- **Embedding strategy is selected:** The strategy comparison (Notebook 5) has identified the best default embedding strategy for the C# library.
- **Design decisions are documented:** All experimental findings are documented in the notebook outputs and summarized in a "Prototyping Findings" document that will be referenced during C# implementation.

The C# implementation does not need to wait for Notebook 6 (cross-domain validation), which can proceed in parallel with early C# development.

---

## 11. Evaluation Framework

### 11.1. Metrics

FractalRecall's effectiveness is measured using standard information retrieval metrics. These metrics are computed against a ground-truth evaluation set where the "correct" results for each query are known in advance (determined by human judgment).

**Precision@K:** Of the top K results returned, what fraction are actually relevant? Precision@5 = 0.8 means that 4 out of 5 returned results were relevant. This measures the system's ability to avoid returning irrelevant results.

**Recall@K:** Of all the relevant chunks in the corpus, what fraction appear in the top K results? Recall@5 = 0.6 means that the top 5 results captured 60% of all relevant chunks. This measures the system's ability to find all relevant content.

**NDCG@K (Normalized Discounted Cumulative Gain):** A ranking-aware metric that rewards systems that place the *most* relevant results at the *top* of the ranking. A system that returns all relevant results but in the wrong order scores lower than one that places the most relevant result first. This is the most informative single metric for evaluating retrieval quality.

**MRR (Mean Reciprocal Rank):** The average of the reciprocal ranks of the first relevant result across all queries. If the first relevant result for a query is at position 3, the reciprocal rank is 1/3. MRR measures how quickly the system surfaces *at least one* relevant result. High MRR means the user finds useful information in the first few results.

**Structural Accuracy:** A FractalRecall-specific metric that measures whether the retrieved results have the *correct structural properties* (not just the correct semantic content). If a query specifies `authority=canonical`, what fraction of results are actually canonical? If a query specifies `temporal="Third Age"`, what fraction of results are actually from the Third Age? This metric captures the structural filtering quality that standard metrics don't measure.

### 11.2. Baseline Comparisons

Every evaluation includes comparison against the following baselines.

**Baseline 1 — Standard RAG:** Chunks are embedded without any context enrichment. Retrieval is pure cosine similarity. This represents the current state of the art for naive RAG implementations.

**Baseline 2 — Metadata-Filtered RAG:** Chunks are embedded without context enrichment, but retrieval includes metadata filters (e.g., `WHERE canon = true AND era = 'Third Age'`). The vector similarity search runs only over the filtered subset. This isolates the impact of metadata filtering from the impact of embedding enrichment.

**Baseline 3 — Contextual Retrieval (Anthropic-style):** Chunks are embedded with a single document-level context prefix (the approach described in Anthropic's 2024 report). This isolates the impact of *multi-layer* enrichment by comparing it to single-layer enrichment.

**Experimental Condition — FractalRecall:** Chunks are embedded with the full multi-layer composite representation. Retrieval uses the FractalRecall query pipeline with layer-weighted ranking.

Improvement is measured as the percentage change in each metric relative to each baseline. The key question is whether FractalRecall improves over Baseline 3 (Contextual Retrieval) — since Baselines 1 and 2 are already known to be inferior based on prior research.

### 11.3. Test Corpus Requirements

A valid test corpus for FractalRecall evaluation must satisfy the following requirements.

- The corpus must contain at least 50 documents with structured metadata (YAML frontmatter or equivalent).
- The documents must span at least 3 entity types (e.g., factions, characters, events).
- The documents must include at least 2 authority levels (e.g., canonical and draft/apocryphal).
- The documents must include cross-references between entities (relationship links).
- The documents must include temporal metadata (eras, dates, or version numbers).
- The evaluator (the person judging relevance) must have deep familiarity with the corpus content, sufficient to judge whether a given retrieval result is truly relevant and structurally appropriate for a given query.

The Aethelgard worldbuilding corpus satisfies all of these requirements, making it an ideal primary test corpus. A secondary test corpus from a different domain (technical documentation is the recommended choice) should be developed for cross-domain validation.

### 11.4. Evaluation Protocol

The evaluation protocol proceeds as follows.

**Step 1 — Query Set Construction:** Develop a set of at least 30 test queries, spanning different query types: factual single-hop ("When was the Iron Covenant founded?"), factual multi-hop ("Which factions were active in the same region as Elena Voss's birthplace?"), authority-sensitive ("What is the canonical explanation for the Arcane Purges?"), temporal-scoped ("What major events occurred in the Third Age?"), and exploratory ("What are the political tensions in the Ashenmoor region?").

**Step 2 — Ground Truth Annotation:** For each query, manually identify the set of corpus chunks that constitute a correct and complete answer. Assign relevance grades: 3 (highly relevant and structurally appropriate), 2 (relevant but from a suboptimal structural context), 1 (tangentially relevant), 0 (irrelevant). These graded relevance judgments are used to compute NDCG.

**Step 3 — Retrieval Execution:** Run each query against all four conditions (Baselines 1-3 and FractalRecall) using identical corpus, chunking strategy, and embedding model. Collect the top 10 results for each query under each condition.

**Step 4 — Metric Computation:** Compute Precision@5, Recall@10, NDCG@10, MRR, and Structural Accuracy for each condition. Compute the percentage improvement of FractalRecall over each baseline.

**Step 5 — Statistical Significance:** Because the query set is small (30 queries), use a paired statistical test (Wilcoxon signed-rank test) to assess whether the observed improvements are statistically significant (p < 0.05) rather than due to random variation.

**Step 6 — Ablation Analysis:** Using the results from the layer ablation study (Notebook 4), identify which layer combinations produce statistically significant improvements and which do not. This informs the library's default configuration and documentation recommendations.

---

## 12. Risk Register

**Risk 1 — Embedding Model Sensitivity:** Different embedding models may respond differently to context-enriched input. A technique that works well with `nomic-embed-text` might not work as well with `all-MiniLM-L6-v2`. Mitigation: Test with at least 2 different embedding models during the Colab prototyping phase. Document which model families the technique works best with.

**Risk 2 — Token Budget Exhaustion:** For long content chunks, the context layer prefixes may consume a significant fraction of the embedding model's input window, potentially crowding out the actual content. Mitigation: The library implements graceful degradation (Section 6.3, Rule 5) that truncates outermost layers first. The prototyping phase should measure the relationship between prefix length and retrieval quality to identify the optimal balance.

**Risk 3 — Over-Engineering for Minimal Gain:** It's possible that the multi-layer approach provides only marginal improvement over Anthropic's simpler single-layer approach, in which case the additional complexity of FractalRecall would not be justified. Mitigation: The evaluation framework (Section 11) is specifically designed to detect this outcome. If the improvement over Contextual Retrieval is not statistically significant, the project scope should be reconsidered. This is a valid outcome, and documenting it would still be a valuable contribution.

**Risk 4 — Domain Specificity:** The technique might work well for worldbuilding (where the structural hierarchy is rich and well-defined) but poorly for other domains. Mitigation: The cross-domain evaluation (Notebook 6) tests this explicitly. If domain specificity is confirmed, the library's documentation should clearly state which types of corpora benefit most from the approach.

**Risk 5 — Adoption Barrier:** If the library requires consuming applications to do significant work (defining layers, constructing composite representations, maintaining metadata), developers may find it too complex to adopt. Mitigation: Provide sensible defaults for all configuration, ship reference implementations for common domains (worldbuilding, technical docs), and ensure the "zero-configuration" experience (just using standard layers with minimal setup) still provides meaningful improvement over standard RAG.

---

## 13. Glossary

**Chunk:** A segment of text extracted from a larger document for the purpose of embedding and retrieval. Chunks are the atomic units of a RAG system.

**Composite Representation:** The assembled collection of context layers for a given chunk, including the raw content and all structural context. The "DNA strand" of the chunk.

**Context Layer:** A single level of structural metadata associated with a chunk. Context layers are typed, ordered, and composable.

**Cosine Similarity:** A mathematical measure of the angle between two vectors. Values range from -1 (opposite) to 1 (identical). Used to rank embedding similarity.

**Embedding:** A vector (list of numbers) representation of text that captures its semantic meaning. Texts with similar meanings produce vectors that are close together in the embedding space.

**Fractal Index:** The storage and retrieval engine that manages composite representations and their embeddings. Supports combined vector and metadata queries.

**NDCG (Normalized Discounted Cumulative Gain):** A retrieval quality metric that accounts for both the relevance of results and their ranking position. Higher is better.

**RAG (Retrieval-Augmented Generation):** A technique where an LLM's responses are grounded in retrieved information from an external knowledge base, rather than relying solely on the model's training data.

**Structural Fingerprint:** A compact hash of a chunk's non-content context layers, used for change detection and cache invalidation.

**Vector Database:** A storage system optimized for storing and querying high-dimensional vectors (embeddings). Examples include Qdrant, Chroma, FAISS, and SQLite with vector extensions.

---

## 14. Open Questions

The following questions remain unresolved and should be addressed during the prototyping phase or early implementation.

**OQ-1:** What is the optimal ordering of layers in the textual rendering? The current specification prescribes outermost-first (broadest context at the top), based on the hypothesis that transformer attention benefits from establishing context before encountering specific content. Is this hypothesis supported empirically, or does innermost-first (content at the top, context below) perform equally well or better?

**OQ-2:** Should the relational layer be embedded as natural language ("founded by Elena Voss, rival of the Silver Hand") or as structured tokens ("RELATIONSHIP:founded_by:elena-voss RELATIONSHIP:rival:silver-hand")? The natural language rendering is more compatible with general-purpose embedding models, but the structured rendering might produce more discriminative embeddings if the model can learn to interpret the tokens.

**OQ-3:** How should the library handle versioned corpora where the same entity exists in multiple versions (e.g., Aethelgard v4.0 and v5.0)? Should version be a dedicated context layer, or should it be encoded within the Corpus layer value?

**OQ-4:** What is the minimum corpus size at which FractalRecall provides meaningful improvement over simpler approaches? For very small corpora (under 20 documents), the overhead of context layers may not be justified. Is there a threshold below which standard RAG is "good enough"?

**OQ-5:** How should the library handle multi-language corpora? If a corpus contains documents in multiple languages, should the context layer rendering be in the same language as the content, or always in English (which most embedding models are optimized for)?

**OQ-6:** Does the fractal recall approach interact synergistically with Late Chunking (Section 3.5), or are the two techniques redundant? Testing this interaction is a candidate for a future Colab notebook beyond the initial six.

---

## 15. Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0-draft | 2026-02-09 | Ryan | Initial draft. Core concepts, architecture, layer specification, user stories, API design, prototyping plan, evaluation framework. |

---

*This document is a living specification. It will be revised as findings from the prototyping phase (Google Colab notebooks) provide empirical data to validate, refine, or challenge the architectural decisions described herein.*
