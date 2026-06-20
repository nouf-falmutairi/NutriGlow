/**
 * translations.js
 * ----------------
 * Central dictionary of every user-facing string in both languages.
 * Keeping this separate from app.js means adding a third language later
 * is a matter of adding one more object here -- no logic changes needed.
 */

/**
 * Diet / Lifestyle values come straight from the spreadsheet (in English)
 * and are also what gets submitted to the backend, stored in sessionStorage,
 * and used for filtering -- so the underlying value must stay in English
 * regardless of UI language. This map only controls how those exact values
 * are *displayed* when Arabic is active. If you add a new Diet/Lifestyle
 * value to the spreadsheet, add its Arabic label here too -- any value
 * without an entry simply falls back to showing the original English text.
 */
const DIET_LIFESTYLE_AR = {
  // Diet options
  Balanced: "متوازن",
  "High Protein": "عالي البروتين",
  "Low Carb": "قليل الكربوهيدرات",

  // Lifestyle options
  "Office job": "وظيفة مكتبية",
  "Stay at Home": "في المنزل",
  Student: "طالب/ة",
  "Work from Home": "العمل من المنزل",
};

/**
 * Translate a Diet/Lifestyle value for display purposes only.
 * English UI (or any value not in the map) returns the value unchanged.
 */
function translateDietOrLifestyle(value) {
  if (getCurrentLanguage() === "ar" && DIET_LIFESTYLE_AR[value]) {
    return DIET_LIFESTYLE_AR[value];
  }
  return value;
}

const TRANSLATIONS = {
  en: {
    dir: "ltr",
    app_name: "NutriGlow",
    slogan: "Fuel your week, effortlessly.",

    // Home page
    home_gender_label: "Gender",
    home_gender_hint: "Used to fine-tune your plan in future updates.",
    gender_male: "Male",
    gender_female: "Female",
    home_diet_label: "Diet",
    home_diet_hint: "Pick the eating style that fits you best.",
    home_lifestyle_label: "Lifestyle",
    home_lifestyle_hint: "Tell us how your days usually look.",
    home_starting_label: "Starting week",
    home_starting_hint: "Your 5-day plan always covers Monday through Friday.",
    start_sunday: "Sunday",
    start_monday: "Monday",
    calculate_btn: "Calculate",
    calculating_btn: "Building your plan…",
    form_error: "Please choose one option in every section before continuing.",

    // Top nav / results shell
    tab_meal_plan: "Meal Plan",
    tab_shopping_list: "Shopping List",
    download_pdf_btn: "Download PDF",
    new_plan_btn: "Generate a new plan",

    // Meal plan view
    meal_plan_title: "Your 5-Day Meal Plan",
    meal_plan_summary: "Crafted for your {diet} • {lifestyle} routine, starting {day}.",
    relaxed_note:
      "Heads up: a few meals come from a related diet or lifestyle because your exact match ran out of unique options for the full week. They're marked below.",
    relaxed_flag: "Adjusted match",
    breakfast: "Breakfast",
    lunch: "Lunch",
    dinner: "Dinner",
    ingredients_label: "Ingredients",

    // Shopping list view
    shopping_list_title: "Your Shopping List",
    shopping_list_summary: "Everything you need for the full week, all in one place.",

    // Exit modal
    modal_title: "You're going to lose your current plan, are you sure?",
    modal_body:
      "Starting a new plan will clear the meal plan and shopping list you have open right now.",
    modal_confirm: "Yes, generate new plan",
    modal_cancel: "No, let me save the result",

    // Misc
    loading_message: "Putting your meals together…",
    no_plan_found: "We couldn't find a saved plan. Taking you back home…",
  },

  ar: {
    dir: "rtl",
    app_name: "نوتري جلو",
    slogan: "غذي أسبوعك بكل سهولة.",

    // Home page
    home_gender_label: "الجنس",
    home_gender_hint: "يساعدنا في تحسين خطتك ضمن التحديثات القادمة.",
    gender_male: "ذكر",
    gender_female: "أنثى",
    home_diet_label: "النظام الغذائي",
    home_diet_hint: "اختر نمط الأكل الأنسب لك.",
    home_lifestyle_label: "نمط الحياة",
    home_lifestyle_hint: "أخبرنا كيف يبدو يومك عادة.",
    home_starting_label: "بداية الأسبوع",
    home_starting_hint: "خطتك لمدة 5 أيام تغطي دائمًا من الإثنين إلى الجمعة.",
    start_sunday: "الأحد",
    start_monday: "الإثنين",
    calculate_btn: "احسب الخطة",
    calculating_btn: "نجهّز خطتك…",
    form_error: "يرجى اختيار خيار واحد من كل قسم قبل المتابعة.",

    // Top nav / results shell
    tab_meal_plan: "خطة الوجبات",
    tab_shopping_list: "قائمة التسوق",
    download_pdf_btn: "تحميل PDF",
    new_plan_btn: "إنشاء خطة جديدة",

    // Meal plan view
    meal_plan_title: "خطة وجباتك لمدة 5 أيام",
    meal_plan_summary: "مُعدّة لنظام {diet} ونمط حياة {lifestyle}، تبدأ من {day}.",
    relaxed_note:
      "تنبيه: بعض الوجبات مأخوذة من نظام أو نمط حياة مقارب لأن خياراتك الدقيقة لم تكفِ لتغطية الأسبوع كاملًا دون تكرار. تم تمييزها أدناه.",
    relaxed_flag: "تطابق معدّل",
    breakfast: "الفطور",
    lunch: "الغداء",
    dinner: "العشاء",
    ingredients_label: "المكوّنات",

    // Shopping list view
    shopping_list_title: "قائمة التسوق",
    shopping_list_summary: "كل ما تحتاجه لتحضير وجبات أسبوعك الكامل في مكان واحد.",

    // Exit modal
    modal_title: "أنت على وشك فقدان خطتك الحالية، هل أنت متأكد؟",
    modal_body: "إنشاء خطة جديدة سيؤدي إلى محو خطة الوجبات وقائمة التسوق المفتوحة حاليًا.",
    modal_confirm: "نعم، أنشئ خطة جديدة",
    modal_cancel: "لا، دعني أحفظ النتيجة",

    // Misc
    loading_message: "نقوم بتجهيز وجباتك…",
    no_plan_found: "لم نتمكن من العثور على خطة محفوظة. سنعيدك إلى الصفحة الرئيسية…",
  },
};

/** Returns the current language code ("en" or "ar"), persisted across pages. */
function getCurrentLanguage() {
  return localStorage.getItem("nutriglow_lang") || "en";
}

/** Persists the chosen language so it survives navigation between pages. */
function setCurrentLanguage(lang) {
  localStorage.setItem("nutriglow_lang", lang);
}

/** Shorthand accessor: t("calculate_btn") -> "Calculate" / "احسب الخطة" */
function t(key) {
  const lang = getCurrentLanguage();
  return (TRANSLATIONS[lang] && TRANSLATIONS[lang][key]) || key;
}
