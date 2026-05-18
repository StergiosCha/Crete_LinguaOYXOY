#!/usr/bin/env python3
"""
Polydefinite Experiment
========================
Focused experiment on Greek polydefinites (doubled article).

Research question: Do LLMs distinguish polydefinite vs monodefinite
constructions in Greek, and do they match human felicity judgments
across different semantic/pragmatic contexts?

Conditions tested (from semantic_felicity.jsonl, phenomenon=polydefinite):
  - unique / nonunique referent
  - contrast
  - deictic (with/without relative clause)
  - inanimate (with/without relative clause)
  - possessive (old/new info)
  - epithet
  - narrative

Each condition has a polydefinite and monodefinite variant.
Expected pattern: polydefinite is felicitous (high) when there is
a pragmatic reason for the extra article (nonunique reference, contrast,
deixis, etc.), and degraded (mid/low) when the context does not support it.

Usage:
  python run_polydefinite.py --dry-run --reps 3
  python run_polydefinite.py --models gpt-4o --reps 10
  python run_polydefinite.py --models gpt-4o DeepSeek-V3.1 --reps 10
"""

import os
import sys
import json
import time
import argparse
import random
from datetime import datetime
from collections import defaultdict

# ============================================================
# CONFIG (same Azure setup as main experiment)
# ============================================================

API_KEY = os.environ.get("AZURE_KEY", "")
OPENAI_ENDPOINT = "https://crete-xamoulis-resource.cognitiveservices.azure.com/"
OPENAI_API_VERSION = "2024-12-01-preview"
AI_ENDPOINT = "https://crete-xamoulis-resource.services.ai.azure.com/openai/v1/"

MODELS_PATH = os.path.join(os.path.dirname(__file__), "models.json")

