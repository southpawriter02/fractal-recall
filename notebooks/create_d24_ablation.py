#!/usr/bin/env python3
"""
create_d24_ablation.py — Create D-24 Layer Ablation notebook from D-23 R4

Transforms D-23 Round 4 (D23_multi_layer_5.ipynb) into a D-24 ablation study
that tests 5 enrichment configurations:

  A: raw              — No enrichment (D-21 equivalent control)
  B: domain_entity    — Domain + Entity (~32 tokens)
  C: de_authority     — Domain + Entity + Authority (~42 tokens)
  D: de_section       — Domain + Entity + Section (~48 tokens)
  E: de_relationships — Domain + Entity + Relationships (~50 tokens)

Corpus and Temporal layers are dropped from all configs:
  - Corpus: constant string, zero discriminative value
  - Temporal: 0% population across 4 rounds

Usage:
    python3 create_d24_ablation.py
"""

import json
import os
import sys
from pathlib import Path

# ============================================================================
# PATHS
# ============================================================================

NOTEBOOK_PATH = Path("results/d23/round-4/D23_multi_layer_5.ipynb")
OUTPUT_DIR = Path("results/d24")
OUTPUT_PATH = OUTPUT_DIR / "D24_ablation.ipynb"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_notebook(path):
    with open(path) as f:
        return json.load(f)

def save_notebook(nb, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(nb, f, indent=1)

def make_markdown_cell(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + '\n' for line in source.strip().split('\n')[:-1]] + [source.strip().split('\n')[-1]]
    }

def make_code_cell(source):
    lines = source.strip().split('\n')
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + '\n' for line in lines[:-1]] + [lines[-1]]
    }


# ============================================================================
# CELL 0: HEADER MARKDOWN
# ============================================================================

CELL_0_SOURCE = r'''# D-24: Notebook 4 — Layer Ablation Study

> **Project:** FractalRecall — Hierarchical context-aware embedding retrieval
> **Question this notebook answers:** Which individual context layers contribute most to retrieval improvement?
> **Corpus:** Aethelgard worldbuilding (Markdown + YAML frontmatter)
> **Embedding model:** `nomic-embed-text-v1.5` via sentence-transformers
> **Vector DB:** ChromaDB (in-memory)
> **Metrics:** Precision@5, Recall@10, NDCG@10, MRR
> **Full context for AI assistants:** See `COLAB-SESSION-CONTEXT.md` in this directory

## What is FractalRecall?

FractalRecall tests the hypothesis that embedding retrieval improves when text chunks are enriched with **hierarchical structural context** before embedding. Each chunk carries up to 8 "context layers" prepended as natural language prefixes. The enriched text is embedded as a single vector.

## Notebook Sequence

| # | Notebook | Status |
|---|----------|--------|
| 1 | Baseline (standard RAG, no enrichment) | ✅ D-21 |
| 2 | Single-Layer Enrichment (document-level context only) | ✅ D-22 |
| 3 | Multi-Layer Enrichment (**core hypothesis test**) | ✅ D-23 (4 rounds) |
| 4 | **Layer Ablation (which layers matter most?)** | ✅ D-24 ← THIS NOTEBOOK |
| 5 | Embedding Strategy Comparison | 🔲 |
| 6 | Cross-Domain Validation | 🔲 |'''


# ============================================================================
# CELL 1: DESIGN RATIONALE MARKDOWN
# ============================================================================

