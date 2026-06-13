const raceEl = document.querySelector("#race");
const countdownEl = document.querySelector("#countdown");
const countdownTargetEl = document.querySelector("#countdown-target");
const metadataEl = document.querySelector("#metadata");
const synthesisCardsEl = document.querySelector("#synthesis-cards");
const sessionsEl = document.querySelector("#sessions");
const weatherNoteEl = document.querySelector("#weather-note");
const metricsEl = document.querySelector("#metrics");
const reliabilityEl = document.querySelector("#reliability");
const diagnosticsEl = document.querySelector("#diagnostics");
const benchmarkEl = document.querySelector("#benchmark");
const modelCard = document.querySelector("#model-card");
const modelCardBody = document.querySelector("#model-card-body");
const modelCardOpen = document.querySelector("#model-card-open");
const modelCardClose = document.querySelector("#model-card-close");
const tourOpenButton = document.querySelector("#tour-open");
const tourOverlay = document.querySelector("#tour-overlay");
const tourStepEl = document.querySelector("#tour-step");
const tourTitleEl = document.querySelector("#tour-title");
const tourBodyEl = document.querySelector("#tour-body");
const tourProgressEl = document.querySelector(".tour-progress");
const tourNextButton = document.querySelector("#tour-next");
const tourSkipButton = document.querySelector("#tour-skip");
const predictionsEl = document.querySelector("#predictions");
const geekPredictionsEl = document.querySelector("#geek-predictions");
const predictionHeadEl = document.querySelector("#prediction-head");
const statusEl = document.querySelector("#status");
const refreshButton = document.querySelector("#refresh");
const basicModeButton = document.querySelector("#basic-mode");
const geekModeButton = document.querySelector("#geek-mode");
const qualifyingTab = document.querySelector("#qualifying-tab");
const raceTab = document.querySelector("#race-tab");
const basicNoteEl = document.querySelector("#basic-note");
const forecastStatesEl = document.querySelector("#forecast-states");
const languageSelect = document.querySelector("#language-select");
const unitSelect = document.querySelector("#unit-select");
const productTabs = document.querySelectorAll("[data-section]");
const raceHubSections = document.querySelectorAll(".race-hub-section");
const productSections = document.querySelectorAll("[data-product-section]");
const historySeasonEl = document.querySelector("#history-season");
const historyDriverEl = document.querySelector("#history-driver");
const historyTeamEl = document.querySelector("#history-team");
const historyCoverageEl = document.querySelector("#history-coverage");
const historySeasonCardsEl = document.querySelector("#history-season-cards");
const historyRacesEl = document.querySelector("#history-races");
const historyRaceTitleEl = document.querySelector("#history-race-title");
const historySummaryEl = document.querySelector("#history-summary");
const historyRaceContextEl = document.querySelector("#history-race-context");
const historyResultsEl = document.querySelector("#history-results");
const historyDriverSummaryEl = document.querySelector("#history-driver-summary");
const historyTeamSummaryEl = document.querySelector("#history-team-summary");
const historyGeekContextEl = document.querySelector("#history-geek-context");
const historyLapsEl = document.querySelector("#history-laps");
const historyLapStatusEl = document.querySelector("#history-lap-status");
const compareDriverAEl = document.querySelector("#compare-driver-a");
const compareDriverBEl = document.querySelector("#compare-driver-b");
const compareDriversButton = document.querySelector("#compare-drivers");
const driverCompareSummaryEl = document.querySelector("#driver-compare-summary");
const driverRatingSummaryEl = document.querySelector("#driver-rating-summary");
const driverTrendChartsEl = document.querySelector("#driver-trend-charts");
const driverSplitSummaryEl = document.querySelector("#driver-split-summary");
const profileDriverEl = document.querySelector("#profile-driver");
const loadProfileButton = document.querySelector("#load-profile");
const profileCoverageEl = document.querySelector("#profile-coverage");
const profileHeroEl = document.querySelector("#driver-profile-hero");
const profileTrendChartsEl = document.querySelector("#profile-trend-charts");
const profileRatingSummaryEl = document.querySelector("#profile-rating-summary");
const profileSplitSummaryEl = document.querySelector("#profile-split-summary");
const profileTeammateSummaryEl = document.querySelector("#profile-teammate-summary");
const profileCompareShortcutsEl = document.querySelector("#profile-compare-shortcuts");
const profileRaceLogTitleEl = document.querySelector("#profile-race-log-title");
const profileRaceLogEl = document.querySelector("#profile-race-log");
const circuitKeyEl = document.querySelector("#circuit-key");
const loadCircuitButton = document.querySelector("#load-circuit");
const circuitCoverageEl = document.querySelector("#circuit-coverage");
const circuitHeroEl = document.querySelector("#circuit-profile-hero");
const circuitBehaviorSummaryEl = document.querySelector("#circuit-behavior-summary");
const circuitLeaderSummaryEl = document.querySelector("#circuit-leader-summary");
const circuitTyreSummaryEl = document.querySelector("#circuit-tyre-summary");
const circuitRecentSummaryEl = document.querySelector("#circuit-recent-summary");
const circuitRaceLogTitleEl = document.querySelector("#circuit-race-log-title");
const circuitRaceLogEl = document.querySelector("#circuit-race-log");
const teamProfileKeyEl = document.querySelector("#team-profile-key");
const loadTeamProfileButton = document.querySelector("#load-team-profile");
const teamProfileCoverageEl = document.querySelector("#team-profile-coverage");
const teamProfileHeroEl = document.querySelector("#team-profile-hero");
const teamTrendChartsEl = document.querySelector("#team-trend-charts");
const teamLineupBalanceEl = document.querySelector("#team-lineup-balance");
const teamCircuitStrengthsEl = document.querySelector("#team-circuit-strengths");
const teamLineupHistoryEl = document.querySelector("#team-lineup-history");
const teamRaceLogTitleEl = document.querySelector("#team-race-log-title");
const teamRaceLogEl = document.querySelector("#team-race-log");
const compatDriverEl = document.querySelector("#compat-driver");
const compatTeamEl = document.querySelector("#compat-team");
const runCompatibilityButton = document.querySelector("#run-compatibility");
const compatCoverageEl = document.querySelector("#compat-coverage");
const compatibilityHeroEl = document.querySelector("#compatibility-hero");
const compatibilityComponentsEl = document.querySelector("#compatibility-components");
const compatibilityContextEl = document.querySelector("#compatibility-context");
const compatibilityLinksEl = document.querySelector("#compatibility-links");
const compatibilityNotesEl = document.querySelector("#compatibility-notes");
const compatibilityExplainEl = document.querySelector("#compatibility-explain");
const whatIfDriverAEl = document.querySelector("#whatif-driver-a");
const whatIfDriverBEl = document.querySelector("#whatif-driver-b");
const whatIfCircuitEl = document.querySelector("#whatif-circuit");
const whatIfSessionEl = document.querySelector("#whatif-session");
const whatIfConditionEl = document.querySelector("#whatif-condition");
const runWhatIfButton = document.querySelector("#run-whatif");
const whatIfCoverageEl = document.querySelector("#whatif-coverage");
const whatIfHeroEl = document.querySelector("#whatif-hero");
const whatIfDimensionsEl = document.querySelector("#whatif-dimensions");
const whatIfContextEl = document.querySelector("#whatif-context");
const whatIfLinksEl = document.querySelector("#whatif-links");
const whatIfNotesEl = document.querySelector("#whatif-notes");
const whatIfExplainEl = document.querySelector("#whatif-explain");

let countdownTimer = null;
let activeMode = "basic";
let activeForecast = "race";
let activeSection = "race-hub";
let activeLanguage = localStorage.getItem("f1-language") || "en";
let activeUnits = localStorage.getItem("f1-units") || "metric";
let racePayload = null;
let qualifyingPayload = null;
let weekendPayload = null;
let statesPayload = null;
let historyLoaded = false;
let profileLoaded = false;
let circuitLoaded = false;
let teamProfileLoaded = false;
let compatibilityLoaded = false;
let whatIfLoaded = false;
let selectedHistoryRace = null;
let activeTourStep = 0;
let tourReturnSection = "race-hub";

const I18N = {
  en: {
    language: "Language",
    units: "Units",
    basic_mode: "Basic Mode",
    geek_mode: "Geek Mode",
    model_card: "Model Card",
    help: "Help",
    refresh: "Refresh",
    race_hub: "Race Hub",
    live_race: "Live Race",
    history: "History",
    circuit_profiles: "Circuit Profiles",
    driver_ratings: "Driver Profiles",
    team_profiles: "Team Profiles",
    compatibility_lab: "Compatibility Lab",
    what_if: "What-If Matchups",
    sunny: "Sunny",
    cloudy: "Cloudy",
    dry: "Dry",
    damp_risk: "Damp Risk",
    wet: "Wet",
    storm_risk: "Storm Risk",
    risk: "Risk",
    air: "Air",
    track: "Track",
    rain: "Rain",
    wind: "Wind",
  },
  es: {
    language: "Idioma",
    units: "Unidades",
    basic_mode: "Modo Basico",
    geek_mode: "Modo Geek",
    model_card: "Ficha del modelo",
    help: "Ayuda",
    refresh: "Actualizar",
    race_hub: "Carrera",
    live_race: "En vivo",
    history: "Historia",
    circuit_profiles: "Circuitos",
    driver_ratings: "Pilotos",
    team_profiles: "Equipos",
    compatibility_lab: "Laboratorio",
    what_if: "Comparaciones",
    sunny: "Soleado",
    cloudy: "Nublado",
    dry: "Seco",
    damp_risk: "Riesgo humedo",
    wet: "Mojado",
    storm_risk: "Riesgo tormenta",
    risk: "Riesgo",
    air: "Aire",
    track: "Pista",
    rain: "Lluvia",
    wind: "Viento",
  },
};

function formatDate(value, timeZone) {
  if (!value || value === "NaT") return "TBD";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "TBD";
  const options = {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  };
  if (timeZone) options.timeZone = timeZone;
  return new Intl.DateTimeFormat(activeLanguage === "es" ? "es" : undefined, options).format(date);
}

function t(key) {
  return I18N[activeLanguage]?.[key] ?? I18N.en[key] ?? key;
}

function translateStaticText() {
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
}

function setUrlState(params = {}, replace = true) {
  const url = new URL(window.location.href);
  Object.entries(params).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "") {
      url.searchParams.delete(key);
    } else {
      url.searchParams.set(key, value);
    }
  });
  window.history[replace ? "replaceState" : "pushState"]({}, "", url);
}

function initialParams() {
  return new URLSearchParams(window.location.search);
}

async function copyShareUrl(extraParams = {}) {
  const url = new URL(window.location.href);
  Object.entries(extraParams).forEach(([key, value]) => url.searchParams.set(key, value));
  if (navigator.clipboard?.writeText) {
    try {
      await Promise.race([
        navigator.clipboard.writeText(url.toString()),
        new Promise((resolve) => setTimeout(resolve, 750)),
      ]);
    } catch {
      // Clipboard permission can be unavailable in embedded browsers; the URL state is still updated.
    }
  }
  return url.toString();
}

function coverageBadges(metadata = {}) {
  const coverage = metadata.coverage ?? {};
  return `
    <span class="coverage-badges">
      <i title="Race results and qualifying-style history are available across the packaged archive.">Broad results</i>
      <i title="Modern races can include laps, stints, tyres, weather, and timing context.">${coverage.rich_session_detail ? "Rich modern data" : "Rich data where available"}</i>
      <i title="OpenF1-backed detail is strongest from 2023 onward; older seasons can be thinner.">${coverage.deep_modern_detail ? "OpenF1 2023+" : "Era-limited detail"}</i>
    </span>
  `;
}

