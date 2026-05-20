#!/usr/bin/env python3
"""
Generate all visualizations for the polydefinite LLM experiment.
Compares LLM ratings against human data and paper claims.

Usage:
  python3 visualize_results.py results/polydefinite_20260519_004252.json
  python3 visualize_results.py  # uses latest results file
"""

import csv, json, math, os, sys, unicodedata
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(DIR, "figures")

# ============================================================
# ITEM CLASSIFICATION (from compare_to_paper.py)
# ============================================================

Q1_PAIRS = [
    ("sf_08", "sf_09", "restrictive"),
    ("sf_01", "sf_02", "restrictive"),
    ("sf_07", "sf_06", "non_restrictive"),
    ("sf_04", "sf_03", "non_restrictive"),
    ("sf_10", "sf_13", "contrast"),
    ("sf_11", "sf_12", "contrast"),
    ("sf_14", "sf_15", "recall_short"),
    ("sf_18", "sf_19", "recall_short"),
    ("sf_16", "sf_17", "recall_long"),
    ("sf_38", "sf_37", "recall_short"),
    ("sf_40", "sf_39", "recall_long"),
    ("sf_23", "sf_20", "single_reference"),
    ("sf_22", "sf_21", "single_reference"),
    ("sf_44", "sf_43", "narrative"),
    ("sf_41", "sf_42", "narrative"),
    ("sf_49", "sf_50", "narrative"),
]

WORD_ORDER = {
    "sf_26": "SVO", "sf_27": "VSO", "sf_28": "VOS",
    "sf_29": "OVS", "sf_30": "OSV", "sf_31": "SOV",
    "sf_25": "SVO", "sf_32": "VSO", "sf_33": "VOS",
    "sf_34": "OVS", "sf_35": "OSV", "sf_36": "SOV",
}

Q2_PAIRS = [
    ("sf_q2_01", "sf_q2_02", "jrijoros", "contrast"),
    ("sf_q2_13", "sf_q2_14", "jrijoros", "recall"),
    ("sf_q2_03", "sf_q2_04", "oreos", "contrast"),
    ("sf_q2_15", "sf_q2_16", "oreos", "recall"),
    ("sf_q2_05", "sf_q2_06", "proin", "contrast"),
    ("sf_q2_17", "sf_q2_18", "proin", "recall"),
    ("sf_q2_07", "sf_q2_08", "Italikos", "contrast"),
    ("sf_q2_19", "sf_q2_20", "Italikos", "recall"),
    ("sf_q2_09", "sf_q2_10", "ekpliktikos", "contrast"),
    ("sf_q2_21", "sf_q2_22", "ekpliktikos", "recall"),
    ("sf_q2_11", "sf_q2_12", "feromenos", "contrast"),
    ("sf_q2_23", "sf_q2_24", "feromenos", "recall"),
    ("sf_q2_25", "sf_q2_26", "dhilitiriodhis", "recall"),
    ("sf_q2_27", "sf_q2_28", "dhilitiriodhis_clld", "recall"),
]

# ============================================================
# DATA LOADING
# ============================================================

def norm(s):
    return unicodedata.normalize('NFKD', s).strip()

def load_stimuli():
    path = os.path.join(DIR, "stimuli", "shared", "semantic_felicity.jsonl")
    items = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                it = json.loads(line)
                items[it["id"]] = it
    return items

def load_human_data(stimuli):
    item_lookup = {}
    for item_id, it in stimuli.items():
        ctx = norm(it.get("context", ""))
        sent = norm(it["sentence"])
        item_lookup[item_id] = (ctx, sent)

    def match_header(h):
        hn = norm(h)
        for item_id, (ctx, sent) in item_lookup.items():
            if ctx and ctx[:40] in hn and sent in hn:
                return item_id
        return None

    def parse_csv(path, skip_cols):
        matched = {}
        with open(os.path.join(DIR, path), encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)
            col_map = {}
            for i, h in enumerate(header):
                if i < skip_cols:
                    continue
                item_id = match_header(h)
                if item_id and item_id not in col_map.values():
                    col_map[i] = item_id
            for col_i, item_id in col_map.items():
                ratings = []
                for row in rows:
                    if col_i < len(row) and row[col_i].strip():
                        try:
                            r = float(row[col_i].strip())
                            if 1 <= r <= 10:
                                ratings.append(r)
                        except:
                            pass
                if ratings:
                    m = sum(ratings) / len(ratings)
                    matched[item_id] = {"mean": m, "n": len(ratings)}
        return matched

    h1 = parse_csv("Σημασιολογική Καταλληλότητα_main.csv", 13)
    h2 = parse_csv("Σημασιολογική Καταλληλότητα_2.csv", 12)
    return {**h1, **h2}

