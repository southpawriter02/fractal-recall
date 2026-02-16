#!/usr/bin/env python3
"""
Patch script for D21-baseline.ipynb
Fixes 6 identified bugs programmatically by editing notebook JSON cells.

Bugs fixed:
  1. Remove bogus `mean_reciprocal_rank` import from sklearn
  2. Add missing `chunk_document` function implementation
  3. Fix `config.embedding_model_name` → `config.model_id`
  4. Fix `GROUND_TRUTH_QUERIES` → `QUERIES.values()` / `list(QUERIES.values())`
  5. Add `tabulate` to install list
  6. Fix `encode_query` SentenceTransformer return indexing

Usage:
    python fix_d21.py
"""

import json
import copy
import sys
from pathlib import Path

NOTEBOOK_PATH = Path(__file__).parent / "D21-baseline.ipynb"
OUTPUT_PATH = Path(__file__).parent / "D21-baseline.ipynb"  # overwrite in-place


def load_notebook(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_notebook(nb: dict, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved: {path}")


def get_cell_source(cell: dict) -> str:
    """Join cell source lines into a single string."""
    return "".join(cell.get("source", []))


def set_cell_source(cell: dict, text: str):
    """Split text back into notebook source lines."""
    lines = text.split("\n")
    # Notebook format: each line ends with \n except the last
    cell["source"] = [line + "\n" for line in lines[:-1]]
    if lines:
        cell["source"].append(lines[-1])


def find_cell_containing(cells: list, snippet: str) -> int:
    """Find the index of the first code cell containing snippet."""
    for i, cell in enumerate(cells):
        if cell.get("cell_type") != "code":
            continue
        src = get_cell_source(cell)
        if snippet in src:
            return i
    return -1


# ============================================================================
# Bug 1: Remove mean_reciprocal_rank from sklearn import
# ============================================================================
def fix_bug1(cells: list) -> bool:
    idx = find_cell_containing(cells, "mean_reciprocal_rank, accuracy_score")
    if idx < 0:
        print("  ⚠ Bug 1: Could not find sklearn import cell — already fixed?")
        return False

    src = get_cell_source(cells[idx])
    src = src.replace(
        "from sklearn.metrics import (\n"
        "    precision_score, recall_score, ndcg_score,\n"
        "    mean_reciprocal_rank, accuracy_score\n"
        ")",
        "from sklearn.metrics import (\n"
        "    precision_score, recall_score, ndcg_score, accuracy_score\n"
        ")"
    )
    set_cell_source(cells[idx], src)
    print("  ✓ Bug 1: Removed bogus mean_reciprocal_rank from sklearn import")
    return True


# ============================================================================
# Bug 2: Add missing chunk_document function
# ============================================================================
CHUNK_DOCUMENT_CELL = {
    "cell_type": "code",
    "metadata": {},
    "source": [],
    "outputs": [],
    "execution_count": None,
}

CHUNK_DOCUMENT_SOURCE = '''\
"""
Hybrid Semantic + Fixed-Window Chunking Pipeline

Implements the chunk_document function referenced by the chunking loop.
Strategy (from R-02):
  1. Split document body on markdown headings (## ...)
  2. Estimate token count via words × 1.3
  3. If a section exceeds max_chunk_tokens, apply sliding-window splits
  4. Merge undersized trailing fragments below min_chunk_tokens
  5. Return list of Chunk objects

Reference: D-20 §2 (chunking strategy); R-02 (retrieval research)
"""

import re
from typing import List

def estimate_tokens(text: str) -> int:
    """Approximate token count using word_count × 1.3 heuristic."""
    return int(len(text.split()) * 1.3)

def split_into_sections(body: str) -> List[tuple]:
    """
    Split a markdown body into (heading, content) pairs.
    Splits on lines starting with ## (level-2 headings).
    The first section may have heading="" if text precedes the first heading.
    """
    # Split on markdown headings (## level)
    pattern = r'^(#{1,6}\s+.+)$'
    parts = re.split(pattern, body, flags=re.MULTILINE)

    sections = []
    current_heading = ""
    current_content = ""

    for part in parts:
        part_stripped = part.strip()
        if re.match(r'^#{1,6}\s+', part_stripped):
            # Save previous section if it has content
            if current_content.strip():
                sections.append((current_heading, current_content.strip()))
            current_heading = part_stripped
            current_content = ""
        else:
            current_content += part

    # Don't forget the last section
    if current_content.strip():
        sections.append((current_heading, current_content.strip()))

    # If no sections found, treat entire body as one section
    if not sections and body.strip():
        sections = [("", body.strip())]

    return sections

def sliding_window_split(text: str, max_tokens: int, overlap_tokens: int) -> List[str]:
    """
    Split text into overlapping windows when it exceeds max_tokens.
    Uses word-level splitting with token estimation.
    """
    words = text.split()
    # Convert token limits to approximate word counts
    max_words = int(max_tokens / 1.3)
    overlap_words = int(overlap_tokens / 1.3)
    step = max(1, max_words - overlap_words)

    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + max_words]
        chunks.append(" ".join(chunk_words))
        i += step
        if i + max_words >= len(words) and i < len(words):
            # Last chunk: take remaining words
            chunks.append(" ".join(words[i:]))
            break

    return chunks

def chunk_document(doc, config) -> List:
    """
    Chunk a single LoreDocument using hybrid semantic + fixed-window strategy.

    Args:
        doc: LoreDocument with .filename, .body, .metadata
        config: ModelConfig with chunking parameters

    Returns:
        List of Chunk objects
    """
    chunks = []
    chunk_counter = 0

    # Step 1: Split body into sections by markdown headings
    sections = split_into_sections(doc.body)

    for heading, content in sections:
        token_est = estimate_tokens(content)

        if token_est <= config.max_chunk_tokens:
            # Section fits within limit — create single chunk
            if token_est >= config.min_chunk_tokens:
                chunk_counter += 1
                chunks.append(Chunk(
                    chunk_id=f"{doc.filename}#chunk-{chunk_counter}",
                    doc_filename=doc.filename,
                    section_heading=heading,
                    text=content,
                    token_count_approx=token_est,
                    metadata=doc.metadata.copy(),
                ))
            else:
                # Too small — merge with previous chunk if possible
                if chunks:
                    prev = chunks[-1]
                    merged_text = prev.text + "\\n\\n" + content
                    merged_tokens = estimate_tokens(merged_text)
                    if merged_tokens <= config.max_chunk_tokens:
                        chunks[-1] = Chunk(
                            chunk_id=prev.chunk_id,
                            doc_filename=prev.doc_filename,
                            section_heading=prev.section_heading,
                            text=merged_text,
                            token_count_approx=merged_tokens,
                            metadata=prev.metadata.copy(),
                        )
                    else:
                        # Can't merge — keep as small chunk
                        chunk_counter += 1
                        chunks.append(Chunk(
                            chunk_id=f"{doc.filename}#chunk-{chunk_counter}",
                            doc_filename=doc.filename,
                            section_heading=heading,
                            text=content,
                            token_count_approx=token_est,
                            metadata=doc.metadata.copy(),
                        ))
                else:
                    # First chunk and it's small — keep it anyway
                    chunk_counter += 1
                    chunks.append(Chunk(
                        chunk_id=f"{doc.filename}#chunk-{chunk_counter}",
                        doc_filename=doc.filename,
                        section_heading=heading,
                        text=content,
                        token_count_approx=token_est,
                        metadata=doc.metadata.copy(),
                    ))
        else:
            # Section too large — apply sliding window
            sub_texts = sliding_window_split(
                content,
                config.max_chunk_tokens,
                config.overlap_tokens
            )
            for sub_text in sub_texts:
                chunk_counter += 1
                chunks.append(Chunk(
                    chunk_id=f"{doc.filename}#chunk-{chunk_counter}",
                    doc_filename=doc.filename,
                    section_heading=heading,
                    text=sub_text,
                    token_count_approx=estimate_tokens(sub_text),
                    metadata=doc.metadata.copy(),
                ))

    # Edge case: document with no body at all
    if not chunks and doc.body.strip():
        chunks.append(Chunk(
            chunk_id=f"{doc.filename}#chunk-1",
            doc_filename=doc.filename,
            section_heading="",
            text=doc.body.strip(),
            token_count_approx=estimate_tokens(doc.body),
            metadata=doc.metadata.copy(),
        ))

    return chunks

print("✓ chunk_document function defined")
'''


def fix_bug2(cells: list) -> bool:
    # Find the Chunk dataclass cell and insert chunk_document after it
    chunk_class_idx = find_cell_containing(cells, "class Chunk:")
    if chunk_class_idx < 0:
        print("  ⚠ Bug 2: Could not find Chunk class cell")
        return False

    # Check if chunk_document is already defined
    for cell in cells:
        if "def chunk_document(" in get_cell_source(cell):
            print("  ⚠ Bug 2: chunk_document already defined — skipping")
            return False

    new_cell = copy.deepcopy(CHUNK_DOCUMENT_CELL)
    set_cell_source(new_cell, CHUNK_DOCUMENT_SOURCE)

    # Insert after the Chunk class cell
    cells.insert(chunk_class_idx + 1, new_cell)
    print("  ✓ Bug 2: Inserted chunk_document function cell")
    return True


# ============================================================================
# Bug 3: config.embedding_model_name → config.model_id
# ============================================================================
def fix_bug3(cells: list) -> bool:
    idx = find_cell_containing(cells, "config.embedding_model_name")
    if idx < 0:
        print("  ⚠ Bug 3: Could not find embedding_model_name reference — already fixed?")
        return False

    src = get_cell_source(cells[idx])
    src = src.replace("config.embedding_model_name", "config.model_id")
    set_cell_source(cells[idx], src)
    print("  ✓ Bug 3: Fixed config.embedding_model_name → config.model_id")
    return True


# ============================================================================
# Bug 4: GROUND_TRUTH_QUERIES → QUERIES.values()
# ============================================================================
def fix_bug4(cells: list) -> bool:
    fixed = False

    for i, cell in enumerate(cells):
        if cell.get("cell_type") != "code":
            continue
        src = get_cell_source(cell)
        if "GROUND_TRUTH_QUERIES" not in src:
            continue

        # In the query execution loop: `for query in GROUND_TRUTH_QUERIES`
        src = src.replace(
            "for query in tqdm(\n        GROUND_TRUTH_QUERIES,",
            "for query in tqdm(\n        QUERIES.values(),"
        )

        # In compute_all_results function definition parameter
        src = src.replace(
            "def compute_all_results(all_results, GROUND_TRUTH_QUERIES, MODELS):",
            "def compute_all_results(all_results, ground_truth_queries, MODELS):"
        )

        # In docstring reference
        src = src.replace(
            "        GROUND_TRUTH_QUERIES: List[GroundTruthQuery]",
            "        ground_truth_queries: List[GroundTruthQuery]"
        )

        # In the zip inside compute_all_results
        src = src.replace(
            "for query, result in zip(GROUND_TRUTH_QUERIES, results):",
            "for query, result in zip(ground_truth_queries, results):"
        )

        # In the main execution call
        src = src.replace(
            "results_df = compute_all_results(all_results, GROUND_TRUTH_QUERIES, MODELS)",
            "results_df = compute_all_results(all_results, list(QUERIES.values()), MODELS)"
        )

        set_cell_source(cells[i], src)
        fixed = True

    if fixed:
        print("  ✓ Bug 4: Replaced GROUND_TRUTH_QUERIES with QUERIES.values()")
    else:
        print("  ⚠ Bug 4: Could not find GROUND_TRUTH_QUERIES references — already fixed?")
    return fixed


# ============================================================================
# Bug 5: Add tabulate to install list
# ============================================================================
def fix_bug5(cells: list) -> bool:
    idx = find_cell_containing(cells, "packages = [")
    if idx < 0:
        print("  ⚠ Bug 5: Could not find install cell")
        return False

    src = get_cell_source(cells[idx])
    if "tabulate" in src:
        print("  ⚠ Bug 5: tabulate already in install list — skipping")
        return False

    # Insert tabulate before the closing bracket of the packages list
    src = src.replace(
        '    "FlagEmbedding>=1.2.0",              # BGE-m3 model loader (alternative to sentence-transformers)\n]',
        '    "FlagEmbedding>=1.2.0",              # BGE-m3 model loader (alternative to sentence-transformers)\n'
        '    "tabulate>=0.9.0",                    # Table formatting for results display\n]'
    )
    set_cell_source(cells[idx], src)
    print("  ✓ Bug 5: Added tabulate to install list")
    return True


# ============================================================================
# Bug 6: Fix encode_query SentenceTransformer return indexing
# ============================================================================
def fix_bug6(cells: list) -> bool:
    idx = find_cell_containing(cells, 'prompt_name="search_query"')
    if idx < 0:
        print("  ⚠ Bug 6: Could not find encode_query cell")
        return False

    src = get_cell_source(cells[idx])
    old = (
        '        embedding = model.encode(\n'
        '            query_text,\n'
        '            prompt_name="search_query"\n'
        '        )[0]'
    )
    new = (
        '        embedding = model.encode(\n'
        '            query_text,\n'
        '            prompt_name="search_query"\n'
        '        )'
    )

    if old not in src:
        print("  ⚠ Bug 6: Could not find exact encode pattern — already fixed?")
        return False

    src = src.replace(old, new)
    set_cell_source(cells[idx], src)
    print("  ✓ Bug 6: Fixed encode_query return indexing (removed [0])")
    return True


# ============================================================================
# Bug 7: Add trust_remote_code=True to SentenceTransformer
# ============================================================================
def fix_bug7(cells: list) -> bool:
    idx = find_cell_containing(cells, "SentenceTransformer(config.model_id)")
    if idx < 0:
        print("  ⚠ Bug 7: Could not find SentenceTransformer loading — already fixed?")
        return False

    src = get_cell_source(cells[idx])
    src = src.replace(
        "SentenceTransformer(config.model_id)",
        "SentenceTransformer(config.model_id, trust_remote_code=True)"
    )
    set_cell_source(cells[idx], src)
    print("  ✓ Bug 7: Added trust_remote_code=True to SentenceTransformer")
    return True


# ============================================================================
# Bug 8: Fix prompt_name values for nomic models
# ============================================================================
def fix_bug8(cells: list) -> bool:
    """
    Nomic models register prompts as 'document' and 'query',
    not 'search_document' and 'search_query'.
    """
    fixed = False

    for i, cell in enumerate(cells):
        if cell.get("cell_type") != "code":
            continue
        src = get_cell_source(cell)
        if 'prompt_name=' not in src:
            continue

        new_src = src.replace(
            'prompt_name="search_document"',
            'prompt_name="document"'
        ).replace(
            'prompt_name="search_query"',
            'prompt_name="query"'
        )

        if new_src != src:
            set_cell_source(cells[i], new_src)
            fixed = True

    if fixed:
        print("  ✓ Bug 8: Fixed prompt_name values (search_document→document, search_query→query)")
    else:
        print("  ⚠ Bug 8: Could not find prompt_name references — already fixed?")
    return fixed


# ============================================================================
# Bug 9: ChromaDB client mismatch + UMAP empty-data crash
# ============================================================================
def fix_bug9(cells: list) -> bool:
    """
    The embedding cell uses chromadb.Client() (ephemeral/in-memory),
    but the visualization and export cells create new PersistentClient instances.
    Fix: Change embedding cell to PersistentClient and make downstream cells
    reuse the existing chroma_client variable.
    Also add a guard to the UMAP cell for empty data.
    """
    fixed = False

    # Fix 9a: Change chromadb.Client() to PersistentClient in embedding cell
    idx = find_cell_containing(cells, "chroma_client = chromadb.Client()")
    if idx >= 0:
        src = get_cell_source(cells[idx])
        src = src.replace(
            "chroma_client = chromadb.Client()",
            'chroma_client = chromadb.PersistentClient(path="./d21-chromadb")'
        )
        set_cell_source(cells[idx], src)
        print("  ✓ Bug 9a: Changed chromadb.Client() → PersistentClient")
        fixed = True

    # Fix 9b: In UMAP visualization cell, remove the standalone client creation
    # and add a guard for empty data
    for i, cell in enumerate(cells):
        if cell.get("cell_type") != "code":
            continue
        src = get_cell_source(cell)

        if "plot_embedding_space_by_model" in src and "chroma_client = chromadb.PersistentClient" in src:
            # This is the UMAP main execution cell - remove client creation,
            # reuse existing chroma_client
            src = src.replace(
                '    chroma_client = chromadb.PersistentClient(path="./d21-chromadb")\n'
                '    # Or: chroma_client = chromadb.EphemeralClient()\n\n',
                '    # chroma_client is already defined in the embedding cell\n\n'
            )
            src = src.replace("    import chromadb\n", "")
            set_cell_source(cells[i], src)
            print("  ✓ Bug 9b: UMAP cell now reuses existing chroma_client")
            fixed = True

        # Add empty-data guard in the UMAP function definition
        if "def plot_embedding_space_by_model" in src and "unique_types = sorted(all_entity_types)" in src:
            src = src.replace(
                '    unique_types = sorted(all_entity_types)\n',
                '    if not all_entity_types:\n'
                '        print("  ⚠ No embedding data found in any collection. Skipping visualization.")\n'
                '        return\n\n'
                '    unique_types = sorted(all_entity_types)\n'
            )
            set_cell_source(cells[i], src)
            print("  ✓ Bug 9c: Added empty-data guard to UMAP function")
            fixed = True

    # Fix 9d: In export cell, remove standalone client creation
    for i, cell in enumerate(cells):
        if cell.get("cell_type") != "code":
            continue
        src = get_cell_source(cell)
        if "export_results_to_csv" in src and "chroma_client = chromadb.PersistentClient" in src:
            src = src.replace(
                '    chroma_client = chromadb.PersistentClient(path="./d21-chromadb")\n',
                '    # chroma_client is already defined in the embedding cell\n'
            )
            src = src.replace("    import chromadb\n", "")
            set_cell_source(cells[i], src)
            print("  ✓ Bug 9d: Export cell now reuses existing chroma_client")
            fixed = True

    if not fixed:
        print("  ⚠ Bug 9: Could not find ChromaDB client patterns — already fixed?")
    return fixed


# ============================================================================
# Main
# ============================================================================
def main():
    print(f"Loading notebook: {NOTEBOOK_PATH}")
    nb = load_notebook(NOTEBOOK_PATH)
    cells = nb["cells"]
    print(f"  Found {len(cells)} cells\n")

    print("Applying fixes:")
    fix_bug1(cells)
    fix_bug2(cells)
    fix_bug3(cells)
    fix_bug4(cells)
    fix_bug5(cells)
    fix_bug6(cells)
    fix_bug7(cells)
    fix_bug8(cells)
    fix_bug9(cells)

    print(f"\nSaving patched notebook:")
    save_notebook(nb, OUTPUT_PATH)
    print(f"\n✓ All patches applied. Total cells: {len(cells)}")


if __name__ == "__main__":
    main()
