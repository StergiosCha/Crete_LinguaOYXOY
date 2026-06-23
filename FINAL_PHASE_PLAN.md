# LinguaOYXOY — Final Phase Plan

## 1. Stop the Human Experiment

The experiment is closed. Final dataset: 59 participants (Exp A), 44 participants (Exp B).

Download the final spreadsheet from:
`https://docs.google.com/spreadsheets/d/135gCIdwoJmncXfvfkQ6-EMELOWxdIPUWxCtQcOjRW4k/edit`

Save as `Crete LinguaOYXOY — Experiment Results_FINAL.xlsx` in the repo.

---

## 2. Run Statistics on Human Data

### Tools you already have

- **`run_experiment_notebook.ipynb`** — Sections 8–10 cover analysis: loads results JSON, runs `analyze_results.py`, prints per-phenomenon tables, and generates matplotlib bar charts grouped by condition × model.

- **`analyze_results.py`** — Takes one or more results JSON files, groups by phenomenon × condition × model, computes grand mean and SD across all ratings per group, and prints formatted tables. Also computes **between-model Spearman ρ correlations** per phenomenon (requires scipy). Exports CSV.

  ```bash
  python analyze_results.py results/results_*.json
  ```

### What to compute

**Descriptive:** Mean rating and SD per condition, per phenomenon. Number of participants, demographic breakdown (age, gender, region, education).

**Inferential (Exp A):**
- One-way ANOVA or Kruskal-Wallis on CD conditions (12 levels), post-hoc pairwise comparisons (Tukey or Dunn)
- Same for CLLD conditions (15 levels)
- Paired comparison CD vs CLLD on shared conditions (definite_proper, quantifier_some, quantifier_most, quantifier_neg, etc.) — within-subject if possible, otherwise between-items
- Mixed-effects linear model: `rating ~ phenomenon * condition + (1|participant) + (1|item_id)`

**Inferential (Exp B):**
- Binding vs crossover conditions
- Plural conjunction (kai vs me, singular vs plural, preverbal vs postverbal): 2×2×2 factorial

**Reliability:** Cronbach's alpha or split-half on the ratings.

---

## 3. Polydefinites

### What you already have

The polydefinite experiment is **separate** from the main acceptability experiment. Key differences:

| | Main experiment | Polydefinite experiment |
|---|---|---|
| Scale | 1–7 (grammaticality) | **1–10** (semantic felicity) |
| Format | Bare sentence | **Context + sentence** |
| Script | `run_experiment.py` | **`run_polydefinite.py`** |
| Stimuli | `stimuli/exp_a/`, `stimuli/exp_b/` | **`stimuli/shared/semantic_felicity.jsonl`** (80 items) |
| Prompt | "βαθμολογήστε τη γραμματικότητα" | **"βαθμολογήστε τη σημασιολογική καταλληλότητα"** |

### Existing results

- **LLM results:** `results/polydefinite_20260519_133331.json` — 720 entries (80 items × 9 models, temp=0.7, 3 reps). Also `polydefinite_20260519_004252.json` (temp=0, 1 rep).
- **Human results:** `Σημασιολογική Καταλληλότητα_main.csv` (Q1, 35 participants) and `Σημασιολογική Καταλληλότητα_2.csv` (Q2, 19 participants).

### Existing analysis scripts

- **`compare_to_paper.py`** — Compares LLM + human ratings against 6 claims from the paper (`GreekPolydefinites_R1.pdf`):
  1. Polydefinites are licit in non-restrictive contexts (rated above midpoint 5)
  2. Poly–mono differences are small and non-significant
  3. Word order provides a benchmark of real unacceptability (SVO/VSO high, OSV/SOV low)
  4. Non-intersective adjectives: poly < mono, feromenos 'alleged' is the lowest
  5. Recall long > recall short (relative clauses help)
  6. Polydefinite violations are weaker than word-order violations (discourse-structural, not grammatical)

  Also computes **item-level Pearson r** between human ratings and each LLM.

  ```bash
  python compare_to_paper.py                                   # uses latest results
  python compare_to_paper.py results/polydefinite_*.json       # specific file
  ```

- **`visualize_results.py`** — Generates matplotlib figures for all the polydefinite comparisons (poly vs mono, word order hierarchy, adjective types, recall short vs long). Saves to `figures/`.

  ```bash
  python visualize_results.py
  ```

### Stimuli structure

