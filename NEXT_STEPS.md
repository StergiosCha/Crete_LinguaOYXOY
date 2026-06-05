# Next: Run LLMs on your items

Your items are in `index.html` but NOT in the `.jsonl` files that the experiment reads. You need to sync them first, then run everything from the notebook.

## 1. Export items from index.html to JSONL

For each phenomenon, copy your items from `index.html` into the corresponding `.jsonl` files. One JSON per line:

```json
{"id": "cd_01", "sentence": "Τον είδα τον Γιάννη χθες στο πανεπιστήμιο.", "phenomenon": "cd", "condition": "definite_proper", "expected": "high"}
```

Put them in the right files:

    stimuli/exp_a/cd.jsonl          ← your CD items
    stimuli/exp_a/clld.jsonl        ← your CLLD items
    stimuli/exp_a/pc.jsonl          ← your plural conjunction items (NEW file)
    stimuli/exp_a/fillers.jsonl     ← your word order fillers
    stimuli/exp_b/binding.jsonl     ← your binding items
    stimuli/exp_b/crossover.jsonl   ← your crossover items
    stimuli/exp_b/fillers.jsonl     ← your Exp B fillers

**Delete the old placeholder items** in those files first — replace entirely with your real items from `index.html`.

Quick way with Python — paste your items as a list and write:

```python
import json
items = [
    {"id": "cd_01", "sentence": "Τον είδα τον Γιάννη χθες στο πανεπιστήμιο.", "phenomenon": "cd", "condition": "definite_proper", "expected": "high"},
    # ... paste rest here
]
with open("stimuli/exp_a/cd.jsonl", "w", encoding="utf-8") as f:
    for item in items:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
```

## 2. Open the notebook

Open **`run_experiment_notebook.ipynb`** in Jupyter / Colab / VS Code. Run cells with Shift+Enter.

### Cell 1 — Install
```python
!pip install openai
```

### Cell 2 — API Key (run every time you open the notebook)

To get the key: go to [portal.azure.com](https://portal.azure.com) → search **crete-xamoulis-resource** → **Keys and Endpoint** (left sidebar) → copy **Key 1**.

```python
import os
os.environ['AZURE_KEY'] = 'PASTE-YOUR-KEY-HERE'   # ← paste Key 1 from Azure portal
```

### Cell 3 — Dry Run
Validates your `.jsonl` files without calling the API (free):
```python
%run run_experiment.py --exp a --dry-run --reps 2
%run run_experiment.py --exp b --dry-run --reps 2
```
If you see errors, fix your `.jsonl` files and rerun.

### Cell 4 — Test run (1 model, 2 reps)
```python
%run run_experiment.py --exp a --models gpt-4o --reps 2
%run run_experiment.py --exp b --models gpt-4o --reps 2
```

### Cell 5 — Full run (all 9 models, 10 reps)
This takes 30–60 min and costs API credits. Run only when ready:
```python
%run run_experiment.py --exp a --reps 10
%run run_experiment.py --exp b --reps 10
```

### Cell 6 — Analyze
```python
%run analyze_results.py results/results_*.json
```

Results go to `results/results_YYYYMMDD_HHMMSS.json`.

## Models (9)

gpt-4o, DeepSeek-V3.1, DeepSeek-V4-Pro, DeepSeek-V4-Flash, DeepSeek-R1, Llama-3.3-70B, Mistral-Large-3, grok-4-20-non-reasoning, grok-4-1-fast-reasoning

All configured in `models.json`. No setup needed beyond the API key.

## If something breaks

- `ERROR: export AZURE_KEY` → you forgot Cell 2 (set API key)
- `Δεν βρέθηκαν αρχεία .jsonl` → files not in the right folder
- `Σφάλμα στη γραμμή X` → bad JSON in your .jsonl, check quotes
- Rate limit → wait a minute, rerun (it skips completed items)
