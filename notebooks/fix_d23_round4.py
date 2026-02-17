#!/usr/bin/env python3
"""
fix_d23_round4.py — Port D-21's exact chunking algorithm into D-23

Problem:
  D-23 Rounds 1-3 used a reimplemented chunker that omitted two critical
  features from D-21's chunk_document():
    1. min_chunk_tokens=128 with merge logic (short sections merged into previous)
    2. #{1,6} heading regex (D-23 used #{2,4})
  
  This caused 1,233 chunks vs D-21's 218 — a 5.7× inflation that confounded
  the experiment and invalidated comparisons.

Fix:
  Replace D-23 Cell 8 with D-21's exact chunking algorithm. The ONLY
  modification is subtracting prefix_reserve_tokens from the token budget
  so the enrichment prefix fits within max_chunk_tokens.

Usage:
  python3 fix_d23_round4.py
"""

import json
import os
import sys
from pathlib import Path

# ============================================================================
# PATHS
# ============================================================================

NOTEBOOK_PATH = Path("results/d23/round-2/D23_multi_layer_3.ipynb")
OUTPUT_DIR = Path("results/d23/round-4")
OUTPUT_PATH = OUTPUT_DIR / "D23_multi_layer_5.ipynb"

# ============================================================================
# THE REPLACEMENT CELL 8 — D-21's exact algorithm + prefix_reserve
# ============================================================================