def load_models():
    if os.path.exists(MODELS_PATH):
        with open(MODELS_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {k: v for k, v in raw.items() if not k.startswith("_") and isinstance(v, dict) and "type" in v}
    return {
        "gpt-4o": {"type": "azure_openai", "deployment": "gpt-4o"},
        "DeepSeek-V3.1": {"type": "azure_ai", "deployment": "DeepSeek-V3.1"},
        "Llama-3.3-70B": {"type": "azure_ai", "deployment": "Llama-3.3-70B-Instruct"},
    }

MODELS = load_models()

SYSTEM_PROMPT = (
    "Κάθε παράδειγμα αποτελείται από ένα κείμενο στα Νέα Ελληνικά. "
    "Καλείσαι να δηλώσεις εάν η τελευταία πρόταση του κάθε κειμένου "
    "είναι σημασιολογικά κατάλληλη με βάση το κείμενο που προηγείται αυτής. "
    "Μια πρόταση θεωρείται σημασιολογικά κατάλληλη αν μπορεί να ειπωθεί "
    "ως φυσική συνέχεια του τι προηγείται. "
    "Για τη δήλωση των απαντήσεών σου, χρησιμοποίησε μια κλίμακα από το 1 μέχρι το 10. "
    "Η επιλογή 1 αντιπροσωπεύει τη μέγιστη ακαταλληλότητα, "
    "ενώ η επιλογή 10 τη μέγιστη καταλληλότητα. "
    "Ακολουθούν δυο παραδείγματα:\n\n"
    "1) Η Μαρία με τον Γιώργο έχουν βγει για καφέ και συζητάνε για την πρόσφατη "
    "απόκτηση του πτυχίου της Μαρίας. Η Αντωνία έρχεται λίγο αργότερα και δεν ξέρει "
    "για τι συζητάνε. Ρωτάει λοιπόν και τους δυο: «Τι νέα;»; Ο Γιώργος της απαντά: "
    "«Πήρε η Μαρία πτυχίο». (10)\n\n"
    "2) Η Μαρία με τον Γιώργο έχουν βγει για καφέ και συζητάνε για την πρόσφατη "
    "απόκτηση του πτυχίου της Μαρίας. Η Αντωνία έρχεται λίγο αργότερα και δεν ξέρει "
    "για τι συζητάνε. Ρωτάει λοιπόν και τους δυο: «Τι νέα;»; Ο Γιώργος της απαντά: "
    "«Η Μαρία πτυχίο πήρε». (3)\n\n"
    "Απάντησε ΜΟΝΟ με έναν αριθμό από 1 έως 10."
)


# ============================================================
# API CLIENTS (same as main runner)
# ============================================================

def _get_azure_openai_client():
    from openai import AzureOpenAI
    return AzureOpenAI(api_version=OPENAI_API_VERSION, azure_endpoint=OPENAI_ENDPOINT, api_key=API_KEY, timeout=60)

def _get_ai_client():
    from openai import OpenAI
    return OpenAI(base_url=AI_ENDPOINT, api_key=API_KEY, timeout=60)

def call_model(model_name, messages, temperature=0.7):
    info = MODELS[model_name]
    is_reasoning = info.get("reasoning", False)
    if info["type"] == "azure_openai":
        client = _get_azure_openai_client()
        kwargs = {"model": info["deployment"], "messages": messages, "max_completion_tokens": 10}
        if not is_reasoning:
            kwargs["temperature"] = temperature
        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content
    elif info["type"] == "azure_ai":
        client = _get_ai_client()
        max_tok = 2000 if is_reasoning else 10
        kwargs = {"model": info["deployment"], "messages": messages, "max_tokens": max_tok}
        if not is_reasoning:
            kwargs["temperature"] = temperature
        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content
    else:
        raise ValueError(f"Unknown model type: {info['type']}")

def extract_rating(raw_response):
    text = raw_response.strip()
    if "</think>" in text:
        text = text.split("</think>")[-1].strip()
    digits = "".join(c for c in text if c.isdigit())
    if digits:
        rating = int(digits[:2])
        if 1 <= rating <= 10:
            return rating
    return None


# ============================================================
# LOAD POLYDEFINITE STIMULI
# ============================================================

def load_polydefinite_stimuli():
    """Load only polydefinite items from semantic_felicity.jsonl."""
    stimuli_path = os.path.join(os.path.dirname(__file__), "stimuli", "shared", "semantic_felicity.jsonl")
    if not os.path.exists(stimuli_path):
        print(f"ERROR: {stimuli_path} not found")
        sys.exit(1)

    items = []
    with open(stimuli_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            if item.get("phenomenon") == "polydefinite":
                items.append(item)

    return items


def group_into_pairs(items):
    """Group polydefinite items into minimal pairs (poly vs mono).

    Returns list of dicts with 'context_label', 'poly_item', 'mono_item'.
    Items are paired by shared context or by condition naming pattern.
    """
    # Group by context (items sharing the same context are pairs)
    by_context = defaultdict(list)
    for item in items:
        ctx = item.get("context", "")
        by_context[ctx].append(item)

    pairs = []
    used = set()

    for ctx, group in by_context.items():
        if len(group) < 2:
            continue
        # Find poly and mono variants
        polys = [i for i in group if "poly" in i["condition"]]
        monos = [i for i in group if "mono" in i["condition"]]

        for p in polys:
            # Try to find matching mono
            # Match by condition prefix (e.g., unique_polydefinite <-> unique_monodefinite)
            prefix = p["condition"].replace("polydefinite", "").replace("poly", "").rstrip("_")
            matched = None
            for m in monos:
                m_prefix = m["condition"].replace("monodefinite", "").replace("mono", "").rstrip("_")
                if prefix == m_prefix and m["id"] not in used:
                    matched = m
                    break

            if matched:
                pairs.append({
                    "context_label": prefix or "base",
                    "poly": p,
                    "mono": matched,
                })
                used.add(p["id"])
                used.add(matched["id"])

    # Also collect unpaired items (e.g., right_disloc, inverted)
    unpaired = [i for i in items if i["id"] not in used]

    return pairs, unpaired


# ============================================================
# RUN EXPERIMENT
# ============================================================

CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "results", "_checkpoint.json")

def _load_checkpoint():
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"results": [], "done_keys": []}

def _save_checkpoint(results, done_keys):
    os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump({"results": results, "done_keys": done_keys}, f, ensure_ascii=False)

def _clear_checkpoint():
    if os.path.exists(CHECKPOINT_PATH):
        os.remove(CHECKPOINT_PATH)

