# Οδηγός: Πώς τρέχουμε τα LLMs για CD, CLLD, Binding, Crossover

Πανεπιστήμιο Κρήτης — Chatzikyriakidis 2026

Αυτός ο οδηγός εξηγεί βήμα-βήμα πώς μετατρέπετε τις προτάσεις σας (από το el_finfin.docx) σε μορφή που καταλαβαίνει ο κώδικας, και πώς τρέχετε το πείραμα.

---

## 1. Εγκατάσταση

```bash
pip install openai
export AZURE_KEY='ζητήστε-το-κλειδί-από-τον-Στέργιο'
```

Δοκιμάστε ότι δουλεύει:

```bash
python test_all_models.py
```

Αν δει `ERROR: export AZURE_KEY`, δεν φόρτωσε το κλειδί. Τρέξτε ξανά τη γραμμή `export`.

---

## 2. Πού μπαίνουν τα stimuli

Τα stimuli είναι αρχεία `.jsonl` (ένα JSON ανά γραμμή). Μπαίνουν σε δύο φακέλους:

```
stimuli/
├── exp_a/          ← Experiment A: CD + CLLD + fillers
│   ├── cd.jsonl
│   ├── clld.jsonl
│   └── fillers.jsonl
├── exp_b/          ← Experiment B: Binding + Crossover + Plural Conjunction + fillers
│   ├── binding.jsonl
│   ├── crossover.jsonl
│   ├── plural_conjunction.jsonl
│   └── fillers.jsonl
└── shared/         ← Κοινά (polydefinites κτλ)
```

**Αυτή τη στιγμή τα αρχεία έχουν placeholder items.** Εσείς πρέπει να τα αντικαταστήσετε με τις πραγματικές σας προτάσεις από το el_finfin.docx.

---

## 3. Μορφή JSONL — πώς γράφω τις προτάσεις

Κάθε γραμμή είναι ένα JSON object. Υποχρεωτικά πεδία: `id`, `sentence`, `phenomenon`, `condition`, `expected`.

### Παράδειγμα CD (Clitic Doubling)

```json
{"id": "cd_01", "sentence": "Τον είδα τον Γιάννη χθες στο πανεπιστήμιο.", "phenomenon": "cd", "condition": "definite_proper", "expected": "high"}
{"id": "cd_02", "sentence": "Την συνάντησα τη Μαρία μετά το μάθημα.", "phenomenon": "cd", "condition": "definite_proper", "expected": "high"}
{"id": "cd_03", "sentence": "Των είπαν των αστυνόμων να πάνε.", "phenomenon": "cd", "condition": "genitive_ton", "expected": "mid"}
{"id": "cd_04", "sentence": "Τους μίλησα στους φοιτητές για την εργασία.", "phenomenon": "cd", "condition": "genitive_doubled_pp", "expected": "high"}
{"id": "cd_05", "sentence": "Τον χρειάζομαι έναν υπνάκο.", "phenomenon": "cd", "condition": "nonspecific_indefinite", "expected": "mid"}
{"id": "cd_06", "sentence": "Τον γνώρισα έναν φίλο φοιτητή από το χθεσινό συνέδριο.", "phenomenon": "cd", "condition": "specific_indefinite", "expected": "high"}
{"id": "cd_07", "sentence": "Τον είδα κάθε φοιτητή στη βιβλιοθήκη να διαβάζει.", "phenomenon": "cd", "condition": "quantifier_kathe", "expected": "mid"}
{"id": "cd_08", "sentence": "Τους απομάκρυνε πολλούς φίλους ο Γιάννης.", "phenomenon": "cd", "condition": "quantifier_pollous", "expected": "mid"}
{"id": "cd_09", "sentence": "Δεν τον είδα κανέναν στην αυλή, ήταν όλοι στο σαλόνι.", "phenomenon": "cd", "condition": "negative_quantifier", "expected": "mid"}
```

### Παράδειγμα CLLD (Clitic Left Dislocation)

```json
{"id": "clld_01", "sentence": "Τον Γιάννη τον είδα χτες στο πανεπιστήμιο.", "phenomenon": "clld", "condition": "definite", "expected": "high"}
{"id": "clld_02", "sentence": "Των αστυνόμων των είπαν να πάνε.", "phenomenon": "clld", "condition": "genitive_ton", "expected": "mid"}
{"id": "clld_03", "sentence": "Στους φοιτητές τους μίλησα για την εργασία.", "phenomenon": "clld", "condition": "genitive_doubled_pp", "expected": "high"}
{"id": "clld_04", "sentence": "Έναν φίλο τον είδα χθες.", "phenomenon": "clld", "condition": "specific_indefinite", "expected": "mid"}
{"id": "clld_05", "sentence": "Κάθε φοιτητή τον είδα στη βιβλιοθήκη να διαβάζει.", "phenomenon": "clld", "condition": "quantifier_kathe", "expected": "low"}
{"id": "clld_06", "sentence": "Νομίζω το σπίτι ότι το άφησα ξεκλείδωτο.", "phenomenon": "clld", "condition": "island_constraint", "expected": "low"}
```

