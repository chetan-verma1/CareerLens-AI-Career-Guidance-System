const SKILL_SUGGESTION_POOL = [
  "python", "sql", "machine learning", "deep learning", "data analysis",
  "data visualization", "tableau", "power bi", "excel", "statistics",
  "feature engineering", "pandas", "numpy", "tensorflow", "pytorch",
  "nlp", "business intelligence", "research methods", "literature review",
  "content development", "teaching", "curriculum design", "assessment design",
  "student records", "faculty coordination", "evaluation", "facilitation",
  "javascript", "linux", "testing", "software engineering", "cloud computing",
  "cybersecurity", "network security", "django", "flask", "react",
  "problem solving", "communication", "leadership", "critical thinking",
  "research", "academic writing", "curriculum", "oracle", "sap"
];

let selectedSkills = [];
let selectedCareerSignals = [];
let DYNAMIC_ROLES = [];
let DYNAMIC_STATES = [];
let DYNAMIC_SKILLS = [...SKILL_SUGGESTION_POOL];

if ("scrollRestoration" in history) {
  history.scrollRestoration = "manual";
}

document.addEventListener("DOMContentLoaded", async function () {
  const navItems = document.querySelectorAll(".nav-item");
  const activeSection = window.activeSectionFromServer || "upload";

  document.querySelectorAll(".section").forEach(section => {
    section.classList.remove("active-section");
  });

  const sectionToShow = document.getElementById(activeSection);
  if (sectionToShow) sectionToShow.classList.add("active-section");

  setTimeout(() => {
    scrollSectionIntoView(sectionToShow || activeSection, "auto");
  }, 60);

  const navMap = {
    upload: 0,
    resumeTool: 1,
    careerTool: 2,
    skillTool: 3,
    salaryTool: 4,
    atsTool: 5,
    reportTool: 6
  };

  navItems.forEach(item => item.classList.remove("active"));
  if (navMap[activeSection] !== undefined) {
    navItems[navMap[activeSection]]?.classList.add("active");
  }

  const toast = document.getElementById("toast");
  if (toast) {
    setTimeout(() => toast.classList.add("show"), 200);
    setTimeout(() => toast.classList.remove("show"), 3000);
  }

  initializeCareerChart();
  initializeDashboardCareerSwitch();
  initializeUploadReset();
  initializeRevealCards();
  initializeExperienceSlider();
  initializeCareerExperienceSlider();
  initializeSkillAutocomplete();
  initializeCareerPredictorControls();

  await initializeDynamicOptions();

  initializeSalaryRoleAutosuggest();
  initializeSkillRoleAutosuggest();
  initializeATSRoleAutosuggest();
});

async function initializeDynamicOptions() {
  try {
    const res = await fetch("/meta/options");
    const data = await res.json();

    DYNAMIC_ROLES = Array.isArray(data.roles) ? data.roles : [];
    DYNAMIC_STATES = Array.isArray(data.states) ? data.states : [];
    DYNAMIC_SKILLS = Array.isArray(data.skills) && data.skills.length ? data.skills : [...SKILL_SUGGESTION_POOL];

    populateSelect("targetCareer", DYNAMIC_ROLES, "Select target role");
    populateSelect("roleInput", DYNAMIC_ROLES, "Select role");
    populateSelect("atsRole", DYNAMIC_ROLES, "Select target role");
    populateSelect("stateSelect", DYNAMIC_STATES, "Select state / UT");
  } catch (err) {
    console.error("Failed to load dynamic options:", err);
  }
}

function populateSelect(id, values, placeholder) {
  const select = document.getElementById(id);
  if (!select) return;

  const currentValue = select.value || "";
  select.innerHTML = "";

  const first = document.createElement("option");
  first.value = "";
  first.textContent = placeholder;
  select.appendChild(first);

  values.forEach(value => {
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = value;
    if (value === currentValue) opt.selected = true;
    select.appendChild(opt);
  });
}

