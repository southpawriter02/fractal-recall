#!/usr/bin/env python3
"""
D-23 Round 3 Fix Script
========================

Fixes three critical issues identified in D-23 Round 2:

1. NDCG BUG — NDCG values exceed 1.0 (up to 2.79) because the .split("#")[0] 
   fix maps multiple chunks to the same document ID, causing DCG to accumulate 
   duplicate relevance gains while IDCG only counts unique documents.
   FIX: Deduplicate retrieved IDs before NDCG computation.

2. MISSING LAYERS — Temporal, Relational, and Chunk Sequence layers are 
   unpopulated (return None for all docs) because FIELD_MAP uses wrong keys:
   - 'era' is mapped but corpus uses 'temporal_markers'
   - 'related_entities' is mapped but corpus uses 'cross_references',
     'factions_mentioned', 'locations_mentioned'
   FIX: Add the actual corpus field names to FIELD_MAP and update the 
   Temporal layer builder to handle temporal_markers format.

3. CONFOUNDING VARIABLES — D-23 changed chunk size (1024→600) and overlap 
   (150→50) simultaneously with enrichment layers, making it impossible to 
   isolate the enrichment effect.
   FIX: Match D-21/D-22 parameters (max_chunk_tokens=1024, overlap=150, 
   prefix_reserve=100) for a controlled comparison.

Usage:
    python3 fix_d23_round3.py

This modifies D23-multi-layer.ipynb in place. Back up before running.
"""

import json
import sys
import os
import copy
from datetime import datetime

NOTEBOOK_PATH = "results/d23/round-2/D23_multi_layer_3.ipynb"

def load_notebook(path):
    """Load notebook JSON."""
    with open(path, 'r') as f:
        return json.load(f)

def save_notebook(nb, path):
    """Save notebook JSON."""
    with open(path, 'w') as f:
        json.dump(nb, f, indent=2)
        f.write('\n')

def get_cell_source(cell):
    """Get cell source as a single string."""
    return ''.join(cell['source'])

def set_cell_source(cell, source_str):
    """Set cell source from a single string, split into lines."""
    lines = source_str.split('\n')
    new_source = []
    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            new_source.append(line + '\n')
        else:
            new_source.append(line)
    cell['source'] = new_source
    # Clear outputs since we're modifying code
    cell['outputs'] = []
    cell['execution_count'] = None

def apply_replacement(source, old, new, description):
    """Apply a string replacement with validation."""
    if old not in source:
        print(f"  WARNING: Could not find target for: {description}")
        print(f"    Looking for: {repr(old[:100])}")
        return source, False
    count = source.count(old)
    if count > 1:
        print(f"  WARNING: Found {count} occurrences for: {description} (replacing first)")
        source = source.replace(old, new, 1)
    else:
        source = source.replace(old, new)
    print(f"  APPLIED: {description}")
    return source, True