### Παράδειγμα Binding

```json
{"id": "bind_01", "sentence": "Ο μπαμπάς της νόμιζε ότι είδε τον εαυτό του στον καθρέφτη.", "phenomenon": "binding", "condition": "principle_a", "expected": "high"}
{"id": "bind_02", "sentence": "Ο Γιάννης είπε ότι η Μαρία θαυμάζει τον εαυτό του.", "phenomenon": "binding", "condition": "principle_a_violation", "expected": "low"}
{"id": "bind_03", "sentence": "Ο Γιάννης είπε ότι η Μαρία τον αγαπάει.", "phenomenon": "binding", "condition": "principle_b", "expected": "high"}
{"id": "bind_04", "sentence": "Κανένας δεν μπορεί να τον σκοτώσει.", "phenomenon": "binding", "condition": "principle_b_violation", "expected": "low"}
```

### Παράδειγμα Crossover (SCO/WCO)

```json
{"id": "sco_01", "sentence": "Ποια ηθοποιό την λατρεύει ο σύντροφός της;", "phenomenon": "crossover", "condition": "sco_wh", "expected": "mid"}
{"id": "sco_02", "sentence": "Κάθε φοιτητή τον αξιολόγησε αυτός αυστηρά.", "phenomenon": "crossover", "condition": "sco_kathe", "expected": "mid"}
{"id": "wco_01", "sentence": "Κανέναν φοιτητή δεν εκτιμά ο καθηγητής του.", "phenomenon": "crossover", "condition": "wco_kanenan", "expected": "low"}
{"id": "wco_02", "sentence": "Μερικούς μουσικούς ψάχνει η παραγωγή τους.", "phenomenon": "crossover", "condition": "wco_merikous", "expected": "low"}
```

### Παράδειγμα Plural Conjunction

```json
{"id": "pc_01", "sentence": "Ο Γιάννης και η Μαρία έφυγαν από το πάρτι μετά τα μεσάνυχτα.", "phenomenon": "plural_conjunction", "condition": "kai_plural_preverbal", "expected": "high"}
{"id": "pc_02", "sentence": "Ο Γιάννης και η Μαρία έφυγε από το πάρτι μετά τα μεσάνυχτα.", "phenomenon": "plural_conjunction", "condition": "kai_singular_preverbal", "expected": "low"}
{"id": "pc_03", "sentence": "Ο Γιάννης με τη Μαρία έφυγαν από το πάρτι μετά τα μεσάνυχτα.", "phenomenon": "plural_conjunction", "condition": "me_plural_preverbal", "expected": "high"}
{"id": "pc_04", "sentence": "Ο Γιάννης με τη Μαρία έφυγε από το πάρτι μετά τα μεσάνυχτα.", "phenomenon": "plural_conjunction", "condition": "me_singular_preverbal", "expected": "mid"}
```

### Fillers

```json
{"id": "fb_01", "sentence": "Η Στέλλα αγόρασε από την αγορά 3 μήλα και 4 μελιτζάνες για μουσακά.", "phenomenon": "filler", "condition": "grammatical", "expected": "high"}
{"id": "fb_02", "sentence": "Για μουσακά από την αγορά 3 μήλα και 4 μελιτζάνες αγόρασε η Στέλλα.", "phenomenon": "filler", "condition": "scrambled", "expected": "low"}
```

---

## 4. Πώς φτιάχνω το JSONL στην πράξη

### Επιλογή Α: Με text editor

1. Ανοίξτε ένα νέο αρχείο (π.χ. `cd.jsonl`) σε οποιονδήποτε editor
2. Γράψτε μία γραμμή JSON ανά πρόταση
3. Σώστε. Τέλος.

**Προσοχή:**
- Κάθε γραμμή πρέπει να είναι valid JSON — χρησιμοποιήστε `"` (διπλά εισαγωγικά), όχι `'`
- Μην βάζετε κόμμα στο τέλος κάθε γραμμής (δεν είναι array, είναι ξεχωριστά JSON objects)
- Ελληνικοί χαρακτήρες δουλεύουν κανονικά (UTF-8)