CELL_8_SOURCE = r'''#!/usr/bin/env python3
"""
D-23 Cell 08: Hybrid Chunking Engine (Round 4 — D-21 Algorithm Port)

CRITICAL FIX (Round 4):
  Rounds 1-3 used a reimplemented chunker that omitted:
    1. min_chunk_tokens=128 merge logic → produced 1,233 tiny chunks
    2. #{1,6} heading regex (used #{2,4} instead)
  
  This cell now uses D-21 Cell 8's EXACT algorithm.
  The ONLY modification: prefix_reserve subtracted from token budget.

Ported from D-21 Cell 8:
  - split_into_sections(): #{1,6} heading regex
  - sliding_window_split(): overlapping windows for oversized sections
  - chunk_document(): min_chunk_tokens merge logic preserved
"""

import re
from typing import List, Tuple, Optional, Dict, Any

# ============================================================================
# CONSTANTS — Match D-21 exactly
# ============================================================================

MIN_CHUNK_TOKENS = 128  # D-21: config.min_chunk_tokens = 128
OVERLAP_TOKENS = 150    # D-21: config.overlap_tokens = 150

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Chunk:
    """A single text chunk with metadata."""
    chunk_id: str
    doc_filename: str
    section_heading: Optional[str]
    text: str
    token_count_approx: int
    metadata: Dict[str, Any]


# ============================================================================
# TOKEN ESTIMATION — Identical to D-21
# ============================================================================

def estimate_tokens(text: str) -> int:
    """Approximate token count using word_count * 1.3 heuristic.
    Identical to D-21 Cell 8."""
    if not text or not text.strip():
        return 0
    return max(1, int(len(text.split()) * 1.3))


# ============================================================================
# HEADING EXTRACTION — D-21's exact regex and logic
# ============================================================================

def split_into_sections(body: str) -> List[Tuple[str, str]]:
    """Split a markdown body into (heading, content) pairs.

    PORTED FROM D-21 CELL 8 — EXACT COPY.
    Splits on lines starting with # through ###### (levels 1-6).
    The first section may have heading="" if text precedes the first heading.
    """
    # D-21's exact regex: matches ALL heading levels 1-6
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


# ============================================================================
# SLIDING WINDOW — D-21's exact logic
# ============================================================================

def sliding_window_split(text: str, max_tokens: int, overlap_tokens: int) -> List[str]:
    """Split text into overlapping windows when it exceeds max_tokens.

    PORTED FROM D-21 CELL 8 — EXACT COPY.
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


# ============================================================================
# DOCUMENT CHUNKING — D-21's exact algorithm + prefix_reserve
# ============================================================================

def chunk_document(
    doc: LoreDocument,
    max_chunk_tokens: int,
    prefix_reserve: Optional[int] = None,
) -> List[Chunk]:
    """Chunk a document using D-21's hybrid heading + sliding-window approach.

    PORTED FROM D-21 CELL 8 with ONE modification:
      prefix_reserve is subtracted from the token budget so the
      enrichment prefix fits within max_chunk_tokens.

    D-21 behavior preserved:
      - split_into_sections() with #{1,6} heading regex
      - MIN_CHUNK_TOKENS=128 merge logic for short sections
      - sliding_window_split() for oversized sections
      - OVERLAP_TOKENS=150
    """
    if prefix_reserve is None:
        prefix_reserve = MODEL_CONFIG.prefix_reserve_tokens

    # The ONLY difference from D-21: subtract prefix_reserve from budget
    # D-21 effective_max = config.max_chunk_tokens (1024, full budget)
    # D-23 effective_max = max_chunk_tokens - prefix_reserve (1024 - 100 = 924)
    effective_max = max_chunk_tokens - prefix_reserve

    chunks = []
    chunk_counter = 0

    # Step 1: Split body into sections by markdown headings
    # D-21's split_into_sections: #{1,6} regex
    sections = split_into_sections(doc.body)

    for heading, content in sections:
        token_est = estimate_tokens(content)

        if token_est <= effective_max:
            # Section fits within limit — check if it meets minimum
            if token_est >= MIN_CHUNK_TOKENS:
                # Normal-sized section — create single chunk
                chunk_counter += 1
                chunks.append(Chunk(
                    chunk_id=f"{doc.filename}#chunk_{chunk_counter:03d}",
                    doc_filename=doc.filename,
                    section_heading=heading if heading else None,
                    text=content,
                    token_count_approx=token_est,
                    metadata=doc.metadata.copy() if hasattr(doc.metadata, 'copy') else dict(doc.metadata),
                ))
            else:
                # *** D-21's MERGE LOGIC — was missing in D-23 Rounds 1-3 ***
                # Section below MIN_CHUNK_TOKENS — merge with previous chunk
                if chunks:
                    prev = chunks[-1]
                    merged_text = prev.text + "\n\n" + content
                    merged_tokens = estimate_tokens(merged_text)
                    if merged_tokens <= effective_max:
                        # Merge into previous chunk
                        chunks[-1] = Chunk(
                            chunk_id=prev.chunk_id,
                            doc_filename=prev.doc_filename,
                            section_heading=prev.section_heading,
                            text=merged_text,
                            token_count_approx=merged_tokens,
                            metadata=prev.metadata.copy() if hasattr(prev.metadata, 'copy') else dict(prev.metadata),
                        )
                    else:
                        # Can't merge (would exceed budget) — keep as small chunk
                        chunk_counter += 1
                        chunks.append(Chunk(
                            chunk_id=f"{doc.filename}#chunk_{chunk_counter:03d}",
                            doc_filename=doc.filename,
                            section_heading=heading if heading else None,
                            text=content,
                            token_count_approx=token_est,
                            metadata=doc.metadata.copy() if hasattr(doc.metadata, 'copy') else dict(doc.metadata),
                        ))
                else:
                    # First chunk and it's small — keep it anyway
                    chunk_counter += 1
                    chunks.append(Chunk(
                        chunk_id=f"{doc.filename}#chunk_{chunk_counter:03d}",
                        doc_filename=doc.filename,
                        section_heading=heading if heading else None,
                        text=content,
                        token_count_approx=token_est,
                        metadata=doc.metadata.copy() if hasattr(doc.metadata, 'copy') else dict(doc.metadata),
                    ))
        else:
            # Section too large — apply sliding window (D-21's logic)
            sub_texts = sliding_window_split(
                content,
                effective_max,
                OVERLAP_TOKENS,
            )
            for sub_text in sub_texts:
                chunk_counter += 1
                chunks.append(Chunk(
                    chunk_id=f"{doc.filename}#chunk_{chunk_counter:03d}",
                    doc_filename=doc.filename,
                    section_heading=heading if heading else None,
                    text=sub_text,
                    token_count_approx=estimate_tokens(sub_text),
                    metadata=doc.metadata.copy() if hasattr(doc.metadata, 'copy') else dict(doc.metadata),
                ))

    # Edge case: document with no body at all (from D-21)
    if not chunks and doc.body.strip():
        chunks.append(Chunk(
            chunk_id=f"{doc.filename}#chunk_001",
            doc_filename=doc.filename,
            section_heading=None,
            text=doc.body.strip(),
            token_count_approx=estimate_tokens(doc.body),
            metadata=doc.metadata.copy() if hasattr(doc.metadata, 'copy') else dict(doc.metadata),
        ))

    return chunks


# ============================================================================
# CONFIGURATION SUMMARY
# ============================================================================

effective = MODEL_CONFIG.max_chunk_tokens - MODEL_CONFIG.prefix_reserve_tokens
print("=" * 70)
print("CHUNKING ENGINE — D-21 Algorithm Port (Round 4 Fix)")
print("=" * 70)
print(f"\n  Model:                {MODEL_CONFIG.name}")
print(f"  Max chunk tokens:     {MODEL_CONFIG.max_chunk_tokens}")
print(f"  Prefix reserve:       {MODEL_CONFIG.prefix_reserve_tokens} tokens")
print(f"  Effective for content:{effective} tokens")
print(f"  Min chunk tokens:     {MIN_CHUNK_TOKENS}  [D-21 match]")
print(f"  Overlap:              {OVERLAP_TOKENS} tokens  [D-21 match]")
print(f"  Heading regex:        #{{1,6}}  [D-21 match]")
print(f"  Token estimator:      word_count x 1.3  [D-21 match]")
print(f"  Merge logic:          ENABLED  [D-21 match — was MISSING in R1-R3]")
print(f"\n  [Round 4] D-21's exact chunking algorithm ported.")
print(f"  Only change: prefix_reserve ({MODEL_CONFIG.prefix_reserve_tokens} tokens) subtracted from budget.")
print(f"  Expected chunk count: ~200-250 (was 1,233 without merge logic)")
print("=" * 70)
'''


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("D-23 Round 4 Fix — Port D-21 Chunking Algorithm")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Step 1: Load the source notebook
    # ------------------------------------------------------------------
    if not NOTEBOOK_PATH.exists():
        print(f"\n✗ Source notebook not found: {NOTEBOOK_PATH}")
        sys.exit(1)

    with open(NOTEBOOK_PATH) as f:
        nb = json.load(f)

    print(f"\n[1] Loaded: {NOTEBOOK_PATH}")
    print(f"    Cells: {len(nb['cells'])}")

    # ------------------------------------------------------------------
    # Step 2: Find and verify Cell 8 (the chunking engine)
    # ------------------------------------------------------------------
    cell_8 = nb['cells'][8]
    old_source = ''.join(cell_8['source'])

    # Verify this IS the chunking cell
    checks = [
        ('chunk_document' in old_source, 'contains chunk_document'),
        ('estimate_tokens' in old_source, 'contains estimate_tokens'),
        ('Chunk' in old_source, 'contains Chunk dataclass'),
    ]

    print(f"\n[2] Verifying Cell 8 is the chunking engine:")
    for ok, label in checks:
        status = "✓" if ok else "✗"
        print(f"    {status} {label}")
        if not ok:
            print(f"\n✗ Cell 8 verification failed. Aborting.")
            sys.exit(1)

    # Show what we're replacing
    print(f"\n    Old Cell 8 characteristics:")
    if 'min_chunk_tokens' in old_source or 'MIN_CHUNK_TOKENS' in old_source:
        print(f"      - Has min_chunk_tokens: YES")
    else:
        print(f"      - Has min_chunk_tokens: NO  ← THIS IS THE BUG")

    if '#{1,6}' in old_source:
        print(f"      - Heading regex #{'{1,6}'}: YES")
    elif '#{2,4}' in old_source:
        print(f"      - Heading regex #{'{2,4}'}: NO (uses #{'{2,4}'})  ← DIFFERS FROM D-21")
    
    if 'merge' in old_source.lower() or 'merged' in old_source.lower():
        print(f"      - Merge logic: YES")
    else:
        print(f"      - Merge logic: NO  ← THIS IS THE BUG")

    # ------------------------------------------------------------------
    # Step 3: Replace Cell 8 with D-21's algorithm
    # ------------------------------------------------------------------
    new_source_lines = CELL_8_SOURCE.strip().split('\n')
    cell_8['source'] = [line + '\n' for line in new_source_lines[:-1]] + [new_source_lines[-1]]
    cell_8['outputs'] = []
    cell_8['execution_count'] = None

    print(f"\n[3] Replaced Cell 8:")
    print(f"    Old: {len(old_source)} chars")
    print(f"    New: {len(CELL_8_SOURCE.strip())} chars")

    # Verify the new source has all required features
    new_source = ''.join(cell_8['source'])
    required = [
        ('MIN_CHUNK_TOKENS = 128', 'min_chunk_tokens constant'),
        ('#{1,6}', 'D-21 heading regex'),
        ('merged_text = prev.text', 'merge logic'),
        ('sliding_window_split', 'sliding window function'),
        ('effective_max = max_chunk_tokens - prefix_reserve', 'prefix reserve'),
        ('OVERLAP_TOKENS = 150', 'overlap constant'),
        ('split_into_sections', 'D-21 section splitter'),
    ]

    print(f"\n    Verification of new Cell 8:")
    all_ok = True
    for pattern, label in required:
        found = pattern in new_source
        status = "✓" if found else "✗"
        print(f"      {status} {label}")
        if not found:
            all_ok = False

    if not all_ok:
        print(f"\n✗ New Cell 8 verification failed. Aborting.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 4: Clear all cell outputs (make it Colab-ready)
    # ------------------------------------------------------------------
    cleared = 0
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            if cell.get('outputs'):
                cell['outputs'] = []
                cleared += 1
            cell['execution_count'] = None

    print(f"\n[4] Cleared outputs from {cleared} cells")

    # ------------------------------------------------------------------
    # Step 5: Save the patched notebook
    # ------------------------------------------------------------------
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, 'w') as f:
        json.dump(nb, f, indent=1)

    size = os.path.getsize(OUTPUT_PATH)
    print(f"\n[5] Saved: {OUTPUT_PATH} ({size:,} bytes)")

    # ------------------------------------------------------------------
    # Step 6: Final verification — diff summary
    # ------------------------------------------------------------------
    print(f"\n{'=' * 70}")
    print("VERIFICATION SUMMARY")
    print(f"{'=' * 70}")

    with open(OUTPUT_PATH) as f:
        nb_verify = json.load(f)

    cell8_verify = ''.join(nb_verify['cells'][8]['source'])

    checks_final = [
        ('MIN_CHUNK_TOKENS = 128' in cell8_verify,
         'min_chunk_tokens = 128 (D-21 match)'),
        ('OVERLAP_TOKENS = 150' in cell8_verify,
         'overlap_tokens = 150 (D-21 match)'),
        ('#{1,6}' in cell8_verify,
         'Heading regex #{1,6} (D-21 match)'),
        ('merged_text = prev.text + "\\n\\n" + content' in cell8_verify,
         'Merge logic for short sections (D-21 match)'),
        ('token_est >= MIN_CHUNK_TOKENS' in cell8_verify,
         'Min-chunk threshold check (D-21 match)'),
        ('effective_max = max_chunk_tokens - prefix_reserve' in cell8_verify,
         'Prefix reserve subtraction (D-23 addition)'),
        ('sliding_window_split' in cell8_verify,
         'D-21 sliding_window_split function'),
        ('split_into_sections' in cell8_verify,
         'D-21 split_into_sections function'),
        (not any('#{2,4}' in line for line in cell8_verify.split('\n')
                 if 're.split' in line or 're.match' in line or "pattern" in line.lower() and "=" in line),
         'Old #{2,4} regex not in executable code'),
        ('fixed_window_split' not in cell8_verify,
         'Old fixed_window_split removed'),
        ('split_by_headings' not in cell8_verify,
         'Old split_by_headings removed'),
    ]

    passed = 0
    for ok, label in checks_final:
        status = "✓" if ok else "✗"
        print(f"  {status} {label}")
        if ok:
            passed += 1

    total = len(checks_final)
    print(f"\n  Result: {passed}/{total} checks passed")

    if passed == total:
        print(f"\n✓ ALL CHECKS PASSED")
        print(f"\n  Upload {OUTPUT_PATH} to Google Colab for Round 4.")
        print(f"\n  Expected changes:")
        print(f"    - Chunk count: ~200-250 (was 1,233)")
        print(f"    - Mean raw tokens/chunk: ~700-800 (was 134.7)")
        print(f"    - P@5 and R@10 should improve significantly")
        print(f"    - Controlled comparison with D-21/D-22 now valid")
    else:
        print(f"\n✗ {total - passed} checks FAILED. Review the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
