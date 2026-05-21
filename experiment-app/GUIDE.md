# Student Guide: Greek Linguistics Experiment App

Single-file React app (`index.html`) for two Greek linguistics experiments. No build tools needed.

---

## 1. Quick Start

Open `index.html` in any browser to test locally.

Live URLs for participants:
- **Experiment A**: `https://stergioscha.github.io/Crete_LinguaOYXOY/?exp=a`
- **Experiment B**: `https://stergioscha.github.io/Crete_LinguaOYXOY/?exp=b`

---

## 2. File Structure

Everything lives in one HTML file. The top of the file has four arrays you need to edit:

| Array | What it is |
|-------|------------|
| `EXPERIMENT_A_ITEMS` | Main items for Experiment A |
| `EXPERIMENT_A_PRACTICE` | Practice items for Experiment A (shown with feedback) |
| `EXPERIMENT_B_ITEMS` | Main items for Experiment B |
| `EXPERIMENT_B_PRACTICE` | Practice items for Experiment B (shown with feedback) |

Everything below the line `// ===== APPLICATION CODE BELOW =====` should not be edited.

---

## 3. How to Add/Edit Items

### Experiment A (Acceptability Judgments — CD/CLLD/Plural Conjunction)

Add items to the `EXPERIMENT_A_ITEMS` array. Each item looks like this:

```javascript
{
  id: "cd_01",
  sentence: "Τον είδα τον Γιάννη χθες στο πανεπιστήμιο.",
  context: "",
  phenomenon: "cd",
  condition: "definite_proper",
  expected: "high"
}
```

| Field | Description |
|-------|-------------|
| `id` | Unique identifier. Use prefix for phenomenon: `cd_01`, `clld_05`, `pc_03` |
| `sentence` | The Greek sentence participants will rate |
| `context` | Discourse context shown in a gray box above the sentence. Use `""` for none |
| `phenomenon` | One of: `cd`, `clld`, `plural_conjunction`, `genitive_clitic`, `filler` |
| `condition` | The experimental condition (your design) |
| `expected` | Expected rating: `high`, `mid`, or `low`. Not shown to participants |

### Experiment B (Coreference Judgments — Binding/Crossover)

Add items to the `EXPERIMENT_B_ITEMS` array. The sentence field uses HTML spans with color classes to mark coreference:

```javascript
{
  id: "bind_01",
  sentence: "Ο <span class='idx-a'>Γιάννης</span> είδε <span class='idx-a'>τον εαυτό του</span> στον καθρέφτη.",
  phenomenon: "binding",
  condition: "principle_a",
  expected: "high"
}
```

| CSS Class | Color | Meaning |
|-----------|-------|---------|
| `idx-a` | Red | Coreference group 1 |
| `idx-b` | Blue | Coreference group 2 |
| `idx-c` | Green | Coreference group 3 |

Words with the **same** color class co-refer (same person/thing). Participants see the colors and rate how acceptable that interpretation is.

### Practice Items

Practice items have an extra `feedback` field shown after the participant responds:

```javascript
{
  id: "practice_a_01",
  sentence: "Χθες πήγα στην αγορά και αγόρασα φρούτα.",
  context: "",
  phenomenon: "practice",
  condition: "grammatical",
  expected: "high",
  feedback: "Αυτή η πρόταση είναι φυσιολογική — οι περισσότεροι ομιλητές θα τη βαθμολογούσαν ψηλά (6–7)."
}
```

---

## 4. How to Add Fillers

Add items with `"phenomenon": "filler"` to either items array:

```javascript
{id: "filler_01", sentence: "Clearly grammatical sentence", context: "", phenomenon: "filler", condition: "grammatical", expected: "high"},
{id: "filler_02", sentence: "Clearly ungrammatical sentence", context: "", phenomenon: "filler", condition: "ungrammatical", expected: "low"}
```

Aim for roughly 20-30% fillers. Use them to catch inattentive participants.

---

## 5. Data Collection

Results are **automatically sent to Google Sheets** when a participant finishes. No downloads, no manual steps.

The Google Sheet receives one row per item with columns: timestamp, participant_id, experiment, age, gender, education, native_speaker, region, item_id, phenomenon, condition, rating, rt_ms, item_order.

---

## 6. Deployment

After editing items, push changes and redeploy:

```bash
rm -f .git/HEAD.lock
git add experiment-app/index.html
git commit -m "Update stimuli"
git push origin main
git push origin `git subtree split --prefix experiment-app main`:gh-pages --force
```

Wait 1-2 minutes for GitHub Pages to update.

---

## 7. Common Tasks

### Change the rating scale from 1-7 to 1-5

Search for the `RatingScale` component and change `[1,2,3,4,5,6,7]` to your range.

### Add a new condition

Just add new items with your new condition name in the `condition` field. No other changes needed.

### Change coreference colors

Find the CSS at the top and edit:

```css
.idx-a { color: #E15759; font-weight: 700; }  /* red */
.idx-b { color: #4E79A7; font-weight: 700; }  /* blue */
.idx-c { color: #59A14F; font-weight: 700; }  /* green */
```

### Add more than 3 colors

Add new classes in the CSS:

```css
.idx-d { color: #f57c00; font-weight: 700; }  /* orange */
.idx-e { color: #7b1fa2; font-weight: 700; }  /* purple */
```

Then use `<span class='idx-d'>word</span>` in your sentences.

---

## Tips

- Always test locally (`open index.html` in browser) before deploying
- Item order is randomized per participant (seeded by participant ID)
- Back up your item lists separately
- Use browser dev console (F12) to debug issues
