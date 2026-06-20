#!/usr/bin/env python3
"""
Crete Acceptability Experiment Runner
======================================
Πανεπιστήμιο Κρήτης — Chatzikyriakidis 2026

Τρέχει ερεθίσματα (stimuli) μέσα από LLMs στο Azure και καταγράφει
τις βαθμολογίες αποδεκτότητας (1-7).

Χρήση:
  python run_experiment.py                          # τρέχει ΟΛΑ τα stimuli
  python run_experiment.py --file stimuli/cd.jsonl  # μόνο ένα φαινόμενο
  python run_experiment.py --models gpt-4o          # μόνο ένα μοντέλο
  python run_experiment.py --reps 3 --dry-run       # δοκιμαστικά (3 reps, δεν καλεί API)

Πριν τρέξετε:
  pip install openai
  export AZURE_KEY="your-api-key"
"""

import os
import sys
import json
import time
import glob
import argparse
import random
from datetime import datetime

# ============================================================
# AZURE CONFIGURATION
# Μην αλλάζετε — ρωτήστε τον Στέργιο αν κάτι δεν δουλεύει.
# ============================================================

API_KEY = os.environ.get("AZURE_KEY", "")

# Azure OpenAI endpoint (GPT-4o, GPT-5.4-pro)
OPENAI_ENDPOINT = "https://crete-xamoulis-resource.cognitiveservices.azure.com/"
OPENAI_API_VERSION = "2024-12-01-preview"
GPT54_API_VERSION = "2025-04-01-preview"

# Azure AI endpoint (DeepSeek, Llama)
AI_ENDPOINT = "https://crete-xamoulis-resource.services.ai.azure.com/openai/v1/"

# Default models (used if no models.json found)
DEFAULT_MODELS = {
    "gpt-4o":       {"type": "azure_openai", "deployment": "gpt-4o"},
    "gpt-5.4-pro":  {"type": "gpt54_responses", "deployment": "gpt-5.4-pro"},
    "DeepSeek-V3.1": {"type": "azure_ai", "deployment": "DeepSeek-V3.1"},
    "Llama-3.3-70B": {"type": "azure_ai", "deployment": "Llama-3.3-70B-Instruct"},
}

