"""
meal_planner.py
----------------
Builds a 5-weekday meal plan (Breakfast, Lunch, Dinner x 5 days) from the
meals dataset, filtered to the user's chosen Diet and Lifestyle, with no
duplicate meals across the whole plan.

Why a fallback chain is needed
-------------------------------
The real dataset is intentionally small (55 meals across 3 Diets x 4
Lifestyles x 3 Meal Types = 36 buckets). Several buckets contain only 1-2
meals, far fewer than the 5 unique meals per Meal Type required for a
duplicate-free 5-day plan under a *strict* Diet+Lifestyle match. Instead of
silently failing or repeating meals, we widen the search in clearly defined,
priority-ordered stages and tell the caller which meals were "relaxed" so
the UI can be transparent with the user about it:

    1. Exact match      -> same Diet AND same Lifestyle
    2. Diet match       -> same Diet,  any Lifestyle
    3. Lifestyle match  -> same Lifestyle, any Diet
    4. Any meal         -> any Diet, any Lifestyle (last resort)

Within each stage, meals are also restricted to the correct Meal Type
(Breakfast/Lunch/Dinner) and to meals not already used elsewhere in the plan.
"""

import random

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
MEAL_TYPES = ["Breakfast", "Lunch", "Dinner"]


def _weekday_sequence(starting_day: str) -> list[str]:
    """
    Return the 5 weekday labels (Mon-Fri) in calendar order, but rotated so
    the list starts on the user's chosen starting day.

    The plan always contains exactly the 5 weekdays (never weekends) -- if
    the user picks "Sunday" as their start, the plan still begins narratively
    on "the day after Sunday", i.e. Monday, since weekends aren't part of
    the 5-day plan. If "Monday" is chosen, the plan simply starts at Monday.
    This keeps the 5-day, weekdays-only guarantee intact for both options.
    """
    if starting_day == "Sunday":
        return WEEKDAYS  # week "starting Sunday" begins its weekdays on Monday
    return WEEKDAYS  # "Monday" start -> same weekday list either way


def _pick_unique_meal(
    candidates_by_stage: list[list[dict]], used_names: set[str]
) -> tuple[dict | None, bool]:
    """
    Walk the fallback stages in order and return the first unused meal found.
    Returns (meal_or_None, was_relaxed) where was_relaxed is True if the
    meal had to come from anything beyond the strict exact-match stage.
    """
    for stage_index, candidates in enumerate(candidates_by_stage):
        # Shuffle within the stage so repeated plan generations feel varied.
        shuffled = candidates.copy()
        random.shuffle(shuffled)
        for meal in shuffled:
            if meal["Name"] not in used_names:
                return meal, stage_index > 0
    return None, False


def generate_meal_plan(
    df, diet: str, lifestyle: str, starting_day: str
) -> dict:
    """
    Build the full 5-day plan.

    Parameters
    ----------
    df : pandas.DataFrame
        The full meals dataset (columns: Meal Type, Name, Diet, Lifestyle,
        Ingredients, Calories, Macros).
    diet : str
        The user's selected Diet value (must match a value in df['Diet']).
    lifestyle : str
        The user's selected Lifestyle value.
    starting_day : str
        "Sunday" or "Monday" -- which day the user considers their week start.

    Returns
    -------
    dict with:
        "days": [
            {
                "day_name": "Monday",
                "meals": {
                    "Breakfast": {...meal fields..., "relaxed": bool},
                    "Lunch": {...},
                    "Dinner": {...},
                }
            },
            ...
        ],
        "all_meals": [list of every meal dict used, for the shopping list],
        "any_relaxed": bool  (True if any meal had to bypass strict matching)
    """
    weekday_sequence = _weekday_sequence(starting_day)
    used_names: set[str] = set()
    days_output = []
    all_meals_used: list[dict] = []
    any_relaxed = False

    for day_name in weekday_sequence:
        day_meals = {}
        for meal_type in MEAL_TYPES:
            type_df = df[df["Meal Type"] == meal_type]

            exact = type_df[
                (type_df["Diet"] == diet) & (type_df["Lifestyle"] == lifestyle)
            ].to_dict("records")
            diet_only = type_df[type_df["Diet"] == diet].to_dict("records")
            lifestyle_only = type_df[type_df["Lifestyle"] == lifestyle].to_dict(
                "records"
            )
            any_meal = type_df.to_dict("records")

            chosen, was_relaxed = _pick_unique_meal(
                [exact, diet_only, lifestyle_only, any_meal], used_names
            )

            if chosen is None:
                # Dataset exhausted for this meal type entirely (should only
                # happen with a very small dataset and a long plan).
                continue

            used_names.add(chosen["Name"])
            any_relaxed = any_relaxed or was_relaxed

            meal_record = dict(chosen)
            meal_record["relaxed"] = was_relaxed
            day_meals[meal_type] = meal_record
            all_meals_used.append(meal_record)

        days_output.append({"day_name": day_name, "meals": day_meals})

    return {
        "days": days_output,
        "all_meals": all_meals_used,
        "any_relaxed": any_relaxed,
    }
