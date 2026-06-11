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
const statusEl = document.querySelector("#status");
const refreshButton = document.querySelector("#refresh");

let countdownTimer = null;

function formatDate(value) {
  if (!value || value === "NaT") return "TBD";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "TBD";
  return new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function pct(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function fixed(value, decimals = 1) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(decimals) : "TBD";
}

function renderRace(race, hub = {}) {
  const details = hub.race ?? race ?? {};
  const raceStart = new Date(details.race_date ?? race?.race_date);
  const raceLabel = raceStart.getTime() && raceStart.getTime() < Date.now() ? "Latest Forecast" : "Next Race";
  raceEl.innerHTML = `
    <div>
      <span class="label">${raceLabel}</span>
      <h2>${details.event_name ?? race?.event_name ?? `Round ${race?.round ?? ""}`}</h2>
      <p>${details.country ?? race?.country ?? "Location TBD"} · ${details.location ?? race?.location ?? "Circuit TBD"}</p>
    </div>
    <dl class="race-facts">
      <div><dt>Circuit</dt><dd>${details.circuit ?? details.location ?? "TBD"}</dd></div>
      <div><dt>Round</dt><dd>${details.year ?? race?.year} · ${details.round ?? race?.round}</dd></div>
      <div><dt>Race</dt><dd>${formatDate(details.race_date ?? race?.race_date)}</dd></div>
    </dl>
  `;
  startCountdown(details.race_date ?? race?.race_date);
}

function startCountdown(raceDate) {
  if (countdownTimer) clearInterval(countdownTimer);
  const target = new Date(raceDate);
  countdownTargetEl.textContent = `Race start · ${formatDate(raceDate)}`;
  if (!raceDate || Number.isNaN(target.getTime())) {
    countdownEl.textContent = "TBD";
    return;
  }
  const update = () => {
    const ms = target.getTime() - Date.now();
    if (ms <= 0) {
      countdownEl.textContent = "Completed";
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

function renderMetadata(metadata) {
  const model = metadata.model ?? {};
  const dataset = metadata.dataset ?? {};
  const simulation = metadata.simulation ?? {};
  const data = metadata.data_included ?? {};
  const updatedAt = simulation.built_at_utc ?? model.trained_at_utc;
  const chips = [
    data.practice ? "Practice included" : "Practice pending",
    data.qualifying ? "Qualifying included" : "Qualifying not yet included",
    data.upgrade_news ? "Upgrade news included" : "Upgrade news pending",
  ];
  metadataEl.innerHTML = `
    <span><strong>${metadata.prediction_mode ?? "pre-race forecast"}</strong></span>
    <span>Updated from ${updatedAt ? formatDate(updatedAt) : "unknown timestamp"}</span>
    <span>Dataset ${dataset.dataset_version ?? model.dataset_version ?? simulation.rich_dataset ?? "unknown"}</span>
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

function renderSessions(hub) {
  const sessions = hub.sessions ?? [];
  weatherNoteEl.textContent = hub.weather_note ?? "Weather shown when available.";
  if (!sessions.length) {
    sessionsEl.innerHTML = `<span>Session schedule unavailable.</span>`;
    return;
  }
  sessionsEl.innerHTML = sessions
    .map((session) => {
      const weather = session.weather
        ? `${fixed(session.weather.air_temp_c, 0)}C air · ${fixed(session.weather.track_temp_c, 0)}C track · rain ${fixed(session.weather.rainfall, 1)}`
        : "Weather TBD";
      return `
        <article class="session-card">
          <div>
            <strong>${session.name}</strong>
            <span>${formatDate(session.starts_at)}</span>
          </div>
          <p>${weather}</p>
          <small>${session.time_status ?? "scheduled"} · ${session.weather_status ?? "weather pending"}</small>
        </article>
      `;
    })
    .join("");
}

function renderPredictions(predictions) {
  if (!predictions.length) {
    predictionsEl.innerHTML = `<tr><td colspan="10">No predictions available.</td></tr>`;
    return;
  }

  predictionsEl.innerHTML = predictions
    .map((row) => {
      const gridValue = row.grid_position ?? row.qualifying_position;
      const gridNumber = Number(gridValue);
      const grid = Number.isFinite(gridNumber) && gridNumber > 0 ? `P${gridNumber.toFixed(0)}` : "TBD";
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
    })
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
  return parts.join(" · ") || "Form TBD";
}

function finishBandFromDistribution(row) {
  const probabilities = Object.entries(row)
    .filter(([key]) => /^p\d+_probability$/.test(key))
    .map(([key, value]) => [Number(key.match(/\d+/)[0]), Number(value || 0)])
    .sort((a, b) => a[0] - b[0]);
  let cumulative = 0;
  let low = null;
  let high = null;
  for (const [position, probability] of probabilities) {
    cumulative += probability;
    if (low === null && cumulative >= 0.1) low = position;
    if (high === null && cumulative >= 0.9) high = position;
  }
  return { low, high };
}

function mergeSimulationPredictions(predictions, simulation) {
  const simulated = simulation.predictions ?? [];
  if (!simulated.length) return predictions;
  const distributions = new Map((simulation.finish_distributions ?? []).map((row) => [row.driver_code, row]));
  const byDriver = new Map(simulated.map((row) => [row.driver_code, row]));
  return predictions
    .map((row) => {
      const sim = byDriver.get(row.driver_code);
      if (!sim) return row;
      const band = finishBandFromDistribution(distributions.get(row.driver_code) ?? {});
      return {
        ...row,
        prediction_rank: sim.simulation_rank ?? row.prediction_rank,
        win_probability: sim.win_probability,
        podium_probability: sim.podium_probability,
        top10_probability: sim.top10_probability,
        expected_finish: sim.expected_finish,
        finish_low: band.low ?? row.finish_low,
        finish_high: band.high ?? row.finish_high,
      };
    })
    .sort((a, b) => Number(a.prediction_rank) - Number(b.prediction_rank));
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
        <span>${row.diagnostic_reason ?? "weak window"} · Brier ${Number(row.podium_brier).toFixed(3)} · MAE ${Number(row.finish_mae).toFixed(2)}</span>
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
    <ol class="replay-list">
      ${(benchmark.replay_plan ?? []).map((item) => `<li>${item}</li>`).join("")}
    </ol>
  `;
}

function formatDriverCodes(codes = []) {
  return codes.length ? codes.join(" · ") : "TBD";
}

async function loadPredictions() {
  refreshButton.disabled = true;
  statusEl.textContent = "Loading forecast...";
  try {
    const response = await fetch("/api/predictions/next");
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail ?? "Failed to load predictions");
    }

    const hubResponse = await fetch(`/api/race-hub/${payload.race.year}/${payload.race.round}`);
    const hub = hubResponse.ok ? await hubResponse.json() : { race: payload.race, sessions: [] };
    renderRace(payload.race, hub);
    renderMetadata(payload.metadata ?? {});
    renderSessions(hub);

    const simulationResponse = await fetch(`/api/simulations/${payload.race.year}/${payload.race.round}`);
    const simulation = simulationResponse.ok ? await simulationResponse.json() : { predictions: [] };
    renderPredictions(mergeSimulationPredictions(payload.predictions, simulation));

    const [backtestResponse, calibrationResponse] = await Promise.all([
      fetch("/api/reports/backtest"),
      fetch("/api/reports/podium-calibration"),
    ]);
    const backtest = backtestResponse.ok ? await backtestResponse.json() : { summary: {}, worst_windows: [] };
    const calibration = calibrationResponse.ok ? await calibrationResponse.json() : { rows: [] };
    renderMetrics(payload.metadata ?? {}, backtest);
    renderReliability(calibration.rows ?? []);
    renderDiagnostics(backtest.worst_windows ?? []);
    const benchmarkResponse = await fetch("/api/benchmarks/monaco-2026");
    const benchmark = benchmarkResponse.ok ? await benchmarkResponse.json() : {};
    renderBenchmark(benchmark);
    statusEl.textContent = `Updated ${new Date().toLocaleTimeString()} · Practice-adjusted forecast`;
  } catch (error) {
    raceEl.innerHTML = `<span>Prediction data unavailable</span>`;
    metadataEl.innerHTML = `<span>Metadata unavailable</span>`;
    sessionsEl.innerHTML = `<span>Session schedule unavailable</span>`;
    metricsEl.innerHTML = `<span>Metrics unavailable</span>`;
    reliabilityEl.innerHTML = `<span>Calibration unavailable</span>`;
    diagnosticsEl.innerHTML = `<span>Diagnostics unavailable</span>`;
    benchmarkEl.innerHTML = `<span>Benchmark unavailable</span>`;
    predictionsEl.innerHTML = `<tr><td colspan="10">${error.message}</td></tr>`;
    statusEl.textContent = "Run ingestion, feature generation, and training first.";
  } finally {
    refreshButton.disabled = false;
  }
}

refreshButton.addEventListener("click", loadPredictions);
modelCardOpen.addEventListener("click", () => modelCard.showModal());
modelCardClose.addEventListener("click", () => modelCard.close());
loadPredictions();
