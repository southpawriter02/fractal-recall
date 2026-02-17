#!/usr/bin/env python3
"""
create_d24_ablation_part2.py — Patch cells 11-21 for D-24 ablation

Operates on the D24_ablation.ipynb produced by create_d24_ablation.py.
Replaces embedding, query, analysis, visualization, and export cells
to support the 5-config ablation pipeline.

Usage:
    python3 create_d24_ablation.py         # Part 1: cells 0,1,9,10
    python3 create_d24_ablation_part2.py   # Part 2: cells 11-21
"""

import json
import os
import sys
from pathlib import Path

NOTEBOOK_PATH = Path("results/d24/D24_ablation.ipynb")

def load_notebook(path):
    with open(path) as f:
        return json.load(f)

def save_notebook(nb, path):
    with open(path, 'w') as f:
        json.dump(nb, f, indent=1)

def make_code_cell(source):
    lines = source.strip().split('\n')
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + '\n' for line in lines[:-1]] + [lines[-1]]
    }

def make_markdown_cell(source):
    lines = source.strip().split('\n')
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + '\n' for line in lines[:-1]] + [lines[-1]]
    }


# ============================================================================
# CELL 11: PER-CONFIG EMBEDDING & INDEXING
# ============================================================================

CELL_11_SOURCE = r'''#!/usr/bin/env python3
"""
D-24 Cell 11: Per-Config Embedding & ChromaDB Indexing

Creates one ChromaDB collection per ablation config. Embeds all enriched
chunks and indexes them using the same pipeline as D-23 Cell 11.

Collections: d24_raw, d24_domain_entity, d24_de_authority, d24_de_section, d24_de_relationships
"""

import chromadb

client = chromadb.Client()
ablation_collections: Dict[str, Any] = {}

print("=" * 80)
print("D-24 PER-CONFIG EMBEDDING & INDEXING")
print("=" * 80)

for config_name in ABLATION_CONFIG_ORDER:
    enriched_chunks = ablation_results[config_name]["enriched_chunks"]

    collection_name = f"d24_{config_name}"
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    print(f"\n  [{config_name}] Embedding {len(enriched_chunks)} chunks...")

    # Batch encode
    texts = [c.text for c in enriched_chunks]
    embeddings = model.encode(texts, prompt_name="search_document", batch_size=64, show_progress_bar=True)

    # Index in ChromaDB
    ids = [c.chunk_id for c in enriched_chunks]
    metadatas = [{"doc_filename": c.doc_filename, "section": c.section_heading or ""} for c in enriched_chunks]

    collection.add(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=metadatas,
    )

    ablation_collections[config_name] = collection
    print(f"  ✓ {collection_name}: {collection.count()} vectors indexed")

print(f"\n{'=' * 80}")
print(f"✓ {len(ablation_collections)} collections created")
for name, col in ablation_collections.items():
    print(f"  {name:20s}: {col.count()} vectors")
print(f"{'=' * 80}")
'''


# ============================================================================
# CELL 12: PER-CONFIG QUERY EXECUTION
# ============================================================================

CELL_12_SOURCE = r'''#!/usr/bin/env python3
"""
D-24 Cell 12: Per-Config Query Execution

Runs all 36 ground-truth queries against each ablation config's collection.
Stores results in ablation_query_results dict.
"""

ablation_query_results: Dict[str, Dict[str, Dict]] = {}

print("=" * 80)
print("D-24 PER-CONFIG QUERY EXECUTION")
print("=" * 80)

for config_name in ABLATION_CONFIG_ORDER:
    collection = ablation_collections[config_name]
    config_results: Dict[str, Dict] = {}

    print(f"\n  [{config_name}] Querying {len(GROUND_TRUTH)} queries against {collection.count()} vectors...")

    for query_id, query_info in GROUND_TRUTH.items():
        query_text = query_info["query"]

        # Encode query
        query_embedding = model.encode(query_text, prompt_name="search_query")

        # Retrieve top-10
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=10,
            include=["distances", "documents", "metadatas"],
        )

        # Extract document filenames from chunk IDs
        retrieved_ids = results["ids"][0]
        retrieved_docs = [rid.split("#")[0] for rid in retrieved_ids]
        distances = results["distances"][0]

        config_results[query_id] = {
            "query_type": query_info["type"],
            "retrieved_ids": retrieved_ids,
            "retrieved_docs": retrieved_docs,
            "distances": distances,
            "relevant_docs": query_info["relevant"],
        }

    ablation_query_results[config_name] = config_results
    print(f"  ✓ {config_name}: {len(config_results)} queries executed")

print(f"\n✓ All queries complete across {len(ablation_query_results)} configs")
'''


# ============================================================================
# CELL 13: MARKDOWN (keep as-is but update text)
# ============================================================================

