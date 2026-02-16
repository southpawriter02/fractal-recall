#!/usr/bin/env python3
"""
Comprehensive audit fix script for D23-multi-layer.ipynb.

Fixes all 12 issues from D23-audit-and-fixes.md:
  1. Add METRIC_LABELS (Cell 03)
  2. Fix compute_all_metrics call — all_results/QUERIES → query_results/GROUND_TRUTH_QUERIES (Cell 15)
  3. Fix total_chunks → len(enriched_chunks) (Cell 20)
  4. Fix layer_token_audit → layer_token_audits (Cells 19, 21)
  5. Replace placeholder queries with full 36-query set from D22 (Cell 04)
  6. Fix prompt_name="passage" → "document" (Cell 11)
  7. Update query type loops from 3 to 5 types (Cells 04, 12, 16, 18, 20)
  8. Fix hardcoded /mnt/... paths to relative paths (Cell 03)
  9. Remove .yaml/.yml glob from corpus loading (Cell 06)
  10. Fix Cell 12 docstring (cosmetic)
  11. Fix H3 hypothesis text (cosmetic)
  12. Model column alignment (cosmetic)
"""
import json
from pathlib import Path

NOTEBOOK_PATH = Path(__file__).parent / "D23-multi-layer.ipynb"


def get_cell_source(cell) -> str:
    """Join cell source lines into a single string."""
    return "".join(cell.get("source", []))


def set_cell_source(cell, new_src: str):
    """Split a string back into notebook source lines."""
    lines = new_src.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    cell["source"] = lines


def apply_fix(cell, old: str, new: str, label: str) -> bool:
    """Replace old with new in cell source. Returns True if changed."""
    src = get_cell_source(cell)
    if old in src:
        src = src.replace(old, new)
        set_cell_source(cell, src)
        print(f"  ✓ {label}")
        return True
    else:
        print(f"  ✗ {label} — pattern not found")
        return False