function initializeCareerChart() {
  const chartCanvas = document.getElementById("careerChart");
  if (!chartCanvas) return;

  let labels = [];
  let data = [];

  try {
    labels = JSON.parse(chartCanvas.dataset.labels || "[]");
    data = JSON.parse(chartCanvas.dataset.values || "[]");
  } catch (e) {
    console.error("Error parsing chart data:", e);
    return;
  }

  if (!data.length) return;

  const maxVal = Math.max(...data);
  if (maxVal > 0 && maxVal < 50) {
    data = data.map(v => Math.round((v / maxVal) * 100));
  }

  new Chart(chartCanvas, {
    type: "bar",
    data: {
      labels: labels.map(l => capitalizeWords(l)),
      datasets: [{
        data: data,
        backgroundColor: [
          "rgba(52, 211, 153, 0.95)",
          "rgba(96, 165, 250, 0.95)",
          "rgba(251, 191, 36, 0.95)"
        ],
        borderRadius: 12,
        borderSkipped: false,
        barThickness: 26,
        maxBarThickness: 30,
        categoryPercentage: 0.58,
        barPercentage: 0.66
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 900,
        easing: "easeOutQuart"
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(15,23,42,0.96)",
          borderColor: "rgba(255,255,255,0.08)",
          borderWidth: 1,
          titleColor: "#f8fafc",
          bodyColor: "#e2e8f0",
          padding: 12,
          displayColors: false
        }
      },
      layout: {
        padding: {
          top: 6,
          right: 10,
          left: 10,
          bottom: 0
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            color: "rgba(203,213,225,0.82)",
            stepSize: 10,
            font: { size: 11 }
          },
          grid: {
            color: "rgba(255,255,255,0.06)",
            drawBorder: false
          },
          border: { display: false }
        },
        x: {
          ticks: {
            color: "rgba(203,213,225,0.86)",
            font: { size: 11 }
          },
          grid: { display: false },
          border: { display: false }
        }
      }
    }
  });
}

function initializeDashboardCareerSwitch() {
  const careerDataEl = document.getElementById("careerData");
  if (!careerDataEl) return;

  let careerData = {};
  try {
    careerData = JSON.parse(careerDataEl.textContent);
  } catch (e) {
    console.error("Could not parse careerData JSON", e);
    return;
  }

  window.switchCareer = function (career) {
    const normalizedCareer = (career || "").toLowerCase();
    let data = null;

    Object.keys(careerData).forEach(key => {
      if (key.toLowerCase() === normalizedCareer) data = careerData[key];
    });

    if (!data) return;

    document.querySelectorAll(".career-card").forEach(c => c.classList.remove("active"));
    const activeCard = document.getElementById("card-" + normalizedCareer);
    if (activeCard) activeCard.classList.add("active");

    const salaryBox = document.getElementById("salaryBox");
    if (salaryBox) {
      const salaryDetails = data.salary_details || {};
      salaryBox.innerText = salaryDetails.display_text || "Salary estimate unavailable";
    }

    const domainBox = document.getElementById("domainBox");
    if (domainBox) {
      domainBox.innerText = data.domain || "Not available";
    }

    const matchedDiv = document.getElementById("matchedSkills");
    if (matchedDiv) {
      matchedDiv.innerHTML = "";
      if (data.no_skill_data) {
        matchedDiv.innerHTML = "<p>No skill data ⚠️</p>";
      } else if (data.no_skills_matched) {
        matchedDiv.innerHTML = "<p style='color:orange;'>No matching skills ⚠️</p>";
      } else {
        (data.matched_skills || []).forEach(skill => {
          matchedDiv.innerHTML += `<div class="skill-box matched">${capitalizeWords(skill)}</div>`;
        });
      }
    }

    const missingDiv = document.getElementById("missingSkills");
    if (missingDiv) {
      missingDiv.innerHTML = "";
      if (data.no_skill_data) {
        missingDiv.innerHTML = "<p>No skill data ⚠️</p>";
      } else if (data.all_skills_matched) {
        missingDiv.innerHTML = "<p style='color:lightgreen;'>All skills matched perfectly 😊</p>";
      } else {
        (data.missing_skills || []).forEach(skill => {
          missingDiv.innerHTML += `<div class="skill-box missing">${capitalizeWords(skill)}</div>`;
        });
      }
    }
  };

  const firstCareer = Object.keys(careerData)[0];
  if (firstCareer) window.switchCareer(firstCareer);
}