def load_llm_results(path):
    with open(os.path.join(DIR, path), encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    for r in data["results"]:
        model = r["model"]
        if model not in out:
            out[model] = {}
        if r["mean"] is not None:
            out[model][r["id"]] = {"mean": r["mean"], "ratings": r["ratings"]}
    return out

def pearson(x, y):
    n = len(x)
    if n < 3:
        return None
    mx, my = sum(x)/n, sum(y)/n
    num = sum((a-mx)*(b-my) for a, b in zip(x, y))
    dx = math.sqrt(sum((a-mx)**2 for a in x))
    dy = math.sqrt(sum((b-my)**2 for b in y))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)

# ============================================================
# STYLE
# ============================================================

MODEL_SHORT = {
    "gpt-4o": "GPT-4o",
    "DeepSeek-V3.1": "DS-V3.1",
    "DeepSeek-V4-Pro": "DS-V4-Pro",
    "DeepSeek-V4-Flash": "DS-V4-Fl",
    "DeepSeek-R1": "DS-R1",
    "Llama-3.3-70B": "Llama-70B",
    "Mistral-Large-3": "Mistral-L3",
    "grok-4-20-non-reasoning": "Grok-NR",
    "grok-4-1-fast-reasoning": "Grok-R",
}

MODEL_COLORS = {
    "gpt-4o": "#10a37f",
    "DeepSeek-V3.1": "#4e79a7",
    "DeepSeek-V4-Pro": "#1b4f72",
    "DeepSeek-V4-Flash": "#76b7b2",
    "DeepSeek-R1": "#59a14f",
    "Llama-3.3-70B": "#9c755f",
    "Mistral-Large-3": "#f28e2b",
    "grok-4-20-non-reasoning": "#e15759",
    "grok-4-1-fast-reasoning": "#b07aa1",
}

HUMAN_COLOR = "#2c2c2c"
PAPER_COLOR = "#888888"

MODEL_ORDER = ["gpt-4o", "DeepSeek-V3.1", "DeepSeek-V4-Pro", "DeepSeek-V4-Flash",
               "DeepSeek-R1", "Llama-3.3-70B", "Mistral-Large-3",
               "grok-4-20-non-reasoning", "grok-4-1-fast-reasoning"]

def setup_style():
    plt.rcParams.update({
        'font.size': 11,
        'axes.titlesize': 13,
        'axes.labelsize': 11,
        'figure.facecolor': 'white',
        'axes.facecolor': '#fafafa',
        'axes.grid': True,
        'grid.alpha': 0.3,
        'figure.dpi': 150,
    })

# ============================================================
# FIGURE 1: Overall correlation bar chart
# ============================================================

