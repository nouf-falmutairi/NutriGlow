/**
 * home.js
 * --------
 * Handles the Home page: language toggle + form submission.
 *
 * On submit, POSTs the form to /generate, stores the returned plan in
 * sessionStorage (so it survives the navigation to /results and the
 * back-and-forth between the Meal Plan / Shopping List tabs), then
 * navigates to /results.
 */

const STORAGE_KEY = "nutriglow_plan";

/** Apply the given language to every translatable element on this page. */
function applyLanguage(lang) {
  setCurrentLanguage(lang);
  const dict = TRANSLATIONS[lang];

  document.getElementById("html-root").setAttribute("lang", lang);
  document.getElementById("html-root").setAttribute("dir", dict.dir);

  document.getElementById("lang-en-btn").classList.toggle("active", lang === "en");
  document.getElementById("lang-ar-btn").classList.toggle("active", lang === "ar");

  document.getElementById("brand-name").textContent = dict.app_name;
  document.getElementById("brand-slogan").textContent = dict.slogan;

  document.getElementById("label-gender").childNodes[0].textContent = dict.home_gender_label + " ";
  document.getElementById("hint-gender").textContent = dict.home_gender_hint;
  document.getElementById("label-diet").childNodes[0].textContent = dict.home_diet_label + " ";
  document.getElementById("hint-diet").textContent = dict.home_diet_hint;
  document.getElementById("label-lifestyle").childNodes[0].textContent =
    dict.home_lifestyle_label + " ";
  document.getElementById("hint-lifestyle").textContent = dict.home_lifestyle_hint;
  document.getElementById("label-starting").childNodes[0].textContent =
    dict.home_starting_label + " ";
  document.getElementById("hint-starting").textContent = dict.home_starting_hint;

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) el.textContent = dict[key];
  });

  // Diet/Lifestyle pill labels: relabel for display only. The underlying
  // <input value="..."> stays in English (it's what gets submitted to the
  // backend and matched against the dataset) -- data-value on the <label>
  // holds that original English text so we can always translate from it,
  // regardless of how many times the language is toggled back and forth.
  document.querySelectorAll("#diet-options .pill-label, #lifestyle-options .pill-label").forEach((el) => {
    const originalValue = el.getAttribute("data-value");
    el.textContent = translateDietOrLifestyle(originalValue);
  });

  document.getElementById("calculate-btn").textContent = dict.calculate_btn;
  document.getElementById("form-error").textContent = dict.form_error;
  document.getElementById("loading-message").textContent = dict.loading_message;

  document.title = `${dict.app_name} — ${dict.slogan}`;
}

function setupLanguageToggle() {
  document.getElementById("lang-en-btn").addEventListener("click", () => applyLanguage("en"));
  document.getElementById("lang-ar-btn").addEventListener("click", () => applyLanguage("ar"));
}

function getSelectedValue(name) {
  const checked = document.querySelector(`input[name="${name}"]:checked`);
  return checked ? checked.value : null;
}

function setupFormSubmit() {
  const form = document.getElementById("meal-form");
  const errorEl = document.getElementById("form-error");
  const loadingOverlay = document.getElementById("loading-overlay");
  const calculateBtn = document.getElementById("calculate-btn");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorEl.style.display = "none";

    const formValues = {
      gender: getSelectedValue("gender"),
      diet: getSelectedValue("diet"),
      lifestyle: getSelectedValue("lifestyle"),
      starting_day: getSelectedValue("starting_day"),
    };

    if (!formValues.gender || !formValues.diet || !formValues.lifestyle || !formValues.starting_day) {
      errorEl.style.display = "block";
      return;
    }

    calculateBtn.disabled = true;
    calculateBtn.textContent = t("calculating_btn");
    loadingOverlay.classList.remove("hidden");

    try {
      const response = await fetch("/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formValues),
      });

      if (!response.ok) {
        throw new Error("Server responded with an error.");
      }

      const planData = await response.json();

      // Persist for the result page (and for tab switches / PDF export).
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(planData));

      // Clear the "user confirmed leaving result page" flag from any
      // previous session so the exit-warning logic starts fresh.
      sessionStorage.removeItem("nutriglow_leaving_confirmed");

      window.location.href = "/results";
    } catch (err) {
      loadingOverlay.classList.add("hidden");
      calculateBtn.disabled = false;
      calculateBtn.textContent = t("calculate_btn");
      errorEl.textContent =
        getCurrentLanguage() === "ar"
          ? "حدث خطأ ما. يرجى المحاولة مرة أخرى."
          : "Something went wrong. Please try again.";
      errorEl.style.display = "block";
      console.error(err);
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setupLanguageToggle();
  setupFormSubmit();
  applyLanguage(getCurrentLanguage());
});