CELL_1_SOURCE = r'''## D-24 Ablation Design

### Motivation

D-23 showed that **6-layer enrichment (~80 tokens) degrades retrieval breadth** (P@5, R@10)
compared to both D-21 (no enrichment) and D-22 (single-layer, ~24 tokens), while improving
first-result ranking (MRR). The hypothesis is that fewer, more targeted layers can retain
the MRR benefit without the content-dilution penalty.

### Ablation Configurations

| Config | Label | Layers | ~Prefix Tokens | Purpose |
|--------|-------|--------|----------------|---------|
| **A** | `raw` | None | 0 | Control (D-21 equivalent) |
| **B** | `domain_entity` | Domain + Entity | ~32 | Minimal enrichment |
| **C** | `de_authority` | Domain + Entity + Authority | ~42 | +canonical status |
| **D** | `de_section` | Domain + Entity + Section | ~48 | +document structure |
| **E** | `de_relationships` | Domain + Entity + Relationships | ~50 | +cross-references |

### Dropped Layers

- **Corpus**: Constant string identical for all chunks — zero discriminative value (6 tokens wasted)
- **Temporal**: 0% population across D-23 rounds 1-4 — corpus lacks temporal_markers frontmatter

### Chunking

All configs use D-21's exact chunking algorithm (ported in D-23 R4):
- Config A: `prefix_reserve=0` (matches D-21 geometry exactly)
- Configs B-E: `prefix_reserve=100` (same as D-23 R4)'''


# ============================================================================
# CELL 9: ABLATION-AWARE ENRICHMENT BUILDER
# ============================================================================

