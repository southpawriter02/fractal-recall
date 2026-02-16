#!/usr/bin/env python3
"""
Fix the D23 install cell by writing each source line as a proper
separate element in the notebook JSON source array.
"""
import json
from pathlib import Path

NOTEBOOK_PATH = Path(__file__).parent / "D23-multi-layer.ipynb"

def main():
    print(f"Loading: {NOTEBOOK_PATH}")
    with open(NOTEBOOK_PATH, "r") as f:
        nb = json.load(f)

    cells = nb["cells"]

    # Find the install cell (cell index 1, the first code cell)
    for i, cell in enumerate(cells):
        if cell.get("cell_type") != "code":
            continue
        src_joined = "".join(cell.get("source", []))
        if "packages = [" in src_joined and "subprocess.check_call" in src_joined:
            print(f"  Found install cell at index {i}")
            print(f"  Current source has {len(cell['source'])} elements")

            # Build the correct source as individual lines
            new_source = [
                "#!/usr/bin/env python3\n",
                '"""\n',
                "D-23 Cell 02: Install Dependencies\n",
                "\n",
                "Installs all required packages for D-23 notebook execution.\n",
                "Same package set and versions as D-21 and D-22 for consistency.\n",
                '"""\n',
                "\n",
                "import subprocess\n",
                "import sys\n",
                "\n",
                "packages = [\n",
                '    "sentence-transformers>=3.0.0",\n',
                '    "chromadb>=1.0.0",\n',
                '    "pyyaml>=6.0",\n',
                '    "numpy>=1.24.0",\n',
                '    "scipy>=1.10.0",\n',
                '    "scikit-learn>=1.3.0",\n',
                '    "matplotlib>=3.7.0",\n',
                '    "seaborn>=0.12.0",\n',
                '    "umap-learn>=0.5.0",\n',
                '    "pandas>=2.0.0",\n',
                '    "tqdm>=4.65.0",\n',
                '    "transformers>=4.30.0",\n',
                '    "FlagEmbedding>=1.2.0",\n',
                '    "tabulate>=0.9.0",\n',
                "]\n",
                "\n",
                "print('Installing dependencies...')\n",
                "for package in packages:\n",
                '    subprocess.check_call(\n',
                '        [sys.executable, "-m", "pip", "install", "-q", package]\n',
                '    )\n',
                "\n",
                'print("\\n✓ Dependency Installation Complete\\n")\n',
                'print("Package Version Check:")\n',
                'print("-" * 50)\n',
                "\n",
                "packages_to_check = [\n",
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
                "]\n",
                "\n",
                "for package in packages_to_check:\n",
                "    try:\n",
                "        mod = __import__(package)\n",
                "        version = getattr(mod, '__version__', 'installed (no version attr)')\n",
                '        print(f"  {package:25} {version}")\n',
                "    except ImportError:\n",
                '        print(f"  {package:25} [IMPORT FAILED]")\n',
                "\n",
                'print("-" * 50)\n',
                'print("\\n✓ All critical dependencies installed and verified.")\n',
            ]

            cell["source"] = new_source
            print(f"  Replaced with {len(new_source)} clean elements")

            # Verify each element ends with \n
            for j, line in enumerate(new_source):
                if not line.endswith("\n"):
                    print(f"  WARNING: line {j} missing trailing newline: {repr(line)}")

            break
    else:
        print("  ✗ Could not find install cell!")
        return

    with open(NOTEBOOK_PATH, "w") as f:
        json.dump(nb, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"\n✓ Saved to {NOTEBOOK_PATH}")

    # Verify
    with open(NOTEBOOK_PATH, "r") as f:
        nb2 = json.load(f)
    cell2 = nb2["cells"][i]
    src2 = "".join(cell2["source"])
    print(f"\nVerification:")
    print(f"  Source elements: {len(cell2['source'])}")
    print(f"  Contains 'packages = [': {'packages = [' in src2}")
    print(f"  Contains 'chromadb': {'chromadb' in src2}")
    print(f"  Contains 'FlagEmbedding': {'FlagEmbedding' in src2}")


if __name__ == "__main__":
    main()