def fig1_correlations(human, llm):
    models = [m for m in MODEL_ORDER if m in llm]
    all_ids = sorted(human.keys())

    correlations = []
    for model in models:
        l = llm[model]
        common = [k for k in all_ids if k in l]
        h_vals = [human[k]["mean"] for k in common]
        l_vals = [l[k]["mean"] for k in common]
        r = pearson(h_vals, l_vals)
        correlations.append(r if r else 0)

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(models))
    bars = ax.bar(x, correlations, color=[MODEL_COLORS[m] for m in models], width=0.7, edgecolor='white')

    ax.set_ylabel("Pearson r (item-level)")
    ax.set_title("Correlation with Human Ratings (item-level)")
    ax.set_xticks(x)
    ax.set_xticklabels([MODEL_SHORT[m] for m in models], rotation=30, ha='right')
    ax.set_ylim(0, 1)
    ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, label='r = 0.5')

    for bar, val in zip(bars, correlations):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{val:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig1_correlations.png"))
    plt.savefig(os.path.join(OUT_DIR, "fig1_correlations.pdf"))
    plt.close()
    print("  Fig 1: Correlations")


# ============================================================
# FIGURE 2: Scatter plot - human vs best LLM (per item)
# ============================================================

def fig2_scatter(human, llm):
    best_models = ["DeepSeek-V4-Pro", "DeepSeek-V4-Flash", "grok-4-1-fast-reasoning"]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for ax, model in zip(axes, best_models):
        if model not in llm:
            continue
        l = llm[model]
        common = sorted(set(human.keys()) & set(l.keys()))
        h_vals = [human[k]["mean"] for k in common]
        l_vals = [l[k]["mean"] for k in common]
        r = pearson(h_vals, l_vals)

        ax.scatter(h_vals, l_vals, alpha=0.6, s=30, color=MODEL_COLORS[model], edgecolors='white', linewidth=0.5)
        ax.plot([1, 10], [1, 10], 'k--', alpha=0.3, label='y = x')

        # Regression line
        if r:
            z = np.polyfit(h_vals, l_vals, 1)
            p = np.poly1d(z)
            xs = np.linspace(1, 10, 100)
            ax.plot(xs, p(xs), color=MODEL_COLORS[model], alpha=0.7, linewidth=2)

        ax.set_xlabel("Human mean")
        ax.set_ylabel("LLM rating")
        ax.set_title(f"{MODEL_SHORT[model]} (r={r:.2f})")
        ax.set_xlim(1, 10.5)
        ax.set_ylim(0.5, 10.5)
        ax.legend(fontsize=8)

    plt.suptitle("Human vs LLM Ratings (per item)", fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig2_scatter.png"), bbox_inches='tight')
    plt.savefig(os.path.join(OUT_DIR, "fig2_scatter.pdf"), bbox_inches='tight')
    plt.close()
    print("  Fig 2: Scatter plots")


# ============================================================
# FIGURE 3: Word order hierarchy
# ============================================================

def fig3_word_order(human, llm):
    wo_order = ["SVO", "VSO", "VOS", "OVS", "OSV", "SOV"]
    paper_means = {"SVO": 9.9, "VSO": 9.0, "VOS": 8.4, "OVS": 5.8, "OSV": 3.4, "SOV": 3.6}

    wo_items = {}
    for item_id, wo in WORD_ORDER.items():
        wo_items.setdefault(wo, []).append(item_id)

    def wo_means(data, is_human=False):
        means = []
        for wo in wo_order:
            vals = []
            for k in wo_items[wo]:
                if k in data:
                    v = data[k]["mean"] if isinstance(data[k], dict) else data[k]
                    vals.append(v)
            means.append(sum(vals)/len(vals) if vals else 0)
        return means

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(wo_order))
    width = 0.08

    # Paper
    paper_vals = [paper_means[wo] for wo in wo_order]
    ax.bar(x - 5*width, paper_vals, width, label='Paper', color=PAPER_COLOR, edgecolor='white')

    # Human
    h_vals = wo_means(human, True)
    ax.bar(x - 4*width, h_vals, width, label='Humans', color=HUMAN_COLOR, edgecolor='white')

    # LLMs
    show_models = ["gpt-4o", "DeepSeek-V4-Pro", "DeepSeek-V3.1", "Llama-3.3-70B",
                   "grok-4-20-non-reasoning", "grok-4-1-fast-reasoning"]
    for i, model in enumerate(show_models):
        if model not in llm:
            continue
        l_vals = wo_means(llm[model])
        ax.bar(x + (i-3)*width, l_vals, width, label=MODEL_SHORT[model],
               color=MODEL_COLORS[model], edgecolor='white')

    ax.set_ylabel("Mean rating (1-10)")
    ax.set_title("Word Order Acceptability (Paper benchmark)")
    ax.set_xticks(x)
    ax.set_xticklabels(wo_order, fontsize=12, fontweight='bold')
    ax.set_ylim(0, 11)
    ax.legend(loc='lower left', fontsize=8, ncol=2)

    # Add dividing line between acceptable and unacceptable
    ax.axvline(x=2.5, color='red', linestyle=':', alpha=0.5)
    ax.text(1.0, 0.5, 'Acceptable\nword orders', ha='center', fontsize=9, color='green', alpha=0.7)
    ax.text(4.0, 0.5, 'Unacceptable\nword orders', ha='center', fontsize=9, color='red', alpha=0.7)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig3_word_order.png"))
    plt.savefig(os.path.join(OUT_DIR, "fig3_word_order.pdf"))
    plt.close()
    print("  Fig 3: Word order")


# ============================================================
# FIGURE 4: Poly vs Mono difference (Q1 intersective)
# ============================================================

def fig4_poly_mono_diff(human, llm):
    models = [m for m in MODEL_ORDER if m in llm]

    # Compute mean poly-mono diff for each source
    sources = ["Humans"] + [MODEL_SHORT[m] for m in models]
    diffs = []

    # Human
    h_diffs = []
    for poly_id, mono_id, ctx in Q1_PAIRS:
        hp = human.get(poly_id, {}).get("mean") if isinstance(human.get(poly_id), dict) else None
        hm = human.get(mono_id, {}).get("mean") if isinstance(human.get(mono_id), dict) else None
        if hp is not None and hm is not None:
            h_diffs.append(hp - hm)
    diffs.append(sum(h_diffs)/len(h_diffs) if h_diffs else 0)

    # LLMs
    for model in models:
        l = llm[model]
        m_diffs = []
        for poly_id, mono_id, ctx in Q1_PAIRS:
            lp = l.get(poly_id, {}).get("mean") if isinstance(l.get(poly_id), dict) else None
            lm = l.get(mono_id, {}).get("mean") if isinstance(l.get(mono_id), dict) else None
            if lp is not None and lm is not None:
                m_diffs.append(lp - lm)
        diffs.append(sum(m_diffs)/len(m_diffs) if m_diffs else 0)

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = [HUMAN_COLOR] + [MODEL_COLORS[m] for m in models]
    x = np.arange(len(sources))
    bars = ax.bar(x, diffs, color=colors, width=0.7, edgecolor='white')

    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.axhspan(-1, 1, alpha=0.1, color='green', label='Paper range (-0.68 to +0.21)')
    ax.set_ylabel("Mean poly − mono difference")
    ax.set_title("Poly vs Mono Difference (Q1 intersective adjectives)\nPaper: difference is small and non-significant")
    ax.set_xticks(x)
    ax.set_xticklabels(sources, rotation=30, ha='right')
    ax.set_ylim(-5, 3)

    for bar, val in zip(bars, diffs):
        y_pos = val + 0.15 if val >= 0 else val - 0.3
        ax.text(bar.get_x() + bar.get_width()/2, y_pos,
                f'{val:+.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig4_poly_mono_diff.png"))
    plt.savefig(os.path.join(OUT_DIR, "fig4_poly_mono_diff.pdf"))
    plt.close()
    print("  Fig 4: Poly-mono diff")


# ============================================================
# FIGURE 5: Non-intersective adjectives (Table 2 comparison)
# ============================================================

def fig5_nonintersective(human, llm):
    adj_order = ["jrijoros", "oreos", "ekpliktikos", "Italikos", "proin", "feromenos"]
    adj_labels = ["jrijoros\n'fast'", "oreos\n'beautiful'", "ekpliktikos\n'amazing'",
                  "Italikos\n'Italian'", "proin\n'ex'", "feromenos\n'alleged'"]

    # Paper Table 2 values (contrast context, poly)
    paper_poly = {"jrijoros": 7.72, "oreos": 7.94, "ekpliktikos": 6.78,
                  "Italikos": 7.06, "proin": 5.39, "feromenos": 4.89}
    paper_mono = {"jrijoros": 9.61, "oreos": 7.44, "ekpliktikos": 9.33,
                  "Italikos": 8.72, "proin": 9.33, "feromenos": 8.78}

    # Get human and LLM values for contrast context
    contrast_pairs = {adj: (p, m) for p, m, adj, ctx in Q2_PAIRS if ctx == "contrast" and adj in adj_order}

    show_models = ["DeepSeek-V4-Pro", "DeepSeek-V4-Flash", "gpt-4o", "grok-4-20-non-reasoning"]

    fig, axes = plt.subplots(2, 3, figsize=(14, 9))
    axes = axes.flatten()

    for idx, (adj, label) in enumerate(zip(adj_order, adj_labels)):
        ax = axes[idx]
        poly_id, mono_id = contrast_pairs.get(adj, (None, None))
        if not poly_id:
            continue

        sources = ["Paper", "Humans"] + [MODEL_SHORT[m] for m in show_models if m in llm]
        poly_vals = [paper_poly[adj]]
        mono_vals = [paper_mono[adj]]

        # Human
        hp = human.get(poly_id, {}).get("mean", 0) if isinstance(human.get(poly_id), dict) else 0
        hm = human.get(mono_id, {}).get("mean", 0) if isinstance(human.get(mono_id), dict) else 0
        poly_vals.append(hp)
        mono_vals.append(hm)

        for model in show_models:
            if model not in llm:
                continue
            l = llm[model]
            lp = l.get(poly_id, {}).get("mean", 0) if isinstance(l.get(poly_id), dict) else 0
            lm = l.get(mono_id, {}).get("mean", 0) if isinstance(l.get(mono_id), dict) else 0
            poly_vals.append(lp)
            mono_vals.append(lm)

        x = np.arange(len(sources))
        width = 0.35
        ax.bar(x - width/2, poly_vals, width, label='Polydefinite', color='#e15759', alpha=0.8, edgecolor='white')
        ax.bar(x + width/2, mono_vals, width, label='Monodefinite', color='#4e79a7', alpha=0.8, edgecolor='white')

        ax.set_title(label, fontsize=11, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(sources, rotation=45, ha='right', fontsize=8)
        ax.set_ylim(0, 11)
        ax.set_ylabel("Mean rating")
        if idx == 0:
            ax.legend(fontsize=8)

    plt.suptitle("Non-intersective Adjectives: Poly vs Mono (contrast context)\nPaper Table 2 comparison",
                 fontsize=13, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig5_nonintersective.png"), bbox_inches='tight')
    plt.savefig(os.path.join(OUT_DIR, "fig5_nonintersective.pdf"), bbox_inches='tight')
    plt.close()
    print("  Fig 5: Non-intersective adjectives")


# ============================================================
# FIGURE 6: feromenos detail (contrast vs recall, poly vs mono)
# ============================================================

def fig6_feromenos(human, llm):
    models = [m for m in MODEL_ORDER if m in llm]

    fero_items = {
        "Poly (contrast)": "sf_q2_11",
        "Mono (contrast)": "sf_q2_12",
        "Poly (recall)": "sf_q2_23",
        "Mono (recall)": "sf_q2_24",
    }

    paper_vals = {"Poly (contrast)": 4.89, "Mono (contrast)": 8.78,
                  "Poly (recall)": 6.00, "Mono (recall)": 9.22}

    fig, ax = plt.subplots(figsize=(12, 6))

    conditions = list(fero_items.keys())
    sources = ["Paper", "Humans"] + [MODEL_SHORT[m] for m in models]
    n_sources = len(sources)
    x = np.arange(len(conditions))
    width = 0.8 / n_sources

    # Paper
    vals = [paper_vals[c] for c in conditions]
    ax.bar(x - 0.4 + 0*width, vals, width, label='Paper', color=PAPER_COLOR, edgecolor='white')

    # Human
    vals = []
    for c in conditions:
        item_id = fero_items[c]
        v = human.get(item_id, {}).get("mean", 0) if isinstance(human.get(item_id), dict) else 0
        vals.append(v)
    ax.bar(x - 0.4 + 1*width, vals, width, label='Humans', color=HUMAN_COLOR, edgecolor='white')

    # LLMs
    for i, model in enumerate(models):
        l = llm[model]
        vals = []
        for c in conditions:
            item_id = fero_items[c]
            v = l.get(item_id, {}).get("mean", 0) if isinstance(l.get(item_id), dict) else 0
            vals.append(v)
        ax.bar(x - 0.4 + (i+2)*width, vals, width, label=MODEL_SHORT[model],
               color=MODEL_COLORS[model], edgecolor='white')

    ax.set_ylabel("Mean rating (1-10)")
    ax.set_title("feromenos 'alleged' — Lowest-rated non-intersective adjective\nPaper: poly(contrast)=4.89, poly(recall)=6.00")
    ax.set_xticks(x)
    ax.set_xticklabels(conditions, fontsize=11, fontweight='bold')
    ax.set_ylim(0, 11)
    ax.legend(loc='upper right', fontsize=7, ncol=3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig6_feromenos.png"))
    plt.savefig(os.path.join(OUT_DIR, "fig6_feromenos.pdf"))
    plt.close()
    print("  Fig 6: feromenos detail")


# ============================================================
# FIGURE 7: Poly violations vs word-order violations
# ============================================================

def fig7_violation_gradient(human, llm):
    models = [m for m in MODEL_ORDER if m in llm]

    worst_poly_ids = ["sf_q2_11", "sf_04", "sf_q2_05"]
    worst_wo_ids = ["sf_30", "sf_35", "sf_31", "sf_36"]
    mid_poly_ids = ["sf_07", "sf_22", "sf_44"]  # non-restrictive polys

    def mean_of(data, ids):
        vals = []
        for k in ids:
            v = data.get(k)
            if isinstance(v, dict) and v.get("mean") is not None:
                vals.append(v["mean"])
        return sum(vals)/len(vals) if vals else 0

    categories = ["Worst word order\n(OSV/SOV)", "Worst polydefinite\n(feromenos/unique)", "Non-restrictive\npolydefinite"]
    sources = ["Humans"] + [MODEL_SHORT[m] for m in models]

    data_matrix = []
    # Human
    data_matrix.append([mean_of(human, worst_wo_ids), mean_of(human, worst_poly_ids), mean_of(human, mid_poly_ids)])

    for model in models:
        l = llm[model]
        data_matrix.append([mean_of(l, worst_wo_ids), mean_of(l, worst_poly_ids), mean_of(l, mid_poly_ids)])

    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(sources))
    width = 0.25
    colors = ['#e15759', '#f28e2b', '#59a14f']

    for i, (cat, color) in enumerate(zip(categories, colors)):
        vals = [row[i] for row in data_matrix]
        ax.bar(x + (i-1)*width, vals, width, label=cat, color=color, edgecolor='white', alpha=0.85)

    ax.set_ylabel("Mean rating (1-10)")
    ax.set_title("Violation Gradient: Word Order > Polydefinite > Non-restrictive\nPaper: poly violations are discourse-structural, never as bad as grammatical violations")
    ax.set_xticks(x)
    ax.set_xticklabels(sources, rotation=30, ha='right')
    ax.set_ylim(0, 11)
    ax.legend(fontsize=9)
    ax.axhline(y=5, color='gray', linestyle='--', alpha=0.3, label='midpoint')

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig7_violation_gradient.png"))
    plt.savefig(os.path.join(OUT_DIR, "fig7_violation_gradient.pdf"))
    plt.close()
    print("  Fig 7: Violation gradient")


# ============================================================
# FIGURE 8: Recall short vs long
# ============================================================

def fig8_recall(human, llm):
    models = [m for m in MODEL_ORDER if m in llm]

    short_poly = ["sf_14", "sf_18", "sf_38"]
    long_poly = ["sf_16", "sf_40"]
    short_mono = ["sf_15", "sf_19", "sf_37"]
    long_mono = ["sf_17", "sf_39"]

    def mean_of(data, ids):
        vals = []
        for k in ids:
            v = data.get(k)
            if isinstance(v, dict) and v.get("mean") is not None:
                vals.append(v["mean"])
        return sum(vals)/len(vals) if vals else 0

    categories = ["Short poly", "Long poly", "Short mono", "Long mono"]
    id_groups = [short_poly, long_poly, short_mono, long_mono]

    paper_vals = [6.82, 8.35, 6.74, 8.44]

    sources = ["Paper", "Humans"] + [MODEL_SHORT[m] for m in models]

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(categories))
    n = len(sources)
    width = 0.8 / n

    # Paper
    ax.bar(x - 0.4 + 0*width, paper_vals, width, label='Paper', color=PAPER_COLOR, edgecolor='white')

    # Human
    h_vals = [mean_of(human, ids) for ids in id_groups]
    ax.bar(x - 0.4 + 1*width, h_vals, width, label='Humans', color=HUMAN_COLOR, edgecolor='white')

    # LLMs
    for i, model in enumerate(models):
        l = llm[model]
        l_vals = [mean_of(l, ids) for ids in id_groups]
        ax.bar(x - 0.4 + (i+2)*width, l_vals, width, label=MODEL_SHORT[model],
               color=MODEL_COLORS[model], edgecolor='white')

    ax.set_ylabel("Mean rating (1-10)")
    ax.set_title("Recall Short vs Long (relative clause effect)\nPaper: Long > Short is the only significant difference")
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11, fontweight='bold')
    ax.set_ylim(0, 11)
    ax.legend(loc='lower right', fontsize=7, ncol=3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig8_recall.png"))
    plt.savefig(os.path.join(OUT_DIR, "fig8_recall.pdf"))
    plt.close()
    print("  Fig 8: Recall short vs long")


# ============================================================
# FIGURE 9: Overall mean comparison
# ============================================================

def fig9_overall_means(human, llm):
    models = [m for m in MODEL_ORDER if m in llm]

    fig, ax = plt.subplots(figsize=(10, 5))

    # Human
    h_mean = sum(human[k]["mean"] for k in human) / len(human)
    sources = ["Humans"] + [MODEL_SHORT[m] for m in models]
    means = [h_mean]

    for model in models:
        l = llm[model]
        l_mean = sum(l[k]["mean"] for k in l) / len(l)
        means.append(l_mean)

    colors = [HUMAN_COLOR] + [MODEL_COLORS[m] for m in models]
    x = np.arange(len(sources))
    bars = ax.bar(x, means, color=colors, width=0.7, edgecolor='white')

    ax.axhline(y=h_mean, color=HUMAN_COLOR, linestyle='--', alpha=0.5, label=f'Human mean ({h_mean:.1f})')
    ax.set_ylabel("Overall mean rating (1-10)")
    ax.set_title("Overall Mean Rating Across All Items")
    ax.set_xticks(x)
    ax.set_xticklabels(sources, rotation=30, ha='right')
    ax.set_ylim(0, 11)

    for bar, val in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15,
                f'{val:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig9_overall_means.png"))
    plt.savefig(os.path.join(OUT_DIR, "fig9_overall_means.pdf"))
    plt.close()
    print("  Fig 9: Overall means")


# ============================================================
# FIGURE 10: Heatmap - items x models
# ============================================================

def fig10_heatmap(human, llm):
    models = [m for m in MODEL_ORDER if m in llm]
    all_ids = sorted(human.keys())

    # Build matrix
    sources = ["Humans"] + models
    matrix = []

    # Human row
    h_row = [human[k]["mean"] for k in all_ids]
    matrix.append(h_row)

    for model in models:
        l = llm[model]
        row = [l[k]["mean"] if k in l else np.nan for k in all_ids]
        matrix.append(row)

    matrix = np.array(matrix)

    fig, ax = plt.subplots(figsize=(18, 6))
    im = ax.imshow(matrix, aspect='auto', cmap='RdYlGn', vmin=1, vmax=10)

    ax.set_yticks(range(len(sources)))
    ax.set_yticklabels(["Humans"] + [MODEL_SHORT[m] for m in models], fontsize=9)

    # Show every 5th item label
    tick_positions = list(range(0, len(all_ids), 5))
    ax.set_xticks(tick_positions)
    ax.set_xticklabels([all_ids[i] for i in tick_positions], rotation=90, fontsize=7)

    ax.set_title("Rating Heatmap: All Items × All Sources")
    plt.colorbar(im, ax=ax, label="Rating (1-10)", shrink=0.8)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig10_heatmap.png"), dpi=200)
    plt.savefig(os.path.join(OUT_DIR, "fig10_heatmap.pdf"))
    plt.close()
    print("  Fig 10: Heatmap")


# ============================================================
# MAIN
# ============================================================

def main():
    setup_style()
    os.makedirs(OUT_DIR, exist_ok=True)

    # Find result file
    if len(sys.argv) > 1:
        llm_file = sys.argv[1]
    else:
        results_dir = os.path.join(DIR, "results")
        result_files = sorted([f for f in os.listdir(results_dir)
                               if f.startswith("polydefinite_") and f.endswith(".json")])
        if not result_files:
            print("ERROR: No result files found")
            sys.exit(1)
        llm_file = os.path.join("results", result_files[-1])

    print(f"Loading data...")
    stimuli = load_stimuli()
    human = load_human_data(stimuli)
    llm = load_llm_results(llm_file)

    print(f"  Human items: {len(human)}")
    print(f"  LLM models: {len(llm)}")
    print(f"  Results file: {llm_file}")

    print(f"\nGenerating figures in {OUT_DIR}/...")
    fig1_correlations(human, llm)
    fig2_scatter(human, llm)
    fig3_word_order(human, llm)
    fig4_poly_mono_diff(human, llm)
    fig5_nonintersective(human, llm)
    fig6_feromenos(human, llm)
    fig7_violation_gradient(human, llm)
    fig8_recall(human, llm)
    fig9_overall_means(human, llm)
    fig10_heatmap(human, llm)

    print(f"\nDone. 10 figures saved to {OUT_DIR}/")
    print(f"  PNG (for presentations) + PDF (for paper)")


if __name__ == "__main__":
    main()