function initializeUploadReset() {
  const form = document.getElementById("uploadForm");
  if (form) {
    form.addEventListener("submit", () => {
      setTimeout(() => form.reset(), 100);
    });
  }
}

function initializeRevealCards() {
  const revealCards = document.querySelectorAll(".reveal-card");
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("fade-in");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });

    revealCards.forEach(card => observer.observe(card));
  }
}

function initializeExperienceSlider() {
  const slider = document.getElementById("expInput");
  const expValue = document.getElementById("expValue");
  if (!slider || !expValue) return;

  expValue.textContent = slider.value;
  slider.addEventListener("input", function () {
    expValue.textContent = slider.value;
  });
}

function initializeCareerExperienceSlider() {
  const slider = document.getElementById("careerExperienceInput");
  const expValue = document.getElementById("careerExpValue");
  if (!slider || !expValue) return;

  expValue.textContent = slider.value;
  slider.addEventListener("input", function () {
    expValue.textContent = slider.value;
  });
}

function initializeSalaryRoleAutosuggest() {
  initializeAutosuggestSelect("roleInput", DYNAMIC_ROLES, "Search role");
}

function initializeSkillRoleAutosuggest() {
  initializeAutosuggestSelect("targetCareer", DYNAMIC_ROLES, "Search target role");
}

function initializeATSRoleAutosuggest() {
  initializeAutosuggestSelect("atsRole", DYNAMIC_ROLES, "Search target role");
}

function initializeAutosuggestSelect(selectId, optionsList, placeholderText) {
  const select = document.getElementById(selectId);
  if (!select) return;

  const parent = select.parentNode;
  const oldWrapper = parent.querySelector(".select-search-wrapper");
  if (oldWrapper) {
    oldWrapper.remove();
    select.style.display = "";
  }

  enableSelectSearch(select, optionsList, placeholderText);
}

function enableSelectSearch(selectElement, optionsList, placeholderText) {
  if (!selectElement) return;

  const wrapper = document.createElement("div");
  wrapper.className = "select-search-wrapper";

  const input = document.createElement("input");
  input.type = "text";
  input.className = "interactive-text select-search-input";
  input.placeholder = placeholderText;
  input.autocomplete = "off";

  const dropdown = document.createElement("div");
  dropdown.className = "skill-suggestion-box select-search-dropdown";

  const parent = selectElement.parentNode;
  parent.insertBefore(wrapper, selectElement);
  wrapper.appendChild(input);
  wrapper.appendChild(dropdown);
  wrapper.appendChild(selectElement);

  selectElement.style.display = "none";
  selectElement._searchInput = input;

  function renderOptions(filterText = "") {
    dropdown.innerHTML = "";
    const query = filterText.trim().toLowerCase();

    const filtered = optionsList
      .filter(option => option.toLowerCase().includes(query))
      .slice(0, 12);

    filtered.forEach(optionText => {
      const item = document.createElement("div");
      item.className = "skill-suggestion-item";
      item.textContent = optionText;
      item.addEventListener("click", function () {
        selectElement.value = optionText;
        input.value = optionText;
        dropdown.innerHTML = "";
      });
      dropdown.appendChild(item);
    });
  }

  input.addEventListener("focus", function () {
    renderOptions(input.value);
  });

  input.addEventListener("input", function () {
    renderOptions(input.value);
  });

  document.addEventListener("click", function (e) {
    if (!wrapper.contains(e.target)) dropdown.innerHTML = "";
  });

  if (selectElement.value) input.value = selectElement.value;

  selectElement.addEventListener("change", function () {
    input.value = selectElement.value;
  });
}

