"""
ingredient_parser.py
---------------------
Parses the free-text "Ingredients" column from the meals dataset and
aggregates ingredients across a full meal plan into a clean shopping list.

The raw data looks like:
    "1.5 cup greek yogurt (non-fat), 1 whey protein, and 0.5 cup berries,
     sweetener to preference"

Quirks handled here (discovered by inspecting the real dataset):
  1. Commas appear *inside* parentheses (e.g. "100g beef (ground, 90% lean)")
     and must NOT be treated as ingredient separators.
  2. The final ingredient in a line is joined with " and " instead of a comma.
  3. Trailing seasoning notes ("salt and pepper to preference",
     "sweetener to preference") are not real shopping-list items and are
     filtered out.
  4. Some quantities are written as "<scale> <base> <unit>", e.g.
     "1 1/2 cup oats" (= 1 x 1/2 cup = 0.5 cup) or "2 2 tbsp hummus"
     (= 2 x 2 tbsp = 4 tbsp). This is a recipe-scaling convention, not a
     mixed number, and is resolved by multiplying scale x base.
"""

import re
from collections import defaultdict

from translations_data import translate_ingredient_descriptor

# Units (and size-descriptors that behave like units, e.g. "medium avocado")
# that can appear as the second token in a "<scale> <base> <unit>" pattern.
_UNIT_WORDS = r"(?:cup|tbsp|tsp|oz|g|kg|ml|l|lb|medium|large|small)"

# Matches "<scale> <base or base/denominator> <unit>", e.g. "1 1/2 cup",
# "1.5 1/2 cup", "2 2 tbsp". This must run BEFORE we split on commas.
_SCALE_FIX_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s+(\d+(?:/\d+)?)\s+(" + _UNIT_WORDS + r")\b"
)

# Trailing seasoning notes that are not real, quantifiable shopping items.
_NOTE_RES = [
    re.compile(r"salt and pepper to preference\.?", re.IGNORECASE),
    re.compile(r"sweetener to preference\.?", re.IGNORECASE),
]

# Matches a leading quantity at the start of an ingredient phrase, e.g.
# "1.5 cup greek yogurt (non-fat)" -> ("1.5", "cup greek yogurt (non-fat)")
_LEADING_QTY_RE = re.compile(r"^(\d+(?:\.\d+)?)\s+(.*)$")


def _fraction_to_float(token: str) -> float:
    """Convert '1/2' -> 0.5, or '3' -> 3.0."""
    if "/" in token:
        num, den = token.split("/")
        return int(num) / int(den)
    return float(token)


def _fix_scale_typos(line: str) -> str:
    """
    Resolve the "<scale> <base> <unit>" recipe-scaling pattern into a single
    plain quantity, e.g. "1 1/2 cup oats" -> "0.5 cup oats".
    """

    def _replace(match: "re.Match[str]") -> str:
        scale = float(match.group(1))
        base = _fraction_to_float(match.group(2))
        unit = match.group(3)
        qty = scale * base
        # %g avoids ugly trailing zeros (e.g. 0.5 instead of 0.50)
        return f"{qty:g} {unit}"

    return _SCALE_FIX_RE.sub(_replace, line)


def _strip_notes(line: str) -> str:
    """Remove trailing seasoning notes that aren't real shopping items."""
    for pattern in _NOTE_RES:
        match = pattern.search(line)
        if match:
            line = line[: match.start()] + line[match.end() :]
    return line


def _split_on_top_level_commas(line: str) -> list[str]:
    """
    Split a string on commas, but ignore commas that are nested inside
    parentheses, e.g. "100g beef (ground, 90% lean), 1 egg" splits into
    ["100g beef (ground, 90% lean)", "1 egg"] -- NOT three pieces.
    """
    parts: list[str] = []
    depth = 0
    buffer: list[str] = []
    for char in line:
        if char == "(":
            depth += 1
            buffer.append(char)
        elif char == ")":
            depth = max(0, depth - 1)
            buffer.append(char)
        elif char == "," and depth == 0:
            parts.append("".join(buffer))
            buffer = []
        else:
            buffer.append(char)
    if buffer:
        parts.append("".join(buffer))
    return parts


def parse_ingredient_line(raw_line: str) -> list[str]:
    """
    Convert one CSV "Ingredients" cell into a clean list of ingredient
    phrases, e.g.:
        "3 egg, 1 100g turkey (ground, 93% lean), 1 cup spinach, and
         1 tsp olive oil, salt and pepper to preference"
        ->
        ["3 egg", "1 100g turkey (ground, 93% lean)", "1 cup spinach",
         "1 tsp olive oil"]
    """
    line = raw_line.strip().rstrip(".").strip()
    line = _strip_notes(line)
    line = line.strip(" ,")
    # The final item is joined with " and " instead of a comma -- but only
    # when it's followed by a quantity (avoids mangling phrases like
    # "salt and pepper" if a note slipped through).
    line = re.sub(r",?\s+and\s+(?=\d)", ", ", line)
    line = _fix_scale_typos(line)
    parts = _split_on_top_level_commas(line)
    return [p.strip(" ,") for p in parts if p.strip(" ,")]


def _split_quantity(phrase: str) -> tuple[float | None, str]:
    """
    Split an ingredient phrase into (quantity, descriptor).
    e.g. "1.5 cup greek yogurt (non-fat)" -> (1.5, "cup greek yogurt (non-fat)")
         "garlic"                          -> (None, "garlic")
    """
    match = _LEADING_QTY_RE.match(phrase)
    if not match:
        return None, phrase
    return float(match.group(1)), match.group(2).strip()


def _format_quantity(qty: float) -> str:
    """Render a float quantity without ugly floating point noise."""
    rounded = round(qty, 2)
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:g}"


def build_shopping_list(meals: list[dict]) -> list[dict]:
    """
    Given a list of meal dicts (each must have an 'Ingredients' key holding
    the raw CSV string), parse and aggregate every ingredient across all
    meals into a consolidated shopping list.

    Returns a list of dicts:
        [{"item": "egg", "item_ar": "بيضة", "quantity": "12"}, ...]
    sorted alphabetically by the English item name, ready to render in the
    UI. "item_ar" is the Arabic display label for the same descriptor (see
    translations_data.py) -- the frontend picks whichever of "item"/"item_ar"
    matches the active language, while "item" alone keeps being the
    canonical English key everything else (aggregation, sorting) relies on.
    """
    # Maps a normalized descriptor -> summed quantity (or None if uncountable)
    totals: dict[str, float | None] = defaultdict(float)
    has_quantity: dict[str, bool] = defaultdict(bool)

    for meal in meals:
        raw_ingredients = meal.get("Ingredients", "")
        if not raw_ingredients:
            continue
        for phrase in parse_ingredient_line(raw_ingredients):
            qty, descriptor = _split_quantity(phrase)
            # Normalize descriptor casing/spacing so "1 egg" and "2 egg"
            # aggregate under the same key.
            key = descriptor.strip().lower()
            if qty is None:
                # No leading number found (rare) -- just record presence.
                totals[key] += 0
                has_quantity[key] = has_quantity[key] or False
            else:
                totals[key] += qty
                has_quantity[key] = True

    shopping_list = []
    for descriptor, total_qty in sorted(totals.items()):
        item_ar = translate_ingredient_descriptor(descriptor)
        if has_quantity[descriptor]:
            shopping_list.append(
                {
                    "item": descriptor,
                    "item_ar": item_ar,
                    "quantity": _format_quantity(total_qty),
                }
            )
        else:
            shopping_list.append({"item": descriptor, "item_ar": item_ar, "quantity": ""})

    return shopping_list
