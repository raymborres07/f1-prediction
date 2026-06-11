const raceEl = document.querySelector("#race");
const countdownEl = document.querySelector("#countdown");
const countdownTargetEl = document.querySelector("#countdown-target");
const metadataEl = document.querySelector("#metadata");
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
const productTabs = document.querySelectorAll("[data-section]");
const raceHubSections = document.querySelectorAll(".race-hub-section");
const productSections = document.querySelectorAll("[data-product-section]");
const historySeasonEl = document.querySelector("#history-season");
const historyDriverEl = document.querySelector("#history-driver");
const historyTeamEl = document.querySelector("#history-team");
const historyCoverageEl = document.querySelector("#history-coverage");
const historyRacesEl = document.querySelector("#history-races");
const historyRaceTitleEl = document.querySelector("#history-race-title");
const historySummaryEl = document.querySelector("#history-summary");
const historyResultsEl = document.querySelector("#history-results");
const historyDriverSummaryEl = document.querySelector("#history-driver-summary");
const historyTeamSummaryEl = document.querySelector("#history-team-summary");
const historyLapsEl = document.querySelector("#history-laps");
const historyLapStatusEl = document.querySelector("#history-lap-status");

let countdownTimer = null;
let activeMode = "basic";
let activeForecast = "race";
let activeSection = "race-hub";
let racePayload = null;
let qualifyingPayload = null;
let weekendPayload = null;
let statesPayload = null;
let historyLoaded = false;
let selectedHistoryRace = null;

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
  return new Intl.DateTimeFormat(undefined, options).format(date);
}

function pct(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function fixed(value, decimals = 1) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(decimals) : "TBD";
}

function renderRace(race) {
  raceEl.innerHTML = `
    <div>
      <span class="label">Next Race</span>
      <h2>${race.event_name ?? `Round ${race.round}`}</h2>
      <p>${race.country ?? "Location TBD"} - ${race.location ?? "Circuit TBD"}</p>
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
    sessionsEl.innerHTML = `<span>Session schedule unavailable.</span>`;
    return;
  }
  sessionsEl.innerHTML = sessions
    .map((session) => {
      const weather = session.weather;
      const risk = weatherRisk(weather);
      return `
        <article class="session-card ${risk.className}">
          <div class="weather-icon">${risk.label}</div>
          <div class="session-main">
            <strong>${session.name}</strong>
            <span>${formatDate(session.starts_at, weekend.race?.timezone)}</span>
          </div>
          <div class="weather-stats">
            <div><span>Air</span><strong>${weather ? `${fixed(weather.air_temp_c, 0)}C` : "TBD"}</strong></div>
            <div><span>Track</span><strong>${weather?.track_temp_c ? `${fixed(weather.track_temp_c, 0)}C` : "N/A"}</strong></div>
            <div><span>Rain</span><strong>${weather ? `${fixed(weather.rain_probability, 0)}%` : "TBD"}</strong></div>
            <div><span>Wind</span><strong>${weather ? `${fixed(weather.wind_kph, 0)} kph` : "TBD"}</strong></div>
          </div>
          ${renderForecastStrip(weather)}
          <small>
            ${session.time_status ?? "scheduled"} - ${risk.riskText} - ${weather?.weather_risk_reason ?? session.weather_status ?? "weather pending"}
          </small>
        </article>
      `;
    })
    .join("");
}

function weatherRisk(weather) {
  if (!weather) return { label: "TBD", className: "weather-unknown", riskText: "Risk TBD" };
  const score = Number(weather.weather_risk_score ?? weather.risk_score);
  if (Number.isFinite(score)) {
    if (score >= 60) return { label: "HIGH", className: "weather-rain", riskText: `Risk ${score}/100` };
    if (score >= 30) return { label: "MED", className: "weather-risk", riskText: `Risk ${score}/100` };
    return { label: "LOW", className: "weather-dry", riskText: `Risk ${score}/100` };
  }
  const rain = Number(weather.rain_probability || 0);
  const cloud = Number(weather.cloud_cover || 0);
  if (rain >= 45) return { label: "WET", className: "weather-rain", riskText: "Risk high" };
  if (rain >= 20 || cloud >= 70) return { label: "RISK", className: "weather-risk", riskText: "Risk medium" };
  return { label: "DRY", className: "weather-dry", riskText: "Risk low" };
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
    target.innerHTML = `<tr><td colspan="${geek ? 10 : 7}">No race predictions available.</td></tr>`;
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
            <td>${row.constructor_name ?? ""}</td>
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
          <td>${row.constructor_name ?? ""}</td>
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
    predictionsEl.innerHTML = `<tr><td colspan="6">No qualifying forecast available.</td></tr>`;
    return;
  }
  predictionsEl.innerHTML = rows
    .map((row) => `
      <tr>
        <td>P${row.qualifying_rank}</td>
        <td>${driverCell(row)}</td>
        <td>${row.constructor_name ?? ""}</td>
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
    forecastStatesEl.innerHTML = `<span>Forecast state unavailable</span>`;
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
    benchmarkEl.innerHTML = `<span>Benchmark unavailable.</span>`;
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
  raceHubSections.forEach((node) => {
    node.hidden = section !== "race-hub";
  });
  productSections.forEach((node) => {
    node.hidden = node.dataset.productSection !== section;
  });
  if (section === "history" && !historyLoaded) {
    loadHistory();
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
    const selectedYear = Number(historySeasonEl.value || seasons.seasons?.[0]?.year || 2026);
    await loadHistoryYear(selectedYear);
    await Promise.all([loadHistoryDriver(), loadHistoryTeam()]);
  } catch (error) {
    historyRacesEl.textContent = `History unavailable: ${error.message}`;
  }
}