CELL_13_SOURCE = r'''## D-24 Results: Ablation Comparison Analysis

All 36 ground-truth queries have been executed against each of the 5 ablation
configurations. The following cells compute metrics, deltas, statistical
significance, and visualizations to determine which layers contribute most
to retrieval improvement.'''


# ============================================================================
# CELL 15: PER-CONFIG METRIC COMPUTATION
# ============================================================================

CELL_15_SOURCE = r'''#!/usr/bin/env python3
"""
D-24 Cell 15: Per-Config Metric Computation & Baseline Loading

Computes P@5, R@10, NDCG@10, MRR for each ablation config.
Loads D-21 and D-22 results for cross-experiment comparison.

Outputs:
  - ablation_metrics: Dict[config_name, pd.DataFrame] — per-query metrics
  - d21_results_df, d22_results_df — prior experiment data
"""

# ============================================================================
# COMPUTE D-24 METRICS PER CONFIG
# ============================================================================

ablation_metrics: Dict[str, pd.DataFrame] = {}

for config_name in ABLATION_CONFIG_ORDER:
    config_results = ablation_query_results[config_name]
    rows = []

    for query_id, qr in config_results.items():
        relevant = set(qr["relevant_docs"])
        retrieved = qr["retrieved_docs"]

        p5 = precision_at_k(relevant, retrieved, k=5)
        r10 = recall_at_k(relevant, retrieved, k=10)
        ndcg = ndcg_at_k(relevant, retrieved, k=10)
        mrr_val = mrr(relevant, retrieved)

        rows.append({
            "config": config_name,
            "query_id": query_id,
            "query_type": qr["query_type"],
            "precision@5": p5,
            "recall@10": r10,
            "ndcg@10": ndcg,
            "mrr": mrr_val,
        })

    df = pd.DataFrame(rows)
    ablation_metrics[config_name] = df
    means = df[["precision@5", "recall@10", "ndcg@10", "mrr"]].mean()
    print(f"  {config_name:20s}: P@5={means['precision@5']:.4f}  R@10={means['recall@10']:.4f}  "
          f"NDCG={means['ndcg@10']:.4f}  MRR={means['mrr']:.4f}")

# ============================================================================
# LOAD D-21 AND D-22 BASELINES
# ============================================================================

print(f"\nLoading prior experiment results...")

d21_results_path = Path("d21-output/d21_results.csv")
d22_results_path = Path("d22-output/d22_results.csv")

d21_available = d21_results_path.exists()
d22_available = d22_results_path.exists()

if d21_available:
    d21_results_df = pd.read_csv(d21_results_path)
    print(f"  ✓ D-21: {len(d21_results_df)} rows loaded")
else:
    print(f"  ✗ D-21 baseline not found at {d21_results_path}")
    d21_results_df = None

if d22_available:
    d22_results_df = pd.read_csv(d22_results_path)
    print(f"  ✓ D-22: {len(d22_results_df)} rows loaded")
else:
    print(f"  ✗ D-22 single-layer not found at {d22_results_path}")
    d22_results_df = None

# ============================================================================
# SUMMARY TABLE
# ============================================================================

print(f"\n{'=' * 80}")
print("OVERALL METRICS SUMMARY")
print(f"{'=' * 80}")
print(f"\n  {'Config':20s} {'P@5':>8s} {'R@10':>8s} {'NDCG@10':>8s} {'MRR':>8s}")
print(f"  {'─'*20} {'─'*8} {'─'*8} {'─'*8} {'─'*8}")

if d21_available:
    d21_v15 = d21_results_df[d21_results_df["model"] == "v1.5"]
    d21_means = d21_v15[["precision@5", "recall@10", "ndcg@10", "mrr"]].mean()
    print(f"  {'D-21 (baseline)':20s} {d21_means['precision@5']:>8.4f} {d21_means['recall@10']:>8.4f} "
          f"{d21_means['ndcg@10']:>8.4f} {d21_means['mrr']:>8.4f}")

if d22_available:
    d22_means = d22_results_df[["precision@5", "recall@10", "ndcg@10", "mrr"]].mean()
    print(f"  {'D-22 (single-layer)':20s} {d22_means['precision@5']:>8.4f} {d22_means['recall@10']:>8.4f} "
          f"{d22_means['ndcg@10']:>8.4f} {d22_means['mrr']:>8.4f}")

print(f"  {'─'*20} {'─'*8} {'─'*8} {'─'*8} {'─'*8}")

for config_name in ABLATION_CONFIG_ORDER:
    df = ablation_metrics[config_name]
    means = df[["precision@5", "recall@10", "ndcg@10", "mrr"]].mean()
    print(f"  {config_name:20s} {means['precision@5']:>8.4f} {means['recall@10']:>8.4f} "
          f"{means['ndcg@10']:>8.4f} {means['mrr']:>8.4f}")
'''


