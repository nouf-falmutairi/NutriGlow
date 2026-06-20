"""
translations_data.py
----------------------
Arabic translations for every piece of *dataset-derived* content the app
displays: meal names, ingredient descriptors, macro labels, and the
"Calories" unit word.

Why this file exists
---------------------
`static/js/translations.js` already covers every *static UI string*
(buttons, headings, modal text, etc.) in both languages. What it does NOT
cover is content that comes from `data/Halal_Meals_Plan.xlsx` at runtime
(meal names like "Turkey Omelet", ingredient lines like "3 egg, 1 cup
spinach...", or macro labels like "protein = 38.9 g"). Since that content
originates in English in the spreadsheet, it needs its own translation
layer -- this module is that layer.

This dictionary is applied **server-side** in app.py, once, right after a
plan is generated, so:
  * The frontend (results.js) and the PDF generator (pdf_generator.py) both
    read from the same already-translated fields and never go out of sync.
  * Filtering / matching logic elsewhere in the app keeps using the
    original English values untouched (Name, Diet, Lifestyle, Ingredients),
    exactly like the existing DIET_LIFESTYLE_AR / ARABIC_VALUE_LABELS maps
    already do for Diet/Lifestyle/Gender/Day -- this file just extends the
    same pattern to meal Name/Ingredients/Macros/Calories.

Maintenance note
-----------------
If a new meal, ingredient, or unit is added to the spreadsheet without a
matching entry here, every helper below safely falls back to the original
English text rather than crashing -- so the app keeps working, just with
that one new item temporarily untranslated until an entry is added.
"""

import re

# ---------------------------------------------------------------------------
# 1. Meal names (55 unique values in the current dataset)
# ---------------------------------------------------------------------------
MEAL_NAME_AR: dict[str, str] = {
    "Apple Walnut Yogurt": "زبادي بالتفاح والجوز",
    "Avocado Egg Toast": "توست الأفوكادو والبيض",
    "Avocado Tuna Boat": "قارب الأفوكادو والتونة",
    "Baked Salmon & Sweet Potato": "سلمون مخبوز مع البطاطا الحلوة",
    "Beef & Broccoli": "لحم بقري مع البروكلي",
    "Beef & Kale Salad": "سلطة اللحم البقري والكرنب",
    "Beef Rice Prep": "وجبة الأرز واللحم البقري المجهزة",
    "Beef Stir Fry Rice": "أرز مقلي باللحم البقري",
    "Black Bean Chicken Bowl": "وعاء الدجاج والفاصولياء السوداء",
    "Boiled Egg & Cheese": "بيض مسلوق مع الجبن",
    "Chia Pudding": "بودنغ بذور الشيا",
    "Chicken & Edamame": "دجاج مع إيدامامي",
    "Chicken Bell Pepper Skewers": "أسياخ الدجاج والفليفلة",
    "Chicken Black Bean Rice": "أرز الدجاج والفاصولياء السوداء",
    "Chicken Broccoli Stir Fry": "دجاج مقلي مع البروكلي",
    "Chicken Salad Sandwich": "ساندويتش سلطة الدجاج",
    "Chicken Zucchini Prep": "وجبة الدجاج والكوسا المجهزة",
    "Chickpea Curry": "كاري الحمص",
    "Chickpea Salad Wrap": "راب سلطة الحمص",
    "Cold Lentil Turkey Salad": "سلطة العدس والديك الرومي البارد",
    "Cottage Cheese Fruit Bowl": "وعاء جبن القريش والفواكه",
    "Egg Bean Burrito": "بوريتو البيض والفاصولياء",
    "Garlic Butter Steak & Asparagus": "ستيك بزبدة الثوم مع الهليون",
    "Grilled Chicken & Quinoa": "دجاج مشوي مع الكينوا",
    "Hardboiled Eggs & Almonds": "بيض مسلوق مع اللوز",
    "Hummus Turkey Pita": "خبز بيتا بالحمص والديك الرومي",
    "Lemon Garlic Shrimp": "جمبري بالليمون والثوم",
    "Lemon Herb Chicken": "دجاج بالليمون والأعشاب",
    "Lentil Chicken Stew": "يخنة العدس والدجاج",
    "Overnight Oats": "شوفان منقوع طوال الليل",
    "PB Banana Wrap": "راب زبدة الفول السوداني والموز",
    "Pan-seared Tofu & Mushrooms": "توفو مع الفطر مقلي بالمقلاة",
    "Pasta Marinara Turkey": "باستا مارينارا بالديك الرومي",
    "Quick Turkey Chili": "تشيلي سريع بالديك الرومي",
    "Salmon & Asparagus": "سلمون مع الهليون",
    "Salmon Quinoa Prep": "وجبة السلمون والكينوا المجهزة",
    "Salmon Scramble": "بيض مخلوط بالسلمون",
    "Shrimp Avocado Salad": "سلطة الجمبري والأفوكادو",
    "Shrimp Cabbage Stir Fry": "جمبري مقلي مع الملفوف",
    "Shrimp Pasta": "باستا بالجمبري",
    "Spinach Feta Scramble": "بيض مخلوط بالسبانخ والفيتا",
    "Steak & Eggs": "ستيك مع البيض",
    "Sweet Potato Chicken Skillet": "دجاج بالبطاطا الحلوة على المقلاة",
    "Sweet Potato Turkey Bake": "ديك رومي مخبوز بالبطاطا الحلوة",
    "Tofu Edamame Bowl": "وعاء التوفو والإيدامامي",
    "Tuna Lettuce Wraps": "لفائف الخس بالتونة",
    "Tuna Quinoa Salad": "سلطة التونة والكينوا",
    "Turkey Cucumber Bites": "قطع الديك الرومي والخيار",
    "Turkey Omelet": "أومليت الديك الرومي",
    "Turkey Spinach Salad": "سلطة الديك الرومي والسبانخ",
    "Whey Oat Pancakes": "بان كيك الشوفان والواي بروتين",
    "Yogurt & Whey Bowl": "وعاء الزبادي والواي بروتين",
    "Zucchini Egg Skillet": "بيض بالكوسا على المقلاة",
    "Zucchini Noodles Beef": "معكرونة الكوسا باللحم البقري",
    "Zucchini Turkey Boats": "قوارب الكوسا بالديك الرومي",
}

