# Crete LLM Acceptability Experiment (v2)

**University of Crete — Chatzikyriakidis 2026**

LLMs as syntactic informants for Greek: acceptability judgments on a 1–7 scale, testing phenomena from Greek syntax and Greek dialect variation (via GRDD+).

Split into **two experiments** for human participant feasibility (Latin square, ~15 min each):

- **Experiment A** — Clitic Doubling + CLLD (related clitic phenomena)
- **Experiment B** — Binding + Crossover + Plural Conjunction (nominal/pronominal phenomena)

All models run on **Azure** (no external APIs).

## Quick Start

```bash
pip install -r requirements.txt
export AZURE_KEY='your-key-here'

# Dry run — Experiment A
python run_experiment.py --exp a --dry-run --reps 2

# Dry run — Experiment B
python run_experiment.py --exp b --dry-run --reps 2

# Real run — Experiment A, one model, 3 reps
python run_experiment.py --exp a --models gpt-4o --reps 3

# Real run — Experiment B, all models, 10 reps
python run_experiment.py --exp b

# Single file only
python run_experiment.py --file stimuli/exp_a/cd.jsonl --models gpt-4o --reps 3

# Full run — everything (both experiments combined)
python run_experiment.py

# Analyze
python analyze_results.py results/results_*.json
```

## Structure

```
Crete_LinguaOYXOY_v2/
├── run_experiment.py              # Main experiment runner (--exp a / --exp b)
├── analyze_results.py             # Results analysis & CSV export
├── models.json                    # Model configuration
├── run_experiment_notebook.ipynb   # Jupyter notebook workflow
├── crete_experiment_guide.docx    # Student guide
├── requirements.txt
├── stimuli/
│   ├── exp_a/                     # Experiment A stimuli
│   │   ├── cd.jsonl               #   Clitic Doubling (66 items, 11 conditions × 2 × 3)
│   │   └── clld.jsonl             #   CLLD (68 items, 14 conditions × 2)
│   ├── exp_b/                     # Experiment B stimuli
│   │   ├── binding.jsonl          #   Binding Theory (24 items, 8 conditions × 3)
│   │   ├── crossover.jsonl        #   Crossover effects (27 items, 9 conditions × 3)
│   │   └── plural_conjunction.jsonl  # Plural conjunction (42 items, 14 conditions × 3)
│   └── shared/                    # Shared across both experiments
│       ├── fillers.jsonl          #   Fillers (35 items: 20 grammatical + 15 ungrammatical)
│       └── dialect_template.jsonl #   Dialect examples (8 items, students expand from GRDD+)
└── results/                       # Output directory (gitignored)
```

## Experiment Design

### Experiment A: CD + CLLD (134 critical items + 43 shared = 177 total)

**Clitic Doubling** — 11 conditions, each with doubled/bare pair × 3 lexical variants = 66 items:

| Condition | Doubled | Bare | Expected |
|-----------|---------|------|----------|
| pronoun | high | low | obligatory doubling |
| proper_name | high | mid | strong preference |
| definite_dp | high | mid | strong preference |
| indef_specific (έναν) | mid | high | specificity effect |
| indef_nonspec (κάποιον) | low | high | no doubling |
| bare_np | low | high | no doubling |
| merikous (μερικούς/λίγους) | low | high | quantifier blocks |
| pollous (πολλούς/περισσότερους) | low | high | quantifier blocks |
| kathe (κάθε) | low | high | universal blocks |
| kanenan (κανέναν) | mid | high | NPI licensing |
| island | low | mid | island constraint |

**CLLD** — 14 conditions with doubled/bare pairs = 68 items:

| Condition | Items | Notes |
|-----------|-------|-------|
| definite | 3 × 2 | doubled: high, bare: low |
| proper_name | 3 × 2 | doubled: high, bare: low |
| indef_specific | 3 × 2 | doubled: mid, bare: mid |
| indef_nonspec | 3 × 2 | doubled: low, bare: mid |
| merikous | 3 × 2 | doubled: mid, bare: high |
| pollous | 3 × 2 | doubled: mid, bare: high |
| kathe | 3 × 2 | doubled: low, bare: high |
| kanenan | 3 × 2 | doubled: low, bare: mid |
| focus | 3 × 2 | doubled: low, bare: mid |
| embedded | 3 × 2 | doubled: high, bare: low |
| island_temporal | 1 × 2 | structural variable |
| island_causal | 1 × 2 | structural variable |
| island_relative | 1 × 2 | structural variable |
| island_complement | 1 × 2 | structural variable |