function initializeSkillAutocomplete() {
  const input = document.getElementById("skillSearchInput");
  const suggestionBox = document.getElementById("skillSuggestions");
  if (!input || !suggestionBox) return;

  renderSelectedSkillChips();

  input.addEventListener("input", function () {
    const query = this.value.trim().toLowerCase();
    suggestionBox.innerHTML = "";
    if (!query) return;

    const matches = DYNAMIC_SKILLS
      .filter(skill => skill.toLowerCase().includes(query) && !selectedSkills.includes(skill.toLowerCase()))
      .slice(0, 8);

    matches.forEach(match => {
      const item = document.createElement("div");
      item.className = "skill-suggestion-item";
      item.textContent = capitalizeWords(match);
      item.addEventListener("click", function () {
        addSkillChip(match);
        input.value = "";
        suggestionBox.innerHTML = "";
      });
      suggestionBox.appendChild(item);
    });
  });

  document.addEventListener("click", function (e) {
    if (!suggestionBox.contains(e.target) && e.target !== input) suggestionBox.innerHTML = "";
  });

  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      const rawValue = input.value.trim().toLowerCase();
      if (!rawValue) return;
      addSkillChip(rawValue);
      input.value = "";
      suggestionBox.innerHTML = "";
    }
  });
}

function initializeCareerPredictorControls() {
  const input = document.getElementById("careerSkillSearchInput");
  const suggestionBox = document.getElementById("careerSkillSuggestions");
  if (!input || !suggestionBox) return;

  renderCareerSignalChips();

  input.addEventListener("input", function () {
    const query = this.value.trim().toLowerCase();
    suggestionBox.innerHTML = "";
    if (!query) return;

    const matches = DYNAMIC_SKILLS
      .filter(skill => skill.toLowerCase().includes(query) && !selectedCareerSignals.includes(skill.toLowerCase()))
      .slice(0, 8);

    matches.forEach(match => {
      const item = document.createElement("div");
      item.className = "skill-suggestion-item";
      item.textContent = capitalizeWords(match);
      item.addEventListener("click", function () {
        addCareerSignal(match);
        input.value = "";
        suggestionBox.innerHTML = "";
      });
      suggestionBox.appendChild(item);
    });
  });

  document.addEventListener("click", function (e) {
    if (!suggestionBox.contains(e.target) && e.target !== input) suggestionBox.innerHTML = "";
  });

  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      const rawValue = input.value.trim().toLowerCase();
      if (!rawValue) return;
      addCareerSignal(rawValue);
      input.value = "";
      suggestionBox.innerHTML = "";
    }
  });
}

function addSkillChip(skill) {
  const normalized = skill.toLowerCase().trim();
  if (!normalized || selectedSkills.includes(normalized)) return;
  selectedSkills.push(normalized);
  renderSelectedSkillChips();
}

function removeSkillChip(skill) {
  selectedSkills = selectedSkills.filter(s => s !== skill.toLowerCase());
  renderSelectedSkillChips();
}

function renderSelectedSkillChips() {
  const selectedWrap = document.getElementById("selectedSkillChips");
  if (!selectedWrap) return;

  selectedWrap.innerHTML = "";
  selectedSkills.forEach(skill => {
    const chip = document.createElement("div");
    chip.className = "skill-chip";
    chip.innerHTML = `
      <span>${capitalizeWords(skill)}</span>
      <button type="button" onclick="removeSkillChip('${skill.replace(/'/g, "\\'")}')">×</button>
    `;
    selectedWrap.appendChild(chip);
  });
}

function clearSelectedSkills() {
  selectedSkills = [];
  renderSelectedSkillChips();
}

function addCareerSignal(signal) {
  const normalized = signal.toLowerCase().trim();
  if (!normalized || selectedCareerSignals.includes(normalized)) return;
  selectedCareerSignals.push(normalized);
  renderCareerSignalChips();
}

function removeCareerSignal(signal) {
  selectedCareerSignals = selectedCareerSignals.filter(s => s !== signal.toLowerCase());
  renderCareerSignalChips();
}