const TOUR_STEPS = [
  {
    section: "race-hub",
    selector: "#race",
    title: "Start with the Race Hub",
    body: "This is the fan view: next race, countdown, weather, forecast state, and clean qualifying or race tables.",
  },
  {
    section: "history",
    selector: "[data-product-section='history']",
    title: "Use History for context",
    body: "Browse seasons and races first. Geek mode adds richer lap, tyre, stint, and comparison detail when the data exists.",
  },
  {
    section: "driver-ratings",
    selector: "[data-product-section='driver-ratings']",
    title: "Open driver profiles",
    body: "Profiles explain form, splits, teammate context, and rating evidence without pretending every era has equal data depth.",
  },
  {
    section: "lab",
    selector: "[data-product-section='lab']",
    title: "Try Compatibility Lab",
    body: "Driver-to-team fit is evidence-based. TBD means the app does not have enough support yet, not that the score is zero.",
  },
  {
    section: "what-if",
    selector: "[data-product-section='what-if']",
    title: "Share What-If Matchups",
    body: "Matchups are simulated projections. Share links preserve the drivers, circuit, session, and condition for someone else.",
  },
];

function openTour(step = 0) {
  tourReturnSection = activeSection || "race-hub";
  activeTourStep = Math.max(0, Math.min(step, TOUR_STEPS.length - 1));
  tourOverlay.hidden = false;
  document.body.classList.add("tour-active");
  renderTourStep();
}

function closeTour(markSeen = true) {
  tourOverlay.hidden = true;
  document.body.classList.remove("tour-active");
  document.querySelectorAll(".tour-highlight").forEach((node) => node.classList.remove("tour-highlight"));
  if (markSeen) localStorage.setItem("f1-tour-seen", "true");
  if (tourReturnSection) setProductSection(tourReturnSection);
}

function renderTourStep() {
  const step = TOUR_STEPS[activeTourStep];
  setProductSection(step.section);
  tourStepEl.textContent = `Step ${activeTourStep + 1} of ${TOUR_STEPS.length}`;
  tourTitleEl.textContent = step.title;
  tourBodyEl.textContent = step.body;
  tourNextButton.textContent = activeTourStep === TOUR_STEPS.length - 1 ? "Finish" : "Next";
  tourProgressEl.innerHTML = TOUR_STEPS
    .map((_, index) => `<i class="${index === activeTourStep ? "active" : ""}"></i>`)
    .join("");
  document.querySelectorAll(".tour-highlight").forEach((node) => node.classList.remove("tour-highlight"));
  const target = document.querySelector(step.selector);
  if (target) target.classList.add("tour-highlight");
  requestAnimationFrame(() => {
    if (!target) return;
    target.scrollIntoView({ block: "center", behavior: "smooth" });
  });
}

function advanceTour() {
  if (activeTourStep >= TOUR_STEPS.length - 1) {
    closeTour(true);
    return;
  }
  activeTourStep += 1;
  renderTourStep();
}

function temp(value, decimals = 0) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "TBD";
  if (activeUnits === "imperial") return `${((number * 9) / 5 + 32).toFixed(decimals)}F`;
  return `${number.toFixed(decimals)}C`;
}

function speed(value, decimals = 0) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "TBD";
  if (activeUnits === "imperial") return `${(number * 0.621371).toFixed(decimals)} mph`;
  return `${number.toFixed(decimals)} kph`;
}

function localizeCondition(label) {
  const key = String(label || "")
    .toLowerCase()
    .replace(/[^a-z]+/g, "_")
    .replace(/^_|_$/g, "");
  return t(key) || label || "TBD";
}

function applyPreferences() {
  languageSelect.value = activeLanguage;
  unitSelect.value = activeUnits;
  translateStaticText();
  if (weekendPayload) {
    renderRace(weekendPayload.race);
    renderSessions(weekendPayload);
  }
  if (racePayload && weekendPayload) {
    renderMetadata(racePayload.metadata ?? {}, weekendPayload);
    renderBasicNote(racePayload.metadata ?? {}, weekendPayload);
  }
  if (selectedHistoryRace) {
    loadHistoryRace(selectedHistoryRace.year, selectedHistoryRace.round);
  }
}

function pct(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function fixed(value, decimals = 1) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(decimals) : "TBD";
}

function emptyTableMessage(title, body) {
  return `<div class="empty-state table-empty"><strong>${title}</strong><p>${body}</p></div>`;
}

function circuitKey(value) {
  if (!value) return "current";
  const source = typeof value === "string"
    ? value
    : value.circuit || value.location || value.event_name || "current";
  return String(source);
}

function teamProfileButton(team) {
  if (!team) return "TBD";
  return `<button class="inline-link" type="button" data-open-team="${String(team).replace(/"/g, "&quot;")}">${team}</button>`;
}

function renderRace(race) {
  raceEl.innerHTML = `
    <div>
      <span class="label">Next Race</span>
      <h2>${race.event_name ?? `Round ${race.round}`}</h2>
      <p>${race.country ?? "Location TBD"} - ${race.location ?? "Circuit TBD"}</p>
      <button class="secondary compact-action" type="button" data-open-circuit="${circuitKey(race)}">Circuit profile</button>
    </div>
    <dl class="race-facts">
      <div><dt>Circuit</dt><dd>${race.circuit ?? race.location ?? "TBD"}</dd></div>
      <div><dt>Round</dt><dd>${race.year} - ${race.round}</dd></div>
      <div><dt>Race</dt><dd>${formatDate(race.race_date, race.timezone)}</dd></div>
    </dl>
  `;
  startCountdown(race.race_date);
}

function startCountdown(raceDate) {
  if (countdownTimer) clearInterval(countdownTimer);
  const target = new Date(raceDate);
  countdownTargetEl.textContent = `Race start - ${formatDate(raceDate, weekendPayload?.race?.timezone)}`;
  if (!raceDate || Number.isNaN(target.getTime())) {
    countdownEl.textContent = "TBD";
    return;
  }
  const update = () => {
    const ms = target.getTime() - Date.now();
    if (ms <= 0) {
      countdownEl.textContent = "Race live or complete";
      return;
    }
    const days = Math.floor(ms / 86400000);
    const hours = Math.floor((ms % 86400000) / 3600000);
    const minutes = Math.floor((ms % 3600000) / 60000);
    countdownEl.textContent = `${days}d ${hours}h ${minutes}m`;
  };
  update();
  countdownTimer = setInterval(update, 60000);
}

function renderMetadata(metadata, weekend) {
  const data = metadata.data_included ?? {};
  const context = weekend.context ?? {};
  const chips = [
    data.practice ? "Practice included" : "Practice not yet included",
    data.qualifying ? "Qualifying included" : "Qualifying not yet included",
    data.upgrade_news ? "Upgrade news included" : "Upgrade news included",
  ];
  metadataEl.innerHTML = `
    <span><strong>${context.forecast_mode ?? metadata.prediction_mode ?? "pre-weekend forecast"}</strong></span>
    <span>${context.headline ?? "Race forecast loading"}</span>
    <span class="chip-row">${chips.map((chip) => `<i>${chip}</i>`).join("")}</span>
  `;
  renderModelCard(metadata);
}

function renderSynthesisCards() {
  const topRace = racePayload?.predictions?.[0] ?? {};
  const topQuali = qualifyingPayload?.predictions?.[0] ?? {};
  const race = weekendPayload?.race ?? {};
  const topDriver = topRace.driver_code ?? topQuali.driver_code ?? "ANT";
  const topTeam = topRace.constructor_name ?? "Mercedes";
  synthesisCardsEl.innerHTML = `
    <article>
      <span>Driver Card</span>
      <strong>${topDriver} profile</strong>
      <p>Form, splits, teammate context, and evidence ratings.</p>
      <button type="button" data-open-driver="${topDriver}">Open driver</button>
    </article>
    <article>
      <span>Circuit Context</span>
      <strong>${race.circuit ?? race.location ?? "Current circuit"}</strong>
      <p>Qualifying importance, overtaking, tyre and race-history patterns.</p>
      <button type="button" data-open-circuit="${circuitKey(race)}">Open circuit</button>
    </article>
    <article>
      <span>Team Fit</span>
      <strong>${topDriver} -> ${topTeam}</strong>
      <p>Evidence-based compatibility with confidence and TBD handling.</p>
      <button type="button" data-open-compat-driver="${topDriver}" data-open-compat-team="${topTeam}">Open fit</button>
    </article>
    <article>
      <span>What-if</span>
      <strong>${topDriver} vs VER</strong>
      <p>Simulated matchup at the current circuit with uncertainty notes.</p>
      <button type="button" data-open-whatif-a="${topDriver}" data-open-whatif-b="VER">Run matchup</button>
    </article>
  `;
}

function renderModelCard(metadata) {
  const model = metadata.model ?? {};
  const card = metadata.model_card ?? {};
  const groups = card.feature_groups ?? [];
  const caveats = card.caveats ?? [];
  modelCardBody.innerHTML = `
    <dl class="card-facts">
      <div><dt>Training years</dt><dd>${card.training_years ?? "unknown"}</dd></div>
      <div><dt>Last trained</dt><dd>${model.trained_at_utc ? formatDate(model.trained_at_utc) : "unknown"}</dd></div>
      <div><dt>Model version</dt><dd>${model.model_version ?? "unknown"}</dd></div>
    </dl>
    <h3>Feature groups</h3>
    <ul>${groups.map((item) => `<li>${item}</li>`).join("")}</ul>
    <h3>Caveats</h3>
    <ul>${caveats.map((item) => `<li>${item}</li>`).join("")}</ul>
  `;
}

function renderSessions(weekend) {
  const sessions = weekend.sessions ?? [];
  weatherNoteEl.textContent = weekend.weather_note ?? "Live weather shown when available.";
  if (!sessions.length) {
    sessionsEl.innerHTML = `
      <div class="empty-state">
        <strong>Session schedule is not packaged yet.</strong>
        <p>The Race Hub can still show predictions, but weather cards need weekend schedule data from the latest refresh.</p>
      </div>
    `;
    return;
  }
  sessionsEl.innerHTML = sessions
    .map((session) => {
      const weather = session.weather;
      const condition = weatherCondition(weather);
      return `
        <article class="session-card ${condition.className}">
          <div class="weather-icon" aria-label="${condition.label}">
            <span>${condition.icon}</span>
          </div>
          <div class="session-main">
            <strong>${session.name}</strong>
            <span>${formatDate(session.starts_at, weekend.race?.timezone)}</span>
            <p>${localizeCondition(condition.label)}</p>
          </div>
          <div class="weather-stats">
            <div><span>${t("air")}</span><strong>${weather ? temp(weather.air_temp_c, 0) : "TBD"}</strong></div>
            <div><span>${t("track")}</span><strong>${weather?.track_temp_c ? temp(weather.track_temp_c, 0) : "N/A"}</strong></div>
            <div><span>${t("rain")}</span><strong>${weather ? `${fixed(weather.rain_probability, 0)}%` : "TBD"}</strong></div>
            <div><span>${t("wind")}</span><strong>${weather ? speed(weather.wind_kph, 0) : "TBD"}</strong></div>
          </div>
          ${renderForecastStrip(weather)}
          <small>
            ${session.time_status ?? "scheduled"} - ${condition.supportingText} - ${weatherReason(weather, session.weather_status)}
          </small>
        </article>
      `;
    })
    .join("");
}

function legacyWeatherCondition(weather) {
  if (!weather) return { label: "TBD", icon: "–", className: "weather-unknown", supportingText: "Risk TBD" };
  if (weather.weather_condition && weather.weather_icon && weather.weather_class) {
    const score = Number(weather.weather_risk_score ?? weather.risk_score);
    return {
      label: weather.weather_condition,
      icon: weather.weather_icon,
      className: weather.weather_class,
      supportingText: Number.isFinite(score) ? `Risk ${score}/100` : "Risk TBD",
    };
  }
  const rain = Number(weather.rain_probability || 0);
  const cloud = Number(weather.cloud_cover || 0);
  if (rain >= 45) return { label: "Wet", icon: "🌧️", className: "weather-wet", supportingText: "Risk high" };
  if (rain >= 20) return { label: "Damp Risk", icon: "🌦️", className: "weather-damp", supportingText: "Risk medium" };
  if (cloud >= 70) return { label: "Cloudy", icon: "☁️", className: "weather-cloudy", supportingText: "Risk low" };
  return { label: "Dry", icon: "🌤️", className: "weather-dry", supportingText: "Risk low" };
}