# ============================================================================
# CELL 16: DELTA ANALYSIS
# ============================================================================

CELL_16_SOURCE = r'''#!/usr/bin/env python3
"""
D-24 Cell 16: Ablation Delta Analysis

Computes per-query metric deltas for:
  1. Each config vs D-21 baseline
  2. Each config vs D-22 single-layer
  3. Each config vs Config A (raw — internal control)
  4. Marginal contribution of each added layer (C-B, D-B, E-B)

Outputs:
  - delta_vs_d21: Dict[config, pd.DataFrame]
  - delta_vs_d22: Dict[config, pd.DataFrame]
  - delta_vs_raw: Dict[config, pd.DataFrame]
  - marginal_contributions: pd.DataFrame
"""

METRICS = ["precision@5", "recall@10", "ndcg@10", "mrr"]

# ============================================================================
# DELTAS VS D-21
# ============================================================================

delta_vs_d21: Dict[str, pd.DataFrame] = {}

if d21_available:
    d21_v15 = d21_results_df[d21_results_df["model"] == "v1.5"].copy()
    print("DELTAS VS D-21 (BASELINE)")
    print("-" * 60)

    for config_name in ABLATION_CONFIG_ORDER:
        cfg_df = ablation_metrics[config_name]

        merged = cfg_df.merge(d21_v15, on="query_id", suffixes=("_d24", "_d21"))
        for m in METRICS:
            merged[f"delta_{m}"] = merged[f"{m}_d24"] - merged[f"{m}_d21"]

        delta_vs_d21[config_name] = merged
        means = merged[[f"delta_{m}" for m in METRICS]].mean()
        print(f"  {config_name:20s}: " + "  ".join(f"Δ{m.split('@')[0]}={means[f'delta_{m}']:+.4f}" for m in METRICS))

# ============================================================================
# DELTAS VS D-22
# ============================================================================

delta_vs_d22: Dict[str, pd.DataFrame] = {}

if d22_available:
    print(f"\nDELTAS VS D-22 (SINGLE-LAYER)")
    print("-" * 60)

    for config_name in ABLATION_CONFIG_ORDER:
        cfg_df = ablation_metrics[config_name]

        merged = cfg_df.merge(d22_results_df, on="query_id", suffixes=("_d24", "_d22"))
        for m in METRICS:
            merged[f"delta_{m}"] = merged[f"{m}_d24"] - merged[f"{m}_d22"]

        delta_vs_d22[config_name] = merged
        means = merged[[f"delta_{m}" for m in METRICS]].mean()
        print(f"  {config_name:20s}: " + "  ".join(f"Δ{m.split('@')[0]}={means[f'delta_{m}']:+.4f}" for m in METRICS))

# ============================================================================
# DELTAS VS RAW (INTERNAL CONTROL)
# ============================================================================

delta_vs_raw: Dict[str, pd.DataFrame] = {}
raw_df = ablation_metrics["raw"]

print(f"\nDELTAS VS RAW (INTERNAL CONTROL)")
print("-" * 60)

for config_name in ABLATION_CONFIG_ORDER:
    if config_name == "raw":
        continue

    cfg_df = ablation_metrics[config_name]
    merged = cfg_df.merge(raw_df, on="query_id", suffixes=("_cfg", "_raw"))
    for m in METRICS:
        merged[f"delta_{m}"] = merged[f"{m}_cfg"] - merged[f"{m}_raw"]

    delta_vs_raw[config_name] = merged
    means = merged[[f"delta_{m}" for m in METRICS]].mean()
    print(f"  {config_name:20s}: " + "  ".join(f"Δ{m.split('@')[0]}={means[f'delta_{m}']:+.4f}" for m in METRICS))

# ============================================================================
# MARGINAL LAYER CONTRIBUTIONS
# ============================================================================

print(f"\nMARGINAL LAYER CONTRIBUTIONS (vs domain_entity base)")
print("-" * 60)

base_df = ablation_metrics["domain_entity"]
marginal_rows = []

layer_configs = {
    "Authority":     "de_authority",
    "Section":       "de_section",
    "Relationships": "de_relationships",
}

for layer_name, config_name in layer_configs.items():
    cfg_df = ablation_metrics[config_name]
    merged = cfg_df.merge(base_df, on="query_id", suffixes=("_cfg", "_base"))

    row = {"layer": layer_name}
    for m in METRICS:
        delta = merged[f"{m}_cfg"].mean() - merged[f"{m}_base"].mean()
        row[f"delta_{m}"] = delta
    marginal_rows.append(row)
    print(f"  +{layer_name:15s}: " + "  ".join(f"Δ{m.split('@')[0]}={row[f'delta_{m}']:+.4f}" for m in METRICS))

marginal_contributions = pd.DataFrame(marginal_rows)

# Export deltas
for config_name, df in delta_vs_d21.items():
    csv_path = OUTPUT_DIR / f"d24_delta_{config_name}_vs_d21.csv"
    df.to_csv(csv_path, index=False)

for config_name, df in delta_vs_d22.items():
    csv_path = OUTPUT_DIR / f"d24_delta_{config_name}_vs_d22.csv"
    df.to_csv(csv_path, index=False)

marginal_csv = OUTPUT_DIR / "d24_marginal_contributions.csv"
marginal_contributions.to_csv(marginal_csv, index=False)
print(f"\n✓ Deltas and marginal contributions exported to {OUTPUT_DIR}")
'''