function clearCareerSignals() {
  selectedCareerSignals = [];
  renderCareerSignalChips();
}

function renderCareerSignalChips() {
  const selectedWrap = document.getElementById("careerSelectedChips");
  if (!selectedWrap) return;

  selectedWrap.innerHTML = "";
  selectedCareerSignals.forEach(signal => {
    const chip = document.createElement("div");
    chip.className = "skill-chip";
    chip.innerHTML = `
      <span>${capitalizeWords(signal)}</span>
      <button type="button" onclick="removeCareerSignal('${signal.replace(/'/g, "\\'")}')">×</button>
    `;
    selectedWrap.appendChild(chip);
  });
}

function scrollSectionIntoView(sectionOrId, behavior = "smooth") {
  const target = typeof sectionOrId === "string"
    ? document.getElementById(sectionOrId)
    : sectionOrId;

  if (!target) return;

  const header = document.querySelector(".header");
  const headerHeight = header ? header.offsetHeight : 96;
  const targetTop = Math.max(
    target.getBoundingClientRect().top + window.scrollY - headerHeight - 16,
    0
  );

  window.scrollTo({ top: targetTop, behavior });
}

function showSection(e, id) {
  document.querySelectorAll(".section").forEach(section => {
    section.classList.remove("active-section");
  });

  const target = document.getElementById(id);
  if (target) target.classList.add("active-section");

  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  if (e && e.currentTarget) e.currentTarget.classList.add("active");

  setTimeout(() => {
    scrollSectionIntoView(target || id, "smooth");
  }, 40);
}

function capitalizeWords(text) {
  if (!text) return "";
  return String(text)
    .split(" ")
    .map(word => word ? word.charAt(0).toUpperCase() + word.slice(1) : "")
    .join(" ");
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function predictCareer() {
  const careerResult = document.getElementById("careerResult");
  const education = document.getElementById("careerEducationLevel")?.value || "";
  const experience = document.getElementById("careerExperienceInput")?.value || "0";

  if (!selectedCareerSignals.length ) {
    careerResult.innerHTML = "<p style='color:#f59e0b;'>Please add at least one skill or interest before predicting career.</p>";
    return;
  }

  const composedText = [
    selectedCareerSignals.join(" "),
    education,
    `${experience} years experience`
  ].join(" ").trim();

  careerResult.innerHTML = "<p>Predicting career...</p>";

  fetch("/career_model", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: composedText,
      skills: selectedCareerSignals,
      education: education,
      experience: experience
    })
  })
    .then(async res => {
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Career prediction failed.");
      return data;
    })
    .then(data => {
      const top3 = data.top3_roles || [];
      const isHybrid = data.is_hybrid_profile ? "Yes" : "No";

      let html = `
        <div class="result-summary-block">
          <h3>Prediction Summary</h3>
          <p><strong>Predicted Domain:</strong> ${escapeHtml(data.predicted_domain || "Not available")}</p>
          <p><strong>Hybrid Profile:</strong> ${isHybrid}</p>
          ${data.secondary_domain ? `<p><strong>Secondary Domain:</strong> ${escapeHtml(data.secondary_domain)}</p>` : ""}
        </div>
      `;

      html += `<div class="result-role-list"><h3>Top Career Matches</h3>`;
      if (!top3.length) {
        html += "<p>No predictions available.</p>";
      } else {
        top3.forEach(item => {
          html += `
            <div class="career-result-pill">
              <span>${escapeHtml(capitalizeWords(item[0]))}</span>
            </div>
          `;
        });
      }
      html += `</div>`;

      careerResult.innerHTML = html;
    })
    .catch(err => {
      careerResult.innerHTML = `<p style='color:#ef4444;'>${escapeHtml(err.message || "Error predicting career.")}</p>`;
    });
}

