#!/usr/bin/env python3
"""
Patch D22-single-layer.ipynb to fix:
  1. ModelConfig doc_prefix/query_prefix values: search_document→document, search_query→query
  2. Stale comment referencing "search_query"
"""
import json
from pathlib import Path

NOTEBOOK_PATH = Path(__file__).parent / "D22-single-layer.ipynb"

def get_cell_source(cell):
    return "".join(cell.get("source", []))

def set_cell_source(cell, src):
    cell["source"] = src.splitlines(keepends=True)
    if cell["source"] and not cell["source"][-1].endswith("\n"):
        cell["source"][-1] += "\n"

def main():
    print(f"Loading: {NOTEBOOK_PATH}")
    with open(NOTEBOOK_PATH, "r") as f:
        nb = json.load(f)

    cells = nb["cells"]
    print(f"  Found {len(cells)} cells\n")

    fixes = 0

    for i, cell in enumerate(cells):
        if cell.get("cell_type") != "code":
            continue
        src = get_cell_source(cell)

        # Fix 1: ModelConfig doc_prefix/query_prefix in config cell
        if "ModelConfig" in src and 'doc_prefix="search_document"' in src:
            src = src.replace('doc_prefix="search_document"', 'doc_prefix="document"')
            src = src.replace('query_prefix="search_query"', 'query_prefix="query"')
            set_cell_source(cells[i], src)
            print(f"  ✓ Fix 1: Updated ModelConfig prefix values (cell {i})")
            fixes += 1

        # Fix 2: Stale comment
        if '# Nomic models: use "search_query" prompt' in src:
            src = src.replace(
                '# Nomic models: use "search_query" prompt',
                '# Nomic models: use "query" prompt'
            )
            set_cell_source(cells[i], src)
            print(f"  ✓ Fix 2: Updated stale comment (cell {i})")
            fixes += 1

    if fixes == 0:
        print("  ⚠ No changes needed — already fixed?")
    else:
        with open(NOTEBOOK_PATH, "w") as f:
            json.dump(nb, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"\n✓ Saved {fixes} fixes to {NOTEBOOK_PATH}")

if __name__ == "__main__":
    main()