# ============================================================================
# CELL 17: STATISTICAL SIGNIFICANCE
# ============================================================================

CELL_17_SOURCE = r'''#!/usr/bin/env python3
"""
D-24 Cell 17: Statistical Significance — Per-Config Wilcoxon Tests

Performs Wilcoxon signed-rank tests for:
  1. Each config vs D-21 baseline (if available)
  2. Each config vs D-22 single-layer (if available)
  3. Each enriched config vs raw (internal control)

Bonferroni correction: α = 0.05 / 3 comparisons = 0.0167
"""

from scipy.stats import wilcoxon

ALPHA = 0.05
N_COMPARISONS = 3
BONFERRONI_ALPHA = ALPHA / N_COMPARISONS

sig_rows = []

def run_wilcoxon(label, metric, values_a, values_b):
    """Run Wilcoxon signed-rank test and return result dict."""
    diff = values_a - values_b
    nonzero = np.sum(diff != 0)

    if nonzero < 5:
        return {
            "pair_label": label, "metric": metric,
            "statistic": None, "pvalue": None,
            "significant": False, "effect_size": None,
            "effect_magnitude": "insufficient_data", "n_nonzero": int(nonzero),
        }

    stat, pval = wilcoxon(values_a, values_b, alternative="two-sided")
    r = 1 - (2 * stat) / (nonzero * (nonzero + 1))

    if abs(r) >= 0.5:
        magnitude = "large"
    elif abs(r) >= 0.3:
        magnitude = "medium"
    else:
        magnitude = "small"

    return {
        "pair_label": label, "metric": metric,
        "statistic": float(stat), "pvalue": float(pval),
        "significant": pval < BONFERRONI_ALPHA, "effect_size": float(r),
        "effect_magnitude": magnitude, "n_nonzero": int(nonzero),
    }

print("=" * 80)
print(f"STATISTICAL SIGNIFICANCE (Bonferroni α = {BONFERRONI_ALPHA:.4f})")
print("=" * 80)

# vs D-21
if d21_available:
    d21_v15 = d21_results_df[d21_results_df["model"] == "v1.5"]
    for config_name in ABLATION_CONFIG_ORDER:
        cfg_df = ablation_metrics[config_name]
        merged = cfg_df.merge(d21_v15, on="query_id", suffixes=("_d24", "_d21"))
        label = f"D-24 {config_name} vs D-21"
        for m in METRICS:
            result = run_wilcoxon(label, m, merged[f"{m}_d24"].values, merged[f"{m}_d21"].values)
            sig_rows.append(result)

# vs D-22
if d22_available:
    for config_name in ABLATION_CONFIG_ORDER:
        cfg_df = ablation_metrics[config_name]
        merged = cfg_df.merge(d22_results_df, on="query_id", suffixes=("_d24", "_d22"))
        label = f"D-24 {config_name} vs D-22"
        for m in METRICS:
            result = run_wilcoxon(label, m, merged[f"{m}_d24"].values, merged[f"{m}_d22"].values)
            sig_rows.append(result)

# vs raw (internal)
raw_df = ablation_metrics["raw"]
for config_name in ABLATION_CONFIG_ORDER:
    if config_name == "raw":
        continue
    cfg_df = ablation_metrics[config_name]
    merged = cfg_df.merge(raw_df, on="query_id", suffixes=("_cfg", "_raw"))
    label = f"D-24 {config_name} vs raw"
    for m in METRICS:
        result = run_wilcoxon(label, m, merged[f"{m}_cfg"].values, merged[f"{m}_raw"].values)
        sig_rows.append(result)

sig_df = pd.DataFrame(sig_rows)
sig_csv = OUTPUT_DIR / "d24_significance_results.csv"
sig_df.to_csv(sig_csv, index=False)

# Print significant results
sig_only = sig_df[sig_df["significant"] == True]
print(f"\n  {len(sig_only)} significant results (of {len(sig_df)} tests):")
for _, row in sig_only.iterrows():
    print(f"    {row['pair_label']:40s} {row['metric']:12s} p={row['pvalue']:.6f} r={row['effect_size']:.3f} ({row['effect_magnitude']})")

print(f"\n✓ Significance results exported: {sig_csv}")
'''


