#!/usr/bin/env python3
"""
Compare LLM experiment results against the main claims of:
  Chatzikyriakidis & Spathas - "Polydefinites as Markers of Prominence"

Uses both result files:
  - temp=0, 1 rep:   results/polydefinite_20260519_004252.json
  - temp=0.7, 3 reps: results/polydefinite_20260519_133331.json

And human data from:
  - Σημασιολογική Καταλληλότητα_main.csv  (Q1, 35 participants)
  - Σημασιολογική Καταλληλότητα_2.csv      (Q2, 19 participants)
"""

import csv, json, math, os, sys, unicodedata

DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# ITEM CLASSIFICATION (manual, based on the paper)
# ============================================================

# Q1 minimal pairs: (poly_id, mono_id, context_type)
# Context types from Table 1 of the paper
Q1_PAIRS = [
    # Restrictive context (two referents -> restrictive reading available)
    ("sf_08", "sf_09", "restrictive"),        # 4 black + 2 white cats
    ("sf_01", "sf_02", "restrictive"),        # two brothers

    # Non-restrictive (unique referent, no restrictive reading possible)
    ("sf_07", "sf_06", "non_restrictive"),    # all cats black - poly/mono
    ("sf_04", "sf_03", "non_restrictive"),    # one brother - poly/mono

    # Contrast (contrastive topic)
    ("sf_10", "sf_13", "contrast"),           # small cats vs parrots
    ("sf_11", "sf_12", "contrast"),           # black dogs vs rabbits

    # Recall short (recall context, no relative clause)
    ("sf_14", "sf_15", "recall_short"),       # bushes short
    ("sf_18", "sf_19", "recall_short"),       # bushes short variant

    # Recall long (recall context + relative clause)
    ("sf_16", "sf_17", "recall_long"),        # bushes + relative clause

    # Single reference (proper names, established entities)
    ("sf_23", "sf_20", "single_reference"),   # PAOK poly/mono
    ("sf_22", "sf_21", "single_reference"),   # Kostas Papadopoulos poly/mono

    # Narrative (new definite in narrative)
    ("sf_44", "sf_43", "narrative"),          # car, new info context
    ("sf_41", "sf_42", "narrative"),          # car, old info context
    ("sf_49", "sf_50", "narrative"),          # cold weather
]

# Word order items: (item_id, word_order)
# From paper examples (15)-(20): SVO=9.9, VSO=9.0, VOS=8.4, OVS=5.8, OSV=3.4, SOV=3.6
WORD_ORDER = {
    # Set 1: Jagos tilefonise sti Virna
    "sf_26": "SVO",   # Ο Γιάγκος τηλεφώνησε στη Βίρνα
    "sf_27": "VSO",   # Τηλεφώνησε ο Γιάγκος στη Βίρνα
    "sf_28": "VOS",   # Τηλεφώνησε στη Βίρνα ο Γιάγκος
    "sf_29": "OVS",   # Στη Βίρνα τηλεφώνησε ο Γιάγκος
    "sf_30": "OSV",   # Στη Βίρνα ο Γιάγκος τηλεφώνησε
    "sf_31": "SOV",   # Ο Γιάγκος, στη Βίρνα τηλεφώνησε

    # Set 2: To fortigo trakarase ti motosikleta
    "sf_25": "SVO",   # Tο φορτηγό τράκαρε τη μοτοσυκλέτα
    "sf_32": "VSO",   # Tράκαρε το φορτηγό τη μοτοσυκλέτα
    "sf_33": "VOS",   # Tράκαρε τη μοτοσυκλέτα το φορτηγό
    "sf_34": "OVS",   # Tη μοτοσυκλέτα τράκαρε το φορτηγό
    "sf_35": "OSV",   # Τη μοτοσυκλέτα το φορτηγό τράκαρε
    "sf_36": "SOV",   # Το φορτηγό, τη μοτοσυκλέτα τράκαρε
}