function weatherCondition(weather) {
  if (!weather) return { label: "TBD", icon: "-", className: "weather-unknown", supportingText: `${t("risk")} TBD` };
  if (weather.weather_condition && weather.weather_icon && weather.weather_class) {
    const score = Number(weather.weather_risk_score ?? weather.risk_score);
    return {
      label: weather.weather_condition,
      icon: weather.weather_icon,
      className: weather.weather_class,
      supportingText: Number.isFinite(score) ? `${t("risk")} ${score}/100` : `${t("risk")} TBD`,
    };
  }
  const rain = Number(weather.rain_probability || 0);
  const cloud = Number(weather.cloud_cover || 0);
  if (rain >= 45) return { label: "Wet", icon: "\u{1F327}\uFE0F", className: "weather-wet", supportingText: `${t("risk")} high` };
  if (rain >= 20) return { label: "Damp Risk", icon: "\u{1F326}\uFE0F", className: "weather-damp", supportingText: `${t("risk")} medium` };
  if (cloud >= 70) return { label: "Cloudy", icon: "\u2601\uFE0F", className: "weather-cloudy", supportingText: `${t("risk")} low` };
  return { label: "Dry", icon: "\u{1F324}\uFE0F", className: "weather-dry", supportingText: `${t("risk")} low` };
}

function weatherReason(weather, fallback) {
  if (!weather) return fallback ?? "weather pending";
  const rain = weather.rain_probability !== null && weather.rain_probability !== undefined ? `${fixed(weather.rain_probability, 0)}%` : "TBD";
  return `${localizeCondition(weather.weather_condition)}: ${t("rain")} ${rain}, ${t("wind")} ${speed(weather.wind_kph, 0)}`;
}

function renderForecastStrip(weather) {
  const window = weather?.forecast_window ?? [];
  if (!window.length) {
    return `<div class="forecast-strip unavailable"><i></i><i></i><i></i></div>`;
  }
  return `
    <div class="forecast-strip" aria-label="Forecast window">
      ${window
        .map((point) => {
          const rain = Math.max(0, Math.min(100, Number(point.rain_probability || 0)));
          const height = 20 + rain * 0.6;
          return `<i style="height:${height}%"><span>${fixed(point.rain_probability, 0)}%</span></i>`;
        })
        .join("")}
    </div>
  `;
}

function setMode(mode) {
  activeMode = mode;
  document.body.dataset.mode = mode;
  basicModeButton.classList.toggle("active", mode === "basic");
  geekModeButton.classList.toggle("active", mode === "geek");
  if (mode === "geek") {
    loadGeekReports();
  }
  renderForecastTables();
}

function setForecastTab(tab) {
  activeForecast = tab;
  qualifyingTab.classList.toggle("active", tab === "qualifying");
  raceTab.classList.toggle("active", tab === "race");
  renderForecastTables();
  if (racePayload && qualifyingPayload && weekendPayload) {
    renderBasicNote(racePayload.metadata ?? {}, weekendPayload);
  }
}

function renderForecastTables() {
  if (!racePayload || !qualifyingPayload) return;
  if (activeForecast === "qualifying") {
    renderQualifyingTable(qualifyingPayload.predictions ?? []);
  } else {
    renderRaceTable(racePayload.predictions ?? [], predictionsEl, 999);
  }
  renderRaceTable(racePayload.predictions ?? [], geekPredictionsEl, 999, true);
}

function renderRaceTable(predictions, target, limit = 5, geek = false) {
  const rows = predictions.slice(0, limit);
  if (!rows.length) {
    target.innerHTML = `<tr><td colspan="${geek ? 10 : 7}">${emptyTableMessage("Race forecast missing", "Run the latest prediction export or use the packaged demo snapshot.")}</td></tr>`;
    return;
  }
  if (!geek) {
    predictionHeadEl.innerHTML = `
      <tr>
        <th>Rank</th>
        <th>Driver</th>
        <th>Team</th>
        <th>Win</th>
        <th>Podium</th>
        <th>Top 10</th>
        <th>Expected Finish</th>
      </tr>
    `;
  }
  target.innerHTML = rows
    .map((row) => {
      if (geek) {
        const gridValue = Number(row.grid_position ?? row.qualifying_position);
        const grid = Number.isFinite(gridValue) && gridValue > 0 ? `P${gridValue.toFixed(0)}` : "TBD";
        const finishBand = `${fixed(row.finish_low)}-${fixed(row.finish_high)}`;
        const paceRank = Number.isFinite(Number(row.practice_adjusted_pace_rank))
          ? `P${Number(row.practice_adjusted_pace_rank).toFixed(0)}`
          : "TBD";
        return `
          <tr>
            <td><span class="driver">${row.driver_code}</span><br><span class="muted">${row.driver_name ?? ""}</span></td>
            <td>${teamProfileButton(row.constructor_name)}</td>
            <td>${grid}</td>
            <td class="probability">${pct(row.win_probability)}</td>
            <td class="probability">${pct(row.podium_probability)}</td>
            <td class="probability">${pct(row.top10_probability)}</td>
            <td>P${fixed(row.expected_finish)}</td>
            <td>${finishBand}</td>
            <td>${row.recent_form ?? recentFormFromBaseline(row)}</td>
            <td><span class="pace-rank">${paceRank}</span></td>
          </tr>
        `;
      }
      return `
        <tr>
          <td>${rankCell(row.prediction_rank, row.delta_rank)}</td>
          <td>${driverCell(row)}</td>
          <td>${teamProfileButton(row.constructor_name)}</td>
          <td>${probabilityCell(row.win_probability, row.delta_win_probability)}</td>
          <td>${probabilityCell(row.podium_probability, row.delta_podium_probability)}</td>
          <td>${probabilityCell(row.top10_probability, row.delta_top10_probability)}</td>
          <td>${finishCell(row.expected_finish, row.delta_expected_finish)}</td>
        </tr>
      `;
    })
    .join("");
}

function renderQualifyingTable(predictions) {
  predictionHeadEl.innerHTML = `
    <tr>
      <th>Rank</th>
      <th>Driver</th>
      <th>Team</th>
      <th>Pole</th>
      <th>Front Row</th>
      <th>Practice Rank</th>
    </tr>
  `;
  const rows = predictions;
  if (!rows.length) {
    predictionsEl.innerHTML = `<tr><td colspan="6">${emptyTableMessage("Qualifying forecast missing", "This view needs the qualifying prediction artifact, or a fresh weekend refresh.")}</td></tr>`;
    return;
  }
  predictionsEl.innerHTML = rows
    .map((row) => `
      <tr>
        <td>P${row.qualifying_rank}</td>
        <td>${driverCell(row)}</td>
        <td>${teamProfileButton(row.constructor_name)}</td>
        <td>${probabilityCell(row.pole_probability)}</td>
        <td>${probabilityCell(row.front_row_probability)}</td>
        <td>${row.practice_adjusted_pace_rank ? `P${row.practice_adjusted_pace_rank}` : "TBD"}</td>
      </tr>
    `)
    .join("");
}

function recentFormFromBaseline(row) {
  const parts = [];
  if (row.driver_last3_avg_finish !== null && row.driver_last3_avg_finish !== undefined) {
    parts.push(`L3 avg P${fixed(row.driver_last3_avg_finish)}`);
  }
  if (row.constructor_last5_avg_finish !== null && row.constructor_last5_avg_finish !== undefined) {
    parts.push(`Team L5 P${fixed(row.constructor_last5_avg_finish)}`);
  }
  return parts.join(" - ") || "Form TBD";
}

function renderBasicNote(metadata, weekend) {
  const data = metadata.data_included ?? {};
  const context = weekend.context ?? {};
  const included = [
    data.practice ? "practice included" : "practice not yet included",
    data.qualifying ? "qualifying included" : "qualifying not yet included",
  ].join(", ");
  const raceRussell = findDriver(racePayload?.predictions, "RUS");
  const qualiRussell = findDriver(qualifyingPayload?.predictions, "RUS");
  const note =
    activeForecast === "qualifying"
      ? `Qualifying and race forecasts are separate: Russell is P${qualiRussell?.qualifying_rank ?? "TBD"} in the quali table because this view leans on practice-adjusted pace and one-lap signals, while his race forecast is P${raceRussell?.prediction_rank ?? "TBD"}.`
      : `Antonelli is rated ahead of Russell because recent form is much stronger: Antonelli leads the 2026 standings with 156 points after Monaco, while Russell is on 88 and has gone scoreless in the last two grands prix. Russell is P${raceRussell?.prediction_rank ?? "TBD"} in this race forecast, not the same as his qualifying rank.`;
  basicNoteEl.innerHTML = `
    <strong>${context.conditions ?? "Weather updates live when available."}</strong>
    <span>Data note: ${included}.</span>
    <span>${note}</span>
  `;
}

function renderForecastStates(payload) {
  const states = payload?.states ?? [];
  if (!states.length) {
    forecastStatesEl.innerHTML = `<span class="empty-inline">Forecast timeline missing. The app can still show predictions, but state changes need the forecast-state artifact.</span>`;
    return;
  }
  forecastStatesEl.innerHTML = states
    .map((state) => `
      <span class="state-pill ${state.available ? "available" : "pending"} ${state.state === payload.current_state ? "current" : ""}">
        <b>${state.state}</b>
        <small>${state.available ? "ready" : "pending"}</small>
      </span>
    `)
    .join("");
}

function findDriver(rows = [], code) {
  return rows.find((row) => row.driver_code === code);
}

function probabilityCell(value, delta = null) {
  const percent = Math.max(0, Math.min(100, Number(value || 0) * 100));
  return `
    <div class="probability-cell">
      <span>${pct(value)}</span>
      <i style="width:${percent}%"></i>
      ${deltaChip(delta, "pp")}
    </div>
  `;
}

function finishCell(value, delta = null) {
  return `
    <div class="finish-cell">
      <span>P${fixed(value)}</span>
      ${deltaChip(delta, "pos", true)}
    </div>
  `;
}

function rankCell(value, delta = null) {
  return `
    <div class="finish-cell">
      <span>P${value ?? ""}</span>
      ${deltaChip(delta, "rank", true)}
    </div>
  `;
}

function deltaChip(delta, unit, lowerIsBetter = false) {
  if (delta === null || delta === undefined || Number.isNaN(Number(delta))) return "";
  const numeric = Number(delta);
  const displayValue =
    unit === "pp"
      ? `${Math.abs(numeric * 100).toFixed(1)}pp`
      : unit === "rank"
        ? `${Math.abs(numeric).toFixed(0)} rank`
        : `${Math.abs(numeric).toFixed(1)} ${unit}`;
  const direction = numeric > 0 ? "up" : numeric < 0 ? "down" : "flat";
  const helpful = lowerIsBetter ? numeric < 0 : numeric > 0;
  const className = numeric === 0 ? "flat" : helpful ? "good" : "bad";
  const arrow = direction === "up" ? "▲" : direction === "down" ? "▼" : "•";
  return `<small class="delta ${className}">${arrow} ${displayValue}</small>`;
}

function driverCell(row) {
  const color = teamColor(row.constructor_name);
  return `
    <span class="driver-cell" style="--team-color:${color}">
      <span class="driver">${row.driver_code}</span>
      <span class="muted">${row.driver_name ?? ""}</span>
    </span>
  `;
}

function teamColor(team = "") {
  const normalized = team.toLowerCase();
  if (normalized.includes("ferrari")) return "#ef1a2d";
  if (normalized.includes("mercedes")) return "#00d2be";
  if (normalized.includes("red bull")) return "#3671c6";
  if (normalized.includes("mclaren")) return "#ff8000";
  if (normalized.includes("aston")) return "#229971";
  if (normalized.includes("williams")) return "#64c4ff";
  if (normalized.includes("alpine")) return "#ff87bc";
  if (normalized.includes("haas")) return "#b6babd";
  if (normalized.includes("racing bulls") || normalized.includes("rb")) return "#6692ff";
  if (normalized.includes("sauber") || normalized.includes("audi")) return "#52e252";
  return "#e10600";
}

