#!/usr/bin/env python3
"""
Fix script for D22-single-layer.ipynb
Applies all 11 identified fixes programmatically.
"""

import json
import copy

NOTEBOOK_PATH = "D22-single-layer.ipynb"

def load_notebook(path):
    with open(path, "r") as f:
        return json.load(f)

def save_notebook(nb, path):
    with open(path, "w") as f:
        json.dump(nb, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved patched notebook to {path}")

def get_cell_source(cell):
    """Get the source of a cell as a single string."""
    return "".join(cell["source"])

def set_cell_source(cell, text):
    """Set cell source from a string, splitting into lines for .ipynb format."""
    lines = text.split("\n")
    # Each line except the last gets \n appended
    cell["source"] = [line + "\n" for line in lines[:-1]]
    if lines[-1]:  # If last line is non-empty, add it without trailing \n
        cell["source"].append(lines[-1])

def find_cell_containing(nb, text):
    """Find the index of the first code cell whose source contains `text`."""
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] == "code" and text in get_cell_source(cell):
            return i
    return None


def fix_1_add_import_re(nb):
    """Fix 1: Add 'import re' to the main imports cell."""
    idx = find_cell_containing(nb, "import chromadb")
    if idx is None:
        print("✗ Fix 1: Could not find imports cell")
        return
    src = get_cell_source(nb["cells"][idx])
    if "import re\n" not in src:
        # Insert after 'import math'
        src = src.replace("import math\n", "import math\nimport re\n")
        set_cell_source(nb["cells"][idx], src)
        print("✓ Fix 1: Added 'import re' to imports cell")
    else:
        print("  Fix 1: 'import re' already present")


def fix_2_glob_yaml_to_md(nb):
    """Fix 2: Change load_corpus glob from *.yaml to *.md."""
    idx = find_cell_containing(nb, "def load_corpus")
    if idx is None:
        print("✗ Fix 2: Could not find load_corpus cell")
        return
    src = get_cell_source(nb["cells"][idx])
    src = src.replace('corpus_path.glob("*.yaml")', 'corpus_path.glob("*.md")')
    src = src.replace("yaml_files", "md_files")
    set_cell_source(nb["cells"][idx], src)
    print("✓ Fix 2: Changed glob to *.md, renamed yaml_files → md_files")


def fix_3_4_paths(nb):
    """Fix 3+4: Update CORPUS_DIR, OUTPUT_DIR, D21_RESULTS_PATH."""
    idx = find_cell_containing(nb, "CORPUS_DIR")
    if idx is None:
        print("✗ Fix 3+4: Could not find config cell")
        return
    src = get_cell_source(nb["cells"][idx])
    src = src.replace(
        'CORPUS_DIR = Path("/mnt/0000_concurrent/d20_corpus")',
        'CORPUS_DIR = Path("./test-corpus")  # Same as D-21'
    )
    src = src.replace(
        'OUTPUT_DIR = Path("/mnt/0000_concurrent/d22_output")',
        'OUTPUT_DIR = Path("./d22-output")  # Parallel to d21-output'
    )
    src = src.replace(
        'D21_RESULTS_PATH = Path("/mnt/0000_concurrent/d21_output/d21_results.csv")',
        'D21_RESULTS_PATH = Path("./d21-output/d21_results.csv")  # D-21 export location'
    )
    set_cell_source(nb["cells"][idx], src)
    print("✓ Fix 3+4: Updated CORPUS_DIR, OUTPUT_DIR, D21_RESULTS_PATH")


