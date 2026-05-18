# Crete LLM Acceptability Experiment (v2)

**University of Crete — Chatzikyriakidis 2026**

LLMs as syntactic/semantic informants for Greek. Acceptability judgments on a 1-10 scale. All models run on Azure (crete-xamoulis-resource).

## Setup

```bash
pip install openai python-dotenv
export AZURE_KEY='your-key-here'
```

## Running

```bash
# Main experiment (Exp A: CD+CLLD, Exp B: Binding+Crossover+Plural Conjunction)
python run_experiment.py --exp a --models gpt-4o --reps 10
python run_experiment.py --exp b --models gpt-4o --reps 10

# Polydefinite experiment (58 items from both questionnaires)
python run_polydefinite.py --models gpt-4o --reps 10
python run_polydefinite.py --dry-run --reps 2

# Analyze existing results
python run_polydefinite.py --analyze results/polydefinite_*.json
python analyze_results.py results/results_*.json
```

## Models (9)

All deployed on crete-xamoulis-resource: gpt-4o, DeepSeek-V3.1, DeepSeek-V4-Pro, DeepSeek-V4-Flash, DeepSeek-R1, Llama-3.3-70B, Mistral-Large-3, grok-4-20-non-reasoning, grok-4-1-fast-reasoning.

Edit `models.json` to change.

## Structure

```
├── run_experiment.py          # Main experiment runner
├── run_polydefinite.py        # Polydefinite experiment runner
├── analyze_results.py         # Results analysis & CSV export
├── models.json                # Model config
├── test_all_models.py         # Quick test (1 item, all models)
├── stimuli/
│   ├── exp_a/                 # Clitic Doubling + CLLD
│   ├── exp_b/                 # Binding + Crossover + Plural Conjunction
│   └── shared/                # Semantic felicity (polydefinites + more), fillers, dialect
├── results/                   # Output (gitignored)
├── Σημασιολογική Καταλληλότητα_main.csv   # Human data Q1
└── Σημασιολογική Καταλληλότητα_2.csv      # Human data Q2
```

## Stimuli format

One JSON per line in `.jsonl` files:

```json
{"id": "cd_01a", "sentence": "Αυτόν τον είδα.", "phenomenon": "cd", "condition": "pronoun_doubled", "expected": "high"}
```

## License

Internal use — University of Crete.