def run_polydefinite_experiment(items, model_names, n_reps=10, temperature=0.7, dry_run=False):
    # Load checkpoint if resuming
    cp = _load_checkpoint()
    results = cp["results"]
    done_keys = set(cp["done_keys"])

    if results:
        print(f"\n  RESUMING: {len(results)} items already done, skipping...\n")

    total = len(items) * len(model_names) * n_reps
    done = len(done_keys) * n_reps

    for model_name in model_names:
        print(f"\n{'='*60}")
        print(f"  Model: {model_name}")
        print(f"{'='*60}")

        for item in items:
            key = f"{model_name}|{item['id']}"
            if key in done_keys:
                done += n_reps
                continue

            # Present as one continuous text, same as human experiment
            if item.get("context"):
                user_msg = f"{item['context']} {item['sentence']}"
            else:
                user_msg = item["sentence"]

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ]

            ratings = []
            raw_responses = []

            for rep in range(n_reps):
                done += 1
                if dry_run:
                    fake = random.randint(1, 10)
                    ratings.append(fake)
                    raw_responses.append(str(fake))
                    continue

                try:
                    raw = call_model(model_name, messages, temperature=temperature)
                    raw_responses.append(raw)
                    rating = extract_rating(raw)
                    if rating is not None:
                        ratings.append(rating)
                    else:
                        print(f"    ? {item['id']} rep {rep+1}: could not parse '{raw.strip()[:50]}'")
                except Exception as e:
                    raw_responses.append(f"ERROR: {e}")
                    print(f"    X {item['id']} rep {rep+1}: {e}")

                time.sleep(0.3)

            mean_rating = sum(ratings) / len(ratings) if ratings else None
            sd_rating = None
            if len(ratings) > 1:
                m = mean_rating
                sd_rating = (sum((r - m) ** 2 for r in ratings) / (len(ratings) - 1)) ** 0.5

            result = {
                "id": item["id"],
                "sentence": item["sentence"],
                "context": item.get("context", ""),
                "phenomenon": "polydefinite",
                "condition": item["condition"],
                "expected": item.get("expected", ""),
                "model": model_name,
                "ratings": ratings,
                "mean": round(mean_rating, 2) if mean_rating else None,
                "sd": round(sd_rating, 2) if sd_rating else None,
                "n_valid": len(ratings),
                "n_reps": n_reps,
                "raw_responses": raw_responses,
            }
            results.append(result)
            done_keys.add(key)

            # Save checkpoint after each item
            _save_checkpoint(results, list(done_keys))

            pct = done / total * 100
            is_poly = "poly" in item["condition"]
            tag = "POLY" if is_poly else "MONO" if "mono" in item["condition"] else "OTHER"
            status = f"M={mean_rating:.1f}" if mean_rating else "---"
            print(f"  [{pct:5.1f}%] {item['id']:<8} {tag:<5} {item['condition']:<30} {status}  ({len(ratings)}/{n_reps})")

    # Clear checkpoint on successful completion
    _clear_checkpoint()
    return results


# ============================================================
# ANALYSIS
# ============================================================

