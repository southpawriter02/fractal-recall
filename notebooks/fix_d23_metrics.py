#!/usr/bin/env python3
"""
Fix D-23 Metric Computation Bug — Chunk ID → Document Filename Mismatch

Problem:
  compute_all_metrics() compares chunk IDs (e.g., "000-codex_echo-cant.md#chunk_002")
  against document filenames (e.g., "000-codex_echo-cant.md"). They never match because
  of the "#chunk_NNN" suffix, causing all metrics to return 0.0.

Fix:
  In compute_all_metrics(), normalize retrieved chunk IDs to document filenames by
  stripping the "#chunk_NNN" suffix using .split("#")[0].

Target: results/d23/D23_multi_layer-2.ipynb (post-run notebook with runtime fixes)
"""

import json
import sys
from pathlib import Path

NOTEBOOK = Path("results/d23/D23_multi_layer-2.ipynb")


def main():
    if not NOTEBOOK.exists():
        print(f"✗ Notebook not found: {NOTEBOOK}")
        sys.exit(1)

    nb = json.load(NOTEBOOK.open())
    cells = nb["cells"]
    fixes_applied = 0

    # ── Find the cell containing compute_all_metrics ──
    target_cell = None
    target_idx = None
    for i, cell in enumerate(cells):
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell.get("source", []))
        if "def compute_all_metrics" in src:
            target_cell = cell
            target_idx = i
            break

    if target_cell is None:
        print("✗ Could not find cell with compute_all_metrics")
        sys.exit(1)

    src = "".join(target_cell.get("source", []))
    print(f"Found compute_all_metrics in Cell {target_idx}")

    # ── Fix 1: Normalize chunk IDs to document filenames ──
    old_retrieved = 'retrieved = [r["chunk_id"] for r in qr.results]'
    new_retrieved = 'retrieved = [r["chunk_id"].split("#")[0] for r in qr.results]'

    if old_retrieved in src:
        src = src.replace(old_retrieved, new_retrieved)
        fixes_applied += 1
        print(f"  ✓ Fix 1: Added .split('#')[0] to retrieved chunk ID extraction")
    elif new_retrieved in src:
        print(f"  ○ Fix 1: Already applied (retrieved IDs already normalized)")
    else:
        print(f"  ✗ Fix 1: Could not find expected pattern for retrieved IDs")
        print(f"    Expected: {old_retrieved}")
        # Search for any similar pattern
        for line in src.split("\n"):
            if "retrieved" in line and "chunk_id" in line:
                print(f"    Found:    {line.strip()}")
        sys.exit(1)

    # ── Fix 2: Normalize chunk IDs for NDCG relevance_scores lookup ──
    # The ndcg_at_k function uses relevance_scores.get(chunk_id, 0) internally.
    # Since relevance_scores keys are document filenames, we need to normalize
    # the retrieved IDs BEFORE passing them to ndcg_at_k.
    # 
    # Fix 1 already handles this because the `retrieved` list (now normalized)
    # is passed to all four metric functions including ndcg_at_k.
    print(f"  ✓ Fix 2: NDCG relevance lookup also fixed (uses same normalized list)")

    # ── Write back ──
    lines = src.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    target_cell["source"] = lines

    with NOTEBOOK.open("w") as f:
        json.dump(nb, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"\n{'='*60}")
    print(f"  {fixes_applied} fix(es) applied to {NOTEBOOK}")
    print(f"  Cell {target_idx}: compute_all_metrics")
    print(f"{'='*60}")

    # ── Verify ──
    nb2 = json.load(NOTEBOOK.open())
    verify_src = "".join(nb2["cells"][target_idx].get("source", []))
    if new_retrieved in verify_src:
        print(f"\n✓ Verification passed — .split('#')[0] present in compute_all_metrics")
    else:
        print(f"\n✗ Verification FAILED — fix not found in saved file")
        sys.exit(1)

    if old_retrieved in verify_src:
        print(f"✗ Verification FAILED — old pattern still present")
        sys.exit(1)

    print(f"\n✓ Ready to re-run in Colab.")
    print(f"  Only Cell {target_idx} (metric computation) and downstream cells need re-execution.")
    print(f"  Cells 0–{target_idx - 1} (deps, chunking, embedding, queries) can be skipped.")


if __name__ == "__main__":
    main()
