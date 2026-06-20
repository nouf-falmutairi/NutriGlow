/**
 * results.js
 * -----------
 * Drives the Result page: renders the Meal Plan + Shopping List views from
 * sessionStorage data, handles the tab switch between them (no reload, no
 * warning), the "Generate a new plan" exit-confirmation flow, the browser
 * back-button exit-confirmation flow, language switching, and PDF download.
 *
 * Exit-warning implementation notes
 * ----------------------------------
 * The spec asks for a *custom, styled* popup with two buttons. Browsers
 * will not let JavaScript style or add custom buttons to the native
 * `beforeunload` confirmation dialog (a security restriction so a page
 * can't fake a dialog freely) -- so this page uses two complementary
 * mechanisms:
 *
 *   1. In-app navigation (clicking "Generate a new plan", or pressing the
 *      browser Back button while on this page) is fully intercepted in JS,
 *      so we show our OWN styled modal with the exact two buttons the spec
 *      requires. This covers the two main "exit the result context" paths.
 *
 *   2. Actually closing the tab/window or hard-refreshing is covered by a
 *      `beforeunload` listener as a safety net. Per browser security
 *      rules this can only show the browser's own generic "Leave site?"
 *      dialog (its text is fixed by the browser, not by us) -- it cannot
 *      be restyled. This is a deliberate, unavoidable browser limitation,
 *      not a gap in the implementation.
 *
 * Crucially, switching between the "Meal Plan" and "Shopping List" tabs
 * never triggers either mechanism, because it's a same-page show/hide
 * (no navigation happens at all).
 */

const STORAGE_KEY = "nutriglow_plan";
let planData = null;
let activeView = "meal_plan"; // "meal_plan" | "shopping_list"

/* ============================================================
   Plan loading
   ============================================================ */