def fix_5_6_8_replace_queries(nb):
    """Fix 5+6+8: Replace both QUERIES cells with D21-aligned query set."""
    # Find the two QUERIES cells
    queries_indices = []
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] == "code":
            src = get_cell_source(cell)
            if "QUERIES" in src and ("query_id" in src or "Q01" in src or "Q-01" in src):
                queries_indices.append(i)

    if len(queries_indices) < 1:
        print("✗ Fix 5+6+8: Could not find QUERIES cells")
        return

    # The D21-aligned query set (adapted to D22's dict-of-dicts format)
    new_queries_source = '''#!/usr/bin/env python3
"""
D-22: Ground-Truth Query Set (Aligned with D-21)

This cell defines 36 queries covering five categories:
- SINGLE_HOP (11): Direct attribute lookups
- MULTI_HOP (8): Cross-entity relationship traversal
- AUTHORITY (5): Canonical vs. draft vs. superseded status questions
- TEMPORAL (6): Time-based historical queries
- EXPLORATORY (6): Open-ended relationship discovery

Each query has expected relevant documents with .md filenames matching the corpus.
Reference: D-21 Cell 05 (identical query set); D-20 §7 for query type taxonomy.
"""

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

# Validation
query_type_counts = {}
for q in QUERIES:
    query_type_counts[q["type"]] = query_type_counts.get(q["type"], 0) + 1

assert len(QUERIES) == 36, f"Expected 36 queries, got {len(QUERIES)}"
assert query_type_counts.get("SINGLE_HOP", 0) == 11, f"Expected 11 SINGLE_HOP"
assert query_type_counts.get("MULTI_HOP", 0) == 8, f"Expected 8 MULTI_HOP"
assert query_type_counts.get("AUTHORITY", 0) == 5, f"Expected 5 AUTHORITY"
assert query_type_counts.get("TEMPORAL", 0) == 6, f"Expected 6 TEMPORAL"
assert query_type_counts.get("EXPLORATORY", 0) == 6, f"Expected 6 EXPLORATORY"

print(f"\\u2713 All 36 ground-truth queries validated (aligned with D-21)")
print(f"  Distribution: {query_type_counts}")
'''

    # Remove duplicate QUERIES cells and replace with the new one
    # We keep the FIRST queries cell index and replace it, then delete any extra ones
    if len(queries_indices) >= 2:
        # Delete the first (truncated) cell, keep the second's position for replacement
        first_idx = queries_indices[0]
        second_idx = queries_indices[1]

        # Replace the second cell (the "full" one) with new content
        set_cell_source(nb["cells"][second_idx], new_queries_source)
        nb["cells"][second_idx]["outputs"] = []

        # Delete the first (truncated) cell
        del nb["cells"][first_idx]

        print("✓ Fix 5+6+8: Removed duplicate QUERIES cell, replaced with D21-aligned set")
    elif len(queries_indices) == 1:
        # Only one cell, just replace it
        set_cell_source(nb["cells"][queries_indices[0]], new_queries_source)
        nb["cells"][queries_indices[0]]["outputs"] = []
        print("✓ Fix 5+6+8: Replaced QUERIES cell with D21-aligned set")


