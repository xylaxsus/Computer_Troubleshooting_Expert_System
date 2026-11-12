const ICONS = {
  "1": '<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="4" width="16" height="11" rx="1.5"/><path d="M2 19h20"/></svg>',
  "2": '<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="7" y="2" width="10" height="20" rx="2.5"/><path d="M11 18h2"/></svg>',
  "3": '<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>',
  "4": '<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9V3h12v6"/><rect x="3" y="9" width="18" height="8" rx="2"/><path d="M7 14h10v7H7z"/></svg>',
  "5": '<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 9a15 15 0 0 1 20 0M5 12.5a10 10 0 0 1 14 0M8.5 16a5 5 0 0 1 7 0"/><circle cx="12" cy="19.5" r="1"/></svg>',
};
const CHEVRON = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>';

const $ = (id) => document.getElementById(id);
const state = {
  device: null, problem: null, questions: [], answers: {},
  categories: [], allProblems: [], level: "categories",
};

function show(view) {
  document.querySelectorAll(".view").forEach((v) => { v.hidden = v.id !== view; });
  window.scrollTo({ top: 0, behavior: "smooth" });
  const heading = $(view).querySelector("h1, h2");
  if (heading) { heading.setAttribute("tabindex", "-1"); heading.focus({ preventScroll: true }); }
}

async function getJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error("Request failed: " + res.status);
  return res.json();
}

// ---- Devices ----
async function loadDevices() {
  const grid = $("device-grid");
  try {
    const devices = await getJSON("/api/devices");
    grid.innerHTML = "";
    devices.forEach((d) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "card";
      btn.innerHTML = '<span class="icon">' + (ICONS[d.id] || "") + '</span>' +
        '<span class="name"></span><span class="count"></span>';
      btn.querySelector(".name").textContent = d.name;
      btn.querySelector(".count").textContent = d.count + " known problems";
      btn.addEventListener("click", () => selectDevice(d));
      grid.appendChild(btn);
    });
  } catch (e) {
    grid.textContent = "Could not load devices. Is the Flask server running?";
  }
}

// ---- Problems ----
const CAT_ICON_PATHS = {
  power: '<path d="M12 3v8"/><path d="M6.3 6.8a8 8 0 1 0 11.4 0"/>',
  display: '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
  network: '<path d="M2 9a15 15 0 0 1 20 0M5 12.5a10 10 0 0 1 14 0M8.5 16a5 5 0 0 1 7 0"/><circle cx="12" cy="19.5" r="1"/>',
  audio: '<path d="M11 5 6 9H3v6h3l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 6a9 9 0 0 1 0 12"/>',
  performance: '<path d="M4 17a8 8 0 1 1 16 0"/><path d="M12 17l4-5"/>',
  peripheral: '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M7 10h.01M11 10h.01M15 10h.01M7 14h10"/>',
  printer: '<path d="M6 9V3h12v6"/><rect x="3" y="9" width="18" height="8" rx="2"/><path d="M7 14h10v7H7z"/>',
};
const DEFAULT_CAT_ICON = '<circle cx="12" cy="12" r="8"/><path d="M12 8v4l2 2"/>';

function catIcon(id) {
  return '<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    (CAT_ICON_PATHS[id] || DEFAULT_CAT_ICON) + "</svg>";
}

async function selectDevice(device) {
  state.device = device;
  state.categories = [];
  state.allProblems = [];
  state.level = "categories";
  $("problem-list").innerHTML = "";
  $("problems-title").textContent = device.name + ": choose your problem";
  show("problems");
  try {
    const data = await getJSON("/api/devices/" + device.id + "/problems");
    state.categories = data.categories;
    state.allProblems = data.problems;
    // Only one category? Skip straight to the exact problems.
    if (state.categories.length === 1) {
      renderProblems(state.categories[0]);
    } else {
      renderCategories();
    }
  } catch (e) {
    $("problem-list").textContent = "Could not load problems.";
  }
}