def analyze_polydefinite(results):
    """Focused analysis of polydefinite results."""
    print(f"\n{'='*70}")
    print(f"  POLYDEFINITE ANALYSIS")
    print(f"{'='*70}")

    models = sorted(set(r["model"] for r in results))

    # 1. Overall poly vs mono
    print(f"\n  1. OVERALL: polydefinite vs monodefinite")
    print(f"  {'-'*50}")
    for model in models:
        mr = [r for r in results if r["model"] == model]
        poly_ratings = []
        mono_ratings = []
        for r in mr:
            if r["mean"] is None:
                continue
            if "poly" in r["condition"]:
                poly_ratings.extend(r["ratings"])
            elif "mono" in r["condition"]:
                mono_ratings.extend(r["ratings"])

        poly_mean = sum(poly_ratings) / len(poly_ratings) if poly_ratings else 0
        mono_mean = sum(mono_ratings) / len(mono_ratings) if mono_ratings else 0
        diff = poly_mean - mono_mean
        print(f"  {model:<20} poly={poly_mean:.2f} (n={len(poly_ratings)})  mono={mono_mean:.2f} (n={len(mono_ratings)})  diff={diff:+.2f}")

    # 2. By context type
    print(f"\n  2. BY CONTEXT TYPE")
    print(f"  {'-'*50}")

    # Group conditions into context types
    context_types = {
        "uniqueness": ["unique_polydefinite", "unique_monodefinite", "nonunique_polydefinite", "nonunique_monodefinite"],
        "contrast": ["contrast_polydefinite_a", "contrast_polydefinite_b", "contrast_monodefinite_a", "contrast_monodefinite_b"],
        "deictic": [c for c in set(r["condition"] for r in results) if "deictic" in c],
        "inanimate": [c for c in set(r["condition"] for r in results) if "inanimate" in c],
        "possessive": [c for c in set(r["condition"] for r in results) if "possessive" in c],
        "epithet": [c for c in set(r["condition"] for r in results) if "epithet" in c],
        "narrative": [c for c in set(r["condition"] for r in results) if "narrative" in c],
    }

    for model in models:
        print(f"\n  Model: {model}")
        mr = [r for r in results if r["model"] == model]

        for ctx_name, conditions in sorted(context_types.items()):
            ctx_results = [r for r in mr if r["condition"] in conditions]
            if not ctx_results:
                continue

            poly_r = [r for r in ctx_results if "poly" in r["condition"]]
            mono_r = [r for r in ctx_results if "mono" in r["condition"]]

            poly_ratings = []
            for r in poly_r:
                poly_ratings.extend(r["ratings"])
            mono_ratings = []
            for r in mono_r:
                mono_ratings.extend(r["ratings"])

            poly_mean = sum(poly_ratings) / len(poly_ratings) if poly_ratings else 0
            mono_mean = sum(mono_ratings) / len(mono_ratings) if mono_ratings else 0
            diff = poly_mean - mono_mean

            print(f"    {ctx_name:<15} poly={poly_mean:.2f}  mono={mono_mean:.2f}  diff={diff:+.2f}")

    # 3. Per item detail
    print(f"\n  3. PER ITEM DETAIL")
    print(f"  {'-'*50}")

    for model in models:
        print(f"\n  Model: {model}")
        mr = sorted([r for r in results if r["model"] == model], key=lambda r: r["id"])
        header = f"    {'ID':<8} {'Condition':<32} {'Exp':<5} {'Mean':>5} {'SD':>5}"
        print(header)
        print(f"    {'-'*60}")
        for r in mr:
            exp = r.get("expected", "")
            mean_str = f"{r['mean']:.1f}" if r["mean"] is not None else "---"
            sd_str = f"{r['sd']:.1f}" if r.get("sd") is not None else "---"
            print(f"    {r['id']:<8} {r['condition']:<32} {exp:<5} {mean_str:>5} {sd_str:>5}")

    # 4. Expected vs observed direction
    print(f"\n  4. EXPECTED vs OBSERVED")
    print(f"  {'-'*50}")

    for model in models:
        print(f"\n  Model: {model}")
        mr = [r for r in results if r["model"] == model]
        match = 0
        total_checked = 0
        for r in mr:
            if r["mean"] is None or not r.get("expected"):
                continue
            total_checked += 1
            exp = r["expected"]
            mean = r["mean"]
            if exp == "high" and mean >= 7.0:
                match += 1
            elif exp == "mid" and 4.0 <= mean <= 7.0:
                match += 1
            elif exp == "low" and mean <= 4.0:
                match += 1

        if total_checked > 0:
            print(f"    Direction match: {match}/{total_checked} ({match/total_checked:.0%})")
            print(f"    (high >= 7.0, mid = 4.0-7.0, low <= 4.0)")

    # 5. Key hypothesis tests (descriptive)
    print(f"\n  5. KEY CONTRASTS")
    print(f"  {'-'*50}")
    print(f"  The core prediction: polydefinite is BETTER than mono when")
    print(f"  there is pragmatic motivation (nonunique, contrast, deixis).")
    print(f"  Polydefinite is WORSE or EQUAL to mono when there is no")
    print(f"  pragmatic motivation (unique reference, inanimate, new info).")

    for model in models:
        print(f"\n  Model: {model}")
        mr = {r["condition"]: r for r in results if r["model"] == model and r["mean"] is not None}

        contrasts = [
            ("nonunique_polydefinite", "nonunique_monodefinite", "poly should be >= mono (nonunique)"),
            ("unique_polydefinite", "unique_monodefinite", "poly should be < mono (unique)"),
            ("contrast_polydefinite_a", "contrast_monodefinite_a", "poly should be >= mono (contrast)"),
            ("deictic_poly_no_rel", "deictic_mono_no_rel", "poly should be >= mono (deictic)"),
            ("inanimate_polydefinite", "inanimate_monodefinite", "poly should be <= mono (inanimate)"),
            ("possessive_old_info_poly", "possessive_old_info_mono", "poly should be ~= mono (old info)"),
            ("possessive_new_info_poly", "possessive_new_info_mono", "poly should be < mono (new info)"),
        ]

        for cond_a, cond_b, prediction in contrasts:
            if cond_a in mr and cond_b in mr:
                a = mr[cond_a]["mean"]
                b = mr[cond_b]["mean"]
                diff = a - b
                print(f"    {cond_a:<30} {a:.1f} vs {cond_b:<30} {b:.1f}  diff={diff:+.1f}")
                print(f"      Prediction: {prediction}")