def load_models_config():
    """Load models from models.json if it exists, else use defaults."""
    config_path = os.path.join(os.path.dirname(__file__), "models.json")
    if not os.path.exists(config_path):
        return DEFAULT_MODELS

    with open(config_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Filter: skip keys starting with _ (comments/candidates)
    models = {}
    for key, val in raw.items():
        if key.startswith("_"):
            continue
        if not isinstance(val, dict) or "type" not in val:
            continue
        models[key] = val
    return models

MODELS = load_models_config()


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = (
    "Είσαι φυσικός ομιλητής Ελληνικών. "
    "Βαθμολόγησε την παρακάτω πρόταση σε κλίμακα "
    "1 (τελείως απαράδεκτη / δεν θα λεγόταν ποτέ) "
    "έως 7 (τέλεια φυσική). "
    "Απάντησε ΜΟΝΟ με έναν αριθμό."
)

# Coreference addendum — appended to system prompt for binding/crossover items
COREFERENCE_NOTE = (
    " Σημείωση: Οι αγκύλες [...] με δείκτες (ᵢ, ⱼ) δηλώνουν συναναφορά — "
    "οι εκφράσεις με τον ίδιο δείκτη αναφέρονται στο ίδιο πρόσωπο/πράγμα. "
    "Βαθμολόγησε τη φυσικότητα της πρότασης ΜΕ αυτή τη συγκεκριμένη ανάγνωση."
)

# Phenomena that use coreference bracket notation
COREFERENCE_PHENOMENA = {"binding", "crossover"}

# For dialect experiments, use a dialect-specified prompt instead:
DIALECT_PROMPTS = {
    "cypriot": (
        "Είστε φυσικός ομιλητής της Κυπριακής Ελληνικής. "
        "Βαθμολόγησε την παρακάτω πρόταση σε κλίμακα "
        "1 (τελείως απαράδεκτη / δεν θα λεγόταν ποτέ) "
        "έως 7 (τέλεια φυσική). "
        "Απάντησε ΜΟΝΟ με έναν αριθμό."
    ),
    "pontic": (
        "Είστε φυσικός ομιλητής της Ποντιακής Ελληνικής. "
        "Βαθμολόγησε την παρακάτω πρόταση σε κλίμακα "
        "1 (τελείως απαράδεκτη / δεν θα λεγόταν ποτέ) "
        "έως 7 (τέλεια φυσική). "
        "Απάντησε ΜΟΝΟ με έναν αριθμό."
    ),
    "cretan": (
        "Είστε φυσικός ομιλητής της Κρητικής Ελληνικής. "
        "Βαθμολόγησε την παρακάτω πρόταση σε κλίμακα "
        "1 (τελείως απαράδεκτη / δεν θα λεγόταν ποτέ) "
        "έως 7 (τέλεια φυσική). "
        "Απάντησε ΜΟΝΟ με έναν αριθμό."
    ),
    "northern": (
        "Είστε φυσικός ομιλητής της Βορειοελληνικής. "
        "Βαθμολόγησε την παρακάτω πρόταση σε κλίμακα "
        "1 (τελείως απαράδεκτη / δεν θα λεγόταν ποτέ) "
        "έως 7 (τέλεια φυσική). "
        "Απάντησε ΜΟΝΟ με έναν αριθμό."
    ),
    "heptanesian": (
        "Είστε φυσικός ομιλητής της Επτανησιακής Ελληνικής. "
        "Βαθμολόγησε την παρακάτω πρόταση σε κλίμακα "
        "1 (τελείως απαράδεκτη / δεν θα λεγόταν ποτέ) "
        "έως 7 (τέλεια φυσική). "
        "Απάντησε ΜΟΝΟ με έναν αριθμό."
    ),
    "tsakonian": (
        "Είστε φυσικός ομιλητής της Τσακωνικής. "
        "Βαθμολόγησε την παρακάτω πρόταση σε κλίμακα "
        "1 (τελείως απαράδεκτη / δεν θα λεγόταν ποτέ) "
        "έως 7 (τέλεια φυσική). "
        "Απάντησε ΜΟΝΟ με έναν αριθμό."
    ),
    "maniot": (
        "Είστε φυσικός ομιλητής της Μανιάτικης Ελληνικής. "
        "Βαθμολόγησε την παρακάτω πρόταση σε κλίμακα "
        "1 (τελείως απαράδεκτη / δεν θα λεγόταν ποτέ) "
        "έως 7 (τέλεια φυσική). "
        "Απάντησε ΜΟΝΟ με έναν αριθμό."
    ),
    "griko": (
        "Είστε φυσικός ομιλητής της Griko (Κατωιταλικής Ελληνικής). "
        "Βαθμολόγησε την παρακάτω πρόταση σε κλίμακα "
        "1 (τελείως απαράδεκτη / δεν θα λεγόταν ποτέ) "
        "έως 7 (τέλεια φυσική). "
        "Απάντησε ΜΟΝΟ με έναν αριθμό."
    ),
}

# GRDD+ dialects available for reference:
# Cretan, Cypriot, Pontic, Northern, Heptanesian, Griko, Maniot, Tsakonian, Katharevousa
# Students: pick dialects from GRDD+ data and create stimuli with the "dialect" field


# ============================================================
# API CLIENTS
# ============================================================

def _get_azure_openai_client():
    from openai import AzureOpenAI
    return AzureOpenAI(
        api_version=OPENAI_API_VERSION,
        azure_endpoint=OPENAI_ENDPOINT,
        api_key=API_KEY,
    )

def _get_ai_client():
    from openai import OpenAI
    return OpenAI(base_url=AI_ENDPOINT, api_key=API_KEY)

def _call_gpt54(messages, max_tokens=1000):
    """GPT-5.4-pro uses the Responses API (reasoning model, no temperature)."""
    from urllib.request import Request, urlopen
    url = f"{OPENAI_ENDPOINT}openai/responses?api-version={GPT54_API_VERSION}"

    instructions = None
    input_msgs = []
    for m in messages:
        if m["role"] == "system":
            instructions = m["content"]
        else:
            input_msgs.append(m)

    body = {"model": "gpt-5.4-pro", "input": input_msgs, "max_output_tokens": max_tokens}
    if instructions:
        body["instructions"] = instructions

    payload = json.dumps(body).encode("utf-8")
    headers = {"api-key": API_KEY, "Content-Type": "application/json"}
    req = Request(url, data=payload, headers=headers, method="POST")
    with urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    for item in data.get("output", []):
        if item.get("type") == "message" and item.get("role") == "assistant":
            for c in item.get("content", []):
                if c.get("type") == "output_text" and c.get("text"):
                    return c["text"]
    return data["output"][0]["content"][0]["text"]


def call_model(model_name, messages, temperature=0.7):
    """Call a model and return the raw text response."""
    info = MODELS[model_name]

    # Reasoning models (R1, grok-reasoning) need more tokens for <think>…</think> + answer
    is_reasoning = info.get("reasoning", False)
    token_limit = 1000 if is_reasoning else 10

    if info["type"] == "gpt54_responses":
        return _call_gpt54(messages)

    elif info["type"] == "azure_openai":
        client = _get_azure_openai_client()
        resp = client.chat.completions.create(
            model=info["deployment"],
            messages=messages,
            temperature=temperature,
            max_tokens=token_limit,
        )
        return resp.choices[0].message.content

    elif info["type"] == "azure_ai":
        client = _get_ai_client()
        resp = client.chat.completions.create(
            model=info["deployment"],
            messages=messages,
            temperature=temperature,
            max_tokens=token_limit,
        )
        return resp.choices[0].message.content

    else:
        raise ValueError(f"Unknown model type: {info['type']} for {model_name}. Must be: azure_openai, azure_ai, or gpt54_responses.")


def extract_rating(raw_response):
    """Extract a 1-7 integer from the model's response."""
    text = raw_response.strip()
    # Clean DeepSeek chain-of-thought
    if "</think>" in text:
        text = text.split("</think>")[-1].strip()
    # Extract digits
    digits = "".join(c for c in text if c.isdigit())
    if digits:
        rating = int(digits[:2])
        if 1 <= rating <= 7:
            return rating
    return None


# ============================================================
# STIMULUS LOADING
# ============================================================

def load_stimuli(filepath):
    """Load stimuli from a JSONL file.

    Each line must have:
      {"id": "cd_01", "sentence": "...", "phenomenon": "cd", "condition": "...", "expected": "high/mid/low"}

    Optional fields: "context", "dialect", "notes"
    """
    items = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"  ⚠ Σφάλμα στη γραμμή {line_num} του {filepath}: {e}")
                continue

            # Validate required fields
            required = ["id", "sentence", "phenomenon", "condition"]
            missing = [f for f in required if f not in item]
            if missing:
                print(f"  ⚠ Γραμμή {line_num}: λείπουν τα πεδία {missing}")
                continue

            items.append(item)

    return items


