#!/usr/bin/env python3
"""
fix_d24_data_issues.py — Fix two data issues in D-24 notebook

Issue 1: D-21 merge failure
  - Cell 15 used model filter "v1.5" but D-21 CSV uses "nomic-embed-text-v1.5"
  - Cell 15 also referenced wrong paths (d21-output/ vs results/d21/)
  - Fix: use correct paths and model name filter

Issue 2: GO/NO-GO scorecard inapplicable
  - D-23's 7-criteria framework doesn't fit an ablation study
  - Many criteria returned N/A because they compare against external experiments
  - Fix: replace with ablation-specific scorecard evaluating marginal contribution

Usage:
    python3 fix_d24_data_issues.py
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


# ============================================================================
# FIX 1: Cell 15 — Correct D-21/D-22 paths and model filter
# ============================================================================

CELL_15_FIXED = r'''#!/usr/bin/env python3
"""
D-24 Cell 15: Per-Config Metric Computation & Baseline Loading

FIX: Corrected D-21 path (results/d21/) and model filter (nomic-embed-text-v1.5)
FIX: Corrected D-22 path (results/d22/)

Computes P@5, R@10, NDCG@10, MRR for each ablation config.
Loads D-21 and D-22 results for cross-experiment comparison.
"""

# ============================================================================
# COMPUTE D-24 METRICS PER CONFIG
# ============================================================================

ablation_metrics: Dict[str, pd.DataFrame] = {}

print("=" * 80)
print("D-24 PER-CONFIG METRICS")
print("=" * 80)

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

# FIX: Use correct paths — results/ not d21-output/ / d22-output/
d21_results_path = Path("results/d21/d21_results.csv")
d22_results_path = Path("results/d22/d22_results.csv")

d21_available = d21_results_path.exists()
d22_available = d22_results_path.exists()

if d21_available:
    d21_results_df = pd.read_csv(d21_results_path)
    print(f"  ✓ D-21: {len(d21_results_df)} rows loaded")
    print(f"    Models: {d21_results_df['model'].unique()}")
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
    # FIX: Use full model name "nomic-embed-text-v1.5" not "v1.5"
    d21_v15 = d21_results_df[d21_results_df["model"].str.contains("v1.5")]
    if len(d21_v15) == 0:
        print(f"  ⚠ D-21: No v1.5 rows found. Available models: {d21_results_df['model'].unique()}")
    else:
        d21_means = d21_v15[["precision@5", "recall@10", "ndcg@10", "mrr"]].mean()
        print(f"  {'D-21 (baseline)':20s} {d21_means['precision@5']:>8.4f} {d21_means['recall@10']:>8.4f} "
              f"{d21_means['ndcg@10']:>8.4f} {d21_means['mrr']:>8.4f}")

if d22_available:
    d22_means = d22_results_df[["precision@5", "recall@10", "ndcg@10", "mrr"]].mean()
    print(f"  {'D-22 (single-layer)':20s} {d22_means['precision@5']:>8.4f} {d22_means['recall@10']:>8.4f} "
          f"{d22_means['ndcg@10']:>8.4f} {d22_means['mrr']:>8.4f}")
    print(f"  {'  ⚠ D-22: 43.1% overflow':20s}")

print(f"  {'─'*20} {'─'*8} {'─'*8} {'─'*8} {'─'*8}")

for config_name in ABLATION_CONFIG_ORDER:
    df = ablation_metrics[config_name]
    means = df[["precision@5", "recall@10", "ndcg@10", "mrr"]].mean()
    print(f"  {config_name:20s} {means['precision@5']:>8.4f} {means['recall@10']:>8.4f} "
          f"{means['ndcg@10']:>8.4f} {means['mrr']:>8.4f}")
'''


# ============================================================================
# FIX 1b: Cell 16 — Fix D-21 model filter in delta analysis
# ============================================================================

CELL_16_FIXED = r'''#!/usr/bin/env python3
"""
D-24 Cell 16: Ablation Delta Analysis

FIX: Use str.contains("v1.5") for D-21 model filter instead of exact match.

Computes deltas for:
  1. Each config vs D-21 baseline
  2. Each config vs D-22 single-layer
  3. Each config vs Config A (raw — internal control)
  4. Marginal contribution of each added layer (C-B, D-B, E-B)