def fix_ndcg_bug(nb):
    """
    FIX 1: NDCG computation bug
    
    Root cause: After the .split("#")[0] fix, multiple chunks from the same 
    document all map to the same filename. In ndcg_at_k():
    - DCG accumulates relevance gains for EVERY chunk (including duplicates)  
    - IDCG only uses len(relevance_scores) items (unique documents)
    - When 7 chunks from doc1 each get rel=2, DCG far exceeds IDCG
    
    Fix: Deduplicate retrieved IDs before computing DCG. Only the highest-ranked 
    chunk from each document contributes to the score.
    """
    print("\n" + "=" * 70)
    print("FIX 1: NDCG Computation Bug (values exceeding 1.0)")
    print("=" * 70)
    
    cell = nb['cells'][13]  # Cell 14: Metric Computation Functions
    source = get_cell_source(cell)
    
    # Verify this is the right cell
    if 'def ndcg_at_k(' not in source:
        print("  ERROR: Cell 13 doesn't contain ndcg_at_k function!")
        return False
    
    # Replace the ndcg_at_k function
    old_ndcg = '''def ndcg_at_k(
    retrieved_ids: List[str],
    relevance_scores: Dict[str, int],
    k: int = K_NDCG,
) -> float:
    """Compute NDCG@K (Normalized Discounted Cumulative Gain).

    Formula:
      DCG@K  = Σ(i=1..K) rel(i) / log2(i + 1)
      IDCG@K = DCG of ideal ranking (sorted by relevance descending)
      NDCG@K = DCG@K / IDCG@K

    Uses graded relevance scores (1=marginal, 2=relevant, 3=highly relevant).

    Args:
        retrieved_ids: Ordered list of retrieved chunk IDs
        relevance_scores: Dict mapping chunk_id → relevance grade
        k: Cutoff rank (default K_NDCG=10)

    Returns:
        NDCG@K in [0.0, 1.0]. Returns 0.0 if no relevant documents exist.

    Example:
        >>> ndcg_at_k(["A","B","C"], {"A": 3, "C": 1}, k=3)
        # DCG = 3/log2(2) + 0/log2(3) + 1/log2(4) = 3.0 + 0 + 0.5 = 3.5
        # IDCG = 3/log2(2) + 1/log2(3) = 3.0 + 0.63 = 3.63
        # NDCG = 3.5 / 3.63 ≈ 0.964
    """
    if not relevance_scores:
        return 0.0

    # Compute DCG
    top_k = retrieved_ids[:k]
    dcg = 0.0
    for i, chunk_id in enumerate(top_k):
        rel = relevance_scores.get(chunk_id, 0)
        dcg += rel / np.log2(i + 2)  # i+2 because 0-indexed

    # Compute ideal DCG (IDCG)
    ideal_rels = sorted(relevance_scores.values(), reverse=True)[:k]
    idcg = 0.0
    for i, rel in enumerate(ideal_rels):
        idcg += rel / np.log2(i + 2)

    if idcg == 0:
        return 0.0

    return dcg / idcg'''

    new_ndcg = '''def ndcg_at_k(
    retrieved_ids: List[str],
    relevance_scores: Dict[str, int],
    k: int = K_NDCG,
) -> float:
    """Compute NDCG@K (Normalized Discounted Cumulative Gain).

    Formula:
      DCG@K  = Σ(i=1..K) rel(i) / log2(i + 1)
      IDCG@K = DCG of ideal ranking (sorted by relevance descending)
      NDCG@K = DCG@K / IDCG@K

    Uses graded relevance scores (1=marginal, 2=relevant, 3=highly relevant).

    IMPORTANT: Retrieved IDs are deduplicated before scoring. In chunk-level
    retrieval with document-level relevance, multiple chunks from the same
    document map to the same ID after .split("#")[0]. Without dedup, DCG
    accumulates gains for every duplicate while IDCG only counts unique docs,
    producing NDCG > 1.0 (mathematically impossible).
    [FIX: Round 3 — dedup retrieved IDs before DCG computation]

    Args:
        retrieved_ids: Ordered list of retrieved chunk/document IDs
        relevance_scores: Dict mapping doc_id → relevance grade
        k: Cutoff rank (default K_NDCG=10)

    Returns:
        NDCG@K in [0.0, 1.0]. Returns 0.0 if no relevant documents exist.

    Example:
        >>> ndcg_at_k(["A","B","C"], {"A": 3, "C": 1}, k=3)
        # DCG = 3/log2(2) + 0/log2(3) + 1/log2(4) = 3.0 + 0 + 0.5 = 3.5
        # IDCG = 3/log2(2) + 1/log2(3) = 3.0 + 0.63 = 3.63
        # NDCG = 3.5 / 3.63 ≈ 0.964
    """
    if not relevance_scores:
        return 0.0

    # Deduplicate: only keep first occurrence of each document ID.
    # This prevents counting the same document multiple times when
    # multiple chunks from one doc appear in the top-k results.
    seen = set()
    deduped = []
    for rid in retrieved_ids[:k]:
        if rid not in seen:
            seen.add(rid)
            deduped.append(rid)

    # Compute DCG on deduplicated list
    dcg = 0.0
    for i, chunk_id in enumerate(deduped):
        rel = relevance_scores.get(chunk_id, 0)
        dcg += rel / np.log2(i + 2)  # i+2 because 0-indexed

    # Compute ideal DCG (IDCG)
    ideal_rels = sorted(relevance_scores.values(), reverse=True)[:k]
    idcg = 0.0
    for i, rel in enumerate(ideal_rels):
        idcg += rel / np.log2(i + 2)

    if idcg == 0:
        return 0.0

    return dcg / idcg'''

    source, ok = apply_replacement(source, old_ndcg, new_ndcg, 
                                    "ndcg_at_k: deduplicate retrieved IDs before DCG")
    if not ok:
        return False
    
    set_cell_source(cell, source)
    return True


