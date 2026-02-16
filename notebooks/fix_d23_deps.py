#!/usr/bin/env python3
"""
Patch D23-multi-layer.ipynb to align dependencies with D21-baseline.ipynb.

Changes:
  - Replace bare `!pip install -q ...` with versioned subprocess-based install
    matching D21's exact package list
  - Fix task_prefix_doc/task_prefix_query values (search_document→document, search_query→query)
"""
import json
from pathlib import Path

NOTEBOOK_PATH = Path(__file__).parent / "D23-multi-layer.ipynb"

# D21's exact install cell content (subprocess approach with version pins)
D21_INSTALL_LINES = [
    '#!/usr/bin/env python3\n',
    '"""\n',
    'D-23 Cell 02: Install Dependencies\n',
    '\n',
    'Installs all required packages for D-23 notebook execution.\n',
    'Same package set and versions as D-21 and D-22 for consistency.\n',
    '"""\n',
    '\n',
    'import subprocess\n',
    'import sys\n',
    '\n',
    'packages = [\n',
    '    "sentence-transformers>=3.0.0",      # Primary embedding model loader (v2-moe, v1.5)\n',
    '    "chromadb>=1.0.0",                   # Vector database for retrieval evaluation\n',
    '    "pyyaml>=6.0",                       # YAML parsing for corpus frontmatter\n',
    '    "numpy>=1.24.0",                     # Numerical operations for embeddings\n',
    '    "scipy>=1.10.0",                     # Scientific computing for distance metrics\n',
    '    "scikit-learn>=1.3.0",               # Metrics (precision, recall, NDCG) and clustering\n',
    '    "matplotlib>=3.7.0",                 # Plotting evaluation results\n',
    '    "seaborn>=0.12.0",                   # Statistical visualization\n',
    '    "umap-learn>=0.5.0",                 # Dimensionality reduction for embedding visualization\n',
    '    "pandas>=2.0.0",                     # Data frames for results aggregation\n',
    '    "tqdm>=4.65.0",                      # Progress bars for corpus loading\n',
    '    "transformers>=4.30.0",              # Tokenizer utilities and model infrastructure\n',
    '    "FlagEmbedding>=1.2.0",              # BGE-m3 model loader (alternative to sentence-transformers)\n',
    '    "tabulate>=0.9.0",                    # Table formatting for results display\n',
    ']\n',
    '\n',
    'for package in packages:\n',
    '    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package])\n',
    '\n',
    '# ============================================================================\n',
    '# VERSION VERIFICATION\n',
    '# ============================================================================\n',
    '\n',
    'print("✓ Dependency Installation Complete\\n")\n',
    'print("Package Version Check:")\n',
    'print("-" * 50)\n',
    '\n',
    'packages_to_check = [\n',
    "    'chromadb',\n",
    "    'sentence_transformers',\n",
    "    'torch',\n",
    "    'numpy',\n",
    "    'pandas',\n",
    "    'scipy',\n",
    "    'sklearn',\n",
    "    'matplotlib',\n",
    "    'seaborn',\n",
    "    'tqdm',\n",
    "    'yaml',\n",
    ']\n',
    '\n',
    'for package in packages_to_check:\n',
    '    try:\n',
    '        mod = __import__(package)\n',
    "        version = getattr(mod, '__version__', 'installed (no version attr)')\n",
    '        print(f"  {package:25} {version}")\n',
    '    except ImportError:\n',
    '        print(f"  {package:25} [IMPORT FAILED]")\n',
    '\n',
    'print("-" * 50)\n',
    'print("\\n✓ All critical dependencies installed and verified.")\n',
]


def get_cell_source(cell):
    return "".join(cell.get("source", []))


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

        # Fix 1: Replace bare pip install with versioned subprocess approach
        if "!pip install -q chromadb" in src and "packages_to_check" in src:
            cell["source"] = D21_INSTALL_LINES
            print(f"  ✓ Fix 1: Replaced install cell with D21-aligned versioned dependencies (cell {i})")
            fixes += 1

        # Fix 2: Fix task_prefix_doc/task_prefix_query values
        if "task_prefix_doc" in src and "search_document" in src:
            src = src.replace('task_prefix_doc="search_document: "', 'task_prefix_doc="document: "')
            src = src.replace('task_prefix_query="search_query: "', 'task_prefix_query="query: "')
            cell["source"] = src.splitlines(keepends=True)
            if cell["source"] and not cell["source"][-1].endswith("\n"):
                cell["source"][-1] += "\n"
            print(f"  ✓ Fix 2: Updated task_prefix_doc/query values (cell {i})")
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