function analyzeSkills() {
  const targetSelect = document.getElementById("targetCareer");
  const targetSearchInput = targetSelect?._searchInput;
  const career = (targetSelect?.value || targetSearchInput?.value || "").trim();
  const skillResult = document.getElementById("skillResult");

  if (!career) {
    skillResult.innerHTML = "<p style='color:#f59e0b;'>Please select a target career.</p>";
    return;
  }

  if (!selectedSkills.length) {
    skillResult.innerHTML = "<p style='color:#f59e0b;'>Please add at least one skill.</p>";
    return;
  }

  skillResult.innerHTML = "<p>Analyzing skill gap...</p>";

  fetch("/career_skill", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      skills: selectedSkills,
      career: career
    })
  })
    .then(async res => {
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Skill analysis failed.");
      return data;
    })
    .then(data => {
      const matched = data.matched_skills || [];
      const missing = data.missing_skills || [];
      const readinessScore = data.readiness_score ?? 0;
      const roadmap = data.roadmap || [];

      let html = `<p><strong>Readiness Score:</strong> ${readinessScore}%</p>`;

      html += "<h4>Matched Skills</h4><div class='skill-container'>";
      if (!matched.length) html += "<p>No matched skills found.</p>";
      else matched.forEach(s => html += `<div class="skill-box matched">${capitalizeWords(s)}</div>`);
      html += "</div>";

      html += "<h4>Missing Skills</h4><div class='skill-container'>";
      if (!missing.length) html += "<p>All required skills matched.</p>";
      else missing.forEach(s => html += `<div class="skill-box missing">${capitalizeWords(s)}</div>`);
      html += "</div>";

      if (roadmap.length) {
        html += "<h4>Roadmap</h4><ul class='suggestions'>";
        roadmap.forEach(step => html += `<li>${escapeHtml(step)}</li>`);
        html += "</ul>";
      }

      skillResult.innerHTML = html;
    })
    .catch(err => {
      skillResult.innerHTML = `<p style='color:#ef4444;'>${escapeHtml(err.message || "Error analyzing skills.")}</p>`;
    });
}

function predictSalary() {
  const roleSelect = document.getElementById("roleInput");
  const roleSearchInput = roleSelect?._searchInput;
  const role = (roleSelect?.value || roleSearchInput?.value || "").trim();

  const exp = document.getElementById("expInput").value.trim();
  const state = (document.getElementById("stateSelect")?.value || "").trim();

  const salaryOutput = document.getElementById("salaryOutput");

  if (!role || !state) {
    salaryOutput.innerHTML = "Please fill role, state, and experience.";
    return;
  }

  salaryOutput.innerHTML = "Predicting salary...";

  fetch("/salary_prediction", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      role: role,
      state: state,
      experience: exp
    })
  })
    .then(async res => {
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Salary prediction failed.");
      return data;
    })
    .then(data => {
      const details = data.salary_details || data;
      salaryOutput.innerHTML = `
        <div><strong>${escapeHtml(details.display_text || "Salary estimate unavailable")}</strong></div>
        <div style="margin-top:8px; font-size:13px; color:#cbd5e1;">
          ${escapeHtml(details.note || "")}
        </div>
      `;
    })
    .catch(err => {
      salaryOutput.innerHTML = escapeHtml(err.message || "Error predicting salary.");
    });
}

function checkATS() {
  const fileInput = document.getElementById("atsResume");
  const roleSelect = document.getElementById("atsRole");
  const roleSearchInput = roleSelect?._searchInput;
  const role = (roleSelect?.value || roleSearchInput?.value || "").trim();

  const generalEl = document.getElementById("atsGeneralScore");
  const verdictEl = document.getElementById("atsVerdict");

  if (!fileInput.files.length) {
    generalEl.innerText = "Please upload a resume file.";
    verdictEl.innerText = "";
    return;
  }

  if (!role) {
    generalEl.innerText = "Please select a target role.";
    verdictEl.innerText = "";
    return;
  }

  const formData = new FormData();
  formData.append("resume", fileInput.files[0]);
  formData.append("role", role);

  generalEl.innerText = "Checking ATS...";
  verdictEl.innerText = "";

  fetch("/ats_resume_check", {
    method: "POST",
    body: formData
  })
    .then(async res => {
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "ATS check failed.");
      return data;
    })
    .then(data => {
      generalEl.innerText = "General ATS Score: " + data.general_ats + "%";
      verdictEl.innerText = data.verdict;
    })
    .catch(err => {
      generalEl.innerText = "ATS check failed.";
      verdictEl.innerText = err.message;
    });
}

