# Fractal Recall — Exhaustive Research Plan

> **Goal**: Build an academic-grade understanding of every domain that intersects with Fractal Recall before attempting a feature/version roadmap. Each numbered step below is a research area; lettered sub-steps are individual investigation items. Items marked `[ ]` are pending; mark `[x]` as they are completed and summarized.

---

## 1. Cognitive Science & Neuroscience Foundations

Understand the biological systems that Fractal Recall claims to emulate. Every design decision should be traceable back to a neurological or psychological principle.

### 1.1 Human Memory Architecture

- [ ] **1.1a** Survey Atkinson–Shiffrin multi-store model (sensory register → short-term → long-term) and map each store to a proposed Fractal Recall tier.
- [ ] **1.1b** Study Baddeley's Working Memory model (central executive, phonological loop, visuospatial sketchpad, episodic buffer) — identify which components have digital analogues.
- [ ] **1.1c** Catalog the three long-term memory subtypes (episodic, semantic, procedural) and document how each should be encoded differently in a fractal node.
- [ ] **1.1d** Review Endel Tulving's "encoding specificity principle" — implications for how context metadata should be stored alongside data.

### 1.2 Memory Consolidation

- [ ] **1.2a** Document the hippocampal-cortical two-stage consolidation model: rapid hippocampal encoding → slow neocortical integration.
- [ ] **1.2b** Study Sharp-Wave Ripples (SWRs) and memory replay during sleep — can we design an offline "consolidation pass" that reorganizes the fractal tree?
- [ ] **1.2c** Review complementary learning systems theory (McClelland, McNaughton & O'Reilly, 1995) — how fast (hippocampus) and slow (neocortex) learners coexist and what that implies for dual-store architectures.
- [ ] **1.2d** Investigate synaptic consolidation vs. systems consolidation timescales and map to data freshness / staleness policies.

### 1.3 Hierarchical Predictive Coding

- [ ] **1.3a** Survey Karl Friston's Free Energy Principle and hierarchical predictive coding — the brain as a prediction machine that minimizes surprise.
- [ ] **1.3b** Analyze how prediction errors propagate upward while predictions propagate downward — map to bidirectional traversal of the fractal tree.
- [ ] **1.3c** Study the role of the hippocampus as the apex of a cortical prediction hierarchy (Barron et al.) — implications for positioning a "system-level" node.

### 1.4 Fractal Properties in Biology

- [ ] **1.4a** Document fractal geometry in neuronal dendritic branching, cortical folding, and brain network connectivity.
- [ ] **1.4b** Review the fractal structure of language (polysynthesis, recursive embedding, Chomsky hierarchy parallels).
- [ ] **1.4c** Investigate scale-free networks in brain connectivity and power-law degree distributions — implications for the relationship graph within Fractal Recall.

---

## 2. AI Memory Systems — State of the Art

Survey every significant existing system to understand what has been tried, what works, and where the gaps are.

### 2.1 Classical & Foundational Systems

- [ ] **2.1a** Review Hierarchical Temporal Memory (HTM, Numenta) — biologically-inspired cortical columns, sequence learning, hierarchical layers, sparse distributed representations.
- [ ] **2.1b** Study Neural Turing Machines (Graves et al., 2014) and Differentiable Neural Computers — external memory with learned read/write operations.
- [ ] **2.1c** Survey Memory Networks (Weston et al., 2014) and End-to-End Memory Networks — multi-hop reasoning over memory slots.
- [ ] **2.1d** Review MERLIN (Memory, RL, and Inference Network, DeepMind) — episodic memory for reinforcement learning agents.

### 2.2 LLM-Native Memory Architectures

- [ ] **2.2a** Deep-dive into **MemGPT / Letta**: OS-inspired virtual context management, tiered memory (core ↔ archival ↔ recall), self-directed memory management via function calls.
  - Catalog its memory tier definitions and eviction heuristics.
  - Evaluate strengths and limitations for long-horizon tasks.
- [ ] **2.2b** Study **LongMem** — SideNet architecture that fuses a frozen backbone LLM with a long-term memory module, decoupling memory from the main model.
- [ ] **2.2c** Analyze **MemReasoner** (2025) — transformer with a separate latent memory module for iterative context reading and multi-hop reasoning.
- [ ] **2.2d** Review **M+** (builds on MemoryLLM) — co-trained retriever for dynamic information retrieval, extending retention from ~20K to 160K+ tokens.
- [ ] **2.2e** Study **SECOND ME** (arXiv) — LLM-based parameterization for structured knowledge organization, contextual reasoning, and adaptive retrieval.
- [ ] **2.2f** Survey **LLM4LLM** (UC Berkeley) — storing key memory points in a structured database for on-demand retrieval.

### 2.3 Hierarchical Memory Frameworks

- [ ] **2.3a** Analyze **H-MEM** — memory organized into Domain → Category → Memory Trace → Episode layers. How does route-based retrieval work?
- [ ] **2.3b** Study multi-level caching architectures (L1/L2/L3 analogy) from TowardsAI and similar sources — access-speed-based memory tiering.
- [ ] **2.3c** Review contextual tier models (Personal / Project / Task memory) seen in AI assistant architectures.
- [ ] **2.3d** Survey self-evolving memory systems that integrate reinforcement learning for memory management (EmergentMind papers).

### 2.4 RAG and Hierarchical RAG

- [ ] **2.4a** Document the standard RAG pipeline: chunking → embedding → indexing → retrieval → generation. Identify each stage's failure modes.
- [ ] **2.4b** Deep-dive into **Hierarchical RAG (H-RAG)**: coarse retrieval → fine-grained retrieval → context condensation. How does multi-level abstraction improve recall?
- [ ] **2.4c** Study **HiRAG** (ACL Anthology) — integrating hierarchical knowledge via graph structures to boost semantic indexing.
- [ ] **2.4d** Review **T-RAG** — hierarchical memory indexing for tabular data.
- [ ] **2.4e** Compare RAG against Fractal Recall's proposed approach: where does RAG fall short that a fractal structure could address?

---

## 3. Graph & Tree Data Structures Theory

Fractal Recall is fundamentally a hierarchical data structure. We need mastery of the underlying CS theory.

### 3.1 Tree Fundamentals

- [ ] **3.1a** Review rooted trees, arborescences (directed rooted trees), and DAGs — determine which best models the Fractal Recall hierarchy.
- [ ] **3.1b** Document n-ary trees vs. binary trees vs. B-trees: traversal complexity, insert/delete costs, and implications for memory operations.
- [ ] **3.1c** Study self-balancing trees (AVL, Red-Black, Splay) — should the fractal tree auto-balance? What are the trade-offs?
- [ ] **3.1d** Review trie data structures and radix trees — applicability for prefix-based namespace lookups within the hierarchy.

### 3.2 Graph Theory Essentials

- [ ] **3.2a** Survey scale-free networks and preferential attachment (Barabási–Albert model) — do fractal memory relationships follow power-law distributions?
- [ ] **3.2b** Study small-world networks (Watts–Strogatz) — implications for adding "shortcut" edges across the fractal hierarchy for faster traversal.
- [ ] **3.2c** Review community detection algorithms (Louvain, Leiden) — can we automatically discover clusters within a flat data set and build the hierarchy bottom-up?
- [ ] **3.2d** Analyze hierarchical graph decomposition techniques (tree decomposition, nested dissection).

### 3.3 Fractal-Specific Structures

- [ ] **3.3a** Define mathematical self-similarity formally: a structure S is fractal if subsets of S are isomorphic to S under scaling. Prove/disprove whether the proposed FractalNode tree satisfies this.
- [ ] **3.3b** Study the Sierpiński triangle, Cantor set, and Mandelbrot set as canonical fractal examples — extract structural invariants applicable to data.
- [ ] **3.3c** Review fractal dimension (Hausdorff, box-counting) — can we compute a "fractal dimension" of the memory graph as a health/complexity metric?
- [ ] **3.3d** Investigate fractal graph theory (plainenglish.io survey) — multi-scale organization and self-similar knowledge structures.
- [ ] **3.3e** Document how the Deep Learning analogy applies: earlier layers detect simple patterns, deeper layers detect complex ones (self-similar layer structure in CNNs).

---

## 4. Storage & Infrastructure Options

Determine the best persistence and indexing layer for a fractal memory system.

### 4.1 Vector Databases & Embedding Storage

- [ ] **4.1a** Compare major vector databases: **Chroma**, **Milvus**, **Pinecone**, **Weaviate**, **Qdrant**, **pgvector** — feature matrix (HNSW support, metadata filtering, hybrid search, managed vs. self-hosted, latency).
- [ ] **4.1b** Deep-dive into **HNSW** (Hierarchical Navigable Small World): layered graph structure, coarse-to-fine search, probabilistic layer assignment, recall/speed trade-offs.
- [ ] **4.1c** Evaluate whether HNSW's inherent hierarchy can be mapped directly to Fractal Recall's levels (Level 0–3).
- [ ] **4.1d** Study embedding models for text: OpenAI `text-embedding-3-small/large`, Sentence-Transformers (`all-MiniLM-L6-v2`, `e5-large`), Nomic Embed — dimensional trade-offs and cost.
- [ ] **4.1e** Investigate multi-vector representations (ColBERT, late interaction models) — could each fractal level use a differently-scoped embedding?

### 4.2 Knowledge Graphs & Graph Databases

- [ ] **4.2a** Deep-dive into **Neo4j**: Cypher query language, native graph storage, property graph model, APOC library for graph algorithms.
- [ ] **4.2b** Evaluate **Graphiti** (Zep) — real-time AI knowledge graph with entity/relationship extraction, deduplication, and hybrid search on Neo4j.
- [ ] **4.2c** Study Hierarchical Knowledge Graphs (HKGs) — tree-like or DAG structures for taxonomic classification, containment, and progression.
- [ ] **4.2d** Compare graph databases: Neo4j vs. ArangoDB vs. Amazon Neptune vs. TigerGraph — which best supports hierarchical + relational queries?
- [ ] **4.2e** Analyze the graph-vs.-vector trade-off: when do explicit relationships outperform semantic similarity, and vice versa? Propose a hybrid strategy.

### 4.3 Hybrid & Multi-Modal Storage

- [ ] **4.3a** Design a hybrid architecture: vector store for semantic retrieval + graph store for structural/relational queries. Define the interface boundary.
- [ ] **4.3b** Evaluate SQLite/DuckDB as a lightweight relational layer for metadata, lineage tracking, and configuration.
- [ ] **4.3c** Investigate how to store non-text modalities (images, audio, video) as fractal nodes — embeddings, CLIP, Whisper, multimodal transformers.
- [ ] **4.3d** Review serialization formats for fractal trees: JSON, MessagePack, Protocol Buffers, FlatBuffers — performance and schema evolution.

### 4.4 Python Libraries & Tooling

- [ ] **4.4a** Evaluate **NetworkX** for fractal tree representation: directed graphs, tree identification, traversal algorithms, visualization.
- [ ] **4.4b** Evaluate **igraph** — performance comparison with NetworkX for large graphs, tree-specific layouts.
- [ ] **4.4c** Review **anytree** — purpose-built tree library, node rendering, export formats.
- [ ] **4.4d** Study **Higra** — hierarchical graph analysis, component trees, hierarchical clustering.
- [ ] **4.4e** Assess **LangChain** and **LlamaIndex** integration points for RAG, memory modules, and agent tooling.
- [ ] **4.4f** Review **Pydantic** for data modeling and validation of fractal node schemas.

---

## 5. Core Design Theory for Fractal Recall

Synthesize research into concrete design principles.

### 5.1 The FractalNode — Formal Specification

- [ ] **5.1a** Define the canonical schema for a `FractalNode`: required fields, optional fields, type constraints, and invariants.
- [ ] **5.1b** Specify the "DNA" metaphor rigorously: what exactly does a node carry from its ancestry? Full parent chain? Compressed summary? Hash lineage?
- [ ] **5.1c** Design the metadata schema: timestamps (created, accessed, modified, consolidated), provenance (source, process, agent), confidence scores.
- [ ] **5.1d** Define relationship types: `parent-child`, `sibling`, `cross-reference`, `causal`, `temporal`, `semantic-similarity`. Establish a taxonomy.
- [ ] **5.1e** Determine immutability policy: are nodes append-only (event-sourced), mutable-in-place, or copy-on-write?

### 5.2 The Hierarchy — Level Design

- [ ] **5.2a** Formalize the Level 0–3 hierarchy from the README. Define the semantic meaning, abstraction scope, and expected cardinality at each level.
- [ ] **5.2b** Investigate whether the hierarchy should be fixed-depth or dynamic (nodes create sub-levels as needed, true fractal recursion).
- [ ] **5.2c** Design promotion and demotion rules: when does a Level 0 node get promoted to anchor a new Level 1 branch? What triggers cluster formation at Level 2?
- [ ] **5.2d** Define the "self-similarity invariant" formally: what structural properties must hold at every level?
- [ ] **5.2e** Model the hierarchy mathematically: fractal dimension, branching factor distribution, depth distribution, and expected query complexity.

### 5.3 Memory Operations — Algorithmic Design

- [ ] **5.3a** Design `add_memory`: parent selection algorithm (nearest semantic neighbor? user-specified? automatic clustering?), metadata auto-generation, relationship discovery.
- [ ] **5.3b** Design `retrieve_memory`: level-scoped retrieval, multi-hop traversal, hybrid vector+graph search, context assembly (how much ancestry context to include?).
- [ ] **5.3c** Design `update_memory`: versioning strategy, cascading updates to dependent nodes, relationship re-evaluation.
- [ ] **5.3d** Design `delete_memory`: orphan handling, cascade policies, soft-delete vs. hard-delete, garbage collection of relationship edges.
- [ ] **5.3e** Design `consolidate_memory`: the offline pass that merges, summarizes, re-links, and optimizes the tree — inspired by hippocampal replay (§1.2b).
- [ ] **5.3f** Design `introspect_memory`: self-analysis operations that identify gaps, redundancies, contradictions, and staleness in the memory structure.

### 5.4 Context Propagation

- [ ] **5.4a** Define the "context window" for any given node: how far up the ancestry chain does context propagate? All the way to root? Fixed depth? Adaptive?
- [ ] **5.4b** Design context compression: summarize ancestor context at each level to avoid linear growth. Evaluate abstractive vs. extractive summarization.
- [ ] **5.4c** Study how MemGPT's context compilation approach could apply: compiling the most relevant context from the fractal tree into the LLM's limited window.
- [ ] **5.4d** Define the context assembly algorithm for retrieval: given a query, how do we compose the returned context from nodes across multiple levels?

---

## 6. Integration with LLMs

Fractal Recall's value proposition depends heavily on LLM integration.

### 6.1 Embedding & Encoding

- [ ] **6.1a** Determine embedding strategy: embed the node data alone, data + metadata, data + ancestry context, or all of the above?
- [ ] **6.1b** Evaluate multi-granularity embeddings: different embedding models or dimensionalities for different hierarchy levels.
- [ ] **6.1c** Study incremental embedding updates: when a node's context changes due to tree restructuring, how do we efficiently update embeddings without full re-computation?

### 6.2 Agent Memory Interface

- [ ] **6.2a** Design the API surface for an LLM agent to interact with Fractal Recall: natural language queries, structured queries, CRUD operations.
- [ ] **6.2b** Study how MemGPT exposes memory management as tool calls — should Fractal Recall follow the same pattern?
- [ ] **6.2c** Evaluate LangChain's `Memory` abstractions and LlamaIndex's `ChatMemoryBuffer` — can Fractal Recall plug into these interfaces?
- [ ] **6.2d** Design the prompt engineering strategy: how is fractal context injected into the LLM prompt? System message? Few-shot examples? Structured blocks?

### 6.3 Advanced Reasoning

- [ ] **6.3a** Study multi-hop reasoning over graph structures — how does the LLM navigate the fractal tree to answer complex queries?
- [ ] **6.3b** Investigate chain-of-thought prompting with fractal context: can ancestry context improve step-by-step reasoning?
- [ ] **6.3c** Review ReAct (Reason + Act) and Reflexion patterns — how does persistent fractal memory enhance agent reflection loops?
- [ ] **6.3d** Study causal reasoning over temporal chains: using the fractal tree to trace cause-and-effect across time.

---

## 7. Evaluation, Benchmarking & Quality

Define how we will measure success.

### 7.1 Retrieval Quality Metrics

- [ ] **7.1a** Define Precision@K, Recall@K, MRR, and nDCG for fractal-structured retrieval — adapt standard IR metrics.
- [ ] **7.1b** Design a "context completeness" metric: does the retrieved context include sufficient ancestry information?
- [ ] **7.1c** Create a "hierarchy fidelity" metric: does the auto-constructed hierarchy match human-intuitive topic clustering?

### 7.2 Performance Benchmarks

- [ ] **7.2a** Define latency benchmarks: add_memory, retrieve_memory, consolidate_memory at 100, 1K, 10K, 100K, 1M nodes.
- [ ] **7.2b** Define memory footprint benchmarks: storage per node, index overhead, embedding storage.
- [ ] **7.2c** Compare against flat vector store baselines (plain Chroma, plain FAISS) on identical data sets.

### 7.3 Reasoning & Downstream Task Quality

- [ ] **7.3a** Design evaluation tasks: multi-turn conversation coherence, document QA with deep context, knowledge gap identification.
- [ ] **7.3b** Create a benchmark dataset: a corpus with known hierarchical structure that the system should reconstruct.
- [ ] **7.3c** Define A/B test framework: Fractal Recall vs. flat RAG vs. MemGPT on identical tasks.

---

## 8. Ethical, Safety & Governance Considerations

### 8.1 Data Privacy & Retention

- [ ] **8.1a** Define data retention policies: how long are memories kept? Right-to-deletion compliance (GDPR Article 17)?
- [ ] **8.1b** Study differential privacy techniques for memory systems — can we add noise at the fractal level?
- [ ] **8.1c** Define access control: who can read/write/delete at each hierarchy level?

### 8.2 Bias & Fairness

- [ ] **8.2a** Investigate how hierarchical organization could amplify or mitigate bias — do certain topics get systematically placed at lower levels?
- [ ] **8.2b** Design audit mechanisms for the fractal tree structure: distribution analysis, topic coverage heat maps.

### 8.3 Explainability

- [ ] **8.3a** Leverage the fractal hierarchy for explainable retrieval: the path from root to retrieved node is a built-in explanation chain.
- [ ] **8.3b** Design visualization tools for the fractal tree to support human oversight.

---

## 9. Related & Adjacent Projects

Survey existing open-source projects that overlap with Fractal Recall.

- [ ] **9.1** Catalog and compare: **MemGPT/Letta**, **LangChain Memory modules**, **LlamaIndex**, **Graphiti**, **Mem0**, **Zep**, **Motorhead**, **SuperMemory**.
- [ ] **9.2** Study **Obsidian** and **Roam Research** knowledge graph paradigms — user-facing hierarchical knowledge management.
- [ ] **9.3** Review the **"House of Fractal Gridding"** cognitive architecture framework — fractal principles applied to AI knowledge management.
- [ ] **9.4** Investigate **Numenta's HTM** codebase (nupic) for implementation patterns of hierarchical temporal structures.

---

## 10. Synthesis & Gap Analysis

### 10.1 Landscape Map

- [ ] **10.1a** Create a comparison matrix: Fractal Recall vs. every system surveyed, across dimensions (hierarchy depth, context propagation, persistence, self-improvement, multi-modality).
- [ ] **10.1b** Identify the unique value proposition — what does Fractal Recall do that nothing else does?

### 10.2 Open Research Questions

- [ ] **10.2a** List unresolved questions from each section that require experimentation or prototyping.
- [ ] **10.2b** Prioritize questions by impact × feasibility.

### 10.3 Recommended Reading List

- [ ] **10.3a** Compile an annotated bibliography of the 20–30 most important papers, blog posts, and codebases.
- [ ] **10.3b** Assign each source to the section(s) it informs.

---

> **Next Step**: For each `[ ]` item, we will produce a detailed summary with citations, diagrams where helpful, and explicit design implications for Fractal Recall. Once all items are marked `[x]`, we synthesize into a feature/version roadmap.