# ============================================================
# SAVE
# ============================================================

def save_results(results, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"polydefinite_{timestamp}.json")

    output = {
        "experiment": "polydefinite",
        "timestamp": datetime.now().isoformat(),
        "system_prompt": SYSTEM_PROMPT,
        "n_items": len(set(r["id"] for r in results)),
        "n_models": len(set(r["model"] for r in results)),
        "results": results,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to {filepath}")
    return filepath


# ============================================================
# EXPORT TO CSV (for R / jamovi / JASP)
# ============================================================

def export_csv(results, output_dir):
    """Export individual ratings as CSV for statistical analysis."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(output_dir, f"polydefinite_{timestamp}.csv")

    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("item_id,model,condition,article_type,context_type,expected,rep,rating\n")
        for r in results:
            cond = r["condition"]
            # Determine article type
            if "poly" in cond:
                art = "polydefinite"
            elif "mono" in cond:
                art = "monodefinite"
            elif "right_disloc" in cond:
                art = "right_disloc"
            elif "inverted" in cond:
                art = "inverted"
            else:
                art = "other"

            # Determine context type
            ctx = "other"
            for label in ["unique", "nonunique", "contrast", "deictic", "inanimate", "possessive", "epithet", "narrative"]:
                if label in cond:
                    ctx = label
                    break

            for rep_i, rating in enumerate(r["ratings"], 1):
                f.write(f"{r['id']},{r['model']},{cond},{art},{ctx},{r.get('expected','')},{rep_i},{rating}\n")

    print(f"CSV exported to {csv_path}")
    return csv_path


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Polydefinite Experiment")
    parser.add_argument("--models", nargs="+", default=list(MODELS.keys()), choices=list(MODELS.keys()))
    parser.add_argument("--reps", type=int, default=10)
    parser.add_argument("--temp", type=float, default=0.7)
    parser.add_argument("--output", type=str, default="results")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--analyze", type=str, default=None, help="Analyze existing results file instead of running")
    args = parser.parse_args()

    # If analyzing existing results
    if args.analyze:
        with open(args.analyze, "r", encoding="utf-8") as f:
            data = json.load(f)
        analyze_polydefinite(data["results"])
        export_csv(data["results"], os.path.dirname(args.analyze) or "results")
        return

    if not args.dry_run and not API_KEY:
        print("ERROR: no API key. Run: export AZURE_KEY='your-key'")
        sys.exit(1)

    # Load stimuli
    items = load_polydefinite_stimuli()
    pairs, unpaired = group_into_pairs(items)

    print(f"\nPolydefinite Experiment")
    print(f"  Items: {len(items)} ({len(pairs)} minimal pairs, {len(unpaired)} unpaired)")
    print(f"  Models: {', '.join(args.models)}")
    print(f"  Reps: {args.reps}")
    print(f"  Temperature: {args.temp}")
    if args.dry_run:
        print(f"  ** DRY RUN **")

    total_calls = len(items) * len(args.models) * args.reps
    est_min = total_calls * 0.5 / 60
    print(f"  Total API calls: {total_calls} (~{est_min:.0f} min)")

    # Show pairs
    print(f"\n  Minimal pairs:")
    for p in pairs:
        print(f"    {p['context_label']:<20} poly={p['poly']['id']}  mono={p['mono']['id']}")
    if unpaired:
        print(f"  Unpaired: {', '.join(u['id'] + ' (' + u['condition'] + ')' for u in unpaired)}")

    print()

    # Run
    results = run_polydefinite_experiment(items, args.models, n_reps=args.reps, temperature=args.temp, dry_run=args.dry_run)

    # Save
    output_dir = os.path.join(os.path.dirname(__file__), args.output)
    filepath = save_results(results, output_dir)

    # Export CSV
    export_csv(results, output_dir)

    # Analyze
    analyze_polydefinite(results)

    print(f"\nDone. Results: {filepath}")
    print(f"Re-analyze: python run_polydefinite.py --analyze {filepath}")


if __name__ == "__main__":
    main()