"""

METRICS = ["precision@5", "recall@10", "ndcg@10", "mrr"]

# ============================================================================
# DELTAS VS D-21
# ============================================================================

delta_vs_d21: Dict[str, pd.DataFrame] = {}

if d21_available:
    # FIX: Use str.contains instead of exact match
    d21_v15 = d21_results_df[d21_results_df["model"].str.contains("v1.5")].copy()
    print(f"DELTAS VS D-21 (BASELINE) — {len(d21_v15)} D-21 rows matched")
    print("-" * 60)

    for config_name in ABLATION_CONFIG_ORDER:
        cfg_df = ablation_metrics[config_name]

        merged = cfg_df.merge(d21_v15, on="query_id", suffixes=("_d24", "_d21"))
        for m in METRICS:
            merged[f"delta_{m}"] = merged[f"{m}_d24"] - merged[f"{m}_d21"]

        delta_vs_d21[config_name] = merged
        if len(merged) > 0:
            means = merged[[f"delta_{m}" for m in METRICS]].mean()
            print(f"  {config_name:20s}: " + "  ".join(f"Δ{m.split('@')[0]}={means[f'delta_{m}']:+.4f}" for m in METRICS))
        else:
            print(f"  {config_name:20s}: ⚠ merge produced 0 rows")

# ============================================================================
# DELTAS VS D-22 (with overflow caveat)
# ============================================================================

delta_vs_d22: Dict[str, pd.DataFrame] = {}

if d22_available:
    print(f"\nDELTAS VS D-22 (SINGLE-LAYER) — ⚠ D-22 metrics inflated by 43.1% chunk overflow")
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
# FIX 2: Cell 20 — Ablation-specific GO/NO-GO scorecard
# ============================================================================

CELL_20_FIXED = r'''#!/usr/bin/env python3
"""
D-24 Cell 20: Ablation-Specific Scorecard

Replaces D-23's 7-criteria GO/NO-GO with an ablation-specific evaluation:
  1. CONTROL VALIDITY: raw config matches D-21 within ±5%
  2. ENRICHMENT BENEFIT: best enriched config > raw on ≥2/4 metrics
  3. MARGINAL CONTRIBUTION: ≥1 layer adds >2% improvement over D+E base
  4. NO DEGRADATION: best config has no metric >10% worse than raw
  5. OVERFLOW CLEAN: all configs <5% overflow
  6. OPTIMAL IDENTIFIED: one config clearly dominates (best on ≥3/4 metrics)
