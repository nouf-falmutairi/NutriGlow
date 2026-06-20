"""
app.py
-------
NutriGlow / نوتري جلو -- Flask backend.

Routes
------
GET  /                  Home page: input form (Gender, Diet, Lifestyle, Starting day).
POST /generate          Builds the 5-day meal plan + shopping list from the
                         submitted form, stores nothing server-side (the
                         result is returned as JSON and the *browser* holds
                         the only copy, via sessionStorage), then the
                         frontend renders the Result page client-side.
GET  /results           Renders the Result page shell (Meal Plan / Shopping
                         List tabs). The actual plan data is read out of
                         sessionStorage by JS -- if it's missing (e.g. the
                         user navigated here directly), JS redirects home.
POST /download-pdf      Accepts the current plan JSON + which view + which
                         language, returns the matching PDF as a file
                         attachment.

Why no server-side session/database?
A full meal plan is generated fresh from the dataset every time and only
needs to live for the duration of one browser tab's visit -- there is no
user-accounts or persistence requirement in the spec, so keeping state
entirely on the client (sessionStorage) keeps the backend simple, stateless,
and trivially restart-safe.
"""

from flask import Flask, render_template, request, jsonify, send_file

from data_loader import load_meals_dataframe, get_unique_diets, get_unique_lifestyles
from meal_planner import generate_meal_plan
from ingredient_parser import build_shopping_list
from pdf_generator import generate_meal_plan_pdf, generate_shopping_list_pdf
from translations_data import (
    translate_meal_name,
    translate_calories,
    translate_macros,
    translate_ingredients_line,
)

app = Flask(__name__)

# Load the dataset once at startup -- it's small (tens of rows) and the
# Home page's Diet/Lifestyle options depend on it being ready immediately.
MEALS_DF = load_meals_dataframe()
DIET_OPTIONS = get_unique_diets(MEALS_DF)
LIFESTYLE_OPTIONS = get_unique_lifestyles(MEALS_DF)

# Day-name translations used when building the PDF / display labels.
DAY_NAME_AR = {
    "Monday": "الإثنين",
    "Tuesday": "الثلاثاء",
    "Wednesday": "الأربعاء",
    "Thursday": "الخميس",
    "Friday": "الجمعة",
}
MEAL_TYPE_AR = {
    "Breakfast": "الفطور",
    "Lunch": "الغداء",
    "Dinner": "العشاء",
}


@app.route("/")
def home():
    """Render the Home page with dynamically extracted Diet/Lifestyle options."""
    return render_template(
        "index.html",
        diet_options=DIET_OPTIONS,
        lifestyle_options=LIFESTYLE_OPTIONS,
    )


@app.route("/results")
def results():
    """
    Render the Result page shell. The actual meal-plan/shopping-list data is
    populated client-side from sessionStorage (see static/js/app.js) --
    if no data is found there, the page JS redirects back to Home.
    """
    return render_template("result.html")


@app.route("/generate", methods=["POST"])
def generate():
    """
    Build a 5-day meal plan + shopping list from the submitted form values
    and return it as JSON for the frontend to store and render.
    """
    payload = request.get_json(silent=True) or request.form

    gender = payload.get("gender", "")
    diet = payload.get("diet", "")
    lifestyle = payload.get("lifestyle", "")
    starting_day = payload.get("starting_day", "")

    if diet not in DIET_OPTIONS or lifestyle not in LIFESTYLE_OPTIONS:
        return jsonify({"error": "Invalid diet or lifestyle selection."}), 400
    if starting_day not in ("Sunday", "Monday"):
        return jsonify({"error": "Invalid starting day."}), 400

    plan = generate_meal_plan(
        MEALS_DF, diet=diet, lifestyle=lifestyle, starting_day=starting_day
    )

    # Attach bilingual display labels so the frontend can switch languages
    # instantly without re-fetching or recomputing anything.
    for day in plan["days"]:
        day["day_label_en"] = day["day_name"]
        day["day_label_ar"] = DAY_NAME_AR.get(day["day_name"], day["day_name"])
        for meal_type, meal in day["meals"].items():
            meal["meal_type_label_en"] = meal_type
            meal["meal_type_label_ar"] = MEAL_TYPE_AR.get(meal_type, meal_type)
            # Dataset-derived content (meal name, ingredients line, macros,
            # calories) is only ever stored in English in the spreadsheet --
            # translate it here, once, so results.js and pdf_generator.py
            # both just pick the field matching the active language instead
            # of needing their own translation logic.
            meal["Name_ar"] = translate_meal_name(meal.get("Name", ""))
            meal["Ingredients_ar"] = translate_ingredients_line(meal.get("Ingredients", ""))
            meal["Calories_ar"] = translate_calories(meal.get("Calories", ""))
            meal["Macros_ar"] = translate_macros(meal.get("Macros", ""))

    shopping_list = build_shopping_list(plan["all_meals"])

    return jsonify(
        {
            "form": {
                "gender": gender,
                "diet": diet,
                "lifestyle": lifestyle,
                "starting_day": starting_day,
            },
            "days": plan["days"],
            "shopping_list": shopping_list,
            "any_relaxed": plan["any_relaxed"],
        }
    )


@app.route("/download-pdf", methods=["POST"])
def download_pdf():
    """
    Generate a PDF for the currently active view (meal plan or shopping
    list) in the currently active language, and return it as a download.
    """
    payload = request.get_json(silent=True) or {}
    view = payload.get("view", "meal_plan")  # "meal_plan" | "shopping_list"
    language = payload.get("language", "en")  # "en" | "ar"
    plan_data = payload.get("plan_data", {})

    if view == "shopping_list":
        shopping_list = plan_data.get("shopping_list", [])
        buffer = generate_shopping_list_pdf(shopping_list, language=language)
        filename = "NutriGlow_Shopping_List.pdf"
    else:
        # Build the structure pdf_generator expects (day_label/meal_type_label
        # in the active language already attached by /generate).
        days = []
        for day in plan_data.get("days", []):
            day_copy = dict(day)
            day_copy["day_label"] = (
                day.get("day_label_ar") if language == "ar" else day.get("day_label_en")
            )
            meals_copy = {}
            for meal_type, meal in day.get("meals", {}).items():
                meal_copy = dict(meal)
                meal_copy["meal_type_label"] = (
                    meal.get("meal_type_label_ar")
                    if language == "ar"
                    else meal.get("meal_type_label_en")
                )
                # Resolve dataset-derived content to the active language --
                # mirrors the meal_type_label pattern above. "_ar" fields
                # are attached server-side in /generate (see
                # translations_data.py); English falls back to the original
                # spreadsheet values already present on the meal dict.
                if language == "ar":
                    meal_copy["Name"] = meal.get("Name_ar", meal.get("Name", ""))
                    meal_copy["Ingredients"] = meal.get(
                        "Ingredients_ar", meal.get("Ingredients", "")
                    )
                    meal_copy["Calories"] = meal.get("Calories_ar", meal.get("Calories", ""))
                    meal_copy["Macros"] = meal.get("Macros_ar", meal.get("Macros", ""))
                meals_copy[meal_type] = meal_copy
            day_copy["meals"] = meals_copy
            days.append(day_copy)

        form = plan_data.get("form", {})
        full_plan = {
            "diet": form.get("diet", ""),
            "lifestyle": form.get("lifestyle", ""),
            "gender": form.get("gender", ""),
            "starting_day": form.get("starting_day", ""),
            "days": days,
        }
        buffer = generate_meal_plan_pdf(full_plan, language=language)
        filename = "NutriGlow_Meal_Plan.pdf"

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