function loadPlanData() {
  const raw = sessionStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

/* ============================================================
   Language handling
   ============================================================ */

function applyLanguage(lang) {
  setCurrentLanguage(lang);
  const dict = TRANSLATIONS[lang];

  document.getElementById("html-root").setAttribute("lang", lang);
  document.getElementById("html-root").setAttribute("dir", dict.dir);

  document.getElementById("lang-en-btn").classList.toggle("active", lang === "en");
  document.getElementById("lang-ar-btn").classList.toggle("active", lang === "ar");

  document.getElementById("brand-name-sm").textContent = dict.app_name;
  document.getElementById("tab-meal-plan").textContent = dict.tab_meal_plan;
  document.getElementById("tab-shopping-list").textContent = dict.tab_shopping_list;
  document.getElementById("download-pdf-label").textContent = dict.download_pdf_btn;
  document.getElementById("new-plan-label").textContent = dict.new_plan_btn;

  document.getElementById("meal-plan-title").textContent = dict.meal_plan_title;
  document.getElementById("shopping-list-title").textContent = dict.shopping_list_title;
  document.getElementById("shopping-list-summary").textContent = dict.shopping_list_summary;

  document.getElementById("modal-title").textContent = dict.modal_title;
  document.getElementById("modal-body").textContent = dict.modal_body;
  document.getElementById("modal-confirm-btn").textContent = dict.modal_confirm;
  document.getElementById("modal-cancel-btn").textContent = dict.modal_cancel;
  document.getElementById("loading-message").textContent = dict.loading_message;

  document.title = `${dict.app_name} — ${dict.tab_meal_plan}`;

  if (planData) {
    renderMealPlanSummary();
    renderDayRail();
    renderDayCards();
    renderShoppingList();
  }
}

/* ============================================================
   Rendering: Meal Plan view
   ============================================================ */

function renderMealPlanSummary() {
  const dict = TRANSLATIONS[getCurrentLanguage()];
  const lang = getCurrentLanguage();
  const form = planData.form;

  const summaryText = dict.meal_plan_summary
    .replace("{diet}", translateDietOrLifestyle(form.diet))
    .replace("{lifestyle}", translateDietOrLifestyle(form.lifestyle))
    .replace("{day}", lang === "ar" ? planData.days[0].day_label_ar : planData.days[0].day_label_en);
  document.getElementById("meal-plan-summary").textContent = summaryText;

  const chipsEl = document.getElementById("summary-chips");
  chipsEl.innerHTML = "";
  const genderLabel = form.gender === "Female" ? dict.gender_female : dict.gender_male;
  [translateDietOrLifestyle(form.diet), translateDietOrLifestyle(form.lifestyle), genderLabel].forEach(
    (value) => {
      const chip = document.createElement("span");
      chip.className = "summary-chip";
      chip.textContent = value;
      chipsEl.appendChild(chip);
    }
  );

  const relaxedNote = document.getElementById("relaxed-note");
  if (planData.any_relaxed) {
    relaxedNote.textContent = dict.relaxed_note;
    relaxedNote.style.display = "block";
  } else {
    relaxedNote.style.display = "none";
  }
}

function renderDayRail() {
  const lang = getCurrentLanguage();
  const rail = document.getElementById("day-rail");
  rail.innerHTML = "";
  planData.days.forEach((day) => {
    const node = document.createElement("div");
    node.className = "day-node";
    node.innerHTML = `
      <div class="connector"></div>
      <div class="dot"></div>
      <div class="day-label">${lang === "ar" ? day.day_label_ar : day.day_label_en}</div>
    `;
    rail.appendChild(node);
  });
}

function renderDayCards() {
  const lang = getCurrentLanguage();
  const dict = TRANSLATIONS[lang];
  const container = document.getElementById("day-cards");
  container.innerHTML = "";

  const mealTypeOrder = ["Breakfast", "Lunch", "Dinner"];

  planData.days.forEach((day) => {
    const card = document.createElement("div");
    card.className = "day-card";

    const header = document.createElement("div");
    header.className = "day-card-header";
    header.textContent = lang === "ar" ? day.day_label_ar : day.day_label_en;
    card.appendChild(header);

    mealTypeOrder.forEach((mealType) => {
      const meal = day.meals[mealType];
      if (!meal) return;

      const row = document.createElement("div");
      row.className = "meal-row";

      const typeLabel = lang === "ar" ? meal.meal_type_label_ar : meal.meal_type_label_en;
      const relaxedFlag = meal.relaxed
        ? `<span class="relaxed-flag">${dict.relaxed_flag}</span>`
        : "";

      // Dataset-derived content (Name/Ingredients/Calories/Macros) is
      // translated server-side in app.py's /generate route -- "_ar" fields
      // hold the Arabic display text. Fall back to the English field if an
      // "_ar" value is ever missing (e.g. a plan generated before this
      // translation layer existed and still sitting in sessionStorage).
      const isAr = lang === "ar";
      const name = (isAr && meal.Name_ar) || meal.Name;
      const ingredients = (isAr && meal.Ingredients_ar) || meal.Ingredients;
      const calories = (isAr && meal.Calories_ar) || meal.Calories;
      const macros = (isAr && meal.Macros_ar) || meal.Macros;

      row.innerHTML = `
        <div class="meal-type-badge">${typeLabel}</div>
        <div class="meal-info">
          <div class="meal-name">${name}${relaxedFlag}</div>
          <div class="meal-ingredients">${ingredients}</div>
        </div>
        <div class="meal-macros">
          <span class="calories">${calories}</span>
          <span>${macros.replace(/\n/g, " · ")}</span>
        </div>
      `;
      card.appendChild(row);
    });

    container.appendChild(card);
  });
}

/* ============================================================
   Rendering: Shopping List view
   ============================================================ */

function renderShoppingList() {
  const lang = getCurrentLanguage();
  const isAr = lang === "ar";
  const listEl = document.getElementById("shopping-list");
  listEl.innerHTML = "";
  planData.shopping_list.forEach((entry) => {
    const itemLabel = (isAr && entry.item_ar) || entry.item;
    const li = document.createElement("li");
    li.innerHTML = `
      <span class="shopping-qty">${entry.quantity || "—"}</span>
      <span class="shopping-item">${itemLabel}</span>
    `;
    listEl.appendChild(li);
  });
}

/* ============================================================
   Tab switching (no reload, no exit warning)
   ============================================================ */

function switchView(view) {
  activeView = view;
  document
    .getElementById("tab-meal-plan")
    .classList.toggle("active", view === "meal_plan");
  document
    .getElementById("tab-shopping-list")
    .classList.toggle("active", view === "shopping_list");
  document
    .getElementById("view-meal-plan")
    .classList.toggle("hidden", view !== "meal_plan");
  document
    .getElementById("view-shopping-list")
    .classList.toggle("hidden", view !== "shopping_list");
}

function setupTabs() {
  document.getElementById("tab-meal-plan").addEventListener("click", () => switchView("meal_plan"));
  document
    .getElementById("tab-shopping-list")
    .addEventListener("click", () => switchView("shopping_list"));
}

/* ============================================================
   Exit-confirmation modal (covers "Generate a new plan" + Back button)
   ============================================================ */

let pendingExitAction = null; // function to run if the user confirms leaving

function openExitModal(onConfirm) {
  pendingExitAction = onConfirm;
  document.getElementById("exit-modal").classList.add("visible");
}

function closeExitModal() {
  document.getElementById("exit-modal").classList.remove("visible");
  pendingExitAction = null;
}

function setupExitModal() {
  document.getElementById("modal-confirm-btn").addEventListener("click", () => {
    const action = pendingExitAction;
    closeExitModal();
    sessionStorage.removeItem(STORAGE_KEY);
    sessionStorage.setItem("nutriglow_leaving_confirmed", "true");
    if (action) action();
  });

  document.getElementById("modal-cancel-btn").addEventListener("click", () => {
    closeExitModal();
    // "No, let me save the result" -- if the user triggered this via the
    // Back button, we've already pushed a fresh history entry (see
    // setupBackButtonGuard) so staying put requires no extra action here.
  });
}

/** "Generate a new plan" button always goes through the custom modal. */
function setupNewPlanButton() {
  document.getElementById("new-plan-btn").addEventListener("click", () => {
    openExitModal(() => {
      window.location.href = "/";
    });
  });
}

/**
 * Browser back-button guard.
 * We push an extra history entry on load so the first Back press triggers
 * a `popstate` event WITHOUT actually leaving the page yet. We catch that
 * event, show our custom modal, and only navigate home if the user
 * confirms -- otherwise we push the guard state again so Back continues
 * to be intercepted.
 */
function setupBackButtonGuard() {
  history.pushState({ nutriglowGuard: true }, "");

  window.addEventListener("popstate", () => {
    if (sessionStorage.getItem("nutriglow_leaving_confirmed") === "true") {
      return; // user already confirmed elsewhere; let navigation proceed
    }
    openExitModal(() => {
      window.location.href = "/";
    });
    // Re-arm the guard so the back button stays intercepted if the user
    // cancels (clicks "No, let me save the result").
    history.pushState({ nutriglowGuard: true }, "");
  });
}

/**
 * Tab-close / hard-refresh safety net. Per browser security rules, this
 * dialog's text and buttons are controlled entirely by the browser and
 * cannot be restyled -- see the file header comment for why this is a
 * deliberate, unavoidable limitation rather than a styling oversight.
 */
function setupBeforeUnloadGuard() {
  window.addEventListener("beforeunload", (event) => {
    if (sessionStorage.getItem("nutriglow_leaving_confirmed") === "true") {
      return;
    }
    event.preventDefault();
    event.returnValue = "";
  });
}

/* ============================================================
   PDF download
   ============================================================ */

function setupDownloadButton() {
  document.getElementById("download-pdf-btn").addEventListener("click", async () => {
    const btn = document.getElementById("download-pdf-btn");
    const originalLabel = document.getElementById("download-pdf-label").textContent;
    btn.disabled = true;

    try {
      const response = await fetch("/download-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          view: activeView,
          language: getCurrentLanguage(),
          plan_data: planData,
        }),
      });

      if (!response.ok) throw new Error("PDF generation failed.");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download =
        activeView === "shopping_list"
          ? "NutriGlow_Shopping_List.pdf"
          : "NutriGlow_Meal_Plan.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert(
        getCurrentLanguage() === "ar"
          ? "تعذر إنشاء ملف PDF. حاول مرة أخرى."
          : "Couldn't generate the PDF. Please try again."
      );
    } finally {
      btn.disabled = false;
      document.getElementById("download-pdf-label").textContent = originalLabel;
    }
  });
}

/* ============================================================
   Init
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
  planData = loadPlanData();

  document.getElementById("lang-en-btn").addEventListener("click", () => applyLanguage("en"));
  document.getElementById("lang-ar-btn").addEventListener("click", () => applyLanguage("ar"));

  if (!planData) {
    // No saved plan (e.g. direct navigation to /results) -- bounce home.
    const dict = TRANSLATIONS[getCurrentLanguage()];
    document.getElementById("loading-overlay").classList.remove("hidden");
    document.getElementById("loading-message").textContent = dict.no_plan_found;
    setTimeout(() => {
      window.location.href = "/";
    }, 1400);
    return;
  }

  setupTabs();
  setupExitModal();
  setupNewPlanButton();
  setupBackButtonGuard();
  setupBeforeUnloadGuard();
  setupDownloadButton();

  applyLanguage(getCurrentLanguage());
  switchView("meal_plan");
});