# ============================================================================
# CELL 18: ABLATION VISUALIZATION
# ============================================================================

CELL_18_SOURCE = r'''#!/usr/bin/env python3
"""
D-24 Cell 18: Ablation Visualization — Grouped Bar Chart

Creates a 2x2 figure comparing all 5 configs + D-21 + D-22 baselines
across the 4 metrics.
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle("D-24 Layer Ablation — Metric Comparison", fontsize=16, fontweight="bold")

METRICS_DISPLAY = {
    "precision@5": "Precision@5",
    "recall@10": "Recall@10",
    "ndcg@10": "NDCG@10",
    "mrr": "MRR",
}

# Collect means for all experiments
all_labels = []
all_means = {m: [] for m in METRICS}

# D-21 baseline
if d21_available:
    d21_v15 = d21_results_df[d21_results_df["model"] == "v1.5"]
    d21_means = d21_v15[METRICS].mean()
    all_labels.append("D-21\n(baseline)")
    for m in METRICS:
        all_means[m].append(d21_means[m])

# D-22 single-layer
if d22_available:
    d22_means = d22_results_df[METRICS].mean()
    all_labels.append("D-22\n(single)")
    for m in METRICS:
        all_means[m].append(d22_means[m])

# D-24 configs
config_labels = {
    "raw": "A: raw",
    "domain_entity": "B: D+E",
    "de_authority": "C: D+E+A",
    "de_section": "D: D+E+S",
    "de_relationships": "E: D+E+R",
}

for config_name in ABLATION_CONFIG_ORDER:
    df = ablation_metrics[config_name]
    means = df[METRICS].mean()
    all_labels.append(config_labels[config_name])
    for m in METRICS:
        all_means[m].append(means[m])

# Plot
colors = ["#888888", "#4CAF50"] + ["#2196F3", "#FF9800", "#E91E63", "#9C27B0", "#00BCD4"]
n_bars = len(all_labels)

for idx, (metric, display_name) in enumerate(METRICS_DISPLAY.items()):
    ax = axes[idx // 2][idx % 2]
    x = range(n_bars)
    bars = ax.bar(x, all_means[metric], color=colors[:n_bars], alpha=0.85, edgecolor="white")

    # Value labels
    for bar, val in zip(bars, all_means[metric]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f"{val:.3f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_title(display_name, fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(all_labels, fontsize=9)
    ax.set_ylim(0, 1.1)
    ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
viz_path = OUTPUT_DIR / "visualization_ablation_comparison.png"
plt.savefig(viz_path, dpi=150, bbox_inches="tight")
plt.show()
print(f"✓ Saved: {viz_path}")
'''


# ============================================================================
# CELL 19: MARGINAL CONTRIBUTION CHART
# ============================================================================

CELL_19_SOURCE = r'''#!/usr/bin/env python3
"""
D-24 Cell 19: Marginal Contribution Chart & Config Heatmap

Figure 1: Marginal contribution of each layer (vs domain_entity base)
Figure 2: Per-query-type performance heatmap across configs
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

# ============================================================================
# FIGURE 1: MARGINAL CONTRIBUTIONS
# ============================================================================

fig, ax = plt.subplots(figsize=(12, 6))
fig.suptitle("Marginal Layer Contribution (vs Domain+Entity base)", fontsize=14, fontweight="bold")

layers = marginal_contributions["layer"].tolist()
x = range(len(layers))
width = 0.2
metric_colors = {"precision@5": "#2196F3", "recall@10": "#4CAF50", "ndcg@10": "#FF9800", "mrr": "#E91E63"}

for i, (m, color) in enumerate(metric_colors.items()):
    vals = marginal_contributions[f"delta_{m}"].tolist()
    bars = ax.bar([xi + i*width for xi in x], vals, width, label=m, color=color, alpha=0.8)
    for bar, val in zip(bars, vals):
        y_pos = bar.get_height() + 0.002 if val >= 0 else bar.get_height() - 0.015
        ax.text(bar.get_x() + bar.get_width()/2, y_pos, f"{val:+.3f}", ha="center", fontsize=8)

ax.set_xticks([xi + 1.5*width for xi in x])
ax.set_xticklabels([f"+{l}" for l in layers], fontsize=11, fontweight="bold")
ax.axhline(y=0, color="black", linewidth=0.5)
ax.set_ylabel("Delta vs Domain+Entity")
ax.legend(loc="upper right")
ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
viz1_path = OUTPUT_DIR / "visualization_marginal_contributions.png"
plt.savefig(viz1_path, dpi=150, bbox_inches="tight")
plt.show()
print(f"✓ Saved: {viz1_path}")

# ============================================================================
# FIGURE 2: PER-QUERY-TYPE HEATMAP
# ============================================================================

import seaborn as sns

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle("D-24 Per-Query-Type Performance by Config", fontsize=14, fontweight="bold")

for idx, metric in enumerate(METRICS):
    ax = axes[idx // 2][idx % 2]

    # Build heatmap data: rows=query_types, cols=configs
    query_types = sorted(ablation_metrics["raw"]["query_type"].unique())
    heatmap_data = []

    for qt in query_types:
        row = []
        for cfg in ABLATION_CONFIG_ORDER:
            df = ablation_metrics[cfg]
            mean_val = df[df["query_type"] == qt][metric].mean()
            row.append(mean_val)
        heatmap_data.append(row)

    heatmap_df = pd.DataFrame(heatmap_data, index=query_types, columns=ABLATION_CONFIG_ORDER)
    sns.heatmap(heatmap_df, annot=True, fmt=".3f", cmap="RdYlGn", ax=ax,
                vmin=0, vmax=1, linewidths=0.5, cbar_kws={"shrink": 0.8})
    ax.set_title(METRICS_DISPLAY.get(metric, metric), fontsize=12, fontweight="bold")

plt.tight_layout()
viz2_path = OUTPUT_DIR / "visualization_querytype_heatmap.png"
plt.savefig(viz2_path, dpi=150, bbox_inches="tight")
plt.show()
print(f"✓ Saved: {viz2_path}")
'''


