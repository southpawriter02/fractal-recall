#!/usr/bin/env python3
"""
Patch D21 notebook: Add a CSV-embedding cell that prints results_df
as CSV to the notebook output, making it recoverable by generate_d21_csv.py.

Usage:
    cd notebooks
    python patch_d21_csv_cell.py
"""

import json
import sys
from pathlib import Path


NOTEBOOK_PATH = "D21-baseline.ipynb"

# The new cell source that embeds CSV data in notebook output
NEW_CELL_SOURCE = '''#!/usr/bin/env python3
"""
D-21: Embed Results CSV in Notebook Output

This cell prints the full results_df as CSV text between special markers.
This allows the generate_d21_csv.py script to extract the CSV data from
the executed notebook, even if the d21-output/ directory is not available
(e.g., when running on Colab and only downloading the notebook).

Reference: D-22 loads d21-output/d21_results.csv for delta analysis.
"""

if 'results_df' in globals() and results_df is not None and not results_df.empty:
    print("===BEGIN_D21_RESULTS_CSV===")
    print(results_df.to_csv(index=False), end="")
    print("===END_D21_RESULTS_CSV===")
    print()
    print(f"✓ Embedded {len(results_df)} rows of results CSV in notebook output")
    print(f"  Run generate_d21_csv.py to extract this data to d21-output/d21_results.csv")
else:
    print("⚠ results_df not available. Cannot embed CSV data.")
    print("  Ensure the metrics computation cells have been run first.")
'''


def main():
    print(f"Loading {NOTEBOOK_PATH}...")
    with open(NOTEBOOK_PATH, "r") as f:
        nb = json.load(f)

    print(f"  {len(nb['cells'])} cells loaded")

    # Find the export cell (contains "export_results_to_csv" and "MAIN EXECUTION")
    export_cell_idx = None
    for i, cell in enumerate(nb["cells"]):
        src = "".join(cell.get("source", []))
        if "export_results_to_csv(results_df, OUTPUT_DIR)" in src and "MAIN EXECUTION" in src:
            export_cell_idx = i
            break

    if export_cell_idx is None:
        print("⚠ Could not find the export cell in the notebook.")
        print("  Looking for a cell containing 'export_results_to_csv(results_df, OUTPUT_DIR)' and 'MAIN EXECUTION'")
        sys.exit(1)

    print(f"  Found export cell at index {export_cell_idx}")

    # Check if the CSV-embedding cell already exists
    for cell in nb["cells"]:
        src = "".join(cell.get("source", []))
        if "===BEGIN_D21_RESULTS_CSV===" in src:
            print("  ✓ CSV-embedding cell already exists. No changes needed.")
            return

    # Create the new cell
    lines = NEW_CELL_SOURCE.split("\n")
    new_cell = {
        "cell_type": "code",
        "metadata": {},
        "source": [line + "\n" for line in lines[:-1]],
        "outputs": [],
        "execution_count": None,
    }
    # Last line without trailing newline
    if lines[-1]:
        new_cell["source"].append(lines[-1])

    # Insert after the export cell
    insert_idx = export_cell_idx + 1
    nb["cells"].insert(insert_idx, new_cell)

    print(f"  ✓ Inserted CSV-embedding cell at index {insert_idx}")
    print(f"  Total cells: {len(nb['cells'])}")

    # Save
    with open(NOTEBOOK_PATH, "w") as f:
        json.dump(nb, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved patched notebook to {NOTEBOOK_PATH}")

    # Validate
    with open(NOTEBOOK_PATH, "r") as f:
        validated = json.load(f)
    print(f"✓ Valid JSON ({len(validated['cells'])} cells)")


if __name__ == "__main__":
    main()