# ---------------------------------------------------------------------------
# 2. Ingredient descriptors -- maps the *English descriptor* (the part of an
#    ingredient phrase after the leading quantity, lower-cased) to Arabic.
#    These are the same 54 unique descriptors that build_shopping_list()
#    produces from the real dataset, plus a few qualifier fragments that
#    appear nested in parentheses so word-level replacement also works for
#    the free-text "Ingredients" line shown under each meal.
# ---------------------------------------------------------------------------
INGREDIENT_AR: dict[str, str] = {
    "100g beef (ground, 90% lean)": "لحم بقري مفروم (90٪ خالٍ من الدهن) - 100غ",
    "100g beef steak (sirloin)": "ستيك لحم بقري (سيرلوين) - 100غ",
    "100g chicken breast": "صدر دجاج - 100غ",
    "100g salmon": "سلمون - 100غ",
    "100g shrimp": "جمبري - 100غ",
    "100g tofu (firm)": "توفو صلب - 100غ",
    "100g turkey (ground, 93% lean)": "ديك رومي مفروم (93٪ خالٍ من الدهن) - 100غ",
    "apple": "تفاحة",
    "banana": "موزة",
    "bell pepper": "فليفلة",
    "bread (whole wheat)": "خبز (قمح كامل)",
    "cup asparagus": "كوب هليون",
    "cup berries": "كوب توت",
    "cup black beans": "كوب فاصولياء سوداء",
    "cup broccoli": "كوب بروكلي",
    "cup cabbage": "كوب ملفوف",
    "cup chickpeas": "كوب حمص",
    "cup cottage cheese": "كوب جبن قريش",
    "cup cucumber": "كوب خيار",
    "cup edamame": "كوب إيدامامي",
    "cup greek yogurt (non-fat)": "كوب زبادي يوناني (خالٍ من الدسم)",
    "cup kale": "كوب كرنب",
    "cup lentils": "كوب عدس",
    "cup lettuce": "كوب خس",
    "cup marinara sauce": "كوب صلصة مارينارا",
    "cup mushroom": "كوب فطر",
    "cup oats": "كوب شوفان",
    "cup pasta (whole wheat, cooked)": "كوب باستا (قمح كامل، مطبوخة)",
    "cup quinoa (cooked)": "كوب كينوا (مطبوخة)",
    "cup rice (white, cooked)": "كوب أرز (أبيض، مطبوخ)",
    "cup spinach": "كوب سبانخ",
    "egg": "بيضة",
    "garlic": "ثوم",
    "medium avocado": "حبة أفوكادو متوسطة",
    "onion": "بصلة",
    "oz almonds": "أونصة لوز",
    "oz cheddar cheese": "أونصة جبن شيدر",
    "oz feta cheese": "أونصة جبن فيتا",
    "oz walnuts": "أونصة جوز",
    "pita bread": "خبز بيتا",
    "sweet potato": "بطاطا حلوة",
    "tbsp chia seeds": "ملعقة كبيرة بذور شيا",
    "tbsp hummus": "ملعقة كبيرة حمص",
    "tbsp lemon juice": "ملعقة كبيرة عصير ليمون",
    "tbsp peanut butter": "ملعقة كبيرة زبدة فول سوداني",
    "tbsp soy sauce (low sodium)": "ملعقة كبيرة صوص صويا (قليل الصوديوم)",
    "tomato": "طماطم",
    "tortilla (whole wheat)": "تورتيلا (قمح كامل)",
    "tsp ginger": "ملعقة صغيرة زنجبيل",
    "tsp olive oil": "ملعقة صغيرة زيت زيتون",
    "tsp sesame oil": "ملعقة صغيرة زيت سمسم",
    "tuna (canned)": "تونة (معلبة)",
    "whey protein": "بروتين واي",
    "zucchini": "كوسا",
}

