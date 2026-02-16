#!/usr/bin/env python3
"""
Generate d21_results.csv from the completed D21 notebook.

This script parses the executed D21 notebook (results/D21_baseline.ipynb)
to extract the CSV data that was embedded via a special output cell,
and writes it to d21-output/d21_results.csv where D22 expects it.

Usage:
    cd notebooks
    python generate_d21_csv.py

The D21 notebook must contain a cell with the marker:
    ===BEGIN_D21_RESULTS_CSV===
    ...csv data...
    ===END_D21_RESULTS_CSV===

If the marker is not found in the results notebook, it falls back to
looking in the working notebook (D21-baseline.ipynb) in case it was
run locally.
"""

import json
import os
import sys
from pathlib import Path


# Marker strings that bracket the CSV data in notebook output
CSV_START_MARKER = "===BEGIN_D21_RESULTS_CSV==="
CSV_END_MARKER = "===END_D21_RESULTS_CSV==="


def extract_csv_from_notebook(notebook_path: Path) -> str | None:
    """
    Parse a Jupyter notebook and extract CSV data between markers.

    Args:
        notebook_path: Path to the .ipynb file

    Returns:
        The CSV text if found, or None
    """
    if not notebook_path.exists():
        print(f"  ⚠ Notebook not found: {notebook_path}")
        return None

    with open(notebook_path, "r") as f:
        nb = json.load(f)

    # Search all cells for the CSV marker in outputs
    for i, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue

        for output in cell.get("outputs", []):
            # Check stream outputs (print statements)
            if output.get("output_type") == "stream":
                text = "".join(output.get("text", []))
                if CSV_START_MARKER in text:
                    # Extract between markers
                    start_idx = text.index(CSV_START_MARKER) + len(CSV_START_MARKER)
                    end_idx = text.index(CSV_END_MARKER)
                    csv_text = text[start_idx:end_idx].strip()
                    print(f"  ✓ Found CSV data in cell {i} (stream output)")
                    return csv_text

            # Check execute_result outputs
            if output.get("output_type") == "execute_result":
                text = "".join(output.get("data", {}).get("text/plain", []))
                if CSV_START_MARKER in text:
                    start_idx = text.index(CSV_START_MARKER) + len(CSV_START_MARKER)
                    end_idx = text.index(CSV_END_MARKER)
                    csv_text = text[start_idx:end_idx].strip()
                    print(f"  ✓ Found CSV data in cell {i} (execute_result)")
                    return csv_text

    print(f"  ⚠ CSV markers not found in {notebook_path}")
    return None


def main():
    print("=" * 70)
    print("D-21 Results CSV Generator")
    print("=" * 70)
    print()

    # Define paths relative to the notebooks/ directory
    script_dir = Path(__file__).parent
    output_dir = script_dir / "d21-output"
    output_csv = output_dir / "d21_results.csv"

    # Look for the CSV data in the results notebook first, then the working notebook
    notebooks_to_try = [
        script_dir / "results" / "D21_baseline.ipynb",
        script_dir / "D21-baseline.ipynb",
    ]

    csv_data = None
    for nb_path in notebooks_to_try:
        print(f"Searching: {nb_path}")
        csv_data = extract_csv_from_notebook(nb_path)
        if csv_data:
            break

    if csv_data is None:
        print()
        print("⚠ Could not extract D21 results CSV.")
        print()
        print("The D21 notebook must be run with the CSV-embedding cell")
        print("(the cell containing 'BEGIN_D21_RESULTS_CSV') before this")
        print("script can extract the data.")
        print()
        print("Steps to fix:")
        print("  1. Open D21-baseline.ipynb in Colab")
        print("  2. Run all cells (including the new CSV-embedding cell)")
        print("  3. Download the executed notebook to results/D21_baseline.ipynb")
        print("  4. Re-run this script")
        sys.exit(1)

    # Create output directory and write CSV
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_csv, "w") as f:
        f.write(csv_data)
        f.write("\n")  # Ensure trailing newline

    # Validate the CSV
    line_count = len(csv_data.strip().split("\n"))
    header = csv_data.strip().split("\n")[0]

    print()
    print(f"✓ Wrote {output_csv}")
    print(f"  Rows: {line_count - 1} (excluding header)")
    print(f"  Header: {header}")
    print()
    print("D22 can now load this file for delta analysis.")


if __name__ == "__main__":
    main()