### Experiment B: Binding + Crossover + Plural Conjunction (93 critical items + 43 shared = 136 total)

**Binding** — 8 conditions × 3 = 24 items:

| Condition | Expected |
|-----------|----------|
| reflexive_local | high |
| reflexive_nonlocal | low |
| pronoun_free | high |
| pronoun_local_coref | low |
| pronoun_nonlocal | high |
| quant_kathe_reflexive | high |
| quant_kanenan_reflexive | mid |
| reflexive_fronted | mid |

**Crossover** — 9 conditions × 3 = 27 items:

| Condition | Expected |
|-----------|----------|
| sco_wh_resumptive | mid |
| sco_wh_restrictive | mid |
| wco_wh_possessive | mid |
| wco_long_distance | low |
| clld_bound | high |
| quant_kathe_bound | mid |
| quant_kanenan_bound | low |
| quant_merikous_bound | mid |
| baseline | high |

**Plural Conjunction** — 14 conditions × 3 = 42 items:

| Condition | Expected |
|-----------|----------|
| kai_plural_preverbal | high |
| kai_singular_preverbal | low |
| kai_plural_postverbal | high |
| kai_singular_postverbal | mid |
| me_singular_preverbal | high |
| me_plural_preverbal | mid |
| me_singular_postverbal | high |
| me_plural_postverbal | mid |
| reciprocal_conjoined | high |
| reciprocal_singular | low |
| kathe_conj_plural | mid |
| kathe_conj_singular | high |
| disjunction_plural | low |
| disjunction_singular | high |

### Shared Items (both experiments)

- **35 fillers**: 20 grammatical + 15 ungrammatical (scrambled word order)
- **8 dialect templates**: Cypriot, Pontic, Cretan examples (students expand)

### Human Participants (Latin Square)

- 3 lists per experiment, ~115 items per list for Exp A, ~90 for Exp B
- ~15 min per participant per experiment
- Target: 60–75 participants total (20–25 per list)
- Same fillers in both experiments for cross-session anchoring

## Conditions: Finer Granularity

This v2 design separates quantifier types into distinct conditions (not just items within a single "quantifier" condition). Different quantifiers have different grammatical behavior with clitic constructions:

- **μερικούς/λίγους** (merikous) — partitive, allows some clitic interaction
- **πολλούς/περισσότερους** (pollous) — degree quantifier, distinct behavior
- **κάθε** (kathe) — universal, strongly blocks doubling
- **κανέναν** (kanenan) — NPI, interacts with negation

## Models

Four models deployed, six candidates. Edit `models.json` — keys starting with `_` are candidates (remove prefix + ask Stergios to deploy).

| Model | Type | Size | Status |
|-------|------|------|--------|
| gpt-4o | closed | large | Ready |
| gpt-5.4-pro | closed | very large | Ready |
| DeepSeek-V3.1 | open | 685B MoE | Ready |
| Llama-3.3-70B | open | 70B | Ready |

## Stimuli Format

Each `.jsonl` file has one JSON object per line:

```json
{"id": "cd_01a", "sentence": "Αυτόν τον είδα.", "phenomenon": "cd", "condition": "pronoun_doubled", "expected": "high"}
```

Required: `id`, `sentence`, `phenomenon`, `condition`, `expected` (high/mid/low).
Optional: `dialect`, `context`, `notes`.

## Changes from v1

- Split into 2 experiments (A and B) for human participant feasibility
- Finer-grained conditions: quantifier types separated (merikous, pollous, kathe, kanenan)
- CLLD island sub-conditions (temporal, causal, relative, complement) with 1 item each
- More items overall: 270 total (was ~152)
- Shared fillers for cross-session anchoring
- Updated directory structure: `stimuli/exp_a/`, `stimuli/exp_b/`, `stimuli/shared/`

## For Students

Read `crete_experiment_guide.docx` — it has everything you need:

1. **Choose models** (6–8): edit `models.json`
2. **Review stimuli**: check `.jsonl` files, propose additions
3. **Choose dialects**: pick 2–4 from GRDD+, create minimal pairs
4. **Run**: `python run_experiment.py --exp a` or `--exp b`
5. **Analyze**: `python analyze_results.py results/results_*.json`

## License

Internal use — University of Crete.