# Word/phrase-level fragments used to translate the free-text "Ingredients"
# line shown under each meal (e.g. "3 egg, 1 100g turkey (ground, 93% lean),
# 1 cup spinach, and 1 tsp olive oil, salt and pepper to preference").
# Applied longest-phrase-first so multi-word fragments win over short ones
# (e.g. "olive oil" must be matched before a lone "oil" rule, if one existed).
_INGREDIENT_WORD_FRAGMENTS: dict[str, str] = {
    **INGREDIENT_AR,
    "salt and pepper to preference": "ملح وفلفل حسب الرغبة",
    "sweetener to preference": "محلي حسب الرغبة",
    "and": "و",
    "ground": "مفروم",
    "lean": "خالٍ من الدهن",
    "non-fat": "خالٍ من الدسم",
    "firm": "صلب",
    "whole wheat": "قمح كامل",
    "cooked": "مطبوخ",
    "low sodium": "قليل الصوديوم",
    "white": "أبيض",
    "sirloin": "سيرلوين",
    "canned": "معلبة",
}

# ---------------------------------------------------------------------------
# 3. Macro / unit labels
# ---------------------------------------------------------------------------
MACRO_LABEL_AR = {
    "protein": "بروتين",
    "carb": "كارب",
    "fat": "دهون",
}

CALORIES_WORD_AR = "سعرة حرارية"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def translate_meal_name(name: str) -> str:
    """Arabic label for a meal Name. Falls back to the English name if a
    new meal hasn't been added to MEAL_NAME_AR yet."""
    return MEAL_NAME_AR.get(name.strip(), name)


def translate_calories(calories: str) -> str:
    """'312 Calories' -> '312 سعرة حرارية' (keeps the number, swaps the unit word)."""
    match = re.match(r"^\s*([\d.,]+)\s*Calories?\s*$", calories.strip(), re.IGNORECASE)
    if not match:
        return calories
    return f"{match.group(1)} {CALORIES_WORD_AR}"


def translate_macros(macros: str) -> str:
    """
    'protein = 38.9 g\\ncarb= 2.2 g\\nfat= 27.0 g'
    -> 'بروتين = 38.9 غ\\nكارب= 2.2 غ\\nدهون= 27.0 غ'

    Swaps the English macro-name token at the start of each line for its
    Arabic label and 'g' (grams) for 'غ', while leaving the numbers and
    line structure (and the '\\n'-based layout results.js/pdf_generator.py
    already split on) completely intact.
    """
    out_lines = []
    for line in macros.split("\n"):
        translated = line
        for en_key, ar_key in MACRO_LABEL_AR.items():
            translated = re.sub(
                rf"^(\s*){en_key}(\s*=)", rf"\1{ar_key}\2", translated, flags=re.IGNORECASE
            )
        # Trailing unit "g" (grams) -> "غ", only as a standalone unit token.
        translated = re.sub(r"(?<=[\d.\s])g\b", "غ", translated)
        out_lines.append(translated)
    return "\n".join(out_lines)


def translate_ingredient_descriptor(descriptor: str) -> str:
    """
    Translate one already-split shopping-list descriptor (lower-cased,
    no leading quantity), e.g. 'cup spinach' -> 'كوب سبانخ'.
    Falls back to the original English descriptor if not in the dictionary
    (e.g. a brand-new ingredient added to the spreadsheet).
    """
    return INGREDIENT_AR.get(descriptor.strip().lower(), descriptor)


def translate_ingredients_line(raw_line: str) -> str:
    """
    Translate the full free-text "Ingredients" cell shown under each meal
    card, e.g.:
        "3 egg, 1 100g turkey (ground, 93% lean), 1 cup spinach, and
         1 tsp olive oil, salt and pepper to preference"
        ->
        "3 بيضة، 1 ديك رومي مفروم (93% خالٍ من الدهن) - 100غ، 1 كوب سبانخ، و
         1 ملعقة صغيرة زيت زيتون، ملح وفلفل حسب الرغبة"

    This is a best-effort *display* translation (word/phrase substitution
    over the known ingredient vocabulary) -- it never touches the original
    English string used elsewhere for parsing/matching.
    """
    translated = raw_line
    # Longest phrases first so multi-word fragments aren't partially
    # clobbered by a shorter overlapping rule.
    for en_phrase in sorted(_INGREDIENT_WORD_FRAGMENTS, key=len, reverse=True):
        ar_phrase = _INGREDIENT_WORD_FRAGMENTS[en_phrase]
        translated = re.sub(
            re.escape(en_phrase), ar_phrase, translated, flags=re.IGNORECASE
        )
    # Commas read more naturally as Arabic commas once the rest of the line
    # is Arabic; keep numbers/parentheses/percent signs exactly as they are.
    translated = translated.replace(",", "،")
    return translated