def fix_missing_layers(nb):
    """
    FIX 2: Missing Temporal, Relational, and Chunk Sequence layers
    
    Root cause: The FIELD_MAP in Cell 5 maps:
      - 'era' ← ["era", "age", "time_period", ...] 
        BUT the corpus uses 'temporal_markers' (not listed!)
      - 'related_entities' ← ["related_entities", "relationships", ...]
        BUT the corpus uses 'cross_references', 'factions_mentioned', 
        'locations_mentioned' (not listed!)
    
    Temporal layer builder expects metadata['era'] → always None
    Relational layer builder expects metadata['related_entities'] → always None
    
    Fix Part A: Add corpus field names to FIELD_MAP
    Fix Part B: Update temporal layer builder to handle 'temporal_markers' 
                format (list of strings like "Year 783 PG")
    Fix Part C: Update relational layer builder to also use cross_references
                and factions/locations mentioned
    """
    print("\n" + "=" * 70)
    print("FIX 2: Missing Enrichment Layers (Temporal, Relational)")
    print("=" * 70)
    
    # ── Part A: Fix FIELD_MAP in Cell 4 ──
    cell4 = nb['cells'][4]
    source4 = get_cell_source(cell4)
    
    if 'FIELD_MAP' not in source4:
        print("  ERROR: Cell 4 doesn't contain FIELD_MAP!")
        return False
    
    # Add 'temporal_markers' to the era field mapping
    old_era_map = '"era":               ["era", "age", "time_period", "historical_era", "eras"],'
    new_era_map = '"era":               ["era", "age", "time_period", "historical_era", "eras", "temporal_markers"],'
    
    source4, ok1 = apply_replacement(source4, old_era_map, new_era_map,
                                      "FIELD_MAP: add 'temporal_markers' to era mapping")
    
    # Add cross_references and faction/location mentions to related_entities mapping
    old_rel_map = '"related_entities":  ["related_entities", "relationships", "relations", "links", "see_also"],'
    new_rel_map = '"related_entities":  ["related_entities", "relationships", "relations", "links", "see_also", "cross_references"],'
    
    source4, ok2 = apply_replacement(source4, old_rel_map, new_rel_map,
                                      "FIELD_MAP: add 'cross_references' to related_entities mapping")
    
    if ok1 or ok2:
        set_cell_source(cell4, source4)
    
    # ── Part B: Update temporal layer builder in Cell 8 ──
    cell8 = nb['cells'][8]
    source8 = get_cell_source(cell8)
    
    if 'def build_temporal_layer' not in source8:
        print("  ERROR: Cell 8 doesn't contain build_temporal_layer!")
        return False

    # Replace the temporal layer builder to handle temporal_markers format
    old_temporal = '''def build_temporal_layer(metadata: Dict[str, Any]) -> Optional[str]:
    """Build the Temporal layer (Layer 5).

    Returns None if no era data is available, causing this layer to be omitted.
    Joins multiple eras with " and ".

    Args:
        metadata: Normalized metadata with 'era' field (list of strings or single string).

    Returns:
        Optional[str]: "Temporal: The events described span the {era_text}." or None.

    Examples:
        >>> build_temporal_layer({"era": ["Third Age", "Fourth Age"]})
        'Temporal: The events described span the Third Age and Fourth Age.'

        >>> build_temporal_layer({})
        None
    """
    eras = metadata.get("era", [])

    # Handle single string
    if isinstance(eras, str):
        eras = [eras] if eras.strip() else []

    # Filter empty values
    eras_clean = [str(e).strip() for e in eras if e and str(e).strip()]

    if not eras_clean:
        return None

    era_text = " and ".join(eras_clean)
    return f"Temporal: The events described span the {era_text}."'''

    new_temporal = '''def build_temporal_layer(metadata: Dict[str, Any]) -> Optional[str]:
    """Build the Temporal layer (Layer 5).

    Returns None if no temporal data is available, causing this layer to be omitted.
    Handles both 'era' format (e.g., ["Third Age"]) and 'temporal_markers' format
    (e.g., ["Year 783 PG", "Years 0-122 PG"]) from the Aethelgard corpus.
    [FIX: Round 3 — handle temporal_markers from corpus YAML frontmatter]

    Args:
        metadata: Normalized metadata with 'era' field (list of strings or single string).
            The 'era' key may contain temporal_markers values after FIELD_MAP normalization.

    Returns:
        Optional[str]: Temporal context sentence or None.

    Examples:
        >>> build_temporal_layer({"era": ["Third Age", "Fourth Age"]})
        'Temporal: The events described span the Third Age and Fourth Age.'

        >>> build_temporal_layer({"era": ["Year 783 PG", "Years 0-122 PG"]})
        'Temporal: Events reference Year 783 PG and Years 0-122 PG.'

        >>> build_temporal_layer({})
        None
    """
    eras = metadata.get("era", [])

    # Handle single string
    if isinstance(eras, str):
        eras = [eras] if eras.strip() else []

    # Filter empty values
    eras_clean = [str(e).strip() for e in eras if e and str(e).strip()]

    if not eras_clean:
        return None

    era_text = " and ".join(eras_clean)

    # Detect temporal_markers format (contains "Year" or "PG")
    is_marker_format = any("Year" in e or "PG" in e for e in eras_clean)
    if is_marker_format:
        return f"Temporal: Events reference {era_text}."
    else:
        return f"Temporal: The events described span the {era_text}."'''

    source8, ok3 = apply_replacement(source8, old_temporal, new_temporal,
                                      "build_temporal_layer: handle temporal_markers format")
    
    # ── Part C: Update relational layer builder to handle cross_references format ──
    # cross_references are simple string lists like ["Silent Folk", "Echo-Mothers"]
    # not dict/tuple format. The current builder expects dicts with 'target' and 'type'.
    
    old_relational = '''def build_relational_layer(metadata: Dict[str, Any]) -> Optional[str]:
    """Build the Relational layer (Layer 6).

    Parses the relationships list from metadata. Each relationship has a
    target (file path) and type (relationship kind). Target names are extracted
    from file paths (e.g., 'characters/elena-voss.md' → 'Elena Voss').
    Relationship types are humanized (underscores → spaces).

    Returns None if no relationships are present.

    Args:
        metadata: Normalized metadata with 'related_entities' field.
            Expected format: list of dicts with 'target' and 'type' keys,
            or list of tuples (type, target).

    Returns:
        Optional[str]: "Relationships: {rel_text}." or None.

    Example:
        >>> meta = {"related_entities": [
        ...     {"target": "characters/elena-voss.md", "type": "founded_by"},
        ...     {"target": "factions/silver-hand.md", "type": "rivalry"},
        ... ]}
        >>> build_relational_layer(meta)
        'Relationships: founded by Elena Voss; rivalry Silver Hand.'
    """
    relationships = metadata.get("related_entities", [])
    if not relationships:
        return None

    rel_parts: List[str] = []

    for rel in relationships:
        # Handle dict format: {"target": "...", "type": "..."}
        if isinstance(rel, dict):
            rel_type = str(rel.get("type", "related to")).replace("_", " ")
            target = str(rel.get("target", ""))
        # Handle tuple/list format: (type, target) or [type, target]
        elif isinstance(rel, (tuple, list)) and len(rel) >= 2:
            rel_type = str(rel[0]).replace("_", " ")
            target = str(rel[1])
        else:
            continue

        # Extract human-readable name from file path
        # e.g., "characters/elena-voss.md" → "Elena Voss"
        if "/" in target:
            target = target.split("/")[-1]  # Get filename
        if target.endswith(".md"):
            target = target[:-3]            # Remove extension
        # Convert kebab-case to Title Case
        target_name = " ".join(
            word.capitalize() for word in target.replace("-", " ").replace("_", " ").split()
        )

        if rel_type and target_name:
            rel_parts.append(f"{rel_type} {target_name}")

    if not rel_parts:
        return None

    return f"Relationships: {'; '.join(rel_parts)}."'''

    new_relational = '''def build_relational_layer(metadata: Dict[str, Any]) -> Optional[str]:
    """Build the Relational layer (Layer 6).

    Parses the relationships from metadata. Handles three formats:
      1. Dict format: [{"target": "...", "type": "..."}] (structured)
      2. Tuple/list format: [("type", "target")] (structured)
      3. String list format: ["Silent Folk", "Echo-Mothers"] (cross_references)
    [FIX: Round 3 — handle string-list cross_references from corpus YAML]

    Also incorporates factions_mentioned and locations_mentioned from raw_
    prefixed keys (preserved by map_frontmatter for unmapped keys).

    Returns None if no relationships are present.

    Args:
        metadata: Normalized metadata with 'related_entities' field and
            optionally 'raw_factions_mentioned' and 'raw_locations_mentioned'.

    Returns:
        Optional[str]: "Related to: {entities}." or None.

    Examples:
        >>> build_relational_layer({"related_entities": ["Silent Folk", "Echo-Mothers"]})
        'Related to: Silent Folk, Echo-Mothers.'

        >>> build_relational_layer({"related_entities": [
        ...     {"target": "characters/elena-voss.md", "type": "founded_by"}]})
        'Related to: Elena Voss (founded by).'
    """
    relationships = metadata.get("related_entities", [])
    factions = metadata.get("raw_factions_mentioned", [])
    locations = metadata.get("raw_locations_mentioned", [])

    rel_parts: List[str] = []

    for rel in relationships:
        # Handle dict format: {"target": "...", "type": "..."}
        if isinstance(rel, dict):
            rel_type = str(rel.get("type", "related to")).replace("_", " ")
            target = str(rel.get("target", ""))
            # Extract human-readable name from file path
            if "/" in target:
                target = target.split("/")[-1]
            if target.endswith(".md"):
                target = target[:-3]
            target_name = " ".join(
                word.capitalize() for word in target.replace("-", " ").replace("_", " ").split()
            )
            if rel_type and target_name:
                rel_parts.append(f"{target_name} ({rel_type})")
        # Handle tuple/list format: (type, target) or [type, target]
        elif isinstance(rel, (tuple, list)) and len(rel) >= 2:
            rel_type = str(rel[0]).replace("_", " ")
            target_name = str(rel[1])
            if rel_type and target_name:
                rel_parts.append(f"{target_name} ({rel_type})")
        # Handle string format: "Silent Folk" (from cross_references)
        elif isinstance(rel, str) and rel.strip():
            rel_parts.append(rel.strip())

    # Add factions and locations as additional relational context
    for faction in (factions if isinstance(factions, list) else []):
        if isinstance(faction, str) and faction.strip() and faction.strip() not in rel_parts:
            rel_parts.append(faction.strip())

    for location in (locations if isinstance(locations, list) else []):
        if isinstance(location, str) and location.strip() and location.strip() not in rel_parts:
            rel_parts.append(location.strip())

    if not rel_parts:
        return None

    return f"Related to: {', '.join(rel_parts)}."'''

    source8, ok4 = apply_replacement(source8, old_relational, new_relational,
                                      "build_relational_layer: handle cross_references format")

    if ok3 or ok4:
        set_cell_source(cell8, source8)
    
    return ok1 or ok2 or ok3 or ok4