function renderMetrics(metadata, report) {
  const modelMetrics = metadata.model?.metrics ?? {};
  const summary = report.summary ?? {};
  const items = [
    ["Backtest Brier", summary.mean_podium_brier],
    ["Validation AUC", modelMetrics.podium_auc],
    ["Backtest MAE", summary.mean_finish_mae],
  ];
  metricsEl.innerHTML = items
    .map(([label, value]) => `
      <div class="metric">
        <span>${label}</span>
        <strong>${Number(value ?? 0).toFixed(3)}</strong>
      </div>
    `)
    .join("");
}

function renderReliability(rows) {
  if (!rows.length) {
    reliabilityEl.innerHTML = `<span>No calibration report available.</span>`;
    return;
  }
  reliabilityEl.innerHTML = rows
    .slice(0, 6)
    .map((row) => {
      const predicted = Number(row.mean_predicted_probability || 0);
      const observed = Number(row.observed_podium_rate || 0);
      return `
        <div class="reliability-row">
          <span>${pct(predicted)} forecast</span>
          <div class="calibration-bars">
            <i class="forecast" style="width:${Math.min(100, predicted * 100)}%"></i>
            <i class="observed" style="width:${Math.min(100, observed * 100)}%"></i>
          </div>
          <span>${pct(observed)} actual</span>
        </div>
      `;
    })
    .join("");
}

function renderDiagnostics(rows) {
  if (!rows.length) {
    diagnosticsEl.innerHTML = `<span>No weak windows available.</span>`;
    return;
  }
  diagnosticsEl.innerHTML = rows
    .slice(0, 3)
    .map((row) => `
      <div class="diagnostic">
        <strong>${row.year} ${row.event_name}</strong>
        <span>${row.diagnostic_reason ?? "weak window"} - Brier ${Number(row.podium_brier).toFixed(3)} - MAE ${Number(row.finish_mae).toFixed(2)}</span>
      </div>
    `)
    .join("");
}

function renderBenchmark(benchmark) {
  if (!benchmark?.scorecard) {
    benchmarkEl.innerHTML = `
      <div class="empty-state">
        <strong>No benchmark card packaged.</strong>
        <p>Benchmarks appear here after a replay snapshot is exported for a race such as Monaco or Spain.</p>
      </div>
    `;
    return;
  }
  const score = benchmark.scorecard;
  const actual = benchmark.actual ?? {};
  const forecast = benchmark.forecast ?? {};
  benchmarkEl.innerHTML = `
    <div>
      <span class="label">${benchmark.event?.benchmark_status ?? "Benchmark"}</span>
      <h3>${benchmark.event?.name ?? "Monaco Grand Prix"}: did the forecast understand the weekend?</h3>
      <p>Actual podium: ${formatDriverCodes(actual.race_podium)}. Forecast podium: ${formatDriverCodes(forecast.predicted_podium)}.</p>
      <p>Actual grid top 5: ${formatDriverCodes(actual.qualifying_top5)}. Forecast top 5: ${formatDriverCodes(forecast.predicted_top5)}.</p>
    </div>
    <div class="benchmark-score-grid">
      <div><span>Winner hit</span><strong>${score.winner_hit ? "Yes" : "No"}</strong></div>
      <div><span>Podium recall</span><strong>${Math.round(Number(score.podium_recall || 0) * 100)}%</strong></div>
      <div><span>Quali top-5 overlap</span><strong>${Math.round(Number(score.qualifying_top5_overlap || 0) * 100)}%</strong></div>
      <div><span>Hadjar podium odds</span><strong>${pct(forecast.hadjar_podium_probability)}</strong></div>
    </div>
    <p class="benchmark-miss">${score.main_miss}</p>
  `;
}

function formatDriverCodes(codes = []) {
  return codes.length ? codes.join(" - ") : "TBD";
}

function setProductSection(section) {
  activeSection = section;
  productTabs.forEach((button) => button.classList.toggle("active", button.dataset.section === section));
  document.querySelectorAll(".nav-group").forEach((group) => {
    const isActive = Boolean(group.querySelector(`[data-section="${section}"]`));
    group.classList.toggle("group-active", isActive);
  });
  raceHubSections.forEach((node) => {
    node.hidden = section !== "race-hub";
  });
  productSections.forEach((node) => {
    node.hidden = node.dataset.productSection !== section;
  });
  if (section === "history" && !historyLoaded) {
    loadHistory();
  }
  if (section === "circuits" && !circuitLoaded) {
    loadCircuitProfile();
  }
  if (section === "driver-ratings" && !profileLoaded) {
    loadDriverProfile();
  }
  if (section === "teams" && !teamProfileLoaded) {
    loadTeamProfile();
  }
  if (section === "lab" && !compatibilityLoaded) {
    loadCompatibility();
  }
  if (section === "what-if" && !whatIfLoaded) {
    loadWhatIfMatchup();
  }
}

async function loadHistory() {
  historyLoaded = true;
  historyRacesEl.textContent = "Loading races...";
  try {
    const seasonsResponse = await fetch("/api/history/seasons");
    const seasons = await seasonsResponse.json();
    renderHistoryCoverage(seasons.metadata ?? {});
    renderSeasonOptions(seasons.seasons ?? []);
    renderSeasonCards(seasons.season_cards ?? []);
    const selectedYear = Number(historySeasonEl.value || seasons.seasons?.[0]?.year || 2026);
    await loadHistoryYear(selectedYear);
    await Promise.all([loadHistoryDriver(), loadHistoryTeam(), loadDriverCompare()]);
  } catch (error) {
    historyRacesEl.innerHTML = `
      <div class="empty-state">
        <strong>History did not load.</strong>
        <p>${error.message}. Check that packaged history artifacts are present for the selected season.</p>
      </div>
    `;
  }
}

function renderHistoryCoverage(metadata) {
  const coverage = metadata.coverage ?? {};
  historyCoverageEl.innerHTML = `${coverage.broad_results ?? "Broad results archive"}; ${coverage.rich_session_detail ?? "rich session detail when available"}. ${coverageBadges(metadata)}`;
}

function renderSeasonOptions(seasons) {
  historySeasonEl.innerHTML = seasons
    .map((season) => `<option value="${season.year}">${season.year} (${season.event_count ?? 0} races)</option>`)
    .join("");
}

function renderSeasonCards(cards) {
  historySeasonCardsEl.innerHTML = cards
    .map((card) => `
      <article class="season-card">
        <span>${card.year}</span>
        <strong>${card.race_count ?? 0} races</strong>
        <small>Wins leader: ${leaderText(card.wins_leader)}</small>
        <small>Podiums: ${leaderText(card.podiums_leader)}</small>
        <small>Points: ${leaderText(card.points_leader, "value")}</small>
        <small>Poles: ${leaderText(card.pole_leader)}</small>
      </article>
    `)
    .join("");
}

function leaderText(leader, valueKey = "count") {
  if (!leader) return "TBD";
  return `${leader.code ?? "TBD"} (${leader[valueKey] ?? 0})`;
}

async function loadHistoryYear(year) {
  historyRacesEl.textContent = "Loading races...";
  const response = await fetch(`/api/history/${year}/races`);
  const payload = await response.json();
  const races = payload.races ?? [];
  historyRacesEl.innerHTML = races
    .map((race) => `
      <button class="race-list-item" type="button" data-year="${race.year}" data-round="${race.round}">
        <strong>R${race.round} ${race.event_name ?? "Grand Prix"}</strong>
        <span>${race.circuit ?? race.location ?? "Circuit TBD"}</span>
        <small>Winner ${race.winner ?? "TBD"} - Pole ${race.pole ?? "TBD"} - Podium ${formatDriverCodes(race.podium ?? [])}</small>
      </button>
    `)
    .join("");
  const firstRace = races[0];
  if (firstRace) {
    await loadHistoryRace(firstRace.year, firstRace.round);
  }
}

async function loadHistoryRace(year, round) {
  selectedHistoryRace = { year, round };
  const [summaryResponse, lapsResponse] = await Promise.all([
    fetch(`/api/history/${year}/${round}/summary`),
    fetch(`/api/history/${year}/${round}/laps?limit=80`),
  ]);
  const summary = await summaryResponse.json();
  const laps = await lapsResponse.json();
  renderHistoryRace(summary);
  renderHistoryLaps(laps);
}

function renderHistoryRace(payload) {
  const event = payload.event ?? {};
  historyRaceTitleEl.textContent = `${event.year ?? ""} ${event.event_name ?? `Round ${event.round}`}`;
  const podium = payload.podium ?? [];
  const fastest = payload.fastest_laps ?? [];
  const weather = payload.weather_summary ?? {};
  historySummaryEl.innerHTML = `
    <div><span>Winner</span><strong>${podium[0]?.driver_code ?? "TBD"}</strong></div>
    <div><span>Podium</span><strong>${formatDriverCodes(podium.map((row) => row.driver_code).filter(Boolean))}</strong></div>
    <div><span>Pole</span><strong>${payload.qualifying_top10?.[0]?.driver_code ?? "TBD"}</strong></div>
    <div><span>Fastest lap</span><strong>${fastest[0]?.driver_code ?? "TBD"}</strong></div>
  `;
  historyRaceContextEl.innerHTML = `
    <div><span>Avg air</span><strong>${temp(weather.average_air_temp_c, 1)}</strong></div>
    <div><span>Avg track</span><strong>${temp(weather.average_track_temp_c, 1)}</strong></div>
    <div><span>Rain samples</span><strong>${weather.rain_samples ?? 0}</strong></div>
    <div><span>Wind</span><strong>${speed(weather.average_wind_kph, 1)}</strong></div>
    <div><span>Circuit</span><strong><button class="inline-link" type="button" data-open-circuit="${circuitKey(event)}">${event.location ?? event.event_name ?? "Open profile"}</button></strong></div>
  `;
  renderHistoryGeekContext(payload);
  historyResultsEl.innerHTML = (payload.race_results ?? [])
    .map((row) => `
      <tr>
        <td>P${fixed(row.finish_position, 0)}</td>
        <td>${driverCell(row)}</td>
        <td>${teamProfileButton(row.constructor_name)}</td>
        <td>${row.grid_position ? `P${fixed(row.grid_position, 0)}` : "TBD"}</td>
        <td>${fixed(row.points, 1)}</td>
      </tr>
    `)
    .join("") || `<tr><td colspan="5">No race results available.</td></tr>`;
}

function renderHistoryGeekContext(payload) {
  const tyres = payload.tyre_summary ?? [];
  const stints = payload.stint_summary ?? [];
  const tyreText = tyres.length
    ? tyres.slice(0, 4).map((row) => `${row.compound ?? "?"}: ${fixed(row.total_laps, 0)} laps`).join(" | ")
    : "No packaged tyre table for this race yet";
  const stintText = stints.length
    ? stints.slice(0, 4).map((row) => `${row.driver_code}: ${fixed(row.stints, 0)} stints`).join(" | ")
    : "No packaged stint table for this race yet";
  historyGeekContextEl.innerHTML = `
    <div><span>Tyre usage</span><strong>${tyreText}</strong></div>
    <div><span>Stint leaders</span><strong>${stintText}</strong></div>
  `;
}

function renderHistoryLaps(payload) {
  const rows = payload.rows ?? [];
  const metadata = payload.metadata ?? {};
  historyLapStatusEl.textContent = metadata.available
    ? `${metadata.row_count} rich lap rows available; showing first ${rows.length}.`
    : "No rich lap table packaged for this race yet.";
  historyLapsEl.innerHTML = rows
    .map((row) => `
      <tr>
        <td>${row.driver_code ?? ""}</td>
        <td>${fixed(row.lap_number, 0)}</td>
        <td>${row.stint_number ? fixed(row.stint_number, 0) : "TBD"}</td>
        <td>${row.compound ?? "TBD"}</td>
        <td>${fixed(row.lap_time_seconds, 3)}s</td>
        <td>${formatSector(row.sector1_time)}</td>
        <td>${formatSector(row.sector2_time)}</td>
        <td>${formatSector(row.sector3_time)}</td>
      </tr>
    `)
    .join("") || `<tr><td colspan="8">No lap rows available for this race.</td></tr>`;
}