CELL_9_SOURCE = r'''#!/usr/bin/env python3
"""
D-24 Cell 09: Ablation-Aware Enrichment Builder

Replaces D-23's hardcoded 7-layer build_multi_layer_prefix() with a
config-driven build_ablation_prefix() that activates only the layers
specified by the current ablation configuration.

Key changes from D-23 Cell 09:
  1. ABLATION_CONFIGS dict defines 5 layer combinations
  2. build_ablation_prefix() accepts a config_name parameter
  3. Only builds layers listed in the active config
  4. Individual layer builder functions unchanged from D-23

Layer builders reused from D-23:
  - build_domain_layer(metadata)
  - build_entity_layer(metadata)
  - build_authority_layer(metadata)
  - build_relational_layer(metadata)
  - build_section_layer(section_heading)

Dropped builders:
  - build_corpus_layer() — constant, non-discriminative
  - build_temporal_layer() — 0% population
"""

# ============================================================================
# ABLATION CONFIGURATIONS
# ============================================================================

ABLATION_CONFIGS = {
    "raw":              [],
    "domain_entity":    ["Domain", "Entity"],
    "de_authority":     ["Domain", "Entity", "Authority"],
    "de_section":       ["Domain", "Entity", "Section"],
    "de_relationships": ["Domain", "Entity", "Relationships"],
}

ABLATION_CONFIG_ORDER = ["raw", "domain_entity", "de_authority", "de_section", "de_relationships"]

# Prefix reserve per config: raw gets 0 (match D-21), others get 100
ABLATION_PREFIX_RESERVE = {
    "raw": 0,
    "domain_entity": 100,
    "de_authority": 100,
    "de_section": 100,
    "de_relationships": 100,
}

print("=" * 70)
print("D-24 ABLATION CONFIGURATIONS")
print("=" * 70)
for cfg in ABLATION_CONFIG_ORDER:
    layers = ABLATION_CONFIGS[cfg]
    reserve = ABLATION_PREFIX_RESERVE[cfg]
    layer_str = " + ".join(layers) if layers else "(none)"
    print(f"  {cfg:20s}: {layer_str:45s} reserve={reserve}")
print("=" * 70)

# ============================================================================
# DOMAIN CATEGORY MAPPING (from D-23)
# ============================================================================

DOMAIN_CATEGORY_MAP: Dict[str, str] = {
    "faction":    "organizations",
    "character":  "individuals",
    "location":   "geography",
    "event":      "history",
    "item":       "artifacts",
    "concept":    "metaphysics",
    "spell":      "magic system",
    "creature":   "bestiary",
    "region":     "geography",
    "timeline":   "chronology",
}


# ============================================================================
# LAYER BUILDER FUNCTIONS (unchanged from D-23)
# ============================================================================

def build_domain_layer(metadata: Dict[str, Any]) -> str:
    doc_type = str(metadata.get("type", "unknown")).lower().strip()
    category = DOMAIN_CATEGORY_MAP.get(doc_type, "general")
    return f"Domain: This content is from a {doc_type} document in the {category} category."


def build_entity_layer(metadata: Dict[str, Any]) -> Optional[str]:
    name = str(metadata.get("name", "")).strip()
    if not name or name.lower() == "unknown":
        return None
    return f"Entity: This content describes {name}."


def build_authority_layer(metadata: Dict[str, Any]) -> str:
    canon = metadata.get("canon", "")
    if isinstance(canon, bool):
        canon_str = "true" if canon else "false"
    else:
        canon_str = str(canon).lower().strip()

    if canon_str in ("true", "yes", "canonical"):
        authority_text = "canonical and authoritative"
    elif canon_str == "apocryphal":
        authority_text = "apocryphal (non-canonical, speculative)"
    elif canon_str == "deprecated":
        authority_text = "deprecated and superseded"
    else:
        authority_text = "draft (not yet canonical)"

    return f"Authority: This content is {authority_text}."


def build_relational_layer(metadata: Dict[str, Any]) -> Optional[str]:
    rel_parts = []

    # Standard relationships
    relationships = metadata.get("relationships", [])
    if isinstance(relationships, list):
        for rel in relationships:
            if isinstance(rel, dict):
                target = rel.get("target", "")
                if isinstance(target, str):
                    target_name = target.split("/")[-1].replace(".md", "").replace("-", " ").title()
                else:
                    target_name = str(target)
                rel_type = str(rel.get("type", "related to")).replace("_", " ")
                rel_parts.append(f"{rel_type} {target_name}")

    # Cross-references (added in D-23 R3)
    cross_refs = metadata.get("cross_references", [])
    if isinstance(cross_refs, list):
        for ref in cross_refs:
            if isinstance(ref, str):
                ref_name = ref.split("/")[-1].replace(".md", "").replace("-", " ").title()
                rel_parts.append(f"related to {ref_name}")

    # Factions
    factions = metadata.get("factions", [])
    if isinstance(factions, list):
        for faction in factions:
            if isinstance(faction, str):
                rel_parts.append(f"associated with {faction}")

    # Locations
    location = metadata.get("location", metadata.get("region", ""))
    if isinstance(location, str) and location.strip():
        rel_parts.append(f"located in {location.strip()}")
    elif isinstance(location, list):
        for loc in location:
            if isinstance(loc, str) and loc.strip():
                rel_parts.append(f"located in {loc.strip()}")

    if not rel_parts:
        return None

    return f"Relationships: {'; '.join(rel_parts)}."


def build_section_layer(section_heading: Optional[str]) -> Optional[str]:
    if not section_heading or not section_heading.strip():
        return None
    heading_clean = section_heading.strip().lstrip("#").strip()
    if not heading_clean:
        return None
    return f"Section: This content is from the {heading_clean} section."


# ============================================================================
# ABLATION PREFIX BUILDER (replaces build_multi_layer_prefix)
# ============================================================================

# Map layer names to builder functions
LAYER_BUILDER_MAP = {
    "Domain":        lambda meta, _: build_domain_layer(meta),
    "Entity":        lambda meta, _: build_entity_layer(meta),
    "Authority":     lambda meta, _: build_authority_layer(meta),
    "Relationships": lambda meta, _: build_relational_layer(meta),
    "Section":       lambda _, sh: build_section_layer(sh),
}


def build_ablation_prefix(
    config_name: str,
    metadata: Dict[str, Any],
    section_heading: Optional[str] = None,
) -> Tuple[str, Dict[str, int]]:
    """Build a prefix using only the layers active in the given config.

    Args:
        config_name: Key into ABLATION_CONFIGS (e.g., "domain_entity")
        metadata: Normalized document metadata dict
        section_heading: Section heading for the Section layer

    Returns:
        Tuple of (prefix_text, layer_token_audit)
    """
    active_layers = ABLATION_CONFIGS[config_name]
    layer_token_audit: Dict[str, int] = {}
    prefix_parts: List[str] = []

    for layer_name in active_layers:
        builder_fn = LAYER_BUILDER_MAP[layer_name]
        layer_text = builder_fn(metadata, section_heading)
        if layer_text is not None:
            prefix_parts.append(layer_text)
            layer_token_audit[layer_name] = estimate_tokens(layer_text)

    prefix_text = "\n\n".join(prefix_parts)
    return prefix_text, layer_token_audit


def build_ablation_chunk(
    config_name: str,
    chunk: Chunk,
) -> Tuple[Chunk, Dict[str, int]]:
    """Build an enriched chunk using the ablation config.

    Args:
        config_name: Key into ABLATION_CONFIGS
        chunk: Original Chunk object (raw text)

    Returns:
        Tuple of (enriched_chunk, layer_token_audit)
    """
    prefix_text, layer_audit = build_ablation_prefix(
        config_name, chunk.metadata, chunk.section_heading
    )

    if prefix_text:
        enriched_text = prefix_text + "\n\n" + chunk.text
    else:
        enriched_text = chunk.text

    enriched_chunk = Chunk(
        chunk_id=chunk.chunk_id,
        doc_filename=chunk.doc_filename,
        section_heading=chunk.section_heading,
        text=enriched_text,
        token_count_approx=estimate_tokens(enriched_text),
        metadata=chunk.metadata.copy() if hasattr(chunk.metadata, 'copy') else dict(chunk.metadata),
    )

    return enriched_chunk, layer_audit


print("\n✓ Ablation enrichment builder ready")
print(f"  Configs: {len(ABLATION_CONFIGS)}")
print(f"  Layer builders: {list(LAYER_BUILDER_MAP.keys())}")
'''