function resetAutosuggestSelect(selectId) {
  const select = document.getElementById(selectId);
  if (!select) return;
  select.value = "";
  if (select._searchInput) select._searchInput.value = "";
}

function resetSmartAnalyzerForm() {
  const form = document.getElementById("uploadForm");
  if (form) form.reset();
}

function resetResumeExtractorForm() {
  const form = document.getElementById("resumeExtractorForm");
  if (form) form.reset();

  const fileInput = document.getElementById("resumeExtractorFile");
  if (fileInput) fileInput.value = "";
}

function resetCareerTool() {
  const education = document.getElementById("careerEducationLevel");
  const exp = document.getElementById("careerExperienceInput");
  const expValue = document.getElementById("careerExpValue");
  const input = document.getElementById("careerSkillSearchInput");
  const result = document.getElementById("careerResult");

  selectedCareerSignals = [];
  renderCareerSignalChips();

  if (education) education.value = "";
  if (exp) exp.value = 2;
  if (expValue) expValue.textContent = "2";
  if (input) input.value = "";
  if (result) result.innerHTML = "";
}

function resetSkillTool() {
  const input = document.getElementById("skillSearchInput");
  const result = document.getElementById("skillResult");

  selectedSkills = [];
  renderSelectedSkillChips();
  resetAutosuggestSelect("targetCareer");

  if (input) input.value = "";
  if (result) result.innerHTML = "";
}

function resetSalaryTool() {
  const stateSelect = document.getElementById("stateSelect");
  const expInput = document.getElementById("expInput");
  const expValue = document.getElementById("expValue");
  const salaryOutput = document.getElementById("salaryOutput");

  resetAutosuggestSelect("roleInput");
  if (stateSelect) stateSelect.value = "";
  if (expInput) expInput.value = 3;
  if (expValue) expValue.textContent = "3";
  if (salaryOutput) salaryOutput.innerHTML = "";
}

function resetATSTool() {
  const form = document.getElementById("atsForm");
  const generalEl = document.getElementById("atsGeneralScore");
  const verdictEl = document.getElementById("atsVerdict");

  if (form) form.reset();
  resetAutosuggestSelect("atsRole");
  if (generalEl) generalEl.innerText = "";
  if (verdictEl) verdictEl.innerText = "";
}