# ============================================================================
# CELL 20: PER-CONFIG GO/NO-GO
# ============================================================================

CELL_20_SOURCE = r'''#!/usr/bin/env python3
"""
D-24 Cell 20: Per-Config GO/NO-GO Scorecard

Evaluates 7 criteria for each ablation config (same criteria as D-23).
Identifies the best-performing configuration.
"""

print("=" * 80)
print("D-24 PER-CONFIG GO/NO-GO SCORECARD")
print("=" * 80)

config_scores: Dict[str, Dict] = {}

for config_name in ABLATION_CONFIG_ORDER:
    r = ablation_results[config_name]
    cfg_df = ablation_metrics[config_name]
    cfg_means = cfg_df[METRICS].mean()

    criteria = {}

    # [1] EXECUTION: overflow < 5%
    overflow_pct = 100 * r["overflow_count"] / max(len(r["enriched_chunks"]), 1)
    criteria["execution"] = overflow_pct < 5

    # [2] IMPROVEMENT over D-21: ≥3/4 metrics positive
    if d21_available:
        d21_v15 = d21_results_df[d21_results_df["model"] == "v1.5"]
        d21_means = d21_v15[METRICS].mean()
        positive_d21 = sum(1 for m in METRICS if cfg_means[m] > d21_means[m])
        criteria["improve_d21"] = positive_d21 >= 3
    else:
        criteria["improve_d21"] = None

    # [3] IMPROVEMENT over D-22: ≥2/4 metrics positive
    if d22_available:
        d22_means = d22_results_df[METRICS].mean()
        positive_d22 = sum(1 for m in METRICS if cfg_means[m] > d22_means[m])
        criteria["improve_d22"] = positive_d22 >= 2
    else:
        criteria["improve_d22"] = None

    # [4] Significance: ≥2 metrics significant vs D-21
    sig_vs_d21 = sig_df[sig_df["pair_label"].str.contains(f"D-24 {config_name} vs D-21")]
    n_sig_d21 = sig_vs_d21["significant"].sum() if len(sig_vs_d21) > 0 else 0
    criteria["significance"] = n_sig_d21 >= 2

    # [5] Marginal value: ≥1 metric >5% gain over D-22
    if d22_available:
        gains = [(cfg_means[m] - d22_means[m]) / max(d22_means[m], 0.001) for m in METRICS]
        criteria["marginal_value"] = any(g > 0.05 for g in gains)
    else:
        criteria["marginal_value"] = None

    # [6] No catastrophic degradation: <25% queries degraded vs D-21
    if config_name in delta_vs_d21:
        delta_df = delta_vs_d21[config_name]
        total_pairs = len(delta_df) * len(METRICS)
        degraded = sum(
            (delta_df[f"delta_{m}"] < 0).sum() for m in METRICS
        )
        degraded_pct = 100 * degraded / max(total_pairs, 1)
        criteria["no_catastrophic"] = degraded_pct < 25
    else:
        criteria["no_catastrophic"] = None

    # [7] Authority/Temporal benefit
    authority_mean = cfg_df[cfg_df["query_type"] == "AUTHORITY"]["mrr"].mean() if "AUTHORITY" in cfg_df["query_type"].values else 0
    factual_mean = cfg_df[cfg_df["query_type"] == "SINGLE_HOP"]["mrr"].mean() if "SINGLE_HOP" in cfg_df["query_type"].values else 0
    temporal_mean = cfg_df[cfg_df["query_type"] == "TEMPORAL"]["mrr"].mean() if "TEMPORAL" in cfg_df["query_type"].values else 0
    criteria["auth_temp_benefit"] = (authority_mean > factual_mean) or (temporal_mean > factual_mean)

    score = sum(1 for v in criteria.values() if v is True)
    total = sum(1 for v in criteria.values() if v is not None)

    config_scores[config_name] = {"criteria": criteria, "score": score, "total": total}

    # Print scorecard
    status_map = {True: "PASS ✅", False: "FAIL ❌", None: "N/A  ⚪"}
    print(f"\n  {config_name} — {score}/{total}")
    for k, v in criteria.items():
        print(f"    [{status_map[v]}] {k}")

# ============================================================================
# BEST CONFIG
# ============================================================================

best_config = max(config_scores.keys(), key=lambda k: config_scores[k]["score"])
best_score = config_scores[best_config]

print(f"\n{'=' * 80}")
print(f"BEST CONFIG: {best_config} ({best_score['score']}/{best_score['total']} criteria)")
print(f"{'=' * 80}")

# Export go/no-go
with open(OUTPUT_DIR / "d24_go_nogo_decision.txt", "w") as f:
    f.write("D-24 GO/NO-GO DECISION REPORT\n")
    f.write("=" * 80 + "\n")
    f.write(f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"Bonferroni-adjusted α: {BONFERRONI_ALPHA:.4f}\n\n")
    for config_name in ABLATION_CONFIG_ORDER:
        cs = config_scores[config_name]
        f.write(f"{config_name}: {cs['score']}/{cs['total']} criteria passed\n")
        for k, v in cs["criteria"].items():
            status = "PASS" if v is True else ("FAIL" if v is False else "N/A")
            f.write(f"  [{status}] {k}\n")
        f.write("\n")
    f.write(f"BEST CONFIG: {best_config}\n")

print(f"✓ GO/NO-GO report exported")
'''


