# Student Guide: Greek Linguistics Experiment App

Single-file React app (`index.html`) for two Greek linguistics experiments. No build tools needed.

---

## 1. Quick Start

Open `index.html` in any modern browser. That's it.

To share with participants, deploy to GitHub Pages (see Section 7).

---

## 2. File Structure

Everything lives in one HTML file:

- **Top of file**: JSON arrays of experimental items, marked with comments like `// ITEMS_A` and `// ITEMS_B`
- **Middle**: React components (trial screen, demographics, instructions, results)
- **Bottom**: CSS styles
- React and ReactDOM load from CDN -- no npm, no webpack, no build step

---

## 3. How to Add/Edit Items

### Experiment A (Acceptability Judgments)

Each item is a JSON object in the `ITEMS_A` array:

```json
{
  "id": "cd_01",
  "sentence": "Greek sentence here",
  "context": "optional discourse context",
  "phenomenon": "cd|clld|plural_conjunction",
  "condition": "condition_name",
  "expected": "high|mid|low"
}
```

| Field | Description |
|-------|-------------|
| `id` | Unique identifier. Use prefix for phenomenon: `cd_01`, `clld_05`, `pc_03` |
| `sentence` | The Greek sentence participants will rate |
| `context` | Discourse context shown above the sentence. Use `""` if none |
| `phenomenon` | One of: `cd`, `clld`, `plural_conjunction` |
| `condition` | The experimental condition (your design) |
| `expected` | Expected rating direction: `high`, `mid`, or `low`. For analysis only, not shown to participants |

### Experiment B (Coreference Judgments)

Each item is a JSON object in the `ITEMS_B` array:

```json
{
  "id": "bind_01",
  "sentence": "HTML with colored spans",
  "phenomenon": "binding|crossover",
  "condition": "condition_name",
  "expected": "high|mid|low"
}
```

Same fields as Experiment A, but `sentence` contains HTML with colored spans to mark coreference:

| CSS Class | Color | Usage |
|-----------|-------|-------|
| `idx-a` | Red | Referent group 1 |
| `idx-b` | Blue | Referent group 2 |
| `idx-c` | Green | Referent group 3 |

Words with the **same** color class are meant to co-refer.

Example:

```html
"Ο <span class='idx-a'>Γιάννης</span> αγαπάει <span class='idx-a'>τον εαυτό του</span>."
```

Result: "Γιάννης" and "τον εαυτό του" both appear in red, signaling coreference.

---

## 4. How to Add Fillers

Add items with `"phenomenon": "filler"` to either items array:

```json
{"id": "filler_01", "sentence": "Clearly grammatical sentence", "context": "", "phenomenon": "filler", "condition": "grammatical", "expected": "high"}
{"id": "filler_02", "sentence": "Clearly ungrammatical sentence", "context": "", "phenomenon": "filler", "condition": "ungrammatical", "expected": "low"}
```

Guidelines:
- Mix clearly good and clearly bad sentences
- Use them to catch inattentive participants (anyone rating fillers wrong is suspect)
- Aim for roughly 20-30% fillers in your item list

---

## 5. How to Modify the Interface

Search for these markers in the HTML file:

| What to change | Search for |
|----------------|------------|
| Instructions text | `INSTRUCTIONS_A`, `INSTRUCTIONS_B` |
| Demographics questions | `DEMOGRAPHICS` |
| Practice items | `PRACTICE_ITEMS` |
| Coreference colors | `idx-a`, `idx-b`, `idx-c` (in CSS) |
| Scale labels | `SCALE_LABELS` |
| Number of scale points | `SCALE_MAX` |

---

## 6. Data Collection

### Default: Browser Download

Results are saved in the browser during the experiment. At the end, participants download a CSV.

CSV columns: `participant_id, experiment, item_id, phenomenon, condition, expected, response, response_time_ms`

### Google Sheets Integration

1. Go to [Google Apps Script](https://script.google.com) and create a new project
2. Paste this script:

```javascript
function doPost(e) {
  var sheet = SpreadsheetApp.openById('YOUR_SHEET_ID').getActiveSheet();
  var data = JSON.parse(e.postData.contents);
  data.forEach(function(row) {
    sheet.appendRow(Object.values(row));
  });
  return ContentService.createTextOutput('OK');
}
```

3. Deploy as Web App (Execute as: Me, Access: Anyone)
4. Copy the web app URL
5. In `index.html`, find `BACKEND_URL` and paste the URL there

### Firebase Realtime Database

1. Create a Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
2. Create a Realtime Database (start in test mode for development)
3. In `index.html`, find `BACKEND_URL` and set it to: `https://YOUR-PROJECT.firebaseio.com/results.json`
4. The app will POST results as JSON to this endpoint
5. Before going live, set proper security rules to allow writes only

---

## 7. Deployment to GitHub Pages

### Step by step

1. Create a GitHub repository (or use an existing one)

2. Create a `/docs` folder in your repo and put `index.html` inside it:
   ```
   your-repo/
     docs/
       index.html
   ```

3. Push to GitHub:
   ```bash
   git add docs/index.html
   git commit -m "Add experiment app"
   git push origin main
   ```

4. Go to your repo on GitHub: **Settings** > **Pages**

5. Under **Source**, select:
   - Branch: `main`
   - Folder: `/docs`
   - Click **Save**

6. Wait 1-2 minutes. Your experiment will be live at:
   ```
   https://USERNAME.github.io/REPO-NAME/
   ```

7. Share this URL with participants.

---

## 8. Common Tasks

### Change the rating scale from 1-7 to 1-10

Search for `SCALE_MAX` in the file, change `7` to `10`. Update `SCALE_LABELS` if you have endpoint labels.

### Add a new condition to Experiment A

Just add new items with your new condition name in the `condition` field. No other changes needed.

### Change the colors in Experiment B

Find the CSS section and search for `idx-a`, `idx-b`, `idx-c`. Change the `color` values:

```css
.idx-a { color: #d32f2f; }  /* red -> change to whatever */
.idx-b { color: #1976d2; }  /* blue */
.idx-c { color: #388e3c; }  /* green */
```

### Add attention check items

```json
{"id": "attn_01", "sentence": "Obviously perfect sentence", "context": "", "phenomenon": "attention_check", "condition": "grammatical", "expected": "high"}
```

Your analysis script can flag participants who rate attention checks incorrectly.

### Change the instructions

Search for `INSTRUCTIONS_A` (Experiment A) or `INSTRUCTIONS_B` (Experiment B) and edit the text.

### Add more than 3 colors for coreference

Add new classes in the CSS section following the existing pattern:

```css
.idx-d { color: #f57c00; font-weight: bold; }  /* orange */
.idx-e { color: #7b1fa2; font-weight: bold; }  /* purple */
```

Then use `<span class='idx-d'>word</span>` in your sentences.

---

## Tips

- Always test new items by opening `index.html` locally before deploying
- Back up your item lists separately (copy the JSON arrays to a `.json` file)
- Use your browser's developer console (F12) to debug any issues
- Item presentation order is randomized automatically per participant
