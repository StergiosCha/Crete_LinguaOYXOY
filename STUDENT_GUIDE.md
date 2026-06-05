# Οδηγίες για το πείραμα — Crete LinguaOYXOY

## Πείραμα με ανθρώπους

Στείλτε τους συμμετέχοντες στο σωστό link:

- **Πείραμα Α (φυσικότητα):** https://stergioscha.github.io/Crete_LinguaOYXOY/?exp=a
- **Πείραμα Β (συναναφορά):** https://stergioscha.github.io/Crete_LinguaOYXOY/?exp=b

Ο συμμετέχων συμπληρώνει δημογραφικά, βλέπει οδηγίες, κάνει εξάσκηση, και μετά βαθμολογεί τις προτάσεις (1–7). Στο τέλος βλέπει «Ευχαριστούμε!» και τα δεδομένα αποθηκεύονται αυτόματα.

**Αποτελέσματα:** Τα δεδομένα πηγαίνουν αυτόματα στο Google Sheet «Crete LinguaOYXOY — Experiment Results»:
https://docs.google.com/spreadsheets/d/135gCIdwoJmncXfvfkQ6-EMELOWxdIPUWxCtQcOjRW4k/edit

Κάθε πείραμα γράφει σε ξεχωριστό tab: **Exp A** και **Exp B**. Κάθε γραμμή = 1 item × 1 συμμετέχων, με timestamp, participant_id, phenomenon, condition, rating, rt_ms.

## Πείραμα με LLMs

### 1. Προετοιμασία stimuli
Τα items σας είναι στο `index.html` αλλά ΟΧΙ στα `.jsonl` αρχεία. Μεταφέρετε τα στα:

    stimuli/exp_a/cd.jsonl, clld.jsonl, pc.jsonl, fillers.jsonl
    stimuli/exp_b/binding.jsonl, crossover.jsonl, fillers.jsonl

### 2. Notebook
Ανοίξτε το **`run_experiment_notebook.ipynb`** (Shift+Enter για κάθε κελί):

1. `!pip install openai`
2. API Key — πάρτε το από [portal.azure.com](https://portal.azure.com) → **crete-xamoulis-resource** → Keys and Endpoint → Key 1
3. Dry run: `%run run_experiment.py --exp a --dry-run --reps 2`
4. Δοκιμή: `%run run_experiment.py --exp a --models gpt-4o --reps 2`
5. Πλήρης εκτέλεση: `%run run_experiment.py --exp a --reps 10` (9 μοντέλα × 10 reps, ~60 λεπτά)

### 3. Αποτελέσματα LLM
Αποθηκεύονται στον φάκελο `results/results_YYYYMMDD_HHMMSS.json`. Ανάλυση: `%run analyze_results.py results/results_*.json`