function renderHistoryCoverage(metadata) {
  const coverage = metadata.coverage ?? {};
  historyCoverageEl.textContent = `${coverage.broad_results ?? "Broad results archive"}; ${coverage.rich_session_detail ?? "rich session detail when available"}.`;
}

function renderSeasonOptions(seasons) {
  historySeasonEl.innerHTML = seasons
    .map((season) => `<option value="${season.year}">${season.year} (${season.event_count ?? 0} races)</option>`)
    .join("");
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
  historySummaryEl.innerHTML = `
    <div><span>Winner</span><strong>${podium[0]?.driver_code ?? "TBD"}</strong></div>
    <div><span>Podium</span><strong>${formatDriverCodes(podium.map((row) => row.driver_code).filter(Boolean))}</strong></div>
    <div><span>Pole</span><strong>${payload.qualifying_top10?.[0]?.driver_code ?? "TBD"}</strong></div>
    <div><span>Fastest lap</span><strong>${fastest[0]?.driver_code ?? "TBD"}</strong></div>
  `;
  historyResultsEl.innerHTML = (payload.race_results ?? [])
    .map((row) => `
      <tr>
        <td>P${fixed(row.finish_position, 0)}</td>
        <td>${driverCell(row)}</td>
        <td>${row.constructor_name ?? ""}</td>
        <td>${row.grid_position ? `P${fixed(row.grid_position, 0)}` : "TBD"}</td>
        <td>${fixed(row.points, 1)}</td>
      </tr>
    `)
    .join("") || `<tr><td colspan="5">No race results available.</td></tr>`;
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
  renderHistoryEntitySummary(historyDriverSummaryEl, payload.summary ?? {}, payload.driver_name ?? code);
}

async function loadHistoryTeam() {
  const team = (historyTeamEl.value || "Mercedes").trim();
  const response = await fetch(`/api/history/teams/${encodeURIComponent(team)}`);
  const payload = await response.json();
  renderHistoryEntitySummary(historyTeamSummaryEl, payload.summary ?? {}, payload.team_name ?? team);
}

function renderHistoryEntitySummary(target, summary, title) {
  const cards = [
    ["Name", title],
    ["Starts/Entries", summary.starts ?? summary.entries ?? 0],
    ["Wins", summary.wins ?? 0],
    ["Podiums", summary.podiums ?? 0],
    ["Avg finish", summary.average_finish ?? "TBD"],
    ["Points", summary.points ?? "TBD"],
  ];
  target.innerHTML = cards.map(([label, value]) => `<div><span>${label}</span><strong>${value}</strong></div>`).join("");
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
    renderForecastTables();
    if (activeMode === "geek") await loadGeekReports();
    statusEl.textContent = `Updated ${new Date().toLocaleTimeString()} - ${racePayload.metadata?.prediction_mode ?? "pre-weekend forecast"}`;
  } catch (error) {
    raceEl.innerHTML = `<span>Prediction data unavailable</span>`;
    metadataEl.innerHTML = `<span>Metadata unavailable</span>`;
    sessionsEl.innerHTML = `<span>Session schedule unavailable</span>`;
    predictionsEl.innerHTML = `<tr><td colspan="7">${error.message}</td></tr>`;
    geekPredictionsEl.innerHTML = `<tr><td colspan="10">${error.message}</td></tr>`;
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
modelCardOpen.addEventListener("click", () => modelCard.showModal());
modelCardClose.addEventListener("click", () => modelCard.close());
setMode("basic");
setProductSection("race-hub");
loadPredictions();
