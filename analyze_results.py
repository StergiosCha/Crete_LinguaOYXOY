#!/usr/bin/env python3
"""
Crete Experiment — Analyze Results
===================================
Reads a results JSON file and produces summary statistics.

Usage:
  python analyze_results.py results/results_20260508_143000.json
  python analyze_results.py results/results_*.json    # merge multiple files
"""

import sys
import json
import os
from collections import defaultdict

def load_results(filepaths):
    """Load and merge results from one or more JSON files."""
    all_results = []
    for fp in filepaths:
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
        all_results.extend(data["results"])
        print(f"  Loaded {len(data['results'])} results from {os.path.basename(fp)}")
    return all_results


def compute_stats(results):
    """Group by phenomenon × condition × model and compute stats."""
    groups = defaultdict(list)
    for r in results:
        key = (r["phenomenon"], r["condition"], r["model"])
        if r["mean"] is not None:
            groups[key].append(r)

    stats = []
    for (phenom, cond, model), items in sorted(groups.items()):
        all_ratings = []
        for item in items:
            all_ratings.extend(item["ratings"])

        n_items = len(items)
        n_ratings = len(all_ratings)
        grand_mean = sum(all_ratings) / n_ratings if n_ratings else 0
        grand_sd = 0
        if n_ratings > 1:
            grand_sd = (sum((x - grand_mean)**2 for x in all_ratings) / (n_ratings - 1)) ** 0.5

        # Expected direction
        expected = items[0].get("expected", "")

        stats.append({
            "phenomenon": phenom,
            "condition": cond,
            "model": model,
            "n_items": n_items,
            "n_ratings": n_ratings,
            "mean": round(grand_mean, 2),
            "sd": round(grand_sd, 2),
            "expected": expected,
        })

    return stats


def print_by_phenomenon(stats):
    """Print results grouped by phenomenon."""
    phenomena = defaultdict(list)
    for s in stats:
        phenomena[s["phenomenon"]].append(s)

    models = sorted(set(s["model"] for s in stats))

    for phenom in sorted(phenomena.keys()):
        items = phenomena[phenom]
        print(f"\n{'='*70}")
        print(f"  {phenom.upper()}")
        print(f"{'='*70}")

        # Collect conditions
        conditions = sorted(set(s["condition"] for s in items))

        # Header
        header = f"  {'Condition':<30} {'Exp':>4}"
        for m in models:
            short = m[:8]
            header += f"  {short:>8}"
        print(header)
        print(f"  {'─'*30} {'─'*4}" + "─" * (10 * len(models)))

        for cond in conditions:
            cond_items = [s for s in items if s["condition"] == cond]
            expected = cond_items[0]["expected"] if cond_items else ""
            row = f"  {cond:<30} {expected:>4}"
            for m in models:
                match = [s for s in cond_items if s["model"] == m]
                if match:
                    s = match[0]
                    row += f"  {s['mean']:>5.1f}±{s['sd']:<4.1f}"
                else:
                    row += f"  {'—':>10}"
            print(row)


def print_correlation_matrix(stats):
    """Print between-model correlation for each phenomenon."""
    try:
        # Only if scipy available
        from scipy.stats import spearmanr, pearsonr
        has_scipy = True
    except ImportError:
        has_scipy = False
        print("\n  (Install scipy for correlation analysis: pip install scipy)")
        return

    phenomena = defaultdict(list)
    for s in stats:
        phenomena[s["phenomenon"]].append(s)

    models = sorted(set(s["model"] for s in stats))

    print(f"\n{'='*70}")
    print(f"  BETWEEN-MODEL CORRELATIONS (Spearman ρ)")
    print(f"{'='*70}")

    for phenom in sorted(phenomena.keys()):
        items = phenomena[phenom]
        conditions = sorted(set(s["condition"] for s in items))

        # Build vectors per model
        vectors = {}
        for m in models:
            vec = []
            for cond in conditions:
                match = [s for s in items if s["condition"] == cond and s["model"] == m]
                if match:
                    vec.append(match[0]["mean"])
                else:
                    vec.append(None)
            vectors[m] = vec

        print(f"\n  {phenom.upper()}")
        header = f"  {'':>12}"
        for m in models:
            header += f" {m[:8]:>8}"
        print(header)

        for m1 in models:
            row = f"  {m1[:12]:>12}"
            for m2 in models:
                if m1 == m2:
                    row += f"     —  "
                    continue
                # Pair up non-None values
                pairs = [(a, b) for a, b in zip(vectors[m1], vectors[m2])
                         if a is not None and b is not None]
                if len(pairs) >= 3:
                    x, y = zip(*pairs)
                    rho, p = spearmanr(x, y)
                    row += f"  {rho:>5.2f}  "
                else:
                    row += f"     —  "
            print(row)


def print_experiment_summary(stats):
    """Print a high-level summary by experiment grouping."""
    exp_a = {"cd", "clld"}
    exp_b = {"binding", "crossover", "plural_conjunction"}
    shared = {"filler", "dialect"}

    groups = {"Experiment A (CD + CLLD)": [], "Experiment B (Bind + CO + PC)": [], "Shared (Fillers + Dialect)": []}
    for s in stats:
        ph = s["phenomenon"]
        if ph in exp_a:
            groups["Experiment A (CD + CLLD)"].append(s)
        elif ph in exp_b:
            groups["Experiment B (Bind + CO + PC)"].append(s)
        elif ph in shared:
            groups["Shared (Fillers + Dialect)"].append(s)

    print(f"\n{'='*70}")
    print(f"  EXPERIMENT-LEVEL SUMMARY")
    print(f"{'='*70}")

    for group_name, items in groups.items():
        if not items:
            continue
        phenomena = sorted(set(s["phenomenon"] for s in items))
        n_conditions = len(set((s["phenomenon"], s["condition"]) for s in items))
        models = sorted(set(s["model"] for s in items))
        print(f"\n  {group_name}")
        print(f"    Phenomena: {', '.join(phenomena)}")
        print(f"    Conditions: {n_conditions}")
        print(f"    Models: {len(models)}")
        for m in models:
            m_items = [s for s in items if s["model"] == m]
            overall_mean = sum(s["mean"] for s in m_items) / len(m_items)
            print(f"      {m:<20} overall μ = {overall_mean:.2f}")


def export_csv(stats, output_path):
    """Export stats to CSV for further analysis in R/Excel."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("phenomenon,condition,model,n_items,n_ratings,mean,sd,expected\n")
        for s in stats:
            f.write(f"{s['phenomenon']},{s['condition']},{s['model']},"
                    f"{s['n_items']},{s['n_ratings']},{s['mean']},{s['sd']},{s['expected']}\n")
    print(f"\n  CSV exported → {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_results.py results/results_XXXX.json")
        print("       python analyze_results.py results/*.json")
        sys.exit(1)

    filepaths = sys.argv[1:]
    print(f"\n  Analyzing {len(filepaths)} file(s)...")

    results = load_results(filepaths)
    stats = compute_stats(results)

    print_by_phenomenon(stats)
    print_experiment_summary(stats)
    print_correlation_matrix(stats)

    # Auto-export CSV
    csv_path = os.path.splitext(filepaths[0])[0] + "_summary.csv"
    export_csv(stats, csv_path)

    print()


if __name__ == "__main__":
    main()