# ============================================================================
# CELL 21: EXPORT
# ============================================================================

CELL_21_SOURCE = r'''#!/usr/bin/env python3
"""
D-24 Cell 21: Export Results — Final Artifact Assembly

Exports all D-24 output artifacts.
"""

print("=" * 80)
print("D-24 EXPORT — FINAL ARTIFACTS")
print("=" * 80)

# Per-config results CSVs
for config_name in ABLATION_CONFIG_ORDER:
    df = ablation_metrics[config_name]
    csv_path = OUTPUT_DIR / f"d24_results_{config_name}.csv"
    df.to_csv(csv_path, index=False)
    print(f"  ✓ {csv_path} ({len(df)} rows)")

# Summary CSV (all configs)
all_results = pd.concat([ablation_metrics[cfg] for cfg in ABLATION_CONFIG_ORDER], ignore_index=True)
summary_path = OUTPUT_DIR / "d24_results_all.csv"
all_results.to_csv(summary_path, index=False)
print(f"  ✓ {summary_path} ({len(all_results)} rows)")

# Marginal contributions
print(f"  ✓ d24_marginal_contributions.csv (already exported)")

# Significance
print(f"  ✓ d24_significance_results.csv (already exported)")

# Token audits
print(f"  ✓ d24_layer_token_audits.csv (already exported)")

# GO/NO-GO
print(f"  ✓ d24_go_nogo_decision.txt (already exported)")

# Visualizations
print(f"  ✓ visualization_ablation_comparison.png")
print(f"  ✓ visualization_marginal_contributions.png")
print(f"  ✓ visualization_querytype_heatmap.png")

# Manifest
print(f"\n{'=' * 80}")
print(f"COMPLETE MANIFEST ({OUTPUT_DIR}):")
print(f"{'=' * 80}")
import glob
for f in sorted(glob.glob(str(OUTPUT_DIR / "*"))):
    size = os.path.getsize(f)
    print(f"  {Path(f).name:50s} {size:>8,d} bytes")
'''


# ============================================================================
# CELL 22: SUMMARY MARKDOWN
# ============================================================================