def fix_chunking_parameters(nb):
    """
    FIX 3: Confounding chunking variables
    
    Root cause: D-23 changed max_chunk_tokens from 1024 to 600 and overlap 
    from 150 to 50, simultaneously with adding enrichment layers. This makes 
    it impossible to isolate enrichment effects from chunking effects.
    
    Fix: Match D-21/D-22 chunk parameters:
      - max_chunk_tokens: 600 → 1024 (match D-21/D-22)
      - prefix_reserve_tokens: 150 → 100 (actual overhead maxes at 84 tokens)
      - overlap: 50 → 150 (match D-21/D-22)
    
    Effective content window: 1024 - 100 = 924 tokens (vs D-21/D-22's 1024)
    This isolates the enrichment effect while keeping the chunking geometry 
    comparable to D-21/D-22.
    """
    print("\n" + "=" * 70)
    print("FIX 3: Chunking Parameters (isolate enrichment variable)")
    print("=" * 70)
    
    # ── Fix model config in Cell 2 ──
    cell2 = nb['cells'][2]
    source2 = get_cell_source(cell2)
    
    if 'ModelConfig' not in source2:
        print("  ERROR: Cell 2 doesn't contain ModelConfig!")
        return False
    
    # Fix v1.5 config (the selected model)
    old_v15 = '''    "v1.5": ModelConfig(
        name="v1.5",
        hf_model_id="nomic-ai/nomic-embed-text-v1.5",
        max_tokens=8192,
        max_chunk_tokens=600,
        prefix_reserve_tokens=150,   # 8-layer prefix: ~80-150 tokens'''
    
    new_v15 = '''    "v1.5": ModelConfig(
        name="v1.5",
        hf_model_id="nomic-ai/nomic-embed-text-v1.5",
        max_tokens=8192,
        max_chunk_tokens=1024,       # [FIX Round 3] Match D-21/D-22 for controlled comparison
        prefix_reserve_tokens=100,   # [FIX Round 3] Actual max overhead is 84 tokens; 100 is safe'''
    
    source2, ok1 = apply_replacement(source2, old_v15, new_v15,
                                      "v1.5 config: max_chunk=1024, prefix_reserve=100")
    
    if ok1:
        set_cell_source(cell2, source2)
    
    # ── Fix overlap in Cell 7 (Chunking Engine) ──
    cell7 = nb['cells'][7]
    source7 = get_cell_source(cell7)
    
    if 'overlap_tokens' not in source7:
        print("  ERROR: Cell 7 doesn't contain overlap_tokens!")
        return False
    
    # Fix the default parameter
    old_overlap_param = 'overlap_tokens: int = 50,'
    new_overlap_param = 'overlap_tokens: int = 150,  # [FIX Round 3] Match D-21/D-22'
    source7, ok2 = apply_replacement(source7, old_overlap_param, new_overlap_param,
                                      "fixed_window_split: overlap 50 → 150")
    
    # Fix the hardcoded overlap in hybrid_chunk_document
    old_overlap_call = 'sub_chunks = fixed_window_split(content, available_tokens, overlap_tokens=50)'
    new_overlap_call = 'sub_chunks = fixed_window_split(content, available_tokens, overlap_tokens=150)  # [FIX Round 3]'
    source7, ok3 = apply_replacement(source7, old_overlap_call, new_overlap_call,
                                      "hybrid_chunk_document: overlap 50 → 150")
    
    # Fix the print statement
    old_overlap_print = 'print(f"  Overlap:              50 tokens")'
    new_overlap_print = 'print(f"  Overlap:              150 tokens  [Round 3: matches D-21/D-22]")'
    source7, ok4 = apply_replacement(source7, old_overlap_print, new_overlap_print,
                                      "overlap print statement")
    
    if ok2 or ok3 or ok4:
        set_cell_source(cell7, source7)
    
    return ok1 or ok2 or ok3 or ok4