function renderCategories() {
  state.level = "categories";
  const list = $("problem-list");
  list.className = "cats";
  list.innerHTML = "";
  $("problems-title").textContent = state.device.name + ": what kind of problem?";
  $("problems-sub").textContent = "Choose the category that best describes what is going wrong.";
  $("problems-back").innerHTML = "&larr; Change device";
  state.categories.forEach((c) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "card cat";
    btn.innerHTML = '<span class="icon">' + catIcon(c.id) + '</span>' +
      '<span class="name"></span><span class="count"></span>';
    btn.querySelector(".name").textContent = c.label;
    btn.querySelector(".count").textContent = c.subtitle;
    btn.addEventListener("click", () => renderProblems(c));
    list.appendChild(btn);
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function renderProblems(category) {
  state.level = "problems";
  const list = $("problem-list");
  list.className = "problem-list";
  list.innerHTML = "";
  $("problems-title").textContent = category.label;
  $("problems-sub").textContent = "Pick the exact problem you are experiencing on your " + state.device.name + ".";
  $("problems-back").innerHTML = state.categories.length > 1 ? "&larr; All categories" : "&larr; Change device";
  state.allProblems.filter((p) => p.category === category.id).forEach((p) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "problem";
    btn.innerHTML = '<span><span class="t"></span><span class="s"></span></span>' + CHEVRON;
    btn.querySelector(".t").textContent = p.problem;
    btn.querySelector(".s").textContent = p.symptoms;
    btn.addEventListener("click", () => selectProblem(p));
    list.appendChild(btn);
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

$("problems-back").addEventListener("click", () => {
  if (state.level === "problems" && state.categories.length > 1) renderCategories();
  else show("devices");
});

// ---- Questions ----
async function selectProblem(problem) {
  state.problem = problem;
  state.answers = {};
  const data = await getJSON("/api/problems/" + problem.id);
  state.questions = data.questions;

  $("t-device").textContent = state.device.name;
  $("t-problem").textContent = problem.problem;

  const form = $("questions");
  form.innerHTML = "";
  if (!state.questions.length) {
    form.innerHTML = '<p class="progress">No follow-up questions are needed for this problem.</p>';
  }
  state.questions.forEach((q, i) => {
    const fs = document.createElement("fieldset");
    fs.className = "q";
    fs.innerHTML = '<legend><span class="n">' + (i + 1) + '.</span><span class="qt"></span></legend>' +
      '<div class="choices">' +
      '<label class="choice"><input type="radio" name="q' + i + '" value="yes"><span>Yes</span></label>' +
      '<label class="choice"><input type="radio" name="q' + i + '" value="no"><span>No</span></label>' +
      '</div>';
    fs.querySelector(".qt").textContent = q;
    fs.querySelectorAll("input").forEach((input) => {
      input.addEventListener("change", () => {
        state.answers[i] = input.value === "yes";
        refresh();
      });
    });
    form.appendChild(fs);
  });

  show("troubleshoot");
  refresh();
}

// ---- Diagnosis & summary (updates on every answer) ----
async function refresh() {
  const total = state.questions.length;
  const answered = Object.keys(state.answers).length;

  $("progress").textContent = total ? answered + " of " + total + " answered" : "";

  const summary = $("r-summary");
  summary.innerHTML = "";
  if (!answered) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "No answers yet.";
    summary.appendChild(li);
  }
  state.questions.forEach((q, i) => {
    if (!(i in state.answers)) return;
    const yes = state.answers[i];
    const li = document.createElement("li");
    li.innerHTML = '<span class="qq"></span><span class="a' + (yes ? "" : " no") + '">' + (yes ? "Yes" : "No") + "</span>";
    li.querySelector(".qq").textContent = q;
    summary.appendChild(li);
  });

  const complete = answered === total;
  $("result-empty").hidden = complete;
  $("result-body").hidden = !complete;
  if (!complete) return;

  const payload = {
    problem_id: state.problem.id,
    answers: state.questions.map((q, i) => ({ question: q, answer: !!state.answers[i] })),
  };
  try {
    const r = await getJSON("/api/diagnose", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    $("r-cause").textContent = r.possible_cause;
    $("r-solution").textContent = r.solution;
  } catch (e) {
    $("r-cause").textContent = "Could not reach the expert system.";
    $("r-solution").textContent = "";
  }
}

// ---- Navigation ----
function reset() {
  state.device = null;
  state.problem = null;
  state.questions = [];
  state.answers = {};
  state.categories = [];
  state.allProblems = [];
  state.level = "categories";
  $("questions").innerHTML = "";
  show("home");
}

$("start-btn").addEventListener("click", () => show("devices"));
$("start-over").addEventListener("click", reset);
document.querySelectorAll("[data-go]").forEach((b) =>
  b.addEventListener("click", () => show(b.dataset.go))
);

loadDevices();