def fix_7_9_model_config(nb):
    """Fix 7+9: Update ModelConfig with loader field, fix embedding cell for bge-m3."""
    # First, update the ModelConfig and model configs in the config cell
    idx = find_cell_containing(nb, "class ModelConfig")
    if idx is None:
        print("✗ Fix 7+9: Could not find ModelConfig cell")
        return
    src = get_cell_source(nb["cells"][idx])

    # Replace the ModelConfig class and model configs
    # Find where ModelConfig starts and ends
    old_modelconfig = '''@dataclass
class ModelConfig:
    """Model-specific configuration for embedding and chunking."""
    name: str
    model_id: str
    max_tokens: int       # Context window size
    expected_dim: int     # Expected embedding dimension
    batch_size: int       # Batch size for embedding
    max_chunk_tokens: int # Max tokens per chunk (before enrichment)
    prefix_reserve_tokens: int  # Tokens reserved for enrichment prefix'''

    new_modelconfig = '''@dataclass
class ModelConfig:
    """Model-specific configuration for embedding and chunking.

    Field mapping to D-21:
        max_tokens ↔ context_window
        expected_dim ↔ embedding_dim
        max_chunk_tokens ↔ max_chunk_tokens (same)
        loader: "sentence_transformers" or "flag_embedding"
        doc_prefix / query_prefix: model-specific prompt names
    """
    name: str
    model_id: str
    max_tokens: int       # Context window size (D-21: context_window)
    expected_dim: int     # Expected embedding dimension (D-21: embedding_dim)
    batch_size: int       # Batch size for embedding
    max_chunk_tokens: int # Max tokens per chunk (before enrichment)
    prefix_reserve_tokens: int  # Tokens reserved for enrichment prefix
    loader: str = "sentence_transformers"  # "sentence_transformers" or "flag_embedding"
    doc_prefix: str = ""   # Model-specific document prefix
    query_prefix: str = ""  # Model-specific query prefix'''

    src = src.replace(old_modelconfig, new_modelconfig)

    # Update model configs to include loader and prefix fields
    old_v2moe = '''MODEL_CONFIGS = {
    "v2-moe": ModelConfig(
        name="nomic-embed-text-v2-moe",
        model_id="nomic-ai/nomic-embed-text-v2-moe",
        max_tokens=512,
        expected_dim=768,
        batch_size=32,
        max_chunk_tokens=450,
        prefix_reserve_tokens=30,
    ),'''

    new_v2moe = '''# Mapping from SELECTED_MODEL key → D-21 CSV 'model' column value
D21_MODEL_NAMES = {
    "v2-moe": "nomic-embed-text-v2-moe",
    "v1.5": "nomic-embed-text-v1.5",
    "bge-m3": "BAAI/bge-m3",
}

MODEL_CONFIGS = {
    "v2-moe": ModelConfig(
        name="nomic-embed-text-v2-moe",
        model_id="nomic-ai/nomic-embed-text-v2-moe",
        max_tokens=512,
        expected_dim=768,
        batch_size=32,
        max_chunk_tokens=450,
        prefix_reserve_tokens=30,
        loader="sentence_transformers",
        doc_prefix="search_document",
        query_prefix="search_query",
    ),'''

    src = src.replace(old_v2moe, new_v2moe)

    old_v15 = '''    "v1.5": ModelConfig(
        name="nomic-embed-text-v1.5",
        model_id="nomic-ai/nomic-embed-text-v1.5",
        max_tokens=8192,
        expected_dim=768,
        batch_size=32,
        max_chunk_tokens=1024,
        prefix_reserve_tokens=30,
    ),'''

    new_v15 = '''    "v1.5": ModelConfig(
        name="nomic-embed-text-v1.5",
        model_id="nomic-ai/nomic-embed-text-v1.5",
        max_tokens=8192,
        expected_dim=768,
        batch_size=32,
        max_chunk_tokens=1024,
        prefix_reserve_tokens=30,
        loader="sentence_transformers",
        doc_prefix="search_document",
        query_prefix="search_query",
    ),'''

    src = src.replace(old_v15, new_v15)

    old_bgem3 = '''    "bge-m3": ModelConfig(
        name="BAAI/bge-m3",
        model_id="BAAI/bge-m3",
        max_tokens=8192,
        expected_dim=1024,
        batch_size=32,
        max_chunk_tokens=1024,
        prefix_reserve_tokens=30,
    ),'''

    new_bgem3 = '''    "bge-m3": ModelConfig(
        name="BAAI/bge-m3",
        model_id="BAAI/bge-m3",
        max_tokens=8192,
        expected_dim=1024,
        batch_size=32,
        max_chunk_tokens=1024,
        prefix_reserve_tokens=30,
        loader="flag_embedding",  # Requires FlagEmbedding loader
        doc_prefix="",    # BGE-M3 does not use explicit prefixes
        query_prefix="",
    ),'''

    src = src.replace(old_bgem3, new_bgem3)

    set_cell_source(nb["cells"][idx], src)
    print("✓ Fix 7+9: Updated ModelConfig with loader/prefix fields, added D21_MODEL_NAMES")