"""

print("=" * 80)
print("D-24 ABLATION SCORECARD")
print("=" * 80)

# ============================================================================
# Criterion 1: CONTROL VALIDITY — raw ≈ D-21
# ============================================================================

raw_means = ablation_metrics["raw"][METRICS].mean()
control_valid = False
control_detail = ""

if d21_available:
    d21_v15 = d21_results_df[d21_results_df["model"].str.contains("v1.5")]
    if len(d21_v15) > 0:
        d21_means = d21_v15[METRICS].mean()
        pct_diffs = {m: abs(raw_means[m] - d21_means[m]) / max(d21_means[m], 0.001) * 100
                     for m in METRICS}
        all_within_5pct = all(d < 5 for d in pct_diffs.values())
        control_valid = all_within_5pct
        worst_diff = max(pct_diffs.values())
        control_detail = f"worst diff {worst_diff:.1f}%"
    else:
        control_detail = "D-21 v1.5 data not found"
else:
    control_detail = "D-21 not available"

print(f"\n  [1] CONTROL VALIDITY (raw ≈ D-21 within ±5%)")
print(f"      {'✅ PASS' if control_valid else '❌ FAIL'} — {control_detail}")

# ============================================================================
# Criterion 2: ENRICHMENT BENEFIT — best enriched > raw
# ============================================================================

enriched_configs = [c for c in ABLATION_CONFIG_ORDER if c != "raw"]
best_enriched = None
best_enriched_wins = 0

for cfg in enriched_configs:
    cfg_means = ablation_metrics[cfg][METRICS].mean()
    wins = sum(1 for m in METRICS if cfg_means[m] > raw_means[m])
    if wins > best_enriched_wins:
        best_enriched = cfg
        best_enriched_wins = wins

enrichment_benefit = best_enriched_wins >= 2
print(f"\n  [2] ENRICHMENT BENEFIT (best enriched > raw on ≥2/4 metrics)")
print(f"      {'✅ PASS' if enrichment_benefit else '❌ FAIL'} — {best_enriched} wins {best_enriched_wins}/4 metrics")

if best_enriched:
    cfg_means = ablation_metrics[best_enriched][METRICS].mean()
    for m in METRICS:
        delta = cfg_means[m] - raw_means[m]
        win = "↑" if delta > 0 else ("↓" if delta < 0 else "=")
        print(f"        {m:14s}: {delta:+.4f} {win}")

# ============================================================================
# Criterion 3: MARGINAL CONTRIBUTION — any layer adds >2% over D+E
# ============================================================================

marginal_threshold = 0.02
any_marginal = False
de_means = ablation_metrics["domain_entity"][METRICS].mean()

for _, row in marginal_contributions.iterrows():
    for m in METRICS:
        pct_gain = row[f"delta_{m}"] / max(de_means[m], 0.001) * 100
        if pct_gain > 2:
            any_marginal = True

print(f"\n  [3] MARGINAL CONTRIBUTION (≥1 layer adds >2% over D+E)")
print(f"      {'✅ PASS' if any_marginal else '❌ FAIL'}")
for _, row in marginal_contributions.iterrows():
    gains = [f"{row[f'delta_{m}']:+.4f}" for m in METRICS]
    print(f"        +{row['layer']:15s}: {', '.join(gains)}")

# ============================================================================
# Criterion 4: NO DEGRADATION — best config not >10% worse than raw
# ============================================================================

if best_enriched:
    cfg_means = ablation_metrics[best_enriched][METRICS].mean()
    pct_diffs = {m: (raw_means[m] - cfg_means[m]) / max(raw_means[m], 0.001) * 100
                 for m in METRICS}
    worst_degradation = max(pct_diffs.values())
    no_degradation = worst_degradation < 10
else:
    no_degradation = False
    worst_degradation = float('inf')

print(f"\n  [4] NO DEGRADATION (best config not >10% worse than raw)")
print(f"      {'✅ PASS' if no_degradation else '❌ FAIL'} — worst: {worst_degradation:.1f}%")

# ============================================================================
# Criterion 5: OVERFLOW CLEAN — all configs <5%
# ============================================================================

all_clean = True
for cfg in ABLATION_CONFIG_ORDER:
    r = ablation_results[cfg]
    pct = 100 * r["overflow_count"] / max(len(r["enriched_chunks"]), 1)
    if pct >= 5:
        all_clean = False

print(f"\n  [5] OVERFLOW CLEAN (all configs <5%)")
print(f"      {'✅ PASS' if all_clean else '❌ FAIL'}")

# ============================================================================
# Criterion 6: OPTIMAL IDENTIFIED — one config wins ≥3/4
# ============================================================================

# Find the config that wins each metric
metric_winners = {}
for m in METRICS:
    best_val = -1
    best_cfg = None
    for cfg in ABLATION_CONFIG_ORDER:
        val = ablation_metrics[cfg][m].mean()
        if val > best_val:
            best_val = val
            best_cfg = cfg
    metric_winners[m] = best_cfg

# Count wins per config
from collections import Counter
win_counts = Counter(metric_winners.values())
optimal_cfg = win_counts.most_common(1)[0][0] if win_counts else None
optimal_wins = win_counts.most_common(1)[0][1] if win_counts else 0
optimal_identified = optimal_wins >= 3

print(f"\n  [6] OPTIMAL IDENTIFIED (one config wins ≥3/4 metrics)")
print(f"      {'✅ PASS' if optimal_identified else '❌ FAIL'} — {optimal_cfg} wins {optimal_wins}/4")
for m, winner in metric_winners.items():
    val = ablation_metrics[winner][m].mean()
    print(f"        {m:14s}: {winner} ({val:.4f})")

# ============================================================================
# OVERALL SCORE
# ============================================================================

criteria = {
    "control_validity": control_valid,
    "enrichment_benefit": enrichment_benefit,
    "marginal_contribution": any_marginal,
    "no_degradation": no_degradation,
    "overflow_clean": all_clean,
    "optimal_identified": optimal_identified,
}

score = sum(1 for v in criteria.values() if v)
total = len(criteria)

print(f"\n{'=' * 80}")
print(f"OVERALL SCORE: {score}/{total}")
print(f"{'=' * 80}")

decision = "GO" if score >= 4 else ("CONDITIONAL_GO" if score >= 3 else "NO_GO")
print(f"DECISION: {decision}")

if best_enriched:
    print(f"RECOMMENDED CONFIG: {best_enriched}")

# Export
with open(OUTPUT_DIR / "d24_go_nogo_decision.txt", "w") as f:
    f.write("D-24 ABLATION SCORECARD\n")
    f.write("=" * 80 + "\n")
    f.write(f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n\n")
    for k, v in criteria.items():
        status = "PASS" if v else "FAIL"
        f.write(f"  [{status}] {k}\n")
    f.write(f"\nScore: {score}/{total}\n")
    f.write(f"Decision: {decision}\n")
    f.write(f"Recommended: {best_enriched}\n")
    f.write(f"\nMetric winners:\n")
    for m, w in metric_winners.items():
        f.write(f"  {m}: {w}\n")

print(f"\n✓ Scorecard exported")
'''


# ============================================================================
# FIX 1c: Cell 17 — Fix D-21 model filter in significance testing
# ============================================================================

CELL_17_FIXED = r'''#!/usr/bin/env python3
"""
D-24 Cell 17: Statistical Significance — Per-Config Wilcoxon Tests