# Q2 minimal pairs: non-intersective adjectives (poly_id, mono_id, adjective, context_type)
# From paper's Table 2 and section 2.2
Q2_PAIRS = [
    # jrijoros 'fast' (subsective, highest rated in paper)
    ("sf_q2_01", "sf_q2_02", "jrijoros", "contrast"),
    ("sf_q2_13", "sf_q2_14", "jrijoros", "recall"),

    # oreos 'beautiful' (subsective)
    ("sf_q2_03", "sf_q2_04", "oreos", "contrast"),
    ("sf_q2_15", "sf_q2_16", "oreos", "recall"),

    # proin 'ex' (privative)
    ("sf_q2_05", "sf_q2_06", "proin", "contrast"),
    ("sf_q2_17", "sf_q2_18", "proin", "recall"),

    # Italikos 'Italian' (ethnic)
    ("sf_q2_07", "sf_q2_08", "Italikos", "contrast"),
    ("sf_q2_19", "sf_q2_20", "Italikos", "recall"),

    # ekpliktikos 'amazing' (predicational)
    ("sf_q2_09", "sf_q2_10", "ekpliktikos", "contrast"),
    ("sf_q2_21", "sf_q2_22", "ekpliktikos", "recall"),

    # feromenos 'alleged' (non-subsective, lowest rated in paper)
    ("sf_q2_11", "sf_q2_12", "feromenos", "contrast"),
    ("sf_q2_23", "sf_q2_24", "feromenos", "recall"),

    # dhilitiriodhis 'poisonous' (special: non-restrictive only for cobras)
    ("sf_q2_25", "sf_q2_26", "dhilitiriodhis", "recall"),
    ("sf_q2_27", "sf_q2_28", "dhilitiriodhis_clld", "recall"),
]

# Numeral polydefinites (both poly, different contexts)
NUMERAL_ITEMS = ["sf_q2_29", "sf_q2_30"]

# Epithet items (separate phenomenon per paper's Appendix B)
EPITHET_ITEMS = {
    "sf_45": "epithet_poly",      # ο καμένος ο μπάρμαν
    "sf_46": "epithet_mono",      # ο καμένος μπάρμαν
    "sf_47": "epithet_right_dis", # ο μπάρμαν, ο καμένος
    "sf_48": "epithet_inverted",  # ο μπάρμαν ο καμένος
}

# Recall items with laptop (additional recall pair from Q1)
RECALL_LAPTOP = [
    ("sf_38", "sf_37", "recall_short"),  # laptop poly/mono short
    ("sf_40", "sf_39", "recall_long"),   # laptop poly/mono long
]


# ============================================================
# LOAD DATA
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
    """Load human ratings from both CSVs, matched by context+sentence."""
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
                    sd = (sum((r - m)**2 for r in ratings) / (len(ratings)-1))**0.5 if len(ratings) > 1 else 0
                    matched[item_id] = {"mean": m, "sd": sd, "n": len(ratings), "ratings": ratings}
        return matched

    h1 = parse_csv("Σημασιολογική Καταλληλότητα_main.csv", 13)
    h2 = parse_csv("Σημασιολογική Καταλληλότητα_2.csv", 12)
    return {**h1, **h2}