### Επιλογή Β: Με Python script

```python
import json

items = [
    {"id": "cd_01", "sentence": "Τον είδα τον Γιάννη χθες στο πανεπιστήμιο.", "phenomenon": "cd", "condition": "definite_proper", "expected": "high"},
    {"id": "cd_02", "sentence": "Την συνάντησα τη Μαρία μετά το μάθημα.", "phenomenon": "cd", "condition": "definite_proper", "expected": "high"},
    # ... προσθέστε τις υπόλοιπες
]

with open("stimuli/exp_a/cd.jsonl", "w", encoding="utf-8") as f:
    for item in items:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
```

### Validate: ελέγξτε ότι τα αρχεία σας είναι σωστά

```bash
python -c "
import json, sys
for line_num, line in enumerate(open(sys.argv[1], encoding='utf-8'), 1):
    line = line.strip()
    if not line: continue
    try:
        obj = json.loads(line)
        for field in ['id', 'sentence', 'phenomenon', 'condition']:
            assert field in obj, f'missing {field}'
    except Exception as e:
        print(f'ERROR line {line_num}: {e}')
        sys.exit(1)
print(f'OK — {line_num} items')
" stimuli/exp_a/cd.jsonl
```

---

## 5. Ονομασία conditions

Διαλέξτε ονόματα που έχουν νόημα για εσάς. Ο κώδικας δεν ενδιαφέρεται τι ονόματα βάζετε — τα χρησιμοποιεί μόνο στα αποτελέσματα. Πρόταση:

### CD conditions
| Condition name | Τι είναι |
|---|---|
| `definite_proper` | Proper noun (Τον είδα τον Γιάννη) |
| `definite_full_np` | Full NP (Τον χαιρέτησα τον καινούριο καθηγητή) |
| `genitive_ton` | Genitive με «των» (Των είπαν των αστυνόμων) |
| `genitive_clitic_gen` | Genitive clitic + genitive NP (Τους άκουσα των φοιτητών) |
| `genitive_doubled_pp` | Genitive clitic + doubled PP (Τους μίλησα στους φοιτητές) |
| `genitive_canonical` | Genitive clitic + κανονικό genitive (Του έδειξα του Γιάννη) |
| `nonspecific_indefinite` | Non-specific (Τον χρειάζομαι έναν υπνάκο) |
| `specific_indefinite` | Specific (Τον γνώρισα έναν φίλο) |
| `quantifier_kathe` | Κάθε |
| `quantifier_merikous` | Μερικούς |
| `quantifier_pollous` | Πολλούς |
| `negative_quantifier` | Κανέναν |

### CLLD conditions
Ίδια ονόματα + `island_relative`, `island_temporal`, `island_other` για τα island constraints.

### Binding conditions
`principle_a`, `principle_a_violation`, `principle_b`, `principle_b_violation`, `reciprocal`, `literature_problem`

### Crossover conditions
`sco_wh`, `sco_kathe`, `sco_merikous`, `sco_kanenan`, `wco_kanenan`, `wco_merikous`, `wco_kathe`

### Plural conjunction conditions
`kai_plural_preverbal`, `kai_singular_preverbal`, `kai_plural_postverbal`, `kai_singular_postverbal`, `me_plural_preverbal`, `me_singular_preverbal`, `me_plural_postverbal`, `me_singular_postverbal`

---

## 6. Τρέξιμο του πειράματος

### Βήμα 1: Dry run (δοκιμαστικά, χωρίς API)

```bash
# Ελέγξτε ότι τα stimuli φορτώνονται σωστά
python run_experiment.py --exp a --dry-run --reps 2
python run_experiment.py --exp b --dry-run --reps 2
```

Αν δείτε σφάλματα (`λείπουν τα πεδία`, `Σφάλμα στη γραμμή`), φτιάξτε το JSONL.

### Βήμα 2: Δοκιμή με 1 μοντέλο, λίγες επαναλήψεις

```bash
# CD + CLLD, μόνο gpt-4o, 3 επαναλήψεις
python run_experiment.py --exp a --models gpt-4o --reps 3

# Binding + Crossover + Plural Conjunction
python run_experiment.py --exp b --models gpt-4o --reps 3
```

### Βήμα 3: Πλήρες πείραμα

```bash
# Experiment A, όλα τα μοντέλα, 10 επαναλήψεις
python run_experiment.py --exp a --reps 10

# Experiment B, όλα τα μοντέλα, 10 επαναλήψεις
python run_experiment.py --exp b --reps 10
```

