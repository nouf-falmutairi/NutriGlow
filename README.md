# NutriGlow / نوتري جلو

A modern, minimalist, bilingual (English/Arabic, full RTL support) meal-planning web app.
Built with **Flask** (backend) + **pandas** (data filtering) + vanilla **HTML/CSS/JS** (frontend, no build step required).

https://nutriglow-production-6f3b.up.railway.app/
\---

## 1\. What this app does

1. **Home page** — pick your Gender, Diet, Lifestyle, and Starting day. Diet and Lifestyle options are extracted **dynamically** from your `Halal\_Meals\_Plan.xlsx` file, so if you edit the spreadsheet and add a new Diet, it will automatically show up as a new option next time you restart the app.
2. **Generate** — the backend filters the dataset to your Diet + Lifestyle and builds a 5-weekday plan (Mon–Fri), 3 meals/day, with **no duplicate meals** across the whole week.
3. **Result page** — a single page with two tabs (Meal Plan / Shopping List) that you can switch between freely with **no data loss and no reload**. You can download either view as a polished PDF, or start a new plan (with a styled confirmation popup protecting you from losing your current plan).

\---

## 2\. Project structure

```
nutriglow/
├── app.py                  # Flask routes
├── data\_loader.py          # pandas loading + dynamic Diet/Lifestyle extraction
├── meal\_planner.py         # 5-day plan builder + fallback-matching logic
├── ingredient\_parser.py    # Ingredients-column parser + shopping list aggregator
├── translations\_data.py    # EN→AR dictionary for dataset content (meal names,
│                            # ingredients, macros, calories) -- see §6 below
├── pdf\_generator.py        # ReportLab PDF builder (EN + AR)
├── data/
│   └── Halal\_Meals\_Plan.xlsx
├── static/
│   ├── css/style.css
│   ├── js/translations.js  # all EN/AR \*UI\* strings (buttons, headings, etc.)
│   ├── js/home.js          # Home page logic
│   ├── js/results.js       # Result page logic (tabs, exit modal, PDF download)
│   └── fonts/              # AmiriQuran-Regular.ttf land here automatically (see §4)
└── templates/
    ├── index.html          # Home page
    └── result.html         # Result page (Meal Plan + Shopping List tabs)
```

\---

## 3\. Setup \& running locally