# ============================================================================
# CELL 10: MULTI-CONFIG CHUNK + ENRICH + AUDIT
# ============================================================================

CELL_10_SOURCE = r'''#!/usr/bin/env python3
"""
D-24 Cell 10: Multi-Config Chunk, Enrich & Audit

Runs the chunk → enrich → audit pipeline once per ablation configuration.
Each config gets its own enriched_chunks list and audit data.

Key difference from D-23 Cell 10:
  - Outer loop over ABLATION_CONFIG_ORDER
  - Config A (raw) uses prefix_reserve=0 for D-21-equivalent chunking
  - Stores results in ablation_results dict keyed by config name

Outputs:
  - ablation_results: Dict[str, Dict] with per-config data:
      - "enriched_chunks": List[Chunk]
      - "layer_audits": List[Dict]
      - "tokens_before": List[int]
      - "tokens_after": List[int]
      - "overflow_count": int
"""

ablation_results: Dict[str, Dict] = {}

print("=" * 80)
print("D-24 MULTI-CONFIG CHUNK, ENRICH & AUDIT")
print("=" * 80)

for config_name in ABLATION_CONFIG_ORDER:
    prefix_reserve = ABLATION_PREFIX_RESERVE[config_name]
    active_layers = ABLATION_CONFIGS[config_name]
    layer_str = " + ".join(active_layers) if active_layers else "(none — raw)"

    print(f"\n{'─' * 70}")
    print(f"CONFIG: {config_name}")
    print(f"  Layers: {layer_str}")
    print(f"  Prefix reserve: {prefix_reserve} tokens")
    print(f"{'─' * 70}")

    enriched_chunks: List[Chunk] = []
    layer_audits: List[Dict[str, Any]] = []
    tokens_before: List[int] = []
    tokens_after: List[int] = []
    overflow_count = 0

    for doc in tqdm(corpus, desc=f"  {config_name}"):
        # Chunk with config-specific prefix reserve
        doc_chunks = chunk_document(doc, MODEL_CONFIG.max_chunk_tokens, prefix_reserve=prefix_reserve)

        for chunk in doc_chunks:
            tokens_before.append(chunk.token_count_approx)

            enriched_chunk, layer_audit = build_ablation_chunk(config_name, chunk)
            tokens_after.append(enriched_chunk.token_count_approx)

            if enriched_chunk.token_count_approx > MODEL_CONFIG.max_chunk_tokens:
                overflow_count += 1

            enriched_chunks.append(enriched_chunk)

            audit_record = {
                "config": config_name,
                "chunk_id": chunk.chunk_id,
                "doc_filename": chunk.doc_filename,
                "section_heading": chunk.section_heading or "(none)",
                "tokens_raw": chunk.token_count_approx,
                "tokens_enriched": enriched_chunk.token_count_approx,
                **layer_audit,
            }
            layer_audits.append(audit_record)

    # Store results
    ablation_results[config_name] = {
        "enriched_chunks": enriched_chunks,
        "layer_audits": layer_audits,
        "tokens_before": tokens_before,
        "tokens_after": tokens_after,
        "overflow_count": overflow_count,
    }

    # Summary for this config
    arr_before = np.array(tokens_before)
    arr_after = np.array(tokens_after)
    arr_overhead = arr_after - arr_before

    print(f"\n  ✓ {len(enriched_chunks)} chunks")
    print(f"  Overflow: {overflow_count}/{len(enriched_chunks)} ({100*overflow_count/max(len(enriched_chunks),1):.1f}%)")
    print(f"  Mean tokens: {arr_before.mean():.0f} raw → {arr_after.mean():.0f} enriched (overhead: {arr_overhead.mean():.0f})")

# ============================================================================
# CROSS-CONFIG SUMMARY
# ============================================================================

print(f"\n{'=' * 80}")
print("CROSS-CONFIG SUMMARY")
print(f"{'=' * 80}")
print(f"\n  {'Config':20s} {'Chunks':>7s} {'Overflow':>10s} {'Mean Raw':>10s} {'Mean Enr':>10s} {'Overhead':>10s}")
print(f"  {'─'*20} {'─'*7} {'─'*10} {'─'*10} {'─'*10} {'─'*10}")

for cfg in ABLATION_CONFIG_ORDER:
    r = ablation_results[cfg]
    n = len(r["enriched_chunks"])
    ovf = r["overflow_count"]
    mean_raw = np.mean(r["tokens_before"])
    mean_enr = np.mean(r["tokens_after"])
    overhead = mean_enr - mean_raw
    print(f"  {cfg:20s} {n:>7d} {ovf:>4d}/{n:<5d} {mean_raw:>10.0f} {mean_enr:>10.0f} {overhead:>+10.0f}")

# Export unified token audit
all_audits = []
for cfg in ABLATION_CONFIG_ORDER:
    all_audits.extend(ablation_results[cfg]["layer_audits"])

audit_df = pd.DataFrame(all_audits)
audit_csv_path = OUTPUT_DIR / "d24_layer_token_audits.csv"
audit_df.to_csv(audit_csv_path, index=False)
print(f"\n✓ Token audit exported: {audit_csv_path} ({len(audit_df)} rows)")
'''


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("D-24 Ablation Notebook Creator")
    print("=" * 70)

    # Step 1: Load source notebook
    if not NOTEBOOK_PATH.exists():
        print(f"\n✗ Source notebook not found: {NOTEBOOK_PATH}")
        sys.exit(1)

    nb = load_notebook(NOTEBOOK_PATH)
    print(f"\n[1] Loaded: {NOTEBOOK_PATH}")
    print(f"    Cells: {len(nb['cells'])}")

    # Step 2: Replace Cell 0 (header)
    nb['cells'][0] = make_markdown_cell(CELL_0_SOURCE)
    print(f"\n[2] Replaced Cell 0 (header markdown)")

    # Step 3: Replace Cell 1 (design rationale)
    nb['cells'][1] = make_markdown_cell(CELL_1_SOURCE)
    print(f"\n[3] Replaced Cell 1 (design rationale)")

    # Step 4: Replace Cell 9 (enrichment builder)
    nb['cells'][9] = make_code_cell(CELL_9_SOURCE)
    print(f"\n[4] Replaced Cell 9 (ablation enrichment builder)")

    # Step 5: Replace Cell 10 (chunk + enrich + audit)
    nb['cells'][10] = make_code_cell(CELL_10_SOURCE)
    print(f"\n[5] Replaced Cell 10 (multi-config pipeline)")

    # Step 6: Clear all cell outputs
    cleared = 0
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            if cell.get('outputs'):
                cell['outputs'] = []
                cleared += 1
            cell['execution_count'] = None
    print(f"\n[6] Cleared outputs from {cleared} cells")

    # Step 7: Save
    save_notebook(nb, OUTPUT_PATH)
    size = os.path.getsize(OUTPUT_PATH)
    print(f"\n[7] Saved: {OUTPUT_PATH} ({size:,} bytes)")

    # Step 8: Verification
    print(f"\n{'=' * 70}")
    print("VERIFICATION")
    print(f"{'=' * 70}")

    nb_verify = load_notebook(OUTPUT_PATH)

    checks = [
        (len(nb_verify['cells']) == len(nb['cells']), f"Cell count matches ({len(nb_verify['cells'])})"),
        ("Layer Ablation" in ''.join(nb_verify['cells'][0]['source']), "Cell 0 has D-24 header"),
        ("Ablation Design" in ''.join(nb_verify['cells'][1]['source']), "Cell 1 has ablation design"),
        ("ABLATION_CONFIGS" in ''.join(nb_verify['cells'][9]['source']), "Cell 9 has ablation configs"),
        ("build_ablation_prefix" in ''.join(nb_verify['cells'][9]['source']), "Cell 9 has ablation prefix builder"),
        ("build_ablation_chunk" in ''.join(nb_verify['cells'][9]['source']), "Cell 9 has ablation chunk builder"),
        ("ABLATION_CONFIG_ORDER" in ''.join(nb_verify['cells'][10]['source']), "Cell 10 loops over configs"),
        ("ablation_results" in ''.join(nb_verify['cells'][10]['source']), "Cell 10 stores per-config results"),
        ("d24_layer_token_audits" in ''.join(nb_verify['cells'][10]['source']), "Cell 10 exports d24 audits"),
        ("raw" in ''.join(nb_verify['cells'][9]['source']), "Config A (raw) present"),
        ("domain_entity" in ''.join(nb_verify['cells'][9]['source']), "Config B (domain_entity) present"),
        ("de_authority" in ''.join(nb_verify['cells'][9]['source']), "Config C (de_authority) present"),
        ("de_section" in ''.join(nb_verify['cells'][9]['source']), "Config D (de_section) present"),
        ("de_relationships" in ''.join(nb_verify['cells'][9]['source']), "Config E (de_relationships) present"),
    ]

    passed = 0
    for ok, label in checks:
        status = "✓" if ok else "✗"
        print(f"  {status} {label}")
        if ok:
            passed += 1

    print(f"\n  Result: {passed}/{len(checks)} checks passed")

    if passed == len(checks):
        print(f"\n✓ ALL CHECKS PASSED")
        print(f"\n  Next steps:")
        print(f"    1. Cells 11-21 still need patching for multi-config pipeline")
        print(f"    2. Run create_d24_ablation_part2.py for remaining cells")
        print(f"    3. Upload to Google Colab (A100, High-RAM)")
    else:
        print(f"\n✗ {len(checks) - passed} checks FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