### Μόνο ένα αρχείο

```bash
python run_experiment.py --file stimuli/exp_a/cd.jsonl --models gpt-4o --reps 5
python run_experiment.py --file stimuli/exp_b/binding.jsonl --models DeepSeek-R1 --reps 10
```

### Μόνο συγκεκριμένα μοντέλα

```bash
python run_experiment.py --exp a --models gpt-4o DeepSeek-R1 Llama-3.3-70B --reps 10
```

---

## 7. Αποτελέσματα

Τα αποτελέσματα αποθηκεύονται αυτόματα στον φάκελο `results/`:

```
results/results_20260526_143022.json
```

### Ανάλυση

```bash
python analyze_results.py results/results_20260526_143022.json
```

Εξάγει:
- Πίνακα με mean + SD ανά condition ανά μοντέλο
- CSV για στατιστική ανάλυση (R, jamovi, JASP)

### Τι βλέπω στα αποτελέσματα

Κάθε item έχει:
- `mean`: μέσος όρος βαθμολογίας (1-7) σε N επαναλήψεις
- `sd`: τυπική απόκλιση
- `ratings`: λίστα με όλες τις βαθμολογίες `[5, 6, 5, 7, 6, ...]`
- `raw_responses`: τι ακριβώς απάντησε το μοντέλο

---

## 8. Διαθέσιμα μοντέλα

Ρυθμισμένα στο `models.json`. Αυτή τη στιγμή:

| Μοντέλο | Provider | Τύπος | Reasoning |
|---|---|---|---|
| gpt-4o | OpenAI | closed | Όχι |
| DeepSeek-V3.1 | DeepSeek | open | Όχι |
| DeepSeek-V4-Pro | DeepSeek | open | Όχι |
| DeepSeek-V4-Flash | DeepSeek | open (fast) | Όχι |
| DeepSeek-R1 | DeepSeek | open | **Ναι** |
| Llama-3.3-70B | Meta | open | Όχι |
| Mistral-Large-3 | Mistral | open | Όχι |
| grok-4-20-non-reasoning | xAI | closed | Όχι |
| grok-4-1-fast-reasoning | xAI | closed | **Ναι** |

Τα reasoning μοντέλα (DeepSeek-R1, grok-4-1-fast-reasoning) σκέφτονται πριν απαντήσουν — ο κώδικας αφαιρεί αυτόματα το `<think>...</think>` κομμάτι.

---

## 9. Κόστος και χρόνος

- Κάθε API call παίρνει ~0.5 δευτερόλεπτα
- 100 items × 9 μοντέλα × 10 reps = 9,000 κλήσεις ≈ 75 λεπτά
- Τα reasoning μοντέλα είναι πιο αργά (~2-5 sec/call)
- **Μην τρέχετε όλα μαζί αμέσως** — δοκιμάστε πρώτα με `--reps 2` σε 1 μοντέλο

---

## 10. Συχνά προβλήματα

| Πρόβλημα | Λύση |
|---|---|
| `ERROR: export AZURE_KEY` | `export AZURE_KEY='...'` (ζητήστε το κλειδί) |
| `Δεν βρέθηκαν αρχεία .jsonl` | Ελέγξτε ότι τα αρχεία είναι στο σωστό φάκελο |
| `Σφάλμα στη γραμμή X` | Invalid JSON — ελέγξτε εισαγωγικά, κόμματα |
| `λείπουν τα πεδία ['condition']` | Προσθέστε τα υποχρεωτικά πεδία |
| `could not parse` | Το μοντέλο δεν απάντησε αριθμό — OK, αγνοείται |
| Rate limit errors | Αυξήστε το sleep ή τρέξτε λιγότερα μοντέλα |

---

## Checklist

- [ ] Μετατρέψτε τις προτάσεις CD/CLLD από el_finfin.docx σε `stimuli/exp_a/cd.jsonl` και `stimuli/exp_a/clld.jsonl`
- [ ] Μετατρέψτε Binding/Crossover/PC σε `stimuli/exp_b/binding.jsonl`, `crossover.jsonl`, `plural_conjunction.jsonl`
- [ ] Φτιάξτε fillers (`exp_a/fillers.jsonl` και `exp_b/fillers.jsonl`)
- [ ] Validate τα αρχεία
- [ ] Dry run (`--dry-run --reps 2`)
- [ ] Test run (1 μοντέλο, 3 reps)
- [ ] Full run (όλα τα μοντέλα, 10 reps)
- [ ] Analyze results