def main():
    print(f"Loading: {NOTEBOOK_PATH}")
    with open(NOTEBOOK_PATH, "r") as f:
        nb = json.load(f)

    cells = nb["cells"]
    code_cells = [(i, c) for i, c in enumerate(cells) if c.get("cell_type") == "code"]
    print(f"  Found {len(cells)} cells ({len(code_cells)} code)\n")

    fixes = 0

    # ========================================================================
    # CELL 03 (Config) — Fix 1: Add METRIC_LABELS + Fix 8: Paths
    # ========================================================================
    for idx, cell in code_cells:
        src = get_cell_source(cell)
        if 'METRICS = ["precision@5"' in src and "SELECTED_MODEL" in src:
            print(f"[Cell {idx}] Config cell — Fix 1 (METRIC_LABELS) + Fix 8 (paths)")

            # Fix 1: Add METRIC_LABELS after METRICS
            if "METRIC_LABELS" not in src:
                if apply_fix(cell, 
                    'METRICS = ["precision@5", "recall@10", "ndcg@10", "mrr"]\n',
                    'METRICS = ["precision@5", "recall@10", "ndcg@10", "mrr"]\n'
                    'METRIC_LABELS = ["P@5", "R@10", "NDCG@10", "MRR"]\n',
                    "Fix 1: Added METRIC_LABELS"):
                    fixes += 1

            # Fix 8: Hardcoded paths
            path_fixes = [
                ('/mnt/0000_concurrent/d20_corpus', './corpus'),
                ('/mnt/0000_concurrent/d23_output', './d23-output'),
                ('/mnt/0000_concurrent/d21_output/d21_results.csv', './d21-output/d21_results.csv'),
                ('/mnt/0000_concurrent/d22_output/d22_results.csv', './d22-output/d22_results.csv'),
            ]
            for old_path, new_path in path_fixes:
                if apply_fix(cell, old_path, new_path, f"Fix 8: {old_path} → {new_path}"):
                    fixes += 1
            break

    # ========================================================================
    # CELL 04 (Queries) — Fix 5: Full 36-query set + Fix 7: 5 query types
    # ========================================================================
    for idx, cell in code_cells:
        src = get_cell_source(cell)
        if "GroundTruthQuery" in src and "GROUND_TRUTH_QUERIES" in src:
            print(f"\n[Cell {idx}] Query cell — Fix 5 (full query set) + Fix 7 (5 types)")

            # Replace entire cell with D22-aligned queries + conversion
            new_query_cell = '''#!/usr/bin/env python3
"""
D-23 Cell 04: Ground-Truth Query Set (Aligned with D-21/D-22)

Defines 36 ground-truth queries for evaluation, organized by type:
  - SINGLE_HOP (11): Direct attribute lookups
  - MULTI_HOP (8): Cross-entity relationship traversal
  - AUTHORITY (5): Canonical vs. draft vs. superseded status questions
  - TEMPORAL (6): Time-based historical queries
  - EXPLORATORY (6): Open-ended relationship discovery

Same query set as D-21 Cell 05 and D-22 Cell 04 for consistent 3-way comparison.

Each query includes:
  - query_id: Unique identifier (e.g., "Q-01")
  - type: Category (SINGLE_HOP, MULTI_HOP, AUTHORITY, TEMPORAL, EXPLORATORY)
  - text: Natural language query string
  - relevant_docs: List of corpus files expected to be relevant
"""

@dataclass
class GroundTruthQuery:
    """A single ground-truth query with expected relevant documents.

    Attributes:
        query_id: Unique query identifier (e.g., "Q-01")
        query_text: Natural language query
        query_type: One of SINGLE_HOP, MULTI_HOP, AUTHORITY, TEMPORAL, EXPLORATORY
        expected_filenames: List of corpus filenames expected to be relevant
        relevance_scores: Dict mapping filename → relevance grade (1-3)
    """
    query_id: str
    query_text: str
    query_type: str
    expected_filenames: List[str]
    relevance_scores: Dict[str, int]

# ============================================================================
# FULL QUERY SET: 36 queries (identical to D-21/D-22)
# ============================================================================

# SINGLE_HOP QUERIES (11 total)
# These test direct lookups of facts, entities, and concepts

QUERIES = [
    {
        "query_id": "Q-01",
        "type": "SINGLE_HOP",
        "text": "What is the Echo-Cant communication system?",
        "relevant_docs": ["000-codex_echo-cant.md", "000-resources_comprehensive-glossary.md"],
    },
    {
        "query_id": "Q-02",
        "type": "SINGLE_HOP",
        "text": "What are the defining characteristics of the Void-Marked?",
        "relevant_docs": ["db02-wb_void-marked-assembled-entry.md", "db03-dc_jotun-reader-chronology.md"],
    },
    {
        "query_id": "Q-03",
        "type": "SINGLE_HOP",
        "text": "Describe the Harrow-Sick condition and its effects.",
        "relevant_docs": ["000-codex_harrow-sick.md", "db02-wb_medical-phenomena-entry.md"],
    },
    {
        "query_id": "Q-04",
        "type": "SINGLE_HOP",
        "text": "What is the ODIN Protocol?",
        "relevant_docs": ["000-codex_odin-protocol.md", "standalone_aether-weave-os.md", "standalone_nine-tiers-architecture.md"],
    },
    {
        "query_id": "Q-05",
        "type": "SINGLE_HOP",
        "text": "What is the \\u00c6ther-Weave operating system?",
        "relevant_docs": ["standalone_aether-weave-os.md", "000-resources_comprehensive-glossary.md"],
    },
    {
        "query_id": "Q-06",
        "type": "SINGLE_HOP",
        "text": "Who are the Scavenger-Barons and what do they do?",
        "relevant_docs": ["db02-wb_scavenger-barons-assembled-entry.md", "db03-dc_contract-dispute-case-study.md"],
    },
    {
        "query_id": "Q-07",
        "type": "SINGLE_HOP",
        "text": "What is the Nine-Tiers architectural framework?",
        "relevant_docs": ["standalone_nine-tiers-architecture.md", "000-resources_comprehensive-glossary.md"],
    },
    {
        "query_id": "Q-27",
        "type": "SINGLE_HOP",
        "text": "What are the primary functions of the Warden-Host?",
        "relevant_docs": ["db02-wb_warden-host-assembled-entry.md", "db03-dc_sanctuary-establishment-record.md"],
    },
    {
        "query_id": "Q-28",
        "type": "SINGLE_HOP",
        "text": "Define the Glitch in the context of Aethelgard's history.",
        "relevant_docs": ["000-resources_comprehensive-glossary.md", "standalone_nine-tiers-architecture.md"],
    },
    {
        "query_id": "Q-30",
        "type": "SINGLE_HOP",
        "text": "What is the Spell-Lock system?",
        "relevant_docs": ["000-codex_spell-lock.md", "standalone_aether-weave-os.md"],
    },
    {
        "query_id": "Q-34",
        "type": "SINGLE_HOP",
        "text": "Describe the Weir-Bone material and its properties.",
        "relevant_docs": ["db02-wb_weir-bone-assembled-entry.md", "000-resources_comprehensive-glossary.md"],
    },

    # MULTI_HOP QUERIES (8 total)
    # These require traversing relationships between multiple entities/concepts

    {
        "query_id": "Q-08",
        "type": "MULTI_HOP",
        "text": "How do Iron-Bane and God-Sleeper theological positions on Svin-fylking differ?",
        "relevant_docs": ["db03-dc_iron-bane-theological-analysis.md", "db03-dc_god-sleeper-operational-doctrine.md", "db02-wb_svin-fylking-assembled-entry.md"],
    },
    {
        "query_id": "Q-09",
        "type": "MULTI_HOP",
        "text": "What is the relationship between the Harrow-Sick and the Void-Marked?",
        "relevant_docs": ["000-codex_harrow-sick.md", "db02-wb_void-marked-assembled-entry.md", "db03-dc_medical-causality-research.md"],
    },
    {
        "query_id": "Q-10",
        "type": "MULTI_HOP",
        "text": "How do the Scavenger-Barons use Spell-Lock in their operations?",
        "relevant_docs": ["db02-wb_scavenger-barons-assembled-entry.md", "000-codex_spell-lock.md", "db03-dc_contract-dispute-case-study.md"],
    },
    {
        "query_id": "Q-11",
        "type": "MULTI_HOP",
        "text": "Explain the conflict between Warden-Host sanctuary protocols and Iron-Bane territorial claims.",
        "relevant_docs": ["db02-wb_warden-host-assembled-entry.md", "db03-dc_iron-bane-theological-analysis.md", "db03-dc_sanctuary-establishment-record.md"],
    },
    {
        "query_id": "Q-12",
        "type": "MULTI_HOP",
        "text": "How does the ODIN Protocol interact with the \\u00c6ther-Weave OS?",
        "relevant_docs": ["000-codex_odin-protocol.md", "standalone_aether-weave-os.md", "standalone_nine-tiers-architecture.md"],
    },
    {
        "query_id": "Q-29",
        "type": "MULTI_HOP",
        "text": "What role does the Echo-Cant system play in maintaining Warden-Host operations?",
        "relevant_docs": ["000-codex_echo-cant.md", "db02-wb_warden-host-assembled-entry.md", "db03-dc_sanctuary-establishment-record.md"],
    },
    {
        "query_id": "Q-31",
        "type": "MULTI_HOP",
        "text": "How do Void-Marked and Weir-Bone materials interact in salvage contexts?",
        "relevant_docs": ["db02-wb_void-marked-assembled-entry.md", "db02-wb_weir-bone-assembled-entry.md", "db03-dc_salvage-operations-manual.md"],
    },
    {
        "query_id": "Q-35",
        "type": "MULTI_HOP",
        "text": "What is the relationship between the Nine-Tiers architecture and Svin-fylking religious doctrine?",
        "relevant_docs": ["standalone_nine-tiers-architecture.md", "db02-wb_svin-fylking-assembled-entry.md", "db03-dc_god-sleeper-operational-doctrine.md"],
    },

    # AUTHORITY QUERIES (5 total)
    # These test knowledge of canonical vs. draft vs. superseded information

    {
        "query_id": "Q-13",
        "type": "AUTHORITY",
        "text": "What is the canonical explanation for how the Glitch occurred?",
        "relevant_docs": ["000-resources_comprehensive-glossary.md", "standalone_nine-tiers-architecture.md"],
    },
    {
        "query_id": "Q-14",
        "type": "AUTHORITY",
        "text": "What are the established facts about the God-Sleeper movement origins?",
        "relevant_docs": ["db03-dc_god-sleeper-operational-doctrine.md", "db03-dc_historical-theological-survey.md"],
    },
    {
        "query_id": "Q-15",
        "type": "AUTHORITY",
        "text": "Which interpretations of Harrow-Sick etiology are considered canon?",
        "relevant_docs": ["000-codex_harrow-sick.md", "db03-dc_medical-causality-research.md"],
    },
    {
        "query_id": "Q-16",
        "type": "AUTHORITY",
        "text": "What is the official Warden-Host stance on Void-Marked rights?",
        "relevant_docs": ["db02-wb_warden-host-assembled-entry.md", "db02-wb_void-marked-assembled-entry.md", "db03-dc_sanctuary-establishment-record.md"],
    },
    {
        "query_id": "Q-17",
        "type": "AUTHORITY",
        "text": "According to published sources, what materials constitute a valid Spell-Lock?",
        "relevant_docs": ["000-codex_spell-lock.md", "000-resources_comprehensive-glossary.md"],
    },

    # TEMPORAL QUERIES (6 total)
    # These test time-based historical retrieval across the Aethelgard timeline

    {
        "query_id": "Q-18",
        "type": "TEMPORAL",
        "text": "What major events happened in the first century after the Glitch (Year 0-100 PG)?",
        "relevant_docs": ["db03-dc_jotun-reader-chronology.md", "db03-dc_sanctuary-establishment-record.md"],
    },
    {
        "query_id": "Q-19",
        "type": "TEMPORAL",
        "text": "When was the Warden-Host sanctuary established and what precipitated it?",
        "relevant_docs": ["db03-dc_sanctuary-establishment-record.md", "db02-wb_warden-host-assembled-entry.md"],
    },
    {
        "query_id": "Q-20",
        "type": "TEMPORAL",
        "text": "Trace the chronological development of Iron-Bane theological doctrine.",
        "relevant_docs": ["db03-dc_iron-bane-theological-analysis.md", "db03-dc_historical-theological-survey.md"],
    },
    {
        "query_id": "Q-21",
        "type": "TEMPORAL",
        "text": "What is the timeline of major salvage discoveries in the Aethelgard region?",
        "relevant_docs": ["db03-dc_salvage-operations-manual.md", "db03-dc_jotun-reader-chronology.md"],
    },
    {
        "query_id": "Q-22",
        "type": "TEMPORAL",
        "text": "When did the God-Sleeper movement gain significant political influence?",
        "relevant_docs": ["db03-dc_god-sleeper-operational-doctrine.md", "db03-dc_historical-theological-survey.md"],
    },
    {
        "query_id": "Q-23",
        "type": "TEMPORAL",
        "text": "Describe the sequence of events in the Scavenger-Baron contract dispute.",
        "relevant_docs": ["db03-dc_contract-dispute-case-study.md", "db02-wb_scavenger-barons-assembled-entry.md"],
    },

    # EXPLORATORY QUERIES (6 total)
    # These test open-ended discovery of related concepts and themes

    {
        "query_id": "Q-24",
        "type": "EXPLORATORY",
        "text": "What are the major political tensions in post-Glitch Aethelgard?",
        "relevant_docs": ["db03-dc_iron-bane-theological-analysis.md", "db03-dc_god-sleeper-operational-doctrine.md", "db03-dc_contract-dispute-case-study.md", "db02-wb_scavenger-barons-assembled-entry.md"],
    },
    {
        "query_id": "Q-25",
        "type": "EXPLORATORY",
        "text": "How do different factions view the technological salvage efforts?",
        "relevant_docs": ["db02-wb_scavenger-barons-assembled-entry.md", "db03-dc_salvage-operations-manual.md", "db03-dc_iron-bane-theological-analysis.md", "db03-dc_god-sleeper-operational-doctrine.md"],
    },
    {
        "query_id": "Q-26",
        "type": "EXPLORATORY",
        "text": "What medical and physiological mysteries remain unsolved in Aethelgard?",
        "relevant_docs": ["000-codex_harrow-sick.md", "db03-dc_medical-causality-research.md", "db02-wb_void-marked-assembled-entry.md"],
    },
    {
        "query_id": "Q-32",
        "type": "EXPLORATORY",
        "text": "What are the intersections between religious doctrine and technological systems in Aethelgard?",
        "relevant_docs": ["standalone_nine-tiers-architecture.md", "db02-wb_svin-fylking-assembled-entry.md", "000-codex_odin-protocol.md", "db03-dc_historical-theological-survey.md"],
    },
    {
        "query_id": "Q-33",
        "type": "EXPLORATORY",
        "text": "How do material properties (Weir-Bone, Void-Marked) influence cultural practices?",
        "relevant_docs": ["db02-wb_weir-bone-assembled-entry.md", "db02-wb_void-marked-assembled-entry.md", "db02-wb_warden-host-assembled-entry.md"],
    },
    {
        "query_id": "Q-36",
        "type": "EXPLORATORY",
        "text": "What gaps exist in the documented understanding of Aethelgard's pre-Glitch history?",
        "relevant_docs": ["db03-dc_historical-theological-survey.md", "db03-dc_jotun-reader-chronology.md", "000-resources_comprehensive-glossary.md"],
    },
]

# ============================================================================
# BUILD GROUND_TRUTH_QUERIES from QUERIES (for compatibility with Cell 14)
# ============================================================================

GROUND_TRUTH_QUERIES: List[GroundTruthQuery] = []
for q in QUERIES:
    # Build uniform relevance scores (all docs score 2 by default)
    relevance = {doc: 2 for doc in q["relevant_docs"]}
    GROUND_TRUTH_QUERIES.append(GroundTruthQuery(
        query_id=q["query_id"],
        query_text=q["text"],
        query_type=q["type"],
        expected_filenames=q["relevant_docs"],
        relevance_scores=relevance,
    ))

# ============================================================================
# VALIDATION
# ============================================================================

query_type_counts = {}
for q in QUERIES:
    query_type_counts[q["type"]] = query_type_counts.get(q["type"], 0) + 1

assert len(QUERIES) == 36, f"Expected 36 queries, got {len(QUERIES)}"
assert query_type_counts.get("SINGLE_HOP", 0) == 11, f"Expected 11 SINGLE_HOP"
assert query_type_counts.get("MULTI_HOP", 0) == 8, f"Expected 8 MULTI_HOP"
assert query_type_counts.get("AUTHORITY", 0) == 5, f"Expected 5 AUTHORITY"
assert query_type_counts.get("TEMPORAL", 0) == 6, f"Expected 6 TEMPORAL"
assert query_type_counts.get("EXPLORATORY", 0) == 6, f"Expected 6 EXPLORATORY"

print(f"\\u2713 All 36 ground-truth queries validated (aligned with D-21/D-22)")
print(f"  Distribution: {query_type_counts}")
print(f"  GROUND_TRUTH_QUERIES: {len(GROUND_TRUTH_QUERIES)} GroundTruthQuery objects")
'''
            set_cell_source(cell, new_query_cell)
            print(f"  ✓ Fix 5+7: Replaced query cell with full 36-query set (5 types)")
            fixes += 1
            break

    # ========================================================================
    # CELL 06 (Corpus Loading) — Fix 9: Remove .yaml/.yml glob
    # ========================================================================
    for idx, cell in code_cells:
        src = get_cell_source(cell)
        if "load_corpus" in src and '*.yaml' in src:
            print(f"\n[Cell {idx}] Corpus loading — Fix 9 (remove .yaml/.yml glob)")
            apply_fix(cell,
                '    files = sorted(set(\n'
                '        list(corpus_dir.glob("*.md"))\n'
                '        + list(corpus_dir.glob("*.yaml"))\n'
                '        + list(corpus_dir.glob("*.yml"))\n'
                '    ))',
                '    files = sorted(corpus_dir.glob("*.md"))',
                "Fix 9: Removed .yaml/.yml glob patterns")
            fixes += 1
            break

    # ========================================================================
    # CELL 11 (Embedding) — Fix 6: prompt_name="passage" → "document"
    # ========================================================================
    for idx, cell in code_cells:
        src = get_cell_source(cell)
        if 'prompt_name="passage"' in src and "EMBEDDING" in src:
            print(f"\n[Cell {idx}] Embedding — Fix 6 (prompt_name)")
            if apply_fix(cell, 'prompt_name="passage"', 'prompt_name="document"',
                         'Fix 6: prompt_name="passage" → "document"'):
                fixes += 1
            # Also fix the docstring
            if apply_fix(cell, 'encode with prompt_name="passage"',
                         'encode with prompt_name="document"',
                         'Fix 6b: docstring prompt_name'):
                fixes += 1
            break

    # ========================================================================
    # CELL 12 (Query Execution) — Fix 10: Update docstring query types
    # ========================================================================
    for idx, cell in code_cells:
        src = get_cell_source(cell)
        if "QueryResult" in src and "encode_query" in src:
            print(f"\n[Cell {idx}] Query execution — Fix 10 (docstring types)")
            if apply_fix(cell,
                'query_type: Query category ("authority", "temporal", "factual")',
                'query_type: Query category (SINGLE_HOP, MULTI_HOP, AUTHORITY, TEMPORAL, EXPLORATORY)',
                "Fix 10: Updated QueryResult docstring types"):
                fixes += 1

            # Fix the query type summary loop
            if apply_fix(cell,
                'for qtype in ["authority", "temporal", "factual"]:',
                'for qtype in ["SINGLE_HOP", "MULTI_HOP", "AUTHORITY", "TEMPORAL", "EXPLORATORY"]:',
                "Fix 10b: Updated query type summary loop"):
                fixes += 1
            break

    # ========================================================================
    # CELL 15 (Metrics + Comparison) — Fix 2: all_results/QUERIES
    # ========================================================================
    for idx, cell in code_cells:
        src = get_cell_source(cell)
        if "compute_all_metrics(all_results, QUERIES)" in src:
            print(f"\n[Cell {idx}] Metrics — Fix 2 (variable names)")
            if apply_fix(cell,
                "compute_all_metrics(all_results, QUERIES)",
                "compute_all_metrics(query_results, GROUND_TRUTH_QUERIES)",
                "Fix 2: all_results/QUERIES → query_results/GROUND_TRUTH_QUERIES"):
                fixes += 1
            break

    # ========================================================================
    # CELL 16 (Delta Analysis) — Fix 7 downstream: query type loops
    # ========================================================================
    for idx, cell in code_cells:
        src = get_cell_source(cell)
        if "delta_results" in src and "multi_layer_vs_baseline" in src and "for query_type" in src:
            print(f"\n[Cell {idx}] Delta analysis — Fix 7 (query type loops)")
            if apply_fix(cell,
                'for query_type in ["authority", "temporal", "factual"]:',
                'for query_type in ["SINGLE_HOP", "MULTI_HOP", "AUTHORITY", "TEMPORAL", "EXPLORATORY"]:',
                "Fix 7: Updated delta analysis query type loop"):
                fixes += 1
            break

    # ========================================================================
    # CELL 18 (Visualizations) — Fix 7 downstream: query type list
    # ========================================================================
    for idx, cell in code_cells:
        src = get_cell_source(cell)
        if 'query_types = ["authority", "temporal", "factual"]' in src:
            print(f"\n[Cell {idx}] Visualizations — Fix 7 (query type list)")
            if apply_fix(cell,
                'query_types = ["authority", "temporal", "factual"]',
                'query_types = ["SINGLE_HOP", "MULTI_HOP", "AUTHORITY", "TEMPORAL", "EXPLORATORY"]',
                "Fix 7: Updated visualization query types"):
                fixes += 1
            break

    # ========================================================================
    # CELL 19 (Token Distribution) — Fix 4: layer_token_audit→audits + layer name case
    # ========================================================================
    for idx, cell in code_cells:
        src = get_cell_source(cell)
        if "layer_token_distribution" in src or ("layer_token_audit" in src and "layer_names" in src):
            print(f"\n[Cell {idx}] Token distribution — Fix 4 (singular→plural + case)")
            # Fix the variable name (singular to plural)
            src = get_cell_source(cell)
            src = src.replace("layer_token_audit", "layer_token_audits")
            # Fix layer name case: lowercase → capitalized (matching build_multi_layer_prefix output)
            src = src.replace(
                'layer_names = ["corpus", "domain", "entity", "authority",',
                'layer_names = ["Corpus", "Domain", "Entity", "Authority",')
            src = src.replace(
                '"temporal", "relational", "section"]',
                '"Temporal", "Relational", "Section"]')
            set_cell_source(cell, src)
            fixes += 1
            print(f"  ✓ Fix 4: layer_token_audit → layer_token_audits + capitalized names")
            break

    # ========================================================================
    # CELL 20 (GO/NO-GO) — Fix 3: total_chunks + Fix 7 downstream
    # ========================================================================
    for idx, cell in code_cells:
        src = get_cell_source(cell)
        if "GO/NO-GO" in src and "total_chunks" in src:
            print(f"\n[Cell {idx}] GO/NO-GO — Fix 3 (total_chunks) + Fix 7 (query types)")
            if apply_fix(cell, "total_chunks", "len(enriched_chunks)",
                         "Fix 3: total_chunks → len(enriched_chunks)"):
                fixes += 1
            # Fix query type loops in criterion 7
            if apply_fix(cell,
                'for qtype in ["authority", "temporal", "factual"]:',
                'for qtype in ["SINGLE_HOP", "MULTI_HOP", "AUTHORITY", "TEMPORAL", "EXPLORATORY"]:',
                "Fix 7: Updated GO/NO-GO query type loop"):
                fixes += 1
            # Fix the authority/temporal/factual comparison in criterion 7
            if apply_fix(cell,
                'auth_better = type_mean_deltas.get("authority", -999) > type_mean_deltas.get("factual", -999)',
                'auth_better = type_mean_deltas.get("AUTHORITY", -999) > type_mean_deltas.get("SINGLE_HOP", -999)',
                "Fix 7: Updated auth_better comparison"):
                fixes += 1
            if apply_fix(cell,
                'temp_better = type_mean_deltas.get("temporal", -999) > type_mean_deltas.get("factual", -999)',
                'temp_better = type_mean_deltas.get("TEMPORAL", -999) > type_mean_deltas.get("SINGLE_HOP", -999)',
                "Fix 7: Updated temp_better comparison"):
                fixes += 1
            break

    # ========================================================================
    # CELL 21 (Export) — Fix 4: layer_token_audit→audits
    # ========================================================================
    for idx, cell in code_cells:
        src = get_cell_source(cell)
        if "EXPORTING D-23 RESULTS" in src and "layer_token_audit" in src:
            print(f"\n[Cell {idx}] Export — Fix 4 (singular→plural)")
            src = src.replace("layer_token_audit", "layer_token_audits")
            set_cell_source(cell, src)
            fixes += 1
            print(f"  ✓ Fix 4: layer_token_audit → layer_token_audits")
            break

    # ========================================================================
    # SAVE
    # ========================================================================
    if fixes == 0:
        print("\n⚠ No changes needed — already fixed?")
    else:
        with open(NOTEBOOK_PATH, "w") as f:
            json.dump(nb, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"\n{'=' * 60}")
        print(f"✓ Saved {fixes} fixes to {NOTEBOOK_PATH}")
        print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