def load_all_stimuli(stimuli_dir, experiment=None):
    """Load .jsonl files from stimuli directory.

    If experiment is 'a' or 'b', loads from exp_a/ or exp_b/ + shared/.
    If None, loads from all subdirectories (or top-level if no subdirs).
    """
    all_items = []
    search_dirs = []

    if experiment:
        exp_dir = os.path.join(stimuli_dir, f"exp_{experiment}")
        shared_dir = os.path.join(stimuli_dir, "shared")
        if os.path.isdir(exp_dir):
            search_dirs.append(exp_dir)
        if os.path.isdir(shared_dir):
            search_dirs.append(shared_dir)
    else:
        # Load from all subdirectories + top-level
        for d in sorted(os.listdir(stimuli_dir)):
            full = os.path.join(stimuli_dir, d)
            if os.path.isdir(full):
                search_dirs.append(full)
        # Also check top-level .jsonl files
        search_dirs.append(stimuli_dir)

    files = []
    for d in search_dirs:
        found = sorted(glob.glob(os.path.join(d, "*.jsonl")))
        files.extend(found)

    # Deduplicate (in case top-level and subdir overlap)
    files = list(dict.fromkeys(files))

    if not files:
        print(f"❌ Δεν βρέθηκαν αρχεία .jsonl στο {stimuli_dir}")
        sys.exit(1)

    for f in files:
        items = load_stimuli(f)
        rel = os.path.relpath(f, stimuli_dir)
        print(f"  Φόρτωσε {len(items)} ερεθίσματα από {rel}")
        all_items.extend(items)

    return all_items