def load_llm_results(path):
    """Load LLM results, return dict: model -> item_id -> {mean, sd, ratings}."""
    with open(os.path.join(DIR, path), encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    for r in data["results"]:
        model = r["model"]
        if model not in out:
            out[model] = {}
        if r["mean"] is not None:
            out[model][r["id"]] = {
                "mean": r["mean"],
                "sd": r.get("sd"),
                "ratings": r["ratings"],
            }
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

def get_rating(data, item_id):
    """Get mean rating from a data dict (human or LLM model dict)."""
    if item_id in data:
        return data[item_id]["mean"] if isinstance(data[item_id], dict) else data[item_id]
    return None


# ============================================================
# ANALYSIS
# ============================================================

def print_header(title):
    print(f"\n{'='*75}")
    print(f"  {title}")
    print(f"{'='*75}")

def print_subheader(title):
    print(f"\n  {title}")
    print(f"  {'-'*65}")


def analyze_claim_1(human, llm, models):
    """CLAIM 1: Polydefinites are licit in non-restrictive contexts.
    Paper Table 1: poly means range 6.82-8.35, mono means range 6.74-8.44.
    """
    print_header("CLAIM 1: Polydefinites are licit in non-restrictive contexts")
    print("  Paper: Non-restrictive polydefinites score 6.8-8.7 (Table 1)")
    print("  Test: Do LLMs also rate non-restrictive polydefinites above midpoint (5)?")

    # Collect non-restrictive poly items
    non_restr_poly = []
    for poly_id, mono_id, ctx in Q1_PAIRS:
        if ctx in ("non_restrictive", "contrast", "recall_short", "recall_long", "single_reference", "narrative"):
            non_restr_poly.append(poly_id)
    for poly_id, mono_id, ctx in RECALL_LAPTOP:
        non_restr_poly.append(poly_id)

    print_subheader(f"Non-restrictive polydefinite items (n={len(non_restr_poly)})")
    print(f"  {'Source':<28} {'Mean':>6}  {'Above 5?':>8}  {'Items':>5}")

    # Human
    h_vals = [human[k]["mean"] for k in non_restr_poly if k in human]
    if h_vals:
        h_mean = sum(h_vals) / len(h_vals)
        above = sum(1 for v in h_vals if v >= 5)
        print(f"  {'HUMANS':<28} {h_mean:>6.2f}  {above}/{len(h_vals):>6}  {len(h_vals):>5}")

    for model in models:
        l = llm.get(model, {})
        l_vals = [l[k]["mean"] for k in non_restr_poly if k in l]
        if l_vals:
            l_mean = sum(l_vals) / len(l_vals)
            above = sum(1 for v in l_vals if v >= 5)
            print(f"  {model:<28} {l_mean:>6.2f}  {above}/{len(l_vals):>6}  {len(l_vals):>5}")


def analyze_claim_2(human, llm, models):
    """CLAIM 2: Poly-mono differences are small and non-significant.
    Paper Table 1: differences range from -0.68 to +0.21
    """
    print_header("CLAIM 2: Poly-mono differences are small")
    print("  Paper Table 1: differences range -0.68 to +0.21, never significant")
    print("  Test: What is the mean poly-mono difference per model?")

    all_pairs = Q1_PAIRS + RECALL_LAPTOP

    print_subheader(f"Mean poly-mono difference across Q1 pairs (n={len(all_pairs)})")
    print(f"  {'Source':<28} {'Poly mean':>9} {'Mono mean':>10} {'Diff':>6}  {'Range':>12}")

    # Human
    h_diffs = []
    h_poly_vals, h_mono_vals = [], []
    for poly_id, mono_id, ctx in all_pairs:
        hp = human.get(poly_id, {}).get("mean") if isinstance(human.get(poly_id), dict) else None
        hm = human.get(mono_id, {}).get("mean") if isinstance(human.get(mono_id), dict) else None
        if hp is not None and hm is not None:
            h_diffs.append(hp - hm)
            h_poly_vals.append(hp)
            h_mono_vals.append(hm)
    if h_diffs:
        print(f"  {'HUMANS':<28} {sum(h_poly_vals)/len(h_poly_vals):>9.2f} {sum(h_mono_vals)/len(h_mono_vals):>10.2f} {sum(h_diffs)/len(h_diffs):>+6.2f}  [{min(h_diffs):+.1f}, {max(h_diffs):+.1f}]")

    for model in models:
        l = llm.get(model, {})
        diffs = []
        poly_vals, mono_vals = [], []
        for poly_id, mono_id, ctx in all_pairs:
            lp = l.get(poly_id, {}).get("mean") if isinstance(l.get(poly_id), dict) else None
            lm = l.get(mono_id, {}).get("mean") if isinstance(l.get(mono_id), dict) else None
            if lp is not None and lm is not None:
                diffs.append(lp - lm)
                poly_vals.append(lp)
                mono_vals.append(lm)
        if diffs:
            print(f"  {model:<28} {sum(poly_vals)/len(poly_vals):>9.2f} {sum(mono_vals)/len(mono_vals):>10.2f} {sum(diffs)/len(diffs):>+6.2f}  [{min(diffs):+.1f}, {max(diffs):+.1f}]")


def analyze_claim_3(human, llm, models):
    """CLAIM 3: Word order violations provide a benchmark of real unacceptability.
    Paper: SVO=9.9, VSO=9.0, VOS=8.4 are acceptable
           OVS=5.8, OSV=3.4, SOV=3.6 are unacceptable in context
    """
    print_header("CLAIM 3: Word order as benchmark (SVO/VSO high, OVS/OSV/SOV low)")
    print("  Paper: SVO~9.9, VSO~9.0, VOS~8.4 | OVS~5.8, OSV~3.4, SOV~3.6")
    print("  Test: Do LLMs replicate this word-order hierarchy?")

    wo_order = ["SVO", "VSO", "VOS", "OVS", "OSV", "SOV"]
    wo_items = {}
    for item_id, wo in WORD_ORDER.items():
        wo_items.setdefault(wo, []).append(item_id)

    paper_means = {"SVO": 9.9, "VSO": 9.0, "VOS": 8.4, "OVS": 5.8, "OSV": 3.4, "SOV": 3.6}

    print_subheader("Mean rating by word order")
    header = f"  {'Source':<20}"
    for wo in wo_order:
        header += f" {wo:>5}"
    print(header)

    # Paper
    line = f"  {'PAPER':<20}"
    for wo in wo_order:
        line += f" {paper_means[wo]:>5.1f}"
    print(line)

    # Human
    line = f"  {'HUMANS':<20}"
    for wo in wo_order:
        vals = [human[k]["mean"] for k in wo_items[wo] if k in human]
        m = sum(vals) / len(vals) if vals else 0
        line += f" {m:>5.1f}"
    print(line)

    for model in models:
        l = llm.get(model, {})
        line = f"  {model:<20}"
        for wo in wo_order:
            vals = [l[k]["mean"] for k in wo_items[wo] if k in l]
            m = sum(vals) / len(vals) if vals else 0
            line += f" {m:>5.1f}"
        print(line)


def analyze_claim_4(human, llm, models):
    """CLAIM 4: Non-intersective adjectives in polydefinites score lower than monadics,
    but still above midpoint. feromenos 'alleged' is the lowest.
    Paper Table 2: feromenos poly contrast=4.89, recall=6.00
                   jrijoros poly contrast=7.72, recall=8.94
    """
    print_header("CLAIM 4: Non-intersective adj: poly < mono, feromenos lowest")
    print("  Paper Table 2: All poly versions score lower than mono")
    print("  feromenos is lowest (4.89 contrast, 6.00 recall)")
    print("  jrijoros is highest (7.72 contrast, 8.94 recall)")

    # Group by adjective
    adj_data = {}
    for poly_id, mono_id, adj, ctx in Q2_PAIRS:
        key = f"{adj} ({ctx})"
        adj_data[key] = (poly_id, mono_id, adj, ctx)

    # Paper Table 2 values
    paper_t2 = {
        "jrijoros (contrast)": (7.72, 9.61),
        "jrijoros (recall)": (8.94, 9.33),
        "oreos (contrast)": (7.94, 7.44),
        "oreos (recall)": (8.83, 8.89),
        "proin (contrast)": (5.39, 9.33),
        "proin (recall)": (7.22, 9.56),
        "Italikos (contrast)": (7.06, 8.72),
        "Italikos (recall)": (7.44, 9.95),
        "ekpliktikos (contrast)": (6.78, 9.33),
        "ekpliktikos (recall)": (7.28, 9.56),
        "feromenos (contrast)": (4.89, 8.78),
        "feromenos (recall)": (6.00, 9.22),
        "dhilitiriodhis (recall)": (7.72, 9.56),
    }

    print_subheader("Poly vs Mono by adjective type (Table 2 comparison)")

    for source_label, data_fn in [("PAPER", None), ("HUMANS", human)] + [(m, llm.get(m, {})) for m in models]:
        print(f"\n  {source_label}:")
        print(f"    {'Condition':<30} {'Poly':>5} {'Mono':>5} {'Diff':>6}")

        for key in sorted(adj_data.keys()):
            poly_id, mono_id, adj, ctx = adj_data[key]

            if source_label == "PAPER":
                if key in paper_t2:
                    p, m = paper_t2[key]
                    print(f"    {key:<30} {p:>5.1f} {m:>5.1f} {p-m:>+6.1f}")
                continue

            if source_label == "HUMANS":
                d = human
                p_val = d.get(poly_id, {}).get("mean") if isinstance(d.get(poly_id), dict) else None
                m_val = d.get(mono_id, {}).get("mean") if isinstance(d.get(mono_id), dict) else None
            else:
                d = data_fn
                p_val = d.get(poly_id, {}).get("mean") if isinstance(d.get(poly_id), dict) else None
                m_val = d.get(mono_id, {}).get("mean") if isinstance(d.get(mono_id), dict) else None

            if p_val is not None and m_val is not None:
                print(f"    {key:<30} {p_val:>5.1f} {m_val:>5.1f} {p_val-m_val:>+6.1f}")
            elif p_val is not None:
                print(f"    {key:<30} {p_val:>5.1f}   ---    ---")

        # Only show first 3 models in detail
        if source_label not in ["PAPER", "HUMANS"] and models.index(source_label) >= 3:
            break

    # Summary: feromenos poly across all sources
    print_subheader("Focus: feromenos polydefinite (lowest in paper)")
    fero_poly_contrast = "sf_q2_11"
    fero_poly_recall = "sf_q2_23"
    fero_mono_contrast = "sf_q2_12"
    fero_mono_recall = "sf_q2_24"

    print(f"  {'Source':<28} {'Poly(c)':>7} {'Mono(c)':>7} {'Poly(r)':>7} {'Mono(r)':>7}")
    print(f"  {'PAPER':<28} {'4.89':>7} {'8.78':>7} {'6.00':>7} {'9.22':>7}")

    hp = human.get(fero_poly_contrast, {})
    hm = human.get(fero_mono_contrast, {})
    hpr = human.get(fero_poly_recall, {})
    hmr = human.get(fero_mono_recall, {})
    h_pc = hp.get("mean", 0) if isinstance(hp, dict) else 0
    h_mc = hm.get("mean", 0) if isinstance(hm, dict) else 0
    h_pr = hpr.get("mean", 0) if isinstance(hpr, dict) else 0
    h_mr = hmr.get("mean", 0) if isinstance(hmr, dict) else 0
    print(f"  {'HUMANS':<28} {h_pc:>7.2f} {h_mc:>7.2f} {h_pr:>7.2f} {h_mr:>7.2f}")

    for model in models:
        l = llm.get(model, {})
        pc = l.get(fero_poly_contrast, {}).get("mean", 0) if isinstance(l.get(fero_poly_contrast), dict) else 0
        mc = l.get(fero_mono_contrast, {}).get("mean", 0) if isinstance(l.get(fero_mono_contrast), dict) else 0
        pr = l.get(fero_poly_recall, {}).get("mean", 0) if isinstance(l.get(fero_poly_recall), dict) else 0
        mr = l.get(fero_mono_recall, {}).get("mean", 0) if isinstance(l.get(fero_mono_recall), dict) else 0
        print(f"  {model:<28} {pc:>7.1f} {mc:>7.1f} {pr:>7.1f} {mr:>7.1f}")


def analyze_claim_5(human, llm, models):
    """CLAIM 5: Recall contexts (long definites with relative clauses) improve ratings.
    Paper: Short vs long recall is the only significant difference.
    """
    print_header("CLAIM 5: Recall long > recall short (relative clauses help)")
    print("  Paper: The only significant difference is short vs long definites")

    short_pairs = [p for p in Q1_PAIRS if p[2] == "recall_short"] + [p for p in RECALL_LAPTOP if p[2] == "recall_short"]
    long_pairs = [p for p in Q1_PAIRS if p[2] == "recall_long"] + [p for p in RECALL_LAPTOP if p[2] == "recall_long"]

    short_poly_ids = [p[0] for p in short_pairs]
    long_poly_ids = [p[0] for p in long_pairs]
    short_mono_ids = [p[1] for p in short_pairs]
    long_mono_ids = [p[1] for p in long_pairs]

    print_subheader("Recall short vs long (poly and mono)")
    print(f"  {'Source':<28} {'Short poly':>10} {'Long poly':>10} {'Short mono':>10} {'Long mono':>10}")

    # Paper values from Table 1
    print(f"  {'PAPER':<28} {'6.82':>10} {'8.35':>10} {'6.74':>10} {'8.44':>10}")

    def mean_of(d, ids):
        vals = []
        for k in ids:
            v = d.get(k)
            if isinstance(v, dict) and v.get("mean") is not None:
                vals.append(v["mean"])
        return sum(vals)/len(vals) if vals else None

    for label, d in [("HUMANS", human)] + [(m, llm.get(m, {})) for m in models]:
        sp = mean_of(d, short_poly_ids)
        lp = mean_of(d, long_poly_ids)
        sm = mean_of(d, short_mono_ids)
        lm = mean_of(d, long_mono_ids)
        parts = []
        for v in [sp, lp, sm, lm]:
            parts.append(f"{v:>10.2f}" if v else f"{'---':>10}")
        print(f"  {label:<28} {''.join(parts)}")


def analyze_claim_6(human, llm, models):
    """CLAIM 6: Polydefinite violations are discourse-structural, not grammatical.
    They should never be as low as real grammatical violations (word order).
    Paper p.5: "even the least acceptable cases of polydefinites are never
    as strongly and clearly unacceptable as... infelicitous word-orders"
    """
    print_header("CLAIM 6: Polydefinite violations weaker than word-order violations")
    print("  Paper: Poly violations are discourse-structural, never as bad as")
    print("  grammatical violations like OSV/SOV (3-4 range)")

    # Worst poly items: feromenos contrast, unique poly
    worst_poly_ids = ["sf_q2_11", "sf_04", "sf_q2_05"]  # feromenos contrast, unique poly, proin contrast
    # Worst word orders: OSV, SOV
    worst_wo_ids = ["sf_30", "sf_35", "sf_31", "sf_36"]  # OSV and SOV items

    print_subheader("Lowest polydefinite vs lowest word-order ratings")
    print(f"  {'Source':<28} {'Worst poly':>10} {'Worst WO':>10} {'Poly > WO?':>10}")

    def mean_of(d, ids):
        vals = []
        for k in ids:
            v = d.get(k)
            if isinstance(v, dict) and v.get("mean") is not None:
                vals.append(v["mean"])
        return sum(vals)/len(vals) if vals else None

    for label, d in [("HUMANS", human)] + [(m, llm.get(m, {})) for m in models]:
        wp = mean_of(d, worst_poly_ids)
        ww = mean_of(d, worst_wo_ids)
        if wp is not None and ww is not None:
            verdict = "YES" if wp > ww else "NO"
            print(f"  {label:<28} {wp:>10.2f} {ww:>10.2f} {verdict:>10}")


def analyze_correlations(human, llm, models):
    """Overall correlation between human and LLM ratings at item level."""
    print_header("OVERALL CORRELATION: Human vs LLM (item-level Pearson r)")

    all_item_ids = sorted(human.keys())

    print(f"  {'Model':<28} {'r':>6}  {'N':>3}  {'LLM mean':>8}  {'Human mean':>10}")
    print(f"  {'-'*62}")

    h_overall = sum(human[k]["mean"] for k in all_item_ids) / len(all_item_ids)

    for model in models:
        l = llm.get(model, {})
        common = [k for k in all_item_ids if k in l]
        if len(common) < 3:
            continue
        h_vals = [human[k]["mean"] for k in common]
        l_vals = [l[k]["mean"] for k in common]
        r = pearson(h_vals, l_vals)
        l_mean = sum(l_vals) / len(l_vals)
        r_str = f"{r:.3f}" if r else "---"
        print(f"  {model:<28} {r_str:>6}  {len(common):>3}  {l_mean:>8.2f}  {h_overall:>10.2f}")


# ============================================================
# MAIN
# ============================================================

def main():
    # Find result files
    results_dir = os.path.join(DIR, "results")
    result_files = sorted([f for f in os.listdir(results_dir) if f.startswith("polydefinite_") and f.endswith(".json")])

    if len(sys.argv) > 1:
        # Use specified file(s)
        llm_file = sys.argv[1]
    else:
        # Use latest
        if not result_files:
            print("ERROR: No result files found in results/")
            sys.exit(1)
        llm_file = os.path.join("results", result_files[-1])
        print(f"Using latest results: {llm_file}")
        print(f"(Pass a specific file as argument to use a different one)")

    stimuli = load_stimuli()
    human = load_human_data(stimuli)
    llm = load_llm_results(llm_file)

    models = sorted(llm.keys())
    print(f"\nLoaded: {len(human)} human items, {len(models)} LLM models")
    print(f"Models: {', '.join(models)}")

    analyze_correlations(human, llm, models)
    analyze_claim_1(human, llm, models)
    analyze_claim_2(human, llm, models)
    analyze_claim_3(human, llm, models)
    analyze_claim_4(human, llm, models)
    analyze_claim_5(human, llm, models)
    analyze_claim_6(human, llm, models)

    print(f"\n{'='*75}")
    print(f"  DONE")
    print(f"{'='*75}\n")


if __name__ == "__main__":
    main()
