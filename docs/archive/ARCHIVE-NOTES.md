# Archive Notes

**Archived:** 2026-02-10
**Reason:** Content pivot — FractalRecall's scope has narrowed from a general-purpose AI memory architecture to a focused .NET class library for hierarchical context-aware embedding retrieval.

---

## What's In Here

### `research-plan.md`

An exhaustive research plan (~280 lines) spanning ten major domains: cognitive science foundations (human memory architecture, memory consolidation, predictive coding, fractal properties in biology), AI memory systems survey (MemGPT, Neural Turing Machines, Memory Networks, hierarchical RAG), graph/tree data structure theory, storage infrastructure evaluation, core design theory, LLM integration, evaluation benchmarks, ethics, related projects, and synthesis. None of the ~100+ checklist items were completed.

This plan was written when FractalRecall was conceptualized as a comprehensive AI memory system inspired by neuroscience. The current design draws its technical substance from RAG/embedding literature instead (Anthropic's Contextual Retrieval, GraphRAG, RAPTOR, Late Chunking).

### `scope/1.1-human-memory-architecture.md`

A detailed scope breakdown (~270 lines) for the first sub-section of the research plan, covering four cognitive science topics:

- **1.1a** — Atkinson-Shiffrin multi-store model (sensory → STM → LTM tier mapping)
- **1.1b** — Baddeley's Working Memory model (central executive, phonological loop, visuospatial sketchpad, episodic buffer)
- **1.1c** — Long-term memory subtypes (episodic, semantic, procedural encoding schemas)
- **1.1d** — Tulving's encoding specificity principle (context metadata design rules)

Each sub-part includes objectives, scope boundaries, limitations, deliverable specifications, acceptance criteria, research approach tables, and work estimates. Total estimated effort: 16.5-19 hours.

---

## Why It Was Archived (Not Deleted)

These documents represent genuine intellectual groundwork that influenced the current design. Five specific concepts survived the pivot and are documented in `Chronicle-FractalRecall-Master-Strategy.md` §4.3:

1. **The DNA Metaphor** — every chunk carries its full ancestry context
2. **Encoding Specificity** — retrieval cues must match encoding context
3. **Fractal Self-Similarity** — meaningful structure at every level of granularity
4. **Hierarchical Memory Tiers** — the origin of context layer hierarchy positions
5. **Context Propagation** — how far up the ancestry chain context reaches

The research plan also contains useful survey content (§2: AI Memory Systems, §4: Storage Infrastructure) that may be valuable background reading for future contributors.

---

## Current Authoritative Documents

For the current FractalRecall design, see:

- `../fractalrecall-conceptual-architectural-design.md` — Full technical specification
- `../../Chronicle-FractalRecall-Design-Proposal.md` — Unified design proposal (both projects)
- `../../Chronicle-FractalRecall-Master-Strategy.md` — Execution strategy and document manifest
