#!/usr/bin/env python3
"""
Patch D22-single-layer.ipynb to align dependency versions with D21-baseline.ipynb.

Changes:
  - chromadb==0.4.24 → chromadb>=1.0.0
  - sentence-transformers==2.2.2 → sentence-transformers>=3.0.0
  - Add missing packages: scikit-learn, matplotlib, seaborn, umap-learn,
    transformers, FlagEmbedding, tabulate
"""
import json
from pathlib import Path

NOTEBOOK_PATH = Path(__file__).parent / "D22-single-layer.ipynb"

# D21's exact dependency list
D21_PACKAGES = [
    '    "sentence-transformers>=3.0.0",      # Primary embedding model loader (v2-moe, v1.5)\\n',
    '    "chromadb>=1.0.0",                   # Vector database for retrieval evaluation\\n',
    '    "pyyaml>=6.0",                       # YAML parsing for corpus frontmatter\\n',
    '    "numpy>=1.24.0",                     # Numerical operations for embeddings\\n',
    '    "scipy>=1.10.0",                     # Scientific computing for distance metrics\\n',
    '    "scikit-learn>=1.3.0",               # Metrics (precision, recall, NDCG) and clustering\\n',
    '    "matplotlib>=3.7.0",                 # Plotting evaluation results\\n',
    '    "seaborn>=0.12.0",                   # Statistical visualization\\n',
    '    "umap-learn>=0.5.0",                 # Dimensionality reduction for embedding visualization\\n',
    '    "pandas>=2.0.0",                     # Data frames for results aggregation\\n',
    '    "tqdm>=4.65.0",                      # Progress bars for corpus loading\\n',
    '    "transformers>=4.30.0",              # Tokenizer utilities and model infrastructure\\n',
    '    "FlagEmbedding>=1.2.0",              # BGE-m3 model loader (alternative to sentence-transformers)\\n',
    '    "tabulate>=0.9.0",                    # Table formatting for results display\\n',
]


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

    fixed = False
    for i, cell in enumerate(cells):
        if cell.get("cell_type") != "code":
            continue
        src = get_cell_source(cell)

        if "packages = [" in src and "chromadb" in src and "subprocess" in src:
            # Replace the packages list
            lines = cell["source"]
            new_lines = []
            in_packages = False
            packages_done = False

            for line in lines:
                if "packages = [" in line and not packages_done:
                    new_lines.append(line)
                    new_lines.extend(D21_PACKAGES)
                    in_packages = True
                    continue

                if in_packages:
                    if "]" in line and "packages" not in line:
                        new_lines.append(line)
                        in_packages = False
                        packages_done = True
                    # Skip old package lines
                    continue

                new_lines.append(line)

            cell["source"] = new_lines
            fixed = True
            print(f"  ✓ Replaced dependency list in cell {i} with D21-aligned versions")
            break

    if not fixed:
        print("  ⚠ Could not find install cell — already fixed?")
    else:
        with open(NOTEBOOK_PATH, "w") as f:
            json.dump(nb, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"\n✓ Saved to {NOTEBOOK_PATH}")


if __name__ == "__main__":
    main()