def fix_7_embedding_cell(nb):
    """Fix 7: Add conditional loading for bge-m3 in the embedding cell."""
    idx = find_cell_containing(nb, "SentenceTransformer(MODEL_CONFIG.model_id)")
    if idx is None:
        print("✗ Fix 7 (embedding): Could not find embedding cell")
        return
    src = get_cell_source(nb["cells"][idx])

    # Replace the hardcoded SentenceTransformer loading
    old_load = '''print(f"Loading embedding model: {MODEL_CONFIG.model_id}")
print(f"  (This may take a minute the first time...)")

start_load_time = time.time()
embedding_model = SentenceTransformer(MODEL_CONFIG.model_id)
load_time = time.time() - start_load_time

print(f"✓ Model loaded in {load_time:.1f} seconds")
print(f"  Embedding dimension: {embedding_model.get_sentence_embedding_dimension()}")
print()

# Verify embedding dimension matches config
actual_dim = embedding_model.get_sentence_embedding_dimension()
if actual_dim != MODEL_CONFIG.expected_dim:
    print(f"⚠ WARNING: Expected dimension {MODEL_CONFIG.expected_dim}, got {actual_dim}")

# Prepare embeddings
print(f"Embedding {len(enriched_chunks)} chunks...")
chunk_texts = [chunk.text for chunk in enriched_chunks]

start_embed_time = time.time()
embeddings = embedding_model.encode(
    chunk_texts,
    batch_size=MODEL_CONFIG.batch_size,
    show_progress_bar=True,
)
embed_time = time.time() - start_embed_time

print(f"✓ Embedding completed in {embed_time:.1f} seconds ({len(enriched_chunks)/embed_time:.1f} chunks/sec)")
print(f"  Shape: {embeddings.shape}")'''

    new_load = '''print(f"Loading embedding model: {MODEL_CONFIG.model_id}")
print(f"  Loader: {MODEL_CONFIG.loader}")
print(f"  (This may take a minute the first time...)")

start_load_time = time.time()

# Load model based on loader type (D-21 compatibility)
if MODEL_CONFIG.loader == "flag_embedding":
    # BGE-M3 requires FlagEmbedding loader
    from FlagEmbedding import BGEM3FlagModel
    embedding_model = BGEM3FlagModel(MODEL_CONFIG.model_id, use_fp16=True)
else:
    # Nomic models use sentence-transformers with trust_remote_code
    embedding_model = SentenceTransformer(MODEL_CONFIG.model_id, trust_remote_code=True)

load_time = time.time() - start_load_time

if MODEL_CONFIG.loader != "flag_embedding":
    actual_dim = embedding_model.get_sentence_embedding_dimension()
    print(f"✓ Model loaded in {load_time:.1f} seconds")
    print(f"  Embedding dimension: {actual_dim}")
    if actual_dim != MODEL_CONFIG.expected_dim:
        print(f"⚠ WARNING: Expected dimension {MODEL_CONFIG.expected_dim}, got {actual_dim}")
else:
    print(f"✓ Model loaded in {load_time:.1f} seconds (FlagEmbedding)")
    print(f"  Expected dimension: {MODEL_CONFIG.expected_dim}")
print()

# Prepare embeddings
print(f"Embedding {len(enriched_chunks)} chunks...")
chunk_texts = [chunk.text for chunk in enriched_chunks]

start_embed_time = time.time()

if MODEL_CONFIG.loader == "flag_embedding":
    # BGE-M3 returns dict with 'dense_vecs'; we use only dense vectors
    embeddings = embedding_model.encode(
        chunk_texts,
        batch_size=MODEL_CONFIG.batch_size,
    )["dense_vecs"]
    embeddings = np.array(embeddings)
elif MODEL_CONFIG.doc_prefix:
    # Nomic models use prompt_name for document prefix
    embeddings = embedding_model.encode(
        chunk_texts,
        prompt_name="document",
        batch_size=MODEL_CONFIG.batch_size,
        show_progress_bar=True,
    )
else:
    embeddings = embedding_model.encode(
        chunk_texts,
        batch_size=MODEL_CONFIG.batch_size,
        show_progress_bar=True,
    )

embed_time = time.time() - start_embed_time

print(f"✓ Embedding completed in {embed_time:.1f} seconds ({len(enriched_chunks)/embed_time:.1f} chunks/sec)")
print(f"  Shape: {embeddings.shape}")'''

    src = src.replace(old_load, new_load)
    set_cell_source(nb["cells"][idx], src)
    print("✓ Fix 7: Updated embedding cell with conditional bge-m3/nomic loading")