function formatSector(value) {
  if (value === null || value === undefined) return "TBD";
  const seconds = Number(value);
  return Number.isFinite(seconds) ? `${seconds.toFixed(3)}s` : String(value);
}

async function loadHistoryDriver() {
  const code = (historyDriverEl.value || "ANT").trim().toUpperCase();
  const response = await fetch(`/api/history/drivers/${encodeURIComponent(code)}`);
  const payload = await response.json();
  renderHistoryEntitySummary(historyDriverSummaryEl, payload.summary ?? {}, payload.driver_name ?? code, payload.season_summaries ?? [], payload.teammate_summary ?? []);
}

async function loadHistoryTeam() {
  const team = (historyTeamEl.value || "Mercedes").trim();
  const response = await fetch(`/api/history/teams/${encodeURIComponent(team)}`);
  const payload = await response.json();
  renderHistoryEntitySummary(historyTeamSummaryEl, payload.summary ?? {}, payload.team_name ?? team, payload.season_summaries ?? [], payload.lineup_history ?? []);
}

function renderHistoryEntitySummary(target, summary, title, seasons = [], comparison = []) {
  const cards = [
    ["Name", title],
    ["Starts/Entries", summary.starts ?? summary.entries ?? 0],
    ["Wins", summary.wins ?? 0],
    ["Podiums", summary.podiums ?? 0],
    ["Avg finish", summary.average_finish ?? "TBD"],
    ["Points", summary.points ?? "TBD"],
  ];
  const seasonText = seasons.length
    ? seasons.slice(0, 3).map((row) => `${row.year}: ${row.wins}W, ${row.podiums}P, ${fixed(row.average_finish, 1)} avg`).join(" | ")
    : "Season trends pending";
  const comparisonText = comparison.length
    ? comparison.slice(0, 3).map((row) => `${row.teammate ?? row.drivers?.join("/") ?? row.year}: ${row.head_to_head_wins ?? row.drivers?.join(", ") ?? ""}`).join(" | ")
    : "Comparison detail pending";
  target.innerHTML = `
    ${cards.map(([label, value]) => `<div><span>${label}</span><strong>${value}</strong></div>`).join("")}
    <div class="wide"><span>Recent seasons</span><strong>${seasonText}</strong></div>
    <div class="wide"><span>Head-to-head / lineup</span><strong>${comparisonText}</strong></div>
  `;
}

async function loadDriverCompare() {
  const driverA = (compareDriverAEl.value || "ANT").trim().toUpperCase();
  const driverB = (compareDriverBEl.value || "RUS").trim().toUpperCase();
  driverCompareSummaryEl.textContent = "Loading comparison...";
  driverRatingSummaryEl.textContent = "Loading ratings...";
  driverTrendChartsEl.textContent = "Loading trends...";
  driverSplitSummaryEl.textContent = "Loading splits...";
  const [summaryResponse, trendResponse, splitResponse] = await Promise.all([
    fetch(`/api/history/compare/drivers/${encodeURIComponent(driverA)}/${encodeURIComponent(driverB)}`),
    fetch(`/api/history/compare/drivers/${encodeURIComponent(driverA)}/${encodeURIComponent(driverB)}/trends?window=5`),
    fetch(`/api/history/compare/drivers/${encodeURIComponent(driverA)}/${encodeURIComponent(driverB)}/splits`),
  ]);
  const [summary, trends, splits] = await Promise.all([
    summaryResponse.json(),
    trendResponse.json(),
    splitResponse.json(),
  ]);
  renderDriverCompare(summary, trends, splits);
}

function renderDriverCompare(payload, trends = {}, splits = {}) {
  const drivers = payload.drivers ?? [];
  const comparison = payload.comparison ?? [];
  const driverA = drivers[0]?.driver_code ?? "A";
  const driverB = drivers[1]?.driver_code ?? "B";
  const important = comparison.filter((row) =>
    ["wins", "podiums", "podium_rate", "average_finish", "average_qualifying", "average_teammate_finish_delta"].includes(row.metric),
  );
  driverCompareSummaryEl.innerHTML = important
    .map((row) => `
      <div>
        <span>${metricLabel(row.metric)}</span>
        <strong>${driverA}: ${metricValue(row.driver_a, row.metric)} | ${driverB}: ${metricValue(row.driver_b, row.metric)}</strong>
        <small>${row.leader ? `${row.leader} edge` : "Even or not enough data"}</small>
      </div>
    `)
    .join("");
  renderDriverRatings(payload.ratings ?? {});
  renderDriverTrendCharts(trends);
  renderDriverSplits(splits);
}

function renderDriverTrendCharts(payload) {
  const drivers = payload.drivers ?? Object.keys(payload.series ?? {});
  const series = payload.series ?? {};
  const charts = payload.charts ?? [];
  if (!drivers.length || !charts.length) {
    driverTrendChartsEl.innerHTML = `<article class="trend-card"><h3>Trend charts</h3><p>No trend rows are packaged for this pairing yet. Try a modern-era driver pair or refresh the history export.</p></article>`;
    return;
  }
  driverTrendChartsEl.innerHTML = charts
    .map((chart) => trendChart(chart.label, chart.key, series, drivers, chart.lower_is_better))
    .join("");
}