Items in `semantic_felicity.jsonl` are paired: e.g., sf_01 (polydefinite "Στον έξυπνο τον αδερφό μου") vs sf_02 (monodefinite "Στον έξυπνο αδερφό μου"), each with discourse contexts testing unique/nonunique referent, contrast, deixis, etc. Q2 items (sf_q2_*) test non-intersective adjectives (γρήγορος, ωραίος, πρώην, Ιταλικός, εκπληκτικός, φερόμενος). Word order items (sf_25–sf_36) serve as a benchmark.

### What to do

1. Read `GreekPolydefinites_R1.pdf`
2. Run `compare_to_paper.py` and `visualize_results.py` on the existing results
3. Collect the relevant literature:
   - Alexiadou & Wilder (1998)
   - Campos & Stavrou (2004)
   - Lekakou & Szendrői (2012)
   - Chatzikyriakidis (2015) on polydefinites in MTT semantics
   - The Coq formalisation in `PolydefiniteSemantics.v`
4. Compare the LLM and human polydefinite ratings with the paper's predictions. Where do they agree/disagree?

---

## 4. Finish the LLM Experiments

All 10 models must complete Exp A and Exp B with 10 reps each. Check which models are done:

```bash
ls results/  # look for result files per model
```

Any model not yet run — run it. Priority: DeepSeek-R1 (was broken, now fixed with the `max_tokens` patch — `git pull` first).

Use the notebook (`run_experiment_notebook.ipynb`, Sections 6–7) to run models one by one: uncomment the relevant cell, run it, check output.

---

## 5. Compare LLMs vs Native Speakers

This is the central analysis. For each condition, compare:

| Condition | Humans (mean) | LLM X (mean) | ... |
|-----------|---------------|---------------|-----|

### Tools you already have

- `analyze_results.py` already computes means/SD per condition × model and Spearman ρ between models
- The notebook (Section 9) prints a complete table: phenomenon × condition × model with means and SDs
- The notebook (Section 10) generates bar charts per phenomenon

### What to report

- Pearson/Spearman correlation between human means and each model's means across conditions
- Per-condition deviation: where does a model diverge most from humans?
- Are LLMs better "speakers" of standard grammar (following textbook judgments) or do they track actual native speaker gradience?

---

## 6. What to Report

### 6.1 Findings that follow the literature

- CD follows the definiteness/referentiality hierarchy: proper > canon_gen > full_np > quantifiers
- CLLD is more permissive than CD across the board
- Word order: SVO > VSO > VOS > OVS > OSV (standard hierarchy)

Report the actual values from your data — **do not hardcode numbers.**

### 6.2 Findings that challenge the literature

**Key finding — "ungrammatical" CD patterns behave like marked word orders.**

CD with certain quantifiers gets ratings comparable to OVS/OSV word orders. These word orders are NOT ungrammatical — they are grammatical under specific discourse conditions (focus, contrast, topic). This raises the question: **are the "ungrammatical" CD cases also acceptable under the right discourse conditions?**

This connects to our aspect × quantifier × context study (designed but not yet run): if adding a discourse context that establishes a superset boosts CD acceptability for these quantifiers, then the constraint is discourse-referentiality, not a syntactic ban.

**Flag for future work:** A follow-up experiment with context-favoring vs bare conditions for the low-rated CD items (the 3×3×2 design we already have stimuli for).

### 6.3 LLMs as native speakers

Report at two levels:

1. **Overall correlation:** Do LLMs reproduce the human gradient? (Compute Pearson/Spearman r per model across all conditions — use `analyze_results.py` for between-model ρ, and add a human column)
2. **Systematic biases:** Do LLMs overrate "grammatical" items (ceiling effect)? Underrate "marginal" items (binary grammar)? Do they collapse the gradient into a binary grammatical/ungrammatical split where humans show a continuum?

---

## 7. Timeline

| Day | Task |
|-----|------|
| 1 | Download final data, close experiment, compute descriptive stats |
| 2 | Inferential statistics (ANOVA, mixed effects), reliability |
| 3 | Finish remaining LLM runs (R1, any others incomplete) |
| 4 | LLM vs human comparison tables and correlations |
| 5 | Run `compare_to_paper.py` + `visualize_results.py`, polydefinite literature review |
| 6 | Write-up: findings that follow/challenge literature |
| 7 | Write-up: LLM as native speaker analysis |