def fix_7_query_embedding(nb):
    """Fix 7: Also fix the query embedding cell to handle bge-m3."""
    idx = find_cell_containing(nb, "query_embeddings = embedding_model.encode(query_texts")
    if idx is None:
        print("✗ Fix 7 (query): Could not find query execution cell")
        return
    src = get_cell_source(nb["cells"][idx])

    old_query_embed = '''# Embed all queries at once
query_texts = [q["text"] for q in QUERIES]
query_embeddings = embedding_model.encode(query_texts, batch_size=MODEL_CONFIG.batch_size)'''

    new_query_embed = '''# Embed all queries at once
query_texts = [q["text"] for q in QUERIES]

if MODEL_CONFIG.loader == "flag_embedding":
    # BGE-M3: returns dict with 'dense_vecs'
    query_embeddings = embedding_model.encode(
        query_texts, batch_size=MODEL_CONFIG.batch_size
    )["dense_vecs"]
    query_embeddings = np.array(query_embeddings)
elif MODEL_CONFIG.query_prefix:
    # Nomic models: use "search_query" prompt
    query_embeddings = embedding_model.encode(
        query_texts, prompt_name="query", batch_size=MODEL_CONFIG.batch_size
    )
else:
    query_embeddings = embedding_model.encode(
        query_texts, batch_size=MODEL_CONFIG.batch_size
    )'''

    src = src.replace(old_query_embed, new_query_embed)
    set_cell_source(nb["cells"][idx], src)
    print("✓ Fix 7: Updated query embedding with conditional bge-m3 handling")


def fix_9_remove_redundant_import_re(nb):
    """Fix 1 cont: Remove redundant 'import re' from chunk & enrich cell."""
    idx = find_cell_containing(nb, "enriched_chunks = []\nchunk_stats = []")
    if idx is None:
        return
    src = get_cell_source(nb["cells"][idx])
    if "import re\n" in src:
        src = src.replace("import re\n\n", "")
        src = src.replace("import re\n", "")
        set_cell_source(nb["cells"][idx], src)
        print("✓ Fix 1b: Removed redundant 'import re' from chunk & enrich cell")


def fix_10_d21_comparison(nb):
    """Fix 10: Fix D21 CSV loading — add experiment column and map model name."""
    idx = find_cell_containing(nb, "Loading D-21 baseline from")
    if idx is None:
        print("✗ Fix 10: Could not find comparison cell")
        return
    src = get_cell_source(nb["cells"][idx])

    # Fix the D21 model name mapping — D21 CSV uses .name, not model key
    old_filter = '''# Filter D-21 results to selected model only (D-21 tests three models; we compare to winner)
if not d21_df.empty:
    d21_df = d21_df[d21_df["model"] == SELECTED_MODEL].copy()
    print(f"  Filtered to SELECTED_MODEL={SELECTED_MODEL}: {len(d21_df)} rows")'''

    new_filter = '''# Filter D-21 results to selected model only (D-21 tests three models; we compare to winner)
# Note: D-21 CSV uses the model's full name (e.g., "nomic-embed-text-v1.5"), not the key ("v1.5")
if not d21_df.empty:
    d21_model_name = D21_MODEL_NAMES.get(SELECTED_MODEL, SELECTED_MODEL)
    d21_df = d21_df[d21_df["model"] == d21_model_name].copy()
    print(f"  Filtered to D21 model name='{d21_model_name}': {len(d21_df)} rows")

    # D-21 CSV does not have an 'experiment' column; add it for merging
    d21_df["experiment"] = "baseline"
    # Normalize model name to SELECTED_MODEL key for consistent merging
    d21_df["model"] = SELECTED_MODEL'''

    src = src.replace(old_filter, new_filter)
    set_cell_source(nb["cells"][idx], src)
    print("✓ Fix 10: Fixed D21 CSV model name mapping and added experiment column")