function trendChart(label, key, series, drivers, lowerIsBetter = false) {
  const values = drivers.flatMap((driver) => (series[driver] ?? []).map((row) => Number(row[key])).filter(Number.isFinite));
  if (!values.length) {
    return `<article class="trend-card"><h3>${label}</h3><p>TBD until stronger evidence is generated.</p></article>`;
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(0.1, max - min);
  const width = 320;
  const height = 130;
  const padding = 16;
  const polylines = drivers.map((driver, index) => {
    const rows = (series[driver] ?? []).filter((row) => Number.isFinite(Number(row[key])));
    const points = rows.map((row, pointIndex) => {
      const x = padding + (pointIndex / Math.max(1, rows.length - 1)) * (width - padding * 2);
      const normalized = (Number(row[key]) - min) / range;
      const yValue = lowerIsBetter ? normalized : 1 - normalized;
      const y = padding + yValue * (height - padding * 2);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });
    return `<polyline points="${points.join(" ")}" class="trend-line driver-${index}" />`;
  }).join("");
  const latest = drivers
    .map((driver) => {
      const rows = (series[driver] ?? []).filter((row) => Number.isFinite(Number(row[key])));
      const value = rows.length ? Number(rows[rows.length - 1][key]) : null;
      return `<span><i class="legend-dot"></i>${driver}: ${value === null ? "TBD" : value.toFixed(2)}</span>`;
    })
    .join("");
  return `
    <article class="trend-card">
      <div>
        <h3>${label}</h3>
        <p>${lowerIsBetter ? "Lower is better" : "Higher is better"} | window ${payloadWindowLabel(series)}</p>
      </div>
      <svg class="trend-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${label} chart">
        <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" />
        ${polylines}
      </svg>
      <div class="trend-legend">${latest}</div>
    </article>
  `;
}

function payloadWindowLabel(series) {
  const firstSeries = Object.values(series)[0] ?? [];
  return firstSeries.length ? "5-race" : "TBD";
}

function renderDriverSplits(payload) {
  const drivers = payload.drivers ?? Object.keys(payload.track_type_splits ?? {});
  const splits = payload.track_type_splits ?? {};
  if (!drivers.length) {
    driverSplitSummaryEl.innerHTML = `<div><span>Track splits</span><strong>TBD</strong></div>`;
    return;
  }
  const cards = ["street", "permanent"].map((type) => {
    const rows = drivers.map((driver) => {
      const split = splits[driver]?.[type] ?? {};
      const average = split.average_finish ?? null;
      return `<small>${driver}: ${average === null || average === undefined ? "TBD" : `avg P${Number(average).toFixed(1)}`} (${split.starts ?? 0} starts)</small>`;
    }).join("");
    return `
      <div>
        <span>${type} circuits</span>
        <strong>${type === "street" ? "Walls and low margin" : "Permanent-track form"}</strong>
        ${rows}
      </div>
    `;
  }).join("");
  driverSplitSummaryEl.innerHTML = `
    ${cards}
    <div>
      <span>Data depth</span>
      <strong>Modern timing is richest from 2018 onward; OpenF1 depth starts in 2023.</strong>
    </div>
  `;
}

async function loadDriverProfile() {
  profileLoaded = true;
  const code = (profileDriverEl.value || historyDriverEl.value || "ANT").trim().toUpperCase();
  profileDriverEl.value = code;
  profileHeroEl.textContent = "Loading driver profile...";
  profileTrendChartsEl.textContent = "Loading form charts...";
  profileRatingSummaryEl.textContent = "Loading rating evidence...";
  const response = await fetch(`/api/history/profiles/drivers/${encodeURIComponent(code)}?window=5`);
  const payload = await response.json();
  renderDriverProfile(payload);
}

function renderDriverProfile(payload) {
  const code = payload.driver_code ?? "TBD";
  const summary = payload.summary ?? {};
  const latest = payload.latest_season ?? {};
  const form = payload.recent_form ?? {};
  const metadata = payload.metadata ?? {};
  const coverage = metadata.coverage ?? {};
  profileCoverageEl.innerHTML = `${coverage.broad_results ?? "Broad result history"}; ${coverage.rich_session_detail ?? "rich modern detail when available"}. ${coverageBadges(metadata)}`;
  profileHeroEl.innerHTML = `
    <div>
      <span class="profile-code">${code}</span>
      <h3>${payload.driver_name ?? code}</h3>
      <p>${(summary.teams ?? []).map((team) => teamProfileButton(team)).join(" / ") || "Team history TBD"}</p>
    </div>
    <div class="profile-stat-grid">
      <div><span>Starts</span><strong>${summary.starts ?? 0}</strong></div>
      <div><span>Wins</span><strong>${summary.wins ?? 0}</strong></div>
      <div><span>Podiums</span><strong>${summary.podiums ?? 0}</strong></div>
      <div><span>Points</span><strong>${fixed(summary.points, 1)}</strong></div>
      <div><span>Latest season</span><strong>${latest.year ?? "TBD"}: ${latest.wins ?? 0}W / ${latest.podiums ?? 0}P</strong></div>
      <div><span>Recent form</span><strong>Avg finish ${fixed(form.average_finish, 1)} | Avg quali ${fixed(form.average_qualifying, 1)}</strong></div>
    </div>
  `;
  renderProfileTrends(payload);
  renderProfileRatings(payload.ratings ?? {});
  renderProfileSplits(payload.track_type_splits ?? {});
  renderProfileTeammates(payload.teammate_summary ?? []);
  renderProfileRaceLog(payload);
  renderProfileCompareShortcuts(code, payload.compare_shortcuts ?? []);
}

function renderProfileTrends(payload) {
  const code = payload.driver_code ?? "DRI";
  const series = { [code]: payload.trend_points ?? [] };
  const charts = payload.charts ?? [];
  profileTrendChartsEl.innerHTML = charts.length
    ? charts.map((chart) => trendChart(chart.label, chart.key, series, [code], chart.lower_is_better)).join("")
    : `<article class="trend-card"><h3>Recent form</h3><p>TBD until history artifacts are generated.</p></article>`;
}

function renderProfileRatings(ratings) {
  if (!Object.keys(ratings).length) {
    profileRatingSummaryEl.innerHTML = `<div class="empty-state"><strong>Rating evidence is thin.</strong><p>This profile needs richer modern race or session rows before the app can show reliable evidence metrics.</p></div>`;
    return;
  }
  profileRatingSummaryEl.innerHTML = `
    <article class="rating-card profile-rating-card">
      <h3>Evidence ratings</h3>
      ${Object.entries(ratings)
        .filter(([key]) => key !== "overall_evidence_score")
        .map(([key, value]) => ratingBar(metricLabel(key), value))
        .join("")}
      ${ratingBar("Evidence score", ratings.overall_evidence_score)}
    </article>
  `;
}

function renderProfileSplits(splits) {
  profileSplitSummaryEl.innerHTML = ["street", "permanent"].map((type) => {
    const split = splits[type] ?? {};
    const label = type === "street" ? "Street circuits" : "Permanent circuits";
    return `
      <div>
        <span>${label}</span>
        <strong>${split.starts ?? 0} starts | avg P${split.average_finish === null || split.average_finish === undefined ? "TBD" : Number(split.average_finish).toFixed(1)}</strong>
        <small>${split.wins ?? 0} wins | ${split.podiums ?? 0} podiums</small>
      </div>
    `;
  }).join("");
}

function renderProfileTeammates(teammates) {
  if (!teammates.length) {
    profileTeammateSummaryEl.innerHTML = `<div><span>Teammate delta</span><strong>TBD</strong></div>`;
    return;
  }
  profileTeammateSummaryEl.innerHTML = teammates.slice(0, 4).map((row) => `
    <div>
      <span>${row.year ?? "Year"} vs ${row.teammate ?? "TBD"}</span>
      <strong>${row.head_to_head_wins ?? 0}/${row.comparisons ?? 0} ahead</strong>
      <small>Avg finish delta ${fixed(row.average_finish_delta, 2)}</small>
    </div>
  `).join("");
}

function renderProfileRaceLog(payload) {
  const rows = payload.race_log ?? [];
  profileRaceLogTitleEl.textContent = `${payload.driver_code ?? "Driver"} historical race log`;
  profileRaceLogEl.innerHTML = rows.map((row) => `
    <tr>
      <td>${row.year ?? ""}</td>
      <td>${row.event_name ?? `Round ${row.round ?? ""}`}</td>
      <td>${teamProfileButton(row.constructor_name)}</td>
      <td>${row.grid_position ? `P${fixed(row.grid_position, 0)}` : "TBD"}</td>
      <td>${row.finish_position ? `P${fixed(row.finish_position, 0)}` : "TBD"}</td>
      <td>${fixed(row.points, 1)}</td>
    </tr>
  `).join("") || `<tr><td colspan="6">No race log available.</td></tr>`;
}

function renderProfileCompareShortcuts(code, shortcuts) {
  const teams = [...profileHeroEl.querySelectorAll("[data-open-team]")].map((button) => button.dataset.openTeam);
  const labButtons = teams.map((team) => `<button type="button" data-open-compat-driver="${code}" data-open-compat-team="${team}">Fit with ${team}</button>`).join("");
  const compareButtons = shortcuts.length
    ? shortcuts.map((teammate) => `<button type="button" data-compare-profile="${teammate}">Compare ${code} vs ${teammate}</button>`).join("")
    : `<span class="status">No teammate shortcut yet</span>`;
  const whatIfButtons = shortcuts.length
    ? shortcuts.map((teammate) => `<button type="button" data-open-whatif-a="${code}" data-open-whatif-b="${teammate}">What-if vs ${teammate}</button>`).join("")
    : "";
  profileCompareShortcutsEl.innerHTML = `${labButtons}${whatIfButtons}${compareButtons}`;
}

async function loadCircuitProfile(key = null) {
  circuitLoaded = true;
  const requested = key || circuitKeyEl.value || "current";
  circuitKeyEl.value = requested === "current" ? circuitKeyEl.value : requested;
  circuitHeroEl.textContent = "Loading circuit profile...";
  circuitBehaviorSummaryEl.textContent = "Loading behavior...";
  const url = requested === "current"
    ? "/api/history/circuits/current"
    : `/api/history/circuits/${encodeURIComponent(requested)}`;
  const response = await fetch(url);
  const payload = await response.json();
  renderCircuitProfile(payload);
}

function renderCircuitProfile(payload) {
  const identity = payload.identity ?? {};
  const summary = payload.summary ?? {};
  const leaders = payload.leaders ?? {};
  const metadata = payload.metadata ?? {};
  const coverage = metadata.coverage ?? {};
  circuitKeyEl.value = identity.name ?? payload.circuit_key ?? circuitKeyEl.value;
  circuitCoverageEl.innerHTML = `${coverage.broad_results ?? "Broad result history"}; ${coverage.rich_session_detail ?? "rich modern timing detail when generated"}. ${coverageBadges(metadata)}`;
  circuitHeroEl.innerHTML = `
    <div>
      <span class="profile-code">${identity.track_type ?? "circuit"}</span>
      <h3>${identity.name ?? "Circuit profile"}</h3>
      <p>${identity.event_name ?? "Grand Prix history"} | ${identity.country ?? "Location TBD"}</p>
    </div>
    <div class="profile-stat-grid">
      <div><span>Archive races</span><strong>${identity.races_in_archive ?? 0}</strong></div>
      <div><span>Quali importance</span><strong>${conditionLabel(summary.qualifying_importance)}</strong></div>
      <div><span>Overtaking</span><strong>${conditionLabel(summary.overtaking_difficulty)}</strong></div>
      <div><span>Pit tendency</span><strong>${conditionLabel(summary.pit_stop_tendency)}</strong></div>
      <div><span>Tyre wear</span><strong>${conditionLabel(summary.tyre_wear_tendency)}</strong></div>
      <div><span>Safety car</span><strong>${conditionLabel(summary.safety_car_tendency)}</strong></div>
    </div>
  `;
  circuitBehaviorSummaryEl.innerHTML = `
    <div><span>Pole win rate</span><strong>${summary.pole_win_rate === null || summary.pole_win_rate === undefined ? "TBD" : pct(summary.pole_win_rate)}</strong></div>
    <div><span>Grid movement</span><strong>${fixed(summary.average_grid_to_finish_change, 1)} places</strong></div>
    <div><span>Qualifying</span><strong>${conditionLabel(summary.qualifying_importance)}</strong></div>
    <div><span>Overtaking difficulty</span><strong>${conditionLabel(summary.overtaking_difficulty)}</strong></div>
  `;
  circuitLeaderSummaryEl.innerHTML = `
    <div><span>Wins leader</span><strong>${leaderText(leaders.winners)}</strong></div>
    <div><span>Podium leader</span><strong>${leaderText(leaders.podiums)}</strong></div>
    <div><span>Pole leader</span><strong>${leaderText(leaders.poles)}</strong></div>
    <div><span>Team wins</span><strong>${leaders.teams?.code ? `${teamProfileButton(leaders.teams.code)} (${leaders.teams.count ?? 0})` : "TBD"}</strong></div>
  `;
  renderCircuitTyres(payload.tyre_summary ?? []);
  renderCircuitRecent(payload.recent_races ?? []);
}

function conditionLabel(value) {
  if (!value) return "TBD";
  return String(value).replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function renderCircuitTyres(rows) {
  circuitTyreSummaryEl.innerHTML = rows.length
    ? rows.slice(0, 4).map((row) => `
      <div>
        <span>${row.compound ?? "Tyre"}</span>
        <strong>${fixed(row.total_laps, 0)} laps in archive</strong>
      </div>
    `).join("")
    : `<div><span>Tyres</span><strong>TBD until rich stint data is packaged.</strong></div>`;
}

function renderCircuitRecent(rows) {
  circuitRecentSummaryEl.innerHTML = rows.slice(0, 4).map((row) => `
    <div>
      <span>${row.year} ${row.event_name ?? ""}</span>
      <strong>Winner ${row.winner ?? "TBD"} | Pole ${row.pole ?? "TBD"}</strong>
      <small>Movement ${fixed(row.average_grid_to_finish_change, 1)} places</small>
    </div>
  `).join("") || `<div><span>Recent races</span><strong>TBD</strong></div>`;
  circuitRaceLogTitleEl.textContent = `${circuitKeyEl.value || "Circuit"} race log`;
  circuitRaceLogEl.innerHTML = rows.map((row) => `
    <tr>
      <td>${row.year ?? ""}</td>
      <td>${row.event_name ?? `Round ${row.round ?? ""}`}</td>
      <td>${row.pole ?? "TBD"}</td>
      <td>${row.winner ?? "TBD"}</td>
      <td>${formatDriverCodes(row.podium ?? [])}</td>
      <td>${fixed(row.average_grid_to_finish_change, 1)}</td>
    </tr>
  `).join("") || `<tr><td colspan="6">No circuit race log available.</td></tr>`;
}

async function loadTeamProfile(team = null) {
  teamProfileLoaded = true;
  const requested = team || teamProfileKeyEl.value || historyTeamEl.value || "Mercedes";
  teamProfileKeyEl.value = requested;
  teamProfileHeroEl.textContent = "Loading team profile...";
  teamTrendChartsEl.textContent = "Loading team trends...";
  const response = await fetch(`/api/history/profiles/teams/${encodeURIComponent(requested)}?window=5`);
  const payload = await response.json();
  renderTeamProfile(payload);
}

function renderTeamProfile(payload) {
  const team = payload.team_name ?? teamProfileKeyEl.value ?? "Team";
  const summary = payload.summary ?? {};
  const metadata = payload.metadata ?? {};
  const coverage = metadata.coverage ?? {};
  teamProfileKeyEl.value = team;
  teamProfileCoverageEl.innerHTML = `${coverage.broad_results ?? "Broad result history"}; ${coverage.rich_session_detail ?? "rich modern detail when available"}. ${coverageBadges(metadata)}`;
  teamProfileHeroEl.innerHTML = `
    <div>
      <span class="profile-code">constructor</span>
      <h3>${team}</h3>
      <p>${(summary.drivers ?? []).slice(0, 6).join(" / ") || "Lineup history TBD"}</p>
      <button class="secondary compact-action" type="button" data-open-compat-team="${team}">Open in Compatibility Lab</button>
    </div>
    <div class="profile-stat-grid">
      <div><span>Entries</span><strong>${summary.entries ?? 0}</strong></div>
      <div><span>Wins</span><strong>${summary.wins ?? 0}</strong></div>
      <div><span>Podiums</span><strong>${summary.podiums ?? 0}</strong></div>
      <div><span>Points</span><strong>${fixed(summary.points, 1)}</strong></div>
      <div><span>Avg finish</span><strong>P${fixed(summary.average_finish, 1)}</strong></div>
      <div><span>Latest season</span><strong>${payload.latest_season ?? "TBD"}</strong></div>
    </div>
  `;
  renderTeamTrends(payload);
  renderTeamLineupBalance(payload.current_lineup ?? []);
  renderTeamCircuitStrengths(payload.circuit_strengths ?? []);
  renderTeamLineupHistory(payload.lineup_history ?? []);
  renderTeamRaceLog(payload);
}

function renderTeamTrends(payload) {
  const team = payload.team_name ?? "Team";
  const charts = [
    { key: "rolling_average_finish", label: "Rolling race finish", lower_is_better: true, points: payload.trend_points ?? [] },
    { key: "points", label: "Race points", lower_is_better: false, points: payload.trend_points ?? [] },
    { key: "rolling_average_qualifying", label: "Rolling qualifying", lower_is_better: true, points: payload.qualifying_trend ?? [] },
    { key: "podiums_cumulative", label: "Podium accumulation", lower_is_better: false, points: payload.trend_points ?? [] },
  ];
  teamTrendChartsEl.innerHTML = charts
    .map((chart) => trendChart(chart.label, chart.key, { [team]: chart.points }, [team], chart.lower_is_better))
    .join("");
}

function renderTeamLineupBalance(rows) {
  teamLineupBalanceEl.innerHTML = rows.length
    ? rows.slice(0, 4).map((row) => `
      <div>
        <span>${row.driver_code ?? "Driver"}</span>
        <strong>${fixed(row.points, 1)} pts | avg P${fixed(row.average_finish, 1)}</strong>
        <small>${row.wins ?? 0} wins | ${row.podiums ?? 0} podiums | grid P${fixed(row.average_grid, 1)}</small>
      </div>
    `).join("")
    : `<div><span>Lineup balance</span><strong>TBD</strong></div>`;
}

function renderTeamCircuitStrengths(rows) {
  teamCircuitStrengthsEl.innerHTML = rows.length
    ? rows.slice(0, 6).map((row) => `
      <div>
        <span>${row.circuit ?? "Circuit"}</span>
        <strong>${row.wins ?? 0} wins | ${row.podiums ?? 0} podiums</strong>
        <small>Avg finish P${fixed(row.average_finish, 1)} | ${fixed(row.points, 1)} pts</small>
      </div>
    `).join("")
    : `<div><span>Circuit strengths</span><strong>TBD</strong></div>`;
}

function renderTeamLineupHistory(rows) {
  teamLineupHistoryEl.innerHTML = rows.length
    ? rows.slice(0, 4).map((row) => `
      <div>
        <span>${row.year ?? "Year"}</span>
        <strong>${formatDriverCodes(row.drivers ?? [])}</strong>
      </div>
    `).join("")
    : `<div><span>Lineup history</span><strong>TBD</strong></div>`;
}

function renderTeamRaceLog(payload) {
  const rows = payload.race_log ?? [];
  teamRaceLogTitleEl.textContent = `${payload.team_name ?? "Team"} race log`;
  teamRaceLogEl.innerHTML = rows.map((row) => `
    <tr>
      <td>${row.year ?? ""}</td>
      <td>${row.round ?? ""}</td>
      <td>${row.driver_code ?? ""}</td>
      <td>${row.grid_position ? `P${fixed(row.grid_position, 0)}` : "TBD"}</td>
      <td>${row.finish_position ? `P${fixed(row.finish_position, 0)}` : "TBD"}</td>
      <td>${fixed(row.points, 1)}</td>
    </tr>
  `).join("") || `<tr><td colspan="6">No team race log available.</td></tr>`;
}

async function loadCompatibility(driver = null, team = null) {
  compatibilityLoaded = true;
  const driverCode = (driver || compatDriverEl.value || profileDriverEl.value || "ANT").trim().toUpperCase();
  const teamName = team || compatTeamEl.value || teamProfileKeyEl.value || "Mercedes";
  compatDriverEl.value = driverCode;
  compatTeamEl.value = teamName;
  setUrlState({ section: "lab", driver: driverCode, team: teamName });
  compatibilityHeroEl.textContent = "Loading compatibility evidence...";
  compatibilityComponentsEl.textContent = "Loading fit dimensions...";
  const response = await fetch(`/api/lab/compatibility/driver-team?driver_code=${encodeURIComponent(driverCode)}&team_name=${encodeURIComponent(teamName)}`);
  const payload = await response.json();
  renderCompatibility(payload);
}

function renderCompatibility(payload) {
  const driver = payload.driver ?? {};
  const team = payload.team ?? {};
  const score = payload.compatibility_score;
  const confidence = payload.confidence ?? "low";
  const metadata = payload.metadata ?? {};
  const coverage = metadata.coverage ?? {};
  compatCoverageEl.innerHTML = `${coverage.broad_results ?? "Broad result history"}; ${coverage.rich_session_detail ?? "rich modern detail when available"}. ${coverageBadges(metadata)}`;
  compatibilityHeroEl.innerHTML = `
    <div>
      <span class="profile-code">driver-to-team fit</span>
      <h3>${driver.code ?? "DRI"} -> ${team.name ?? "Team"}</h3>
      <p>${driver.name ?? driver.code ?? "Driver"} measured against ${team.name ?? "constructor"} evidence.</p>
    </div>
    <div class="profile-stat-grid">
      <div><span>Compatibility</span><strong>${score === null || score === undefined ? "TBD" : `${Number(score).toFixed(1)}`}</strong></div>
      <div><span>Confidence</span><strong>${conditionLabel(confidence)}</strong></div>
      <div><span>Evidence fields</span><strong>${payload.evidence_count ?? 0}</strong></div>
      <div><span>TBD fields</span><strong>${payload.tbd_count ?? 0}</strong></div>
      <div><span>Driver starts</span><strong>${driver.summary?.starts ?? 0}</strong></div>
      <div><span>Team entries</span><strong>${team.summary?.entries ?? 0}</strong></div>
    </div>
  `;
  renderCompatibilityComponents(payload.components ?? []);
  renderCompatibilityContext(payload);
  renderCompatibilityNotes(payload);
}

function renderCompatibilityComponents(components) {
  compatibilityComponentsEl.innerHTML = components.length
    ? components.map((component) => compatibilityComponentCard(component)).join("")
    : `<article class="rating-card"><h3>Fit dimensions</h3><p>TBD</p></article>`;
}

function compatibilityComponentCard(component) {
  const score = component.score === null || component.score === undefined ? null : Number(component.score);
  const width = Number.isFinite(score) ? Math.max(0, Math.min(100, score)) : 0;
  return `
    <article class="rating-card compatibility-card">
      <h3>${component.label ?? "Dimension"}</h3>
      <div class="rating-row">
        <span>Fit score</span>
        <strong>${Number.isFinite(score) ? score.toFixed(1) : "TBD"}</strong>
        <i style="width:${width}%"></i>
      </div>
      <small>Driver ${component.driver_score ?? "TBD"} | Team ${component.team_score ?? "TBD"}</small>
      <p>${component.note ?? "Evidence note pending."}</p>
    </article>
  `;
}

function renderCompatibilityContext(payload) {
  const driver = payload.driver ?? {};
  const team = payload.team ?? {};
  const lineup = team.current_lineup ?? [];
  compatibilityContextEl.innerHTML = `
    <div><span>Driver recent form</span><strong>Avg finish ${fixed(driver.recent_form?.average_finish, 1)}</strong></div>
    <div><span>Driver podiums</span><strong>${driver.summary?.podiums ?? 0}</strong></div>
    <div><span>Team lineup</span><strong>${formatDriverCodes(lineup.map((row) => row.driver_code).filter(Boolean))}</strong></div>
    <div><span>Team podiums</span><strong>${team.summary?.podiums ?? 0}</strong></div>
  `;
}

function renderCompatibilityNotes(payload) {
  compatibilityLinksEl.innerHTML = `
    <button type="button" data-open-driver="${payload.driver?.code ?? "ANT"}">Driver profile</button>
    <button type="button" data-open-team="${payload.team?.name ?? "Mercedes"}">Team profile</button>
    <button type="button" data-share-compatibility>Copy share link</button>
  `;
  compatibilityExplainEl.innerHTML = explanationList("Why this fit?", payload.components ?? [], "score");
  compatibilityNotesEl.innerHTML = (payload.notes ?? []).map((note) => `
    <div>
      <span>Lab note</span>
      <strong>${note}</strong>
    </div>
  `).join("");
}

async function loadWhatIfMatchup() {
  whatIfLoaded = true;
  const driverA = (whatIfDriverAEl.value || "ANT").trim().toUpperCase();
  const driverB = (whatIfDriverBEl.value || "VER").trim().toUpperCase();
  const circuit = whatIfCircuitEl.value || "current";
  const session = whatIfSessionEl.value || "race";
  const condition = whatIfConditionEl.value || "dry";
  setUrlState({ section: "what-if", a: driverA, b: driverB, circuit, session, condition });
  whatIfHeroEl.textContent = "Running simulated matchup...";
  whatIfDimensionsEl.textContent = "Loading matchup evidence...";
  const response = await fetch(
    `/api/lab/what-if/driver-matchup?driver_a=${encodeURIComponent(driverA)}&driver_b=${encodeURIComponent(driverB)}&circuit=${encodeURIComponent(circuit)}&session_type=${encodeURIComponent(session)}&condition=${encodeURIComponent(condition)}`,
  );
  const payload = await response.json();
  renderWhatIfMatchup(payload);
}

function renderWhatIfMatchup(payload) {
  const matchup = payload.matchup ?? {};
  const driverA = matchup.driver_a ?? {};
  const driverB = matchup.driver_b ?? {};
  const circuit = matchup.circuit ?? {};
  const metadata = payload.metadata ?? {};
  const coverage = metadata.coverage ?? {};
  const edge = payload.matchup_edge;
  whatIfCoverageEl.innerHTML = `${coverage.broad_results ?? "Broad result history"}; ${coverage.rich_session_detail ?? "rich modern detail when available"}. ${coverageBadges(metadata)}`;
  whatIfHeroEl.innerHTML = `
    <div>
      <span class="profile-code">simulated matchup</span>
      <h3>${driverA.code ?? "A"} vs ${driverB.code ?? "B"}</h3>
      <p>${conditionLabel(matchup.condition)} ${conditionLabel(matchup.session_type)} at ${circuit.name ?? "selected circuit"}.</p>
    </div>
    <div class="profile-stat-grid">
      <div><span>Projected edge</span><strong>${payload.winner_edge ?? "Toss-up"}</strong></div>
      <div><span>Edge value</span><strong>${edge === null || edge === undefined ? "TBD" : `${Number(edge).toFixed(1)} pts`}</strong></div>
      <div><span>Confidence</span><strong>${conditionLabel(payload.confidence)}</strong></div>
      <div><span>Evidence fields</span><strong>${payload.evidence_count ?? 0}</strong></div>
      <div><span>TBD fields</span><strong>${payload.tbd_count ?? 0}</strong></div>
      <div><span>Track type</span><strong>${conditionLabel(circuit.track_type)}</strong></div>
    </div>
  `;
  renderWhatIfDimensions(payload.dimensions ?? [], driverA.code ?? "A", driverB.code ?? "B");
  renderWhatIfContext(payload);
  renderWhatIfNotes(payload);
}

function renderWhatIfDimensions(dimensions, driverA, driverB) {
  whatIfDimensionsEl.innerHTML = dimensions.length
    ? dimensions.map((dimension) => whatIfDimensionCard(dimension, driverA, driverB)).join("")
    : `<article class="rating-card"><h3>Matchup dimensions</h3><p>TBD</p></article>`;
}

function whatIfDimensionCard(dimension, driverA, driverB) {
  const edge = dimension.edge === null || dimension.edge === undefined ? null : Number(dimension.edge);
  const width = Number.isFinite(edge) ? Math.max(0, Math.min(100, 50 + edge / 2)) : 50;
  const leader = !Number.isFinite(edge) ? "TBD" : edge > 0 ? driverA : edge < 0 ? driverB : "Even";
  return `
    <article class="rating-card compatibility-card">
      <h3>${dimension.label ?? "Dimension"}</h3>
      <div class="matchup-bar">
        <span>${driverB}</span>
        <i style="--edge:${width}%"></i>
        <span>${driverA}</span>
      </div>
      <strong>${leader} ${Number.isFinite(edge) ? `+${Math.abs(edge).toFixed(1)}` : "TBD"}</strong>
      <small>${driverA} ${dimension.driver_a_score ?? "TBD"} | ${driverB} ${dimension.driver_b_score ?? "TBD"} | weight ${dimension.weight ?? "TBD"}</small>
      <p>${dimension.note ?? "Evidence note pending."}</p>
    </article>
  `;
}

function renderWhatIfContext(payload) {
  const matchup = payload.matchup ?? {};
  const driverA = matchup.driver_a ?? {};
  const driverB = matchup.driver_b ?? {};
  const circuit = matchup.circuit ?? {};
  whatIfContextEl.innerHTML = `
    <div><span>${driverA.code ?? "A"} starts</span><strong>${driverA.summary?.starts ?? 0}</strong></div>
    <div><span>${driverB.code ?? "B"} starts</span><strong>${driverB.summary?.starts ?? 0}</strong></div>
    <div><span>Circuit</span><strong>${circuit.name ?? "TBD"}</strong></div>
    <div><span>Session</span><strong>${conditionLabel(matchup.session_type)}</strong></div>
  `;
}

function renderWhatIfNotes(payload) {
  const matchup = payload.matchup ?? {};
  whatIfLinksEl.innerHTML = `
    <button type="button" data-open-driver="${matchup.driver_a?.code ?? "ANT"}">${matchup.driver_a?.code ?? "A"} profile</button>
    <button type="button" data-open-driver="${matchup.driver_b?.code ?? "VER"}">${matchup.driver_b?.code ?? "B"} profile</button>
    <button type="button" data-open-circuit="${matchup.circuit?.name ?? "current"}">Circuit profile</button>
    <button type="button" data-share-whatif>Copy share link</button>
  `;
  whatIfExplainEl.innerHTML = explanationList("Why this edge?", payload.dimensions ?? [], "edge");
  whatIfNotesEl.innerHTML = (payload.uncertainty_notes ?? []).map((note) => `
    <div>
      <span>Simulator note</span>
      <strong>${note}</strong>
    </div>
  `).join("");
}

function explanationList(title, rows, valueKey) {
  const top = rows
    .filter((row) => row[valueKey] !== null && row[valueKey] !== undefined && Number.isFinite(Number(row[valueKey])))
    .sort((a, b) => Math.abs(Number(b[valueKey])) - Math.abs(Number(a[valueKey])))
    .slice(0, 3);
  if (!top.length) {
    return `<strong>${title}</strong><p>Evidence is too thin to identify top contributors.</p>`;
  }
  return `
    <strong>${title}</strong>
    <p>${top
      .map((row) => `${row.label}: ${Number(row[valueKey]).toFixed(1)}`)
      .join(" | ")}</p>
  `;
}

function renderDriverRatings(ratings) {
  const entries = Object.entries(ratings);
  if (!entries.length) {
    driverRatingSummaryEl.innerHTML = `<div class="empty-state"><strong>Ratings are not ready for this selection.</strong><p>The app keeps weak evidence as TBD instead of inventing a score.</p></div>`;
    return;
  }
  driverRatingSummaryEl.innerHTML = entries
    .map(([driver, values]) => `
      <article class="rating-card">
        <h3>${driver}</h3>
        ${Object.entries(values)
          .filter(([key]) => key !== "overall_evidence_score")
          .map(([key, value]) => ratingBar(metricLabel(key), value))
          .join("")}
        ${ratingBar("Evidence score", values.overall_evidence_score)}
      </article>
    `)
    .join("");
}

function ratingBar(label, value) {
  const number = value === null || value === undefined ? NaN : Number(value);
  const width = Number.isFinite(number) ? Math.max(0, Math.min(100, number)) : 0;
  return `
    <div class="rating-row">
      <span>${label}</span>
      <strong>${Number.isFinite(number) ? number.toFixed(1) : "TBD"}</strong>
      <i style="width:${width}%"></i>
    </div>
  `;
}

function metricLabel(metric) {
  return String(metric)
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function metricValue(value, metric) {
  if (value === null || value === undefined) return "TBD";
  if (String(metric).includes("rate")) return `${Math.round(Number(value) * 100)}%`;
  return Number.isFinite(Number(value)) ? Number(value).toFixed(String(metric).includes("average") ? 2 : 0) : value;
}

async function loadGeekReports() {
  const [backtestResponse, calibrationResponse, benchmarkResponse] = await Promise.all([
    fetch("/api/reports/backtest"),
    fetch("/api/reports/podium-calibration"),
    fetch("/api/benchmarks/monaco-2026"),
  ]);
  const backtest = backtestResponse.ok ? await backtestResponse.json() : { summary: {}, worst_windows: [] };
  const calibration = calibrationResponse.ok ? await calibrationResponse.json() : { rows: [] };
  const benchmark = benchmarkResponse.ok ? await benchmarkResponse.json() : {};
  renderMetrics(racePayload?.metadata ?? {}, backtest);
  renderReliability(calibration.rows ?? []);
  renderDiagnostics(backtest.worst_windows ?? []);
  renderBenchmark(benchmark);
}

async function loadPredictions() {
  refreshButton.disabled = true;
  statusEl.textContent = "Loading forecast...";
  try {
    const [weekendResponse, raceResponse, qualifyingResponse] = await Promise.all([
      fetch("/api/weekend/current"),
      fetch("/api/predictions/race/post-quali/next"),
      fetch("/api/predictions/qualifying/next"),
    ]);
    const statesResponse = await fetch("/api/forecast-states");
    weekendPayload = await weekendResponse.json();
    const candidateRacePayload = await raceResponse.json();
    racePayload = candidateRacePayload.predictions?.length
      ? candidateRacePayload
      : await (await fetch("/api/predictions/race/next")).json();
    qualifyingPayload = await qualifyingResponse.json();
    statesPayload = statesResponse.ok ? await statesResponse.json() : { states: [] };
    if (!weekendResponse.ok || !raceResponse.ok || !qualifyingResponse.ok) {
      throw new Error("Failed to load weekend forecast");
    }
    renderRace(weekendPayload.race);
    renderMetadata(racePayload.metadata ?? {}, weekendPayload);
    renderSessions(weekendPayload);
    renderBasicNote(racePayload.metadata ?? {}, weekendPayload);
    renderForecastStates(statesPayload);
    renderSynthesisCards();
    renderForecastTables();
    if (activeMode === "geek") await loadGeekReports();
    statusEl.textContent = `Updated ${new Date().toLocaleTimeString()} - ${racePayload.metadata?.prediction_mode ?? "pre-weekend forecast"}`;
  } catch (error) {
    raceEl.innerHTML = `<div class="empty-state"><strong>Prediction data unavailable.</strong><p>The app could not load the packaged forecast snapshot. ${error.message}</p></div>`;
    metadataEl.innerHTML = `<span>Metadata missing: refresh the demo export or check the prediction API.</span>`;
    sessionsEl.innerHTML = `<div class="empty-state"><strong>Schedule and weather unavailable.</strong><p>Weekend cards need the current weekend artifact or a live API response.</p></div>`;
    predictionsEl.innerHTML = `<tr><td colspan="7">${emptyTableMessage("Forecast table could not load", error.message)}</td></tr>`;
    geekPredictionsEl.innerHTML = `<tr><td colspan="10">${emptyTableMessage("Geek forecast table could not load", error.message)}</td></tr>`;
    statusEl.textContent = "Run ingestion, feature generation, and training first.";
  } finally {
    refreshButton.disabled = false;
  }
}

refreshButton.addEventListener("click", loadPredictions);
basicModeButton.addEventListener("click", () => setMode("basic"));
geekModeButton.addEventListener("click", () => setMode("geek"));
qualifyingTab.addEventListener("click", () => setForecastTab("qualifying"));
raceTab.addEventListener("click", () => setForecastTab("race"));
productTabs.forEach((button) => button.addEventListener("click", () => setProductSection(button.dataset.section)));
historySeasonEl.addEventListener("change", () => loadHistoryYear(Number(historySeasonEl.value)));
historyRacesEl.addEventListener("click", (event) => {
  const button = event.target.closest("[data-year][data-round]");
  if (button) loadHistoryRace(Number(button.dataset.year), Number(button.dataset.round));
});
historyDriverEl.addEventListener("change", loadHistoryDriver);
historyTeamEl.addEventListener("change", loadHistoryTeam);
compareDriversButton.addEventListener("click", loadDriverCompare);
loadProfileButton.addEventListener("click", loadDriverProfile);
profileDriverEl.addEventListener("change", loadDriverProfile);
loadCircuitButton.addEventListener("click", () => loadCircuitProfile(circuitKeyEl.value));
circuitKeyEl.addEventListener("change", () => loadCircuitProfile(circuitKeyEl.value));
loadTeamProfileButton.addEventListener("click", () => loadTeamProfile(teamProfileKeyEl.value));
teamProfileKeyEl.addEventListener("change", () => loadTeamProfile(teamProfileKeyEl.value));
document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-open-circuit]");
  if (!button) return;
  circuitKeyEl.value = button.dataset.openCircuit;
  setProductSection("circuits");
  loadCircuitProfile(button.dataset.openCircuit);
});
document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-open-team]");
  if (!button) return;
  teamProfileKeyEl.value = button.dataset.openTeam;
  setProductSection("teams");
  loadTeamProfile(button.dataset.openTeam);
});
document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-open-driver]");
  if (!button) return;
  profileDriverEl.value = button.dataset.openDriver;
  setProductSection("driver-ratings");
  loadDriverProfile();
});
document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-open-compat-team], [data-open-compat-driver]");
  if (!button) return;
  const driver = button.dataset.openCompatDriver || compatDriverEl.value || profileDriverEl.value || "ANT";
  const team = button.dataset.openCompatTeam || compatTeamEl.value || teamProfileKeyEl.value || "Mercedes";
  compatDriverEl.value = driver;
  compatTeamEl.value = team;
  setProductSection("lab");
  loadCompatibility(driver, team);
});
document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-open-whatif-a], [data-open-whatif-b]");
  if (!button) return;
  whatIfDriverAEl.value = button.dataset.openWhatifA || whatIfDriverAEl.value || "ANT";
  whatIfDriverBEl.value = button.dataset.openWhatifB || whatIfDriverBEl.value || "VER";
  setProductSection("what-if");
  loadWhatIfMatchup();
});
document.addEventListener("click", async (event) => {
  const compatibilityShare = event.target.closest("[data-share-compatibility]");
  const whatIfShare = event.target.closest("[data-share-whatif]");
  if (compatibilityShare) {
    await copyShareUrl({ section: "lab", driver: compatDriverEl.value, team: compatTeamEl.value });
    compatibilityShare.textContent = "Copied";
  }
  if (whatIfShare) {
    await copyShareUrl({
      section: "what-if",
      a: whatIfDriverAEl.value,
      b: whatIfDriverBEl.value,
      circuit: whatIfCircuitEl.value,
      session: whatIfSessionEl.value,
      condition: whatIfConditionEl.value,
    });
    whatIfShare.textContent = "Copied";
  }
});
profileCompareShortcutsEl.addEventListener("click", (event) => {
  const button = event.target.closest("[data-compare-profile]");
  if (!button) return;
  compareDriverAEl.value = (profileDriverEl.value || "ANT").trim().toUpperCase();
  compareDriverBEl.value = button.dataset.compareProfile;
  setProductSection("history");
  loadDriverCompare();
});
runCompatibilityButton.addEventListener("click", () => loadCompatibility());
compatDriverEl.addEventListener("change", () => loadCompatibility());
compatTeamEl.addEventListener("change", () => loadCompatibility());
runWhatIfButton.addEventListener("click", loadWhatIfMatchup);
whatIfDriverAEl.addEventListener("change", loadWhatIfMatchup);
whatIfDriverBEl.addEventListener("change", loadWhatIfMatchup);
whatIfCircuitEl.addEventListener("change", loadWhatIfMatchup);
whatIfSessionEl.addEventListener("change", loadWhatIfMatchup);
whatIfConditionEl.addEventListener("change", loadWhatIfMatchup);
languageSelect.addEventListener("change", () => {
  activeLanguage = languageSelect.value;
  localStorage.setItem("f1-language", activeLanguage);
  applyPreferences();
});
unitSelect.addEventListener("change", () => {
  activeUnits = unitSelect.value;
  localStorage.setItem("f1-units", activeUnits);
  applyPreferences();
});
modelCardOpen.addEventListener("click", () => modelCard.showModal());
modelCardClose.addEventListener("click", () => modelCard.close());
tourOpenButton.addEventListener("click", () => openTour(0));
tourNextButton.addEventListener("click", advanceTour);
tourSkipButton.addEventListener("click", () => closeTour(true));
tourOverlay.addEventListener("click", (event) => {
  if (event.target === tourOverlay) closeTour(true);
});
setMode("basic");
const params = initialParams();
if (params.get("section") === "lab") {
  compatDriverEl.value = params.get("driver") || compatDriverEl.value;
  compatTeamEl.value = params.get("team") || compatTeamEl.value;
  setProductSection("lab");
} else if (params.get("section") === "what-if") {
  whatIfDriverAEl.value = params.get("a") || whatIfDriverAEl.value;
  whatIfDriverBEl.value = params.get("b") || whatIfDriverBEl.value;
  whatIfCircuitEl.value = params.get("circuit") || whatIfCircuitEl.value;
  whatIfSessionEl.value = params.get("session") || whatIfSessionEl.value;
  whatIfConditionEl.value = params.get("condition") || whatIfConditionEl.value;
  setProductSection("what-if");
} else {
  setProductSection("race-hub");
}
applyPreferences();
loadPredictions();
if (!localStorage.getItem("f1-tour-seen") && !params.get("section")) {
  window.setTimeout(() => openTour(0), 1000);
}