```bash
# 1. Create and activate a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\\Scripts\\activate

# 2. Install dependencies
pip install flask pandas openpyxl reportlab arabic-reshaper python-bidi

# 3. Run the app
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

> `arabic-reshaper` and `python-bidi` are only needed for \*\*PDF\*\* generation in Arabic (they shape Arabic glyphs and apply right-to-left ordering, which PDF drawing doesn't do automatically). The website itself works in Arabic immediately — the browser handles RTL/shaping natively. If you skip installing these two packages, the app still runs fine; Arabic PDFs will just fall back to a plain font (see step 4).

\---

## 4\. Arabic text in downloaded PDFs

Browsers render Arabic perfectly out of the box. PDFs are different: the PDF library (ReportLab) needs an **Arabic-supporting font file** on disk to draw Arabic glyphs correctly — without one, Arabic text in the PDF shows up as boxes (▪▪▪) instead of letters.

**This now happens automatically.** The first time you download an Arabic PDF, the app downloads the **AmiriQuran** font (the same family used across the website) directly from Google Fonts and caches it in `static/fonts/` — no manual step needed, as long as the machine running the app has internet access. Subsequent downloads are instant since the cached files are reused.

If the machine has no internet access (e.g. an offline server), the automatic download fails gracefully and the app falls back to a default font with a console warning — English PDFs are completely unaffected either way. To fix it manually in that case:

1. Download the **AmiriQuran** font (free, open-source, Google Fonts):

   * https://fonts.google.com/specimen/AmiriQuran → "Download family"
2. From the unzipped folder, copy these two files into `static/fonts/`:

   * `AmiriQuran-Regular.ttf` → rename if needed to exactly `AmiriQuran-Regular.ttf`
3. Restart the Flask app.

Either way, also make sure `arabic-reshaper` and `python-bidi` are installed (they're in `requirements.txt`) — they handle Arabic letter shaping and right-to-left ordering, which the font file alone doesn't do. Without them, Arabic letters will appear disconnected/in the wrong order even with the correct font in place; the app prints a console warning if they're missing.

\---

## 5\. How the meal-plan matching works

The dataset is intentionally compact, so some Diet+Lifestyle+MealType combinations only contain 1–3 meals — not enough for 5 unique days on their own. Rather than repeating a meal or crashing, the planner widens its search in clearly-prioritized stages:

1. **Exact match** — same Diet **and** same Lifestyle (always tried first).
2. **Diet match** — same Diet, any Lifestyle.
3. **Lifestyle match** — same Lifestyle, any Diet.
4. **Any meal** — last resort, any Diet/Lifestyle of the correct meal type.

Any meal that had to come from stage 2–4 is flagged in the UI with a small **"Adjusted match"** badge, and a one-line note appears at the top of the Meal Plan view explaining why — so the substitution is transparent rather than hidden. The more meals you add to `Halal\_Meals\_Plan.xlsx` for a given Diet+Lifestyle combo, the less often this fallback is needed.

\---

## 6\. How Arabic translation works across the app

There are two separate translation layers, by design:

1. **Static UI text** (buttons, headings, the exit-confirmation modal, "Breakfast/Lunch/Dinner", day names, etc.) lives in `static/js/translations.js` (`TRANSLATIONS.en` / `TRANSLATIONS.ar`) and `DIET\_LIFESTYLE\_AR` in the same file. This is everything that's part of the app itself, not the spreadsheet.
2. **Dataset-derived content** — meal names, the free-text ingredients line, the macro breakdown, and the calorie count — comes from `data/Halal\_Meals\_Plan.xlsx`, which only contains English text. `translations\_data.py` is the Arabic dictionary for that content (covering every meal/ingredient currently in the dataset), applied **once, server-side**, in `app.py`'s `/generate` route. Every meal in the API response gets `Name\_ar`, `Ingredients\_ar`, `Calories\_ar`, and `Macros\_ar` fields alongside the original English ones; every shopping-list entry gets an `item\_ar` field. The frontend (`static/js/results.js`) and the PDF generator (`pdf\_generator.py`) both just pick whichever field matches the active language — neither one re-implements translation logic itself, so they can never drift out of sync with each other.

If a field is ever missing an Arabic translation (e.g. a brand-new meal added to the spreadsheet before its translation is added), every helper in `translations\_data.py` falls back to the original English text rather than crashing or showing something broken.

\---

## 7\. Editing the dataset

`data/Halal\_Meals\_Plan.xlsx` (sheet name **"Meals"**) must keep these exact column headers:

|Meal Type|Name|Diet|Lifestyle|Ingredients|Calories|Macros|
|-|-|-|-|-|-|-|

* **Meal Type** must be one of `Breakfast`, `Lunch`, `Dinner`.
* **Ingredients** should be a comma-separated list, e.g. `"1 egg, 1 cup spinach, and 1 tsp olive oil, salt and pepper to preference"`. The parser understands quantities, units, parenthetical notes like `(ground, 93% lean)`, and trailing seasoning notes — it will skip "salt and pepper to preference" / "sweetener to preference" automatically when building the shopping list.
* Restart the Flask app after editing the spreadsheet so the new data loads.
* **If you add a new meal, ingredient, Diet, or Lifestyle value:** the website and PDFs will keep working immediately, but the *Arabic display text* for that one new item will temporarily fall back to its original English text until you add a matching entry to `translations\_data.py` (meal names / ingredients / macros) or `DIET\_LIFESTYLE\_AR` in `static/js/translations.js` + `ARABIC\_VALUE\_LABELS` in `pdf\_generator.py` (Diet/Lifestyle/Gender/Day). See §6 above for how this all fits together.

\---

## 8\. Notes on the exit-confirmation popup

The spec asks for a **custom, styled popup** (not the browser's native dialog) when leaving the result page. This is implemented two ways:

* **Clicking "Generate a new plan"** and **pressing the browser Back button** are both fully intercepted in JavaScript, so they show the exact custom popup described in the spec, with the two required buttons.
* **Closing the tab/window directly or hard-refreshing** is covered by a `beforeunload` listener as a safety net — but browsers do not allow JavaScript to restyle or relabel that particular dialog (a deliberate browser security restriction so pages can't spoof system dialogs). This is the one case where the browser's own generic "Leave site?" prompt will appear instead of the styled one.

Switching between the **Meal Plan** and **Shopping List** tabs never triggers any of this — it's a same-page show/hide with no navigation involved.