def fix_11_query_type_loops(nb):
    """Fix 11: Update all hardcoded 3-type loops to use D21's 5-type taxonomy."""
    QUERY_TYPES = ["SINGLE_HOP", "MULTI_HOP", "AUTHORITY", "TEMPORAL", "EXPLORATORY"]
    old_3type = '["authority", "temporal", "factual"]'
    new_5type = json.dumps(QUERY_TYPES)

    count = 0
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        src = get_cell_source(cell)
        if old_3type in src:
            src = src.replace(old_3type, new_5type)
            set_cell_source(cell, src)
            count += 1

    print(f"✓ Fix 11: Updated {count} cells from 3-type to 5-type query taxonomy")

    # Also fix the markdown cell that references these types
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "markdown":
            continue
        src = get_cell_source(cell)
        if "authority/temporal/factual" in src:
            src = src.replace(
                "authority/temporal/factual",
                "SINGLE_HOP/MULTI_HOP/AUTHORITY/TEMPORAL/EXPLORATORY"
            )
            set_cell_source(cell, src)
            print("  Also updated markdown cell query type reference")

    # Fix the sample query display line that says "Q01 - authority"
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        src = get_cell_source(cell)
        if 'Sample query results (Q01 - authority)' in src:
            src = src.replace(
                'Sample query results (Q01 - authority)',
                'Sample query results (Q-01 - SINGLE_HOP)'
            )
            src = src.replace(
                'sample_query = query_results["Q01"]',
                'sample_query = query_results["Q-01"]'
            )
            set_cell_source(cell, src)
            print("  Also fixed sample query reference Q01 → Q-01")


def fix_markdown_hypothesis(nb):
    """Update hypothesis markdown cell to match 5-type taxonomy."""
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "markdown":
            continue
        src = get_cell_source(cell)
        if "authority-sensitive queries benefit most" in src:
            src = src.replace(
                "Which types (authority/temporal/factual) benefit most?",
                "Which types (SINGLE_HOP/MULTI_HOP/AUTHORITY/TEMPORAL/EXPLORATORY) benefit most?"
            )
            set_cell_source(cell, src)
            print("  Also updated results methodology markdown")


def main():
    print("Loading notebook...")
    nb = load_notebook(NOTEBOOK_PATH)
    print(f"  {len(nb['cells'])} cells loaded")
    print()

    print("=" * 60)
    print("Applying fixes...")
    print("=" * 60)

    fix_1_add_import_re(nb)
    fix_2_glob_yaml_to_md(nb)
    fix_3_4_paths(nb)
    fix_5_6_8_replace_queries(nb)
    fix_7_9_model_config(nb)
    fix_7_embedding_cell(nb)
    fix_7_query_embedding(nb)
    fix_9_remove_redundant_import_re(nb)
    fix_10_d21_comparison(nb)
    fix_11_query_type_loops(nb)
    fix_markdown_hypothesis(nb)

    print()
    print("=" * 60)
    print("Saving patched notebook...")
    print("=" * 60)
    save_notebook(nb, NOTEBOOK_PATH)

    # Validate JSON
    print()
    print("Validating notebook JSON structure...")
    with open(NOTEBOOK_PATH, "r") as f:
        validated = json.load(f)
    print(f"✓ Valid JSON ({len(validated['cells'])} cells)")


if __name__ == "__main__":
    main()