FIX: Use str.contains("v1.5") for D-21 model filter.
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

# vs D-21 — FIX: use str.contains
if d21_available:
    d21_v15 = d21_results_df[d21_results_df["model"].str.contains("v1.5")]
    if len(d21_v15) > 0:
        for config_name in ABLATION_CONFIG_ORDER:
            cfg_df = ablation_metrics[config_name]
            merged = cfg_df.merge(d21_v15, on="query_id", suffixes=("_d24", "_d21"))
            label = f"D-24 {config_name} vs D-21"
            for m in METRICS:
                result = run_wilcoxon(label, m, merged[f"{m}_d24"].values, merged[f"{m}_d21"].values)
                sig_rows.append(result)
    else:
        print("  ⚠ D-21 v1.5 data not found, skipping vs D-21 tests")

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

# Print insufficient data tests
insuf = sig_df[sig_df["effect_magnitude"] == "insufficient_data"]
if len(insuf) > 0:
    print(f"\n  {len(insuf)} tests had insufficient data (n_nonzero < 5)")

print(f"\n✓ Significance results exported: {sig_csv}")
'''


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("D-24 Data Issue Fixes")
    print("=" * 70)

    if not NOTEBOOK_PATH.exists():
        print(f"\n✗ Notebook not found: {NOTEBOOK_PATH}")
        sys.exit(1)

    nb = load_notebook(NOTEBOOK_PATH)
    print(f"\n[1] Loaded: {NOTEBOOK_PATH} ({len(nb['cells'])} cells)")

    # Replace cells
    replacements = [
        (15, "metric computation (D-21 path fix)", CELL_15_FIXED),
        (16, "delta analysis (D-21 model filter fix)", CELL_16_FIXED),
        (17, "significance (D-21 model filter fix)", CELL_17_FIXED),
        (20, "ablation-specific scorecard", CELL_20_FIXED),
    ]

    for cell_idx, label, source in replacements:
        nb['cells'][cell_idx] = make_code_cell(source)
        print(f"  [✓] Cell {cell_idx}: {label}")

    # Clear all outputs
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            cell['outputs'] = []
            cell['execution_count'] = None

    # Save
    save_notebook(nb, NOTEBOOK_PATH)
    size = os.path.getsize(NOTEBOOK_PATH)
    print(f"\n[2] Saved: {NOTEBOOK_PATH} ({size:,} bytes)")

    # Verify
    print(f"\n{'=' * 70}")
    print("VERIFICATION")
    print(f"{'=' * 70}")

    nb_v = load_notebook(NOTEBOOK_PATH)

    checks = [
        ('results/d21/d21_results.csv' in ''.join(nb_v['cells'][15]['source']),
         "Cell 15: correct D-21 path"),
        ('results/d22/d22_results.csv' in ''.join(nb_v['cells'][15]['source']),
         "Cell 15: correct D-22 path"),
        ('str.contains("v1.5")' in ''.join(nb_v['cells'][15]['source']),
         "Cell 15: flexible model filter"),
        ('str.contains("v1.5")' in ''.join(nb_v['cells'][16]['source']),
         "Cell 16: flexible model filter"),
        ('str.contains("v1.5")' in ''.join(nb_v['cells'][17]['source']),
         "Cell 17: flexible model filter"),
        ('ABLATION SCORECARD' in ''.join(nb_v['cells'][20]['source']),
         "Cell 20: ablation-specific scorecard"),
        ('CONTROL VALIDITY' in ''.join(nb_v['cells'][20]['source']),
         "Cell 20: control validity criterion"),
        ('MARGINAL CONTRIBUTION' in ''.join(nb_v['cells'][20]['source']),
         "Cell 20: marginal contribution criterion"),
        ('OPTIMAL IDENTIFIED' in ''.join(nb_v['cells'][20]['source']),
         "Cell 20: optimal identified criterion"),
    ]

    passed = sum(1 for ok, _ in checks if ok)
    for ok, label in checks:
        print(f"  {'✓' if ok else '✗'} {label}")

    print(f"\n  Result: {passed}/{len(checks)} checks passed")

    if passed == len(checks):
        print(f"\n✓ ALL FIXES APPLIED")
        print(f"  Re-upload {NOTEBOOK_PATH} to Colab and re-run from Cell 15 onwards")
    else:
        print(f"\n✗ {len(checks) - passed} checks FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