# ============================================================
# EXPERIMENT RUNNER
# ============================================================

def run_experiment(stimuli, model_names, n_reps=10, temperature=0.7, dry_run=False):
    """Run all stimuli through all models with n_reps repetitions.

    Returns a list of result dicts.
    """
    results = []
    total = len(stimuli) * len(model_names) * n_reps
    done = 0

    for model_name in model_names:
        print(f"\n{'='*60}")
        print(f"  Μοντέλο: {model_name}")
        print(f"{'='*60}")

        for item in stimuli:
            # Choose system prompt
            dialect = item.get("dialect", None)
            if dialect and dialect in DIALECT_PROMPTS:
                sys_prompt = DIALECT_PROMPTS[dialect]
            else:
                sys_prompt = SYSTEM_PROMPT

            # Add coreference instruction for binding/crossover
            if item.get("phenomenon") in COREFERENCE_PHENOMENA:
                sys_prompt = sys_prompt + COREFERENCE_NOTE

            # Build user message
            user_msg = item["sentence"]
            if "context" in item and item["context"]:
                user_msg = f"Πλαίσιο: {item['context']}\nΠρόταση: {item['sentence']}"

            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_msg},
            ]

            ratings = []
            raw_responses = []

            for rep in range(n_reps):
                done += 1
                if dry_run:
                    # Fake rating for testing
                    fake = random.randint(1, 7)
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
                        print(f"    ⚠ {item['id']} rep {rep+1}: δεν κατάλαβα «{raw.strip()[:50]}»")
                except Exception as e:
                    raw_responses.append(f"ERROR: {e}")
                    print(f"    ❌ {item['id']} rep {rep+1}: {e}")

                # Rate limiting — be gentle with the API
                time.sleep(0.3)

            # Compute stats
            mean_rating = sum(ratings) / len(ratings) if ratings else None
            sd_rating = None
            if len(ratings) > 1:
                m = mean_rating
                sd_rating = (sum((r - m) ** 2 for r in ratings) / (len(ratings) - 1)) ** 0.5

            result = {
                "id": item["id"],
                "sentence": item["sentence"],
                "phenomenon": item["phenomenon"],
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

            # Progress
            pct = done / total * 100
            status = f"μ={mean_rating:.1f}" if mean_rating else "—"
            print(f"  [{pct:5.1f}%] {item['id']:<15} {item['condition']:<25} → {status}  ({len(ratings)}/{n_reps} valid)")

    return results


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(results, output_dir):
    """Save results to a timestamped JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"results_{timestamp}.json")

    output = {
        "experiment": "crete_acceptability",
        "timestamp": datetime.now().isoformat(),
        "system_prompt": SYSTEM_PROMPT,
        "n_items": len(set(r["id"] for r in results)),
        "n_models": len(set(r["model"] for r in results)),
        "results": results,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Αποθηκεύτηκαν {len(results)} αποτελέσματα → {filepath}")
    return filepath


# ============================================================
# QUICK SUMMARY TABLE
# ============================================================

def print_summary(results):
    """Print a quick summary table grouped by phenomenon and condition."""
    print(f"\n{'='*70}")
    print(f"  ΣΥΝΟΨΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ")
    print(f"{'='*70}\n")

    # Group by phenomenon
    phenomena = {}
    for r in results:
        key = r["phenomenon"]
        if key not in phenomena:
            phenomena[key] = {}
        cond = r["condition"]
        if cond not in phenomena[key]:
            phenomena[key][cond] = {}
        phenomena[key][cond][r["model"]] = r

    models = sorted(set(r["model"] for r in results))

    for phenom, conditions in sorted(phenomena.items()):
        print(f"  ── {phenom.upper()} {'─'*50}")
        header = f"  {'Condition':<30}"
        for m in models:
            short = m[:10]
            header += f" {short:>10}"
        print(header)
        print(f"  {'─'*30}" + "─" * (11 * len(models)))

        for cond in conditions:
            row = f"  {cond:<30}"
            for m in models:
                if m in conditions[cond]:
                    r = conditions[cond][m]
                    if r["mean"] is not None:
                        row += f" {r['mean']:>8.1f}  "
                    else:
                        row += f"      —   "
                else:
                    row += f"      —   "
            print(row)
        print()


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Crete Acceptability Experiment Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Παραδείγματα:
  python run_experiment.py --exp a                      # Experiment A (CD + CLLD + fillers)
  python run_experiment.py --exp b                      # Experiment B (Binding + Crossover + PC + fillers)
  python run_experiment.py                              # τρέξε τα πάντα
  python run_experiment.py --file stimuli/exp_a/cd.jsonl  # μόνο clitic doubling
  python run_experiment.py --models gpt-4o --reps 3 --dry-run  # δοκιμαστικά
        """
    )
    parser.add_argument("--exp", type=str, choices=["a", "b"], default=None,
                        help="Experiment A (CD+CLLD) ή B (Binding+Crossover+PC). Αν δεν δοθεί, τρέχει όλα.")
    parser.add_argument("--file", type=str, default=None,
                        help="Αρχείο .jsonl με ερεθίσματα (αν δεν δοθεί, φορτώνει από --exp ή όλα)")
    parser.add_argument("--models", nargs="+", default=list(MODELS.keys()),
                        choices=list(MODELS.keys()),
                        help="Ποια μοντέλα να τρέξει (default: όλα)")
    parser.add_argument("--reps", type=int, default=10,
                        help="Πόσες επαναλήψεις ανά πρόταση (default: 10)")
    parser.add_argument("--temp", type=float, default=0.7,
                        help="Temperature (default: 0.7)")
    parser.add_argument("--output", type=str, default="results",
                        help="Φάκελος αποτελεσμάτων (default: results/)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Δοκιμαστική εκτέλεση χωρίς API κλήσεις")

    args = parser.parse_args()

    # Check API key
    if not args.dry_run and not API_KEY:
        print("❌ Δεν βρέθηκε API key!")
        print()
        print("   export AZURE_KEY='your-key'")
        print("   python run_experiment.py")
        sys.exit(1)

    print()
    print("╔══════════════════════════════════════════════╗")
    print("║  Crete Acceptability Experiment              ║")
    print("║  Πανεπιστήμιο Κρήτης — 2026                 ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    # Load stimuli
    stimuli_dir = os.path.join(os.path.dirname(__file__), "stimuli")
    if args.file:
        print(f"  Φορτώνω: {args.file}")
        stimuli = load_stimuli(args.file)
    elif args.exp:
        exp_label = "A (CD + CLLD)" if args.exp == "a" else "B (Binding + Crossover + Plural Conjunction)"
        print(f"  Experiment {exp_label}")
        stimuli = load_all_stimuli(stimuli_dir, experiment=args.exp)
    else:
        print(f"  Φορτώνω όλα τα .jsonl από {stimuli_dir}/")
        stimuli = load_all_stimuli(stimuli_dir)

    if not stimuli:
        print("❌ Δεν βρέθηκαν ερεθίσματα!")
        sys.exit(1)

    print(f"\n  Σύνολο: {len(stimuli)} ερεθίσματα")
    print(f"  Μοντέλα: {', '.join(args.models)}")
    print(f"  Επαναλήψεις: {args.reps}")
    print(f"  Temperature: {args.temp}")
    if args.dry_run:
        print(f"  ⚠ DRY RUN — δεν θα γίνουν API κλήσεις")

    total_calls = len(stimuli) * len(args.models) * args.reps
    est_minutes = total_calls * 0.5 / 60  # ~0.5 sec per call
    print(f"  Εκτιμώμενες κλήσεις: {total_calls} (~{est_minutes:.0f} λεπτά)")
    print()

    # Run
    results = run_experiment(
        stimuli,
        args.models,
        n_reps=args.reps,
        temperature=args.temp,
        dry_run=args.dry_run,
    )

    # Save
    output_dir = os.path.join(os.path.dirname(__file__), args.output)
    filepath = save_results(results, output_dir)

    # Summary
    print_summary(results)

    print(f"\n  Αποτελέσματα: {filepath}")
    print(f"  Για ανάλυση: python analyze_results.py {filepath}")
    print()


if __name__ == "__main__":
    main()