CELL_22_SOURCE = r'''## D-24 Ablation Summary

D-24 tested 5 enrichment configurations, from zero layers (raw) to 3 layers.
All configs used D-21's exact chunking algorithm with identical corpus and queries.

### Configurations Tested

| Config | Layers | Purpose |
|--------|--------|---------|
| A (raw) | None | Internal D-21 control |
| B (domain_entity) | Domain + Entity | Minimal enrichment |
| C (de_authority) | Domain + Entity + Authority | +canonical status |
| D (de_section) | Domain + Entity + Section | +document structure |
| E (de_relationships) | Domain + Entity + Relationships | +cross-references |

### Key Question Answered

**Which individual context layers contribute most to retrieval improvement?**

Review the marginal contribution chart and per-config GO/NO-GO scores above
to determine the optimal layer combination for production use.'''


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("D-24 Ablation Notebook — Part 2 (Cells 11-22)")
    print("=" * 70)

    if not NOTEBOOK_PATH.exists():
        print(f"\n✗ Notebook not found: {NOTEBOOK_PATH}")
        print(f"  Run create_d24_ablation.py first.")
        sys.exit(1)

    nb = load_notebook(NOTEBOOK_PATH)
    print(f"\n[1] Loaded: {NOTEBOOK_PATH}")
    print(f"    Cells: {len(nb['cells'])}")

    # Verify Cell 9 was already patched
    cell9_src = ''.join(nb['cells'][9]['source'])
    if 'ABLATION_CONFIGS' not in cell9_src:
        print("\n✗ Cell 9 does not contain ABLATION_CONFIGS. Run create_d24_ablation.py first.")
        sys.exit(1)
    print("    ✓ Cell 9 already patched (ABLATION_CONFIGS found)")

    # Replace cells
    replacements = [
        (11, "embedding & indexing", CELL_11_SOURCE, "code"),
        (12, "query execution", CELL_12_SOURCE, "code"),
        (13, "results header", CELL_13_SOURCE, "markdown"),
        (15, "metric computation", CELL_15_SOURCE, "code"),
        (16, "delta analysis", CELL_16_SOURCE, "code"),
        (17, "significance testing", CELL_17_SOURCE, "code"),
        (18, "ablation visualization", CELL_18_SOURCE, "code"),
        (19, "marginal contribution chart", CELL_19_SOURCE, "code"),
        (20, "GO/NO-GO scorecard", CELL_20_SOURCE, "code"),
        (21, "export", CELL_21_SOURCE, "code"),
        (22, "summary markdown", CELL_22_SOURCE, "markdown"),
    ]

    for cell_idx, label, source, cell_type in replacements:
        if cell_type == "code":
            nb['cells'][cell_idx] = make_code_cell(source)
        else:
            nb['cells'][cell_idx] = make_markdown_cell(source)
        print(f"  [✓] Cell {cell_idx}: {label}")

    # Clear all outputs
    cleared = 0
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            if cell.get('outputs'):
                cell['outputs'] = []
                cleared += 1
            cell['execution_count'] = None
    print(f"\n  Cleared outputs from {cleared} cells")

    # Save
    save_notebook(nb, NOTEBOOK_PATH)
    size = os.path.getsize(NOTEBOOK_PATH)
    print(f"\n[2] Saved: {NOTEBOOK_PATH} ({size:,} bytes)")

    # Verification
    print(f"\n{'=' * 70}")
    print("VERIFICATION")
    print(f"{'=' * 70}")

    nb_v = load_notebook(NOTEBOOK_PATH)

    checks = [
        ("ABLATION_CONFIGS" in ''.join(nb_v['cells'][9]['source']), "Cell 9: ablation configs"),
        ("ablation_results" in ''.join(nb_v['cells'][10]['source']), "Cell 10: multi-config pipeline"),
        ("ablation_collections" in ''.join(nb_v['cells'][11]['source']), "Cell 11: per-config collections"),
        ("ablation_query_results" in ''.join(nb_v['cells'][12]['source']), "Cell 12: per-config queries"),
        ("ablation_metrics" in ''.join(nb_v['cells'][15]['source']), "Cell 15: per-config metrics"),
        ("marginal_contributions" in ''.join(nb_v['cells'][16]['source']), "Cell 16: marginal analysis"),
        ("BONFERRONI_ALPHA" in ''.join(nb_v['cells'][17]['source']), "Cell 17: significance tests"),
        ("visualization_ablation" in ''.join(nb_v['cells'][18]['source']), "Cell 18: ablation viz"),
        ("visualization_marginal" in ''.join(nb_v['cells'][19]['source']), "Cell 19: marginal viz"),
        ("config_scores" in ''.join(nb_v['cells'][20]['source']), "Cell 20: GO/NO-GO scorecard"),
        ("d24_results" in ''.join(nb_v['cells'][21]['source']), "Cell 21: export"),
        ("Ablation Summary" in ''.join(nb_v['cells'][22]['source']), "Cell 22: summary"),
    ]

    passed = 0
    for ok, label in checks:
        status = "✓" if ok else "✗"
        print(f"  {status} {label}")
        if ok:
            passed += 1

    print(f"\n  Result: {passed}/{len(checks)} checks passed")

    if passed == len(checks):
        print(f"\n✓ ALL CHECKS PASSED")
        print(f"\n  D-24 notebook is ready!")
        print(f"  Upload {NOTEBOOK_PATH} to Google Colab (A100 GPU, High-RAM)")
    else:
        print(f"\n✗ {len(checks) - passed} checks FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