def add_round3_header(nb):
    """Add a markdown cell at the top noting Round 3 fixes."""
    print("\n" + "=" * 70)
    print("Adding Round 3 fix documentation header")
    print("=" * 70)
    
    # Find the first markdown cell and add a notice after it
    header_source = [
        "## ⚠️ Round 3 Fixes Applied\n",
        "\n",
        "This notebook has been patched for Round 3 (re-run after Round 2 analysis).\n",
        "\n",
        "**Fixes applied:**\n",
        "\n",
        "1. **NDCG Bug** (Cell 14): Deduplicate retrieved IDs before DCG computation. ",
        "Round 2 produced NDCG values up to 2.79 because multiple chunks from ",
        "the same document each accumulated relevance gains, but the IDCG denominator ",
        "only counted unique documents.\n",
        "\n",
        "2. **Missing Layers** (Cells 5, 9): Fixed FIELD_MAP to include `temporal_markers` ",
        "and `cross_references` from the corpus YAML frontmatter. Updated layer builders ",
        "to handle the actual data formats. Previously, Temporal, Relational, and Chunk ",
        "Sequence layers returned None for all documents.\n",
        "\n",
        "3. **Chunking Parameters** (Cells 3, 8): Changed `max_chunk_tokens` from 600 → 1024 ",
        "and `overlap` from 50 → 150 to match D-21/D-22. Reduced `prefix_reserve_tokens` ",
        "from 150 → 100 (actual max overhead is 84 tokens). This isolates the enrichment ",
        "effect from chunking geometry changes.\n",
        "\n",
        f"*Patch applied: {datetime.now().strftime('%Y-%m-%d %H:%M')} by fix_d23_round3.py*\n",
    ]
    
    fix_cell = {
        "cell_type": "markdown",
        "metadata": {},
        "source": header_source,
    }
    
    # Insert after the first cell (the main title/description markdown)
    nb['cells'].insert(1, fix_cell)
    print("  APPLIED: Round 3 documentation header inserted after cell 0")
    
    return True