function downloadSmartReport() {
  const source = document.getElementById("smartAnalyzerReport");
  if (!source) {
    alert("Run Smart Analyzer first to generate a printable report.");
    return;
  }

  const printWindow = window.open("", "_blank", "width=1400,height=1000");
  if (!printWindow) {
    alert("Please allow pop-ups to print the Smart Analyzer report.");
    return;
  }

  const reportHtml = source.cloneNode(true);

  const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"], style'))
    .map(node => node.outerHTML)
    .join("\n");

  printWindow.document.open();
  printWindow.document.write(`
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CareerLens Smart Report</title>
        ${styles}
        <style>
          @page {
            size: A4 portrait;
            margin: 12mm;
          }

          html, body {
            margin: 0 !important;
            padding: 0 !important;
            background: #ffffff !important;
            color: #0f172a !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
            font-family: 'Inter', 'Segoe UI', Arial, sans-serif !important;
          }

          body {
            padding: 0 !important;
          }

          .print-shell {
            width: 100%;
            max-width: 100%;
            margin: 0 auto;
            background: #ffffff !important;
          }

          .dashboard-inline,
          .dashboard-shell,
          .tool-panel,
          .glass-card,
          .dashboard-block,
          .dashboard-stat-card,
          .dashboard-hero-card,
          .mini-stat-box,
          .dashboard-verdict-box,
          .dashboard-skill-box,
          .career-card {
            background: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #dbe2ea !important;
            box-shadow: none !important;
            backdrop-filter: none !important;
          }

          .dashboard-inline {
            margin-top: 0 !important;
          }

          .dashboard-shell {
            max-width: 100% !important;
            border-radius: 12px !important;
            padding: 18px !important;
            overflow: visible !important;
          }

          .dashboard-summary-row {
            display: grid !important;
            grid-template-columns: 1.15fr 0.85fr !important;
            gap: 14px !important;
            margin-bottom: 14px !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
          }

          .dashboard-main-grid {
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 14px !important;
            align-items: start !important;
          }

          .dashboard-left,
          .dashboard-right {
            display: flex !important;
            flex-direction: column !important;
            gap: 12px !important;
          }

          .dashboard-block,
          .dashboard-stat-card,
          .dashboard-hero-card,
          .dashboard-verdict-box,
          .dashboard-skill-box,
          .mini-stat-box,
          .career-card {
            page-break-inside: avoid !important;
            break-inside: avoid !important;
          }

          .centered-hero-card {
            min-height: auto !important;
            padding: 18px !important;
          }

          .centered-hero-text {
            gap: 8px !important;
          }

          .dashboard-profile-name.accent-profile-name {
            font-size: 28px !important;
            line-height: 1.1 !important;
            color: #0f172a !important;
          }

          .dashboard-profile-role {
            font-size: 16px !important;
            color: #0f172a !important;
          }

          .dashboard-profile-role strong,
          .career-result-pill strong,
          .mini-stat-box strong,
          .dashboard-block h3,
          .dashboard-skill-box h4,
          .dashboard-suggestions-box h4 {
            color: #0f172a !important;
          }

          .dashboard-profile-desc,
          .dashboard-stat-card p,
          .dashboard-verdict-box p,
          .compact-list li,
          .mini-stat-box span,
          .dashboard-stat-card span {
            color: #334155 !important;
          }

          .dashboard-stat-card {
            padding: 12px !important;
          }

          .dashboard-stat-card h3 {
            font-size: 20px !important;
            color: #0f172a !important;
          }

          .chart-wrap {
            height: 220px !important;
            margin-bottom: 10px !important;
          }

          canvas {
            max-width: 100% !important;
            max-height: 220px !important;
          }

          .role-comparison-list {
            gap: 8px !important;
          }

          .career-card {
            padding: 10px 12px !important;
            border-radius: 10px !important;
          }

          .dashboard-mini-stats.stats-3 {
            grid-template-columns: repeat(3, 1fr) !important;
            gap: 10px !important;
          }

          .mini-stat-box {
            min-height: auto !important;
            padding: 10px !important;
          }

          .dashboard-skill-grid {
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 10px !important;
          }

          .skill-container {
            gap: 6px !important;
          }

          .skill-box {
            font-size: 12px !important;
            padding: 5px 9px !important;
            color: #0f172a !important;
          }

          .skill-box.matched {
            background: #ecfdf5 !important;
            border: 1px solid #86efac !important;
          }

          .skill-box.missing {
            background: #fef2f2 !important;
            border: 1px solid #fca5a5 !important;
          }

          .dashboard-verdict-box {
            padding: 12px !important;
            margin-bottom: 10px !important;
          }

          .dashboard-verdict-box p {
            font-size: 14px !important;
            line-height: 1.45 !important;
          }

          .ats-subscore-grid {
            grid-template-columns: repeat(4, 1fr) !important;
            gap: 8px !important;
          }

          .tool-logo-wrap,
          .success-inline,
          .dashboard-heading,
          .back-home-btn,
          .sidebar,
          .header,
          .app-footer {
            display: none !important;
          }

          * {
            box-shadow: none !important;
          }

          @media print {
            html, body {
              background: #ffffff !important;
            }
          }
        </style>
      </head>
      <body>
        <div class="print-shell">
          ${reportHtml.outerHTML}
        </div>
      </body>
    </html>
  `);
  printWindow.document.close();

  setTimeout(() => {
    printWindow.focus();
    printWindow.print();
  }, 700);
}