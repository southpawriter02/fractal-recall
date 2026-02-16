#!/usr/bin/env python3
"""
Fix script 2: Restore the imports/config cell that was accidentally overwritten,
and add ModelConfig fields (loader, doc_prefix, query_prefix) + D21_MODEL_NAMES.
"""

import json

NOTEBOOK_PATH = "D22-single-layer.ipynb"

def load_notebook(path):
    with open(path, "r") as f:
        return json.load(f)

def save_notebook(nb, path):
    with open(path, "w") as f:
        json.dump(nb, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved patched notebook to {path}")

def set_cell_source(cell, text):
    lines = text.split("\n")
    cell["source"] = [line + "\n" for line in lines[:-1]]
    if lines[-1]:
        cell["source"].append(lines[-1])

# The imports/config cell that was lost — restored with all fixes applied
IMPORTS_CONFIG_SOURCE = '''#!/usr/bin/env python3
"""
D-22: Imports, Configuration & Model Setup

Shared imports, path constants, and embedding model configuration.
This cell must run before all other code cells.

Reference: D-21 Cell 03 (imports); D-21 Cell 04 (model registry)
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import math
import re

import chromadb
from chromadb.config import Settings
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from scipy.stats import wilcoxon
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore")

# ======================================================================
# CONFIGURATION CONSTANTS
# ======================================================================

# Model selection: UPDATE THIS AFTER RUNNING D-21
# Set to the model key that won D-21's weighted comparison.
# Options: "v2-moe", "v1.5", "bge-m3"
# Default: "v1.5" (placeholder — update with actual D-21 winner)
SELECTED_MODEL = "v1.5"

# Paths (relative to notebook directory, matching D-21 conventions)
CORPUS_DIR = Path("./test-corpus")  # Same as D-21
OUTPUT_DIR = Path("./d22-output")  # Parallel to d21-output
CHROMADB_DIR = OUTPUT_DIR / "chromadb"
D21_RESULTS_PATH = Path("./d21-output/d21_results.csv")  # D-21 export location

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHROMADB_DIR.mkdir(parents=True, exist_ok=True)

# Model configurations (reused from D-21; see R-01, R-02, R-03)
# Field mapping to D-21:
#   max_tokens <-> context_window
#   expected_dim <-> embedding_dim
#   max_chunk_tokens <-> max_chunk_tokens (same)
#   loader: "sentence_transformers" or "flag_embedding"
#   doc_prefix / query_prefix: model-specific prompt names

@dataclass
class ModelConfig:
    """Model-specific configuration for embedding and chunking.

    Field mapping to D-21:
        max_tokens -> context_window
        expected_dim -> embedding_dim
        max_chunk_tokens -> max_chunk_tokens (same)
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
    query_prefix: str = ""  # Model-specific query prefix

# Mapping from SELECTED_MODEL key -> D-21 CSV 'model' column value
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
    ),
    "v1.5": ModelConfig(
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
    ),
    "bge-m3": ModelConfig(
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
    ),
}

MODEL_CONFIG = MODEL_CONFIGS[SELECTED_MODEL]

print(f"D-22 Configuration:")
print(f"  Selected model: {SELECTED_MODEL}")
print(f"  Model name: {MODEL_CONFIG.name}")
print(f"  Model ID: {MODEL_CONFIG.model_id}")
print(f"  Loader: {MODEL_CONFIG.loader}")
print(f"  Context window: {MODEL_CONFIG.max_tokens} tokens")
print(f"  Embedding dim: {MODEL_CONFIG.expected_dim}")
print(f"  Max chunk tokens: {MODEL_CONFIG.max_chunk_tokens}")
print(f"  Prefix reserve: {MODEL_CONFIG.prefix_reserve_tokens}")
print()
print(f"  Corpus: {CORPUS_DIR}")
print(f"  Output: {OUTPUT_DIR}")
print(f"  D-21 baseline: {D21_RESULTS_PATH}")
print(f"  D-21 model name: {D21_MODEL_NAMES.get(SELECTED_MODEL, 'N/A')}")
'''

def main():
    print("Loading notebook...")
    nb = load_notebook(NOTEBOOK_PATH)
    print(f"  {len(nb['cells'])} cells loaded")

    # The queries cell is currently at index 2 (after markdown title and install cell)
    # We need to insert the imports/config cell BEFORE it (at index 2)
    # This will push the queries cell to index 3

    new_cell = {
        "cell_type": "code",
        "metadata": {},
        "source": [],
        "outputs": [],
        "execution_count": None,
    }
    set_cell_source(new_cell, IMPORTS_CONFIG_SOURCE)

    # Insert at position 2 (after markdown + install cells)
    nb["cells"].insert(2, new_cell)

    print(f"✓ Inserted imports/config cell at index 2")
    print(f"  Total cells: {len(nb['cells'])}")

    save_notebook(nb, NOTEBOOK_PATH)

    # Validate
    print()
    print("Validating notebook JSON structure...")
    with open(NOTEBOOK_PATH, "r") as f:
        validated = json.load(f)
    print(f"✓ Valid JSON ({len(validated['cells'])} cells)")

    # Print cell summary
    print()
    for i, cell in enumerate(validated["cells"][:6]):
        src = "".join(cell["source"])[:100]
        print(f"  Cell {i} ({cell['cell_type']}): {src[:80]}...")


if __name__ == "__main__":
    main()