def main():
    print("=" * 70)
    print("D-23 ROUND 3 FIX SCRIPT")
    print("=" * 70)
    print(f"Target: {NOTEBOOK_PATH}")
    print(f"Date:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not os.path.exists(NOTEBOOK_PATH):
        print(f"\nERROR: {NOTEBOOK_PATH} not found!")
        print("Run this script from the notebooks/ directory.")
        sys.exit(1)
    
    # Load notebook
    nb = load_notebook(NOTEBOOK_PATH)
    total_cells = len(nb['cells'])
    print(f"\nLoaded notebook with {total_cells} cells")
    
    # Apply fixes (cell indices shift after header insertion, so do header last)
    results = []
    
    # Fix 1: NDCG
    results.append(("NDCG Bug", fix_ndcg_bug(nb)))
    
    # Fix 2: Missing Layers  
    results.append(("Missing Layers", fix_missing_layers(nb)))
    
    # Fix 3: Chunking Parameters
    results.append(("Chunking Parameters", fix_chunking_parameters(nb)))
    
    # Add documentation header (shifts cell indices, do last)
    results.append(("Documentation Header", add_round3_header(nb)))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    all_ok = True
    for name, ok in results:
        status = "✅ APPLIED" if ok else "❌ FAILED"
        print(f"  {status}  {name}")
        if not ok:
            all_ok = False
    
    if all_ok:
        # Save
        save_notebook(nb, NOTEBOOK_PATH)
        print(f"\n✅ All fixes applied. Notebook saved to {NOTEBOOK_PATH}")
        print(f"\nNext steps:")
        print(f"  1. Upload the patched notebook to Google Colab")
        print(f"  2. Run all cells")
        print(f"  3. Download results to notebooks/results/d23/round-3/")
        print(f"  4. Verify NDCG@10 values are in [0.0, 1.0]")
        print(f"  5. Verify Temporal and Relational layers appear in token audit")
        print(f"  6. Verify chunk count is closer to D-21/D-22 (~218) not Round 2 (~1266)")
    else:
        print(f"\n⚠️ Some fixes failed. Review output above.")
        save_notebook(nb, NOTEBOOK_PATH)
        print(f"Notebook saved with partial fixes.")


if __name__ == "__main__":
    main()
