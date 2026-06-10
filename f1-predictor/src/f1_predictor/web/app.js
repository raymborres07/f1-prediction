const raceEl = document.querySelector("#race");
const metadataEl = document.querySelector("#metadata");
const metricsEl = document.querySelector("#metrics");
const reliabilityEl = document.querySelector("#reliability");
const diagnosticsEl = document.querySelector("#diagnostics");
const modelCard = document.querySelector("#model-card");
const modelCardBody = document.querySelector("#model-card-body");
const modelCardOpen = document.querySelector("#model-card-open");
const modelCardClose = document.querySelector("#model-card-close");
const predictionsEl = document.querySelector("#predictions");
const statusEl = document.querySelector("#status");
const refreshButton = document.querySelector("#refresh");

function formatDate(value) {
  if (!value || value === "NaT") return "Date TBD";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Date TBD";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function pct(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function renderRace(race) {
  raceEl.innerHTML = `
    <span class="race-name">${race.event_name ?? `Round ${race.round}`}</span>
    <span class="race-meta">${race.year} Round ${race.round} | ${race.location ?? "Location TBD"} | ${formatDate(race.race_date)}</span>
  `;
}

function renderMetadata(metadata) {
  const model = metadata.model ?? {};
  const dataset = metadata.dataset ?? {};
  const trainedAt = model.trained_at_utc ? formatDate(model.trained_at_utc) : "not trained";
  metadataEl.innerHTML = `
    <span><strong>${metadata.prediction_mode ?? "unknown mode"}</strong></span>
    <span>Model ${model.model_version ?? "unknown"}</span>
    <span>Trained ${trainedAt}</span>
    <span>Dataset ${dataset.dataset_version ?? model.dataset_version ?? "unknown"}</span>
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

function renderPredictions(predictions) {
  if (!predictions.length) {
    predictionsEl.innerHTML = `<tr><td colspan="10">No predictions available.</td></tr>`;
    return;
  }

  predictionsEl.innerHTML = predictions
    .map((row) => {
      const gridValue = row.grid_position ?? row.qualifying_position;
      const grid = Number.isFinite(Number(gridValue)) ? `P${Number(gridValue).toFixed(0)}` : "TBD";
      const finishBand = `${Number(row.finish_low).toFixed(1)}-${Number(row.finish_high).toFixed(1)}`;
      return `
        <tr>
          <td>${row.prediction_rank}</td>
          <td><span class="driver">${row.driver_code}</span><br><span class="muted">${row.driver_name ?? ""}</span></td>
          <td>${row.constructor_name ?? ""}</td>
          <td>${grid}</td>
          <td class="probability">${pct(row.win_probability)}</td>
          <td class="probability">${pct(row.podium_probability)}</td>
          <td class="probability">${pct(row.top10_probability)}</td>
          <td>${Number(row.expected_finish).toFixed(1)} <span class="muted">(${finishBand})</span></td>
          <td class="explain">${renderContributionText(row)}</td>
          <td><span class="pill">${row.data_freshness ?? "unknown"}</span></td>
        </tr>
      `;
    })
    .join("");
}

function renderContributionText(row) {
  const contributions = row.feature_contributions ?? [];
  if (!contributions.length) return row.explanation ?? "";
  const top = contributions
    .map((item) => `${item.name}: ${Number(item.impact).toFixed(1)}`)
    .join(", ");
  return `${row.explanation ?? ""}<br><span class="muted">${top}</span>`;
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
    .map((row) => {
      const predicted = Number(row.mean_predicted_probability || 0);
      const observed = Number(row.observed_podium_rate || 0);
      return `
        <div class="reliability-row">
          <span>${pct(predicted)}</span>
          <div class="bar"><i style="width:${Math.min(100, observed * 100)}%"></i></div>
          <span>${pct(observed)}</span>
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
        <span>${row.diagnostic_reason ?? "weak window"} | Brier ${Number(row.podium_brier).toFixed(3)} | MAE ${Number(row.finish_mae).toFixed(2)}</span>
      </div>
    `)
    .join("");
}

async function loadPredictions() {
  refreshButton.disabled = true;
  statusEl.textContent = "Loading predictions...";
  try {
    const response = await fetch("/api/predictions/next");
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail ?? "Failed to load predictions");
    }
    renderRace(payload.race);
    renderMetadata(payload.metadata ?? {});
    renderPredictions(payload.predictions);
    const [backtestResponse, calibrationResponse] = await Promise.all([
      fetch("/api/reports/backtest"),
      fetch("/api/reports/podium-calibration"),
    ]);
    const backtest = backtestResponse.ok ? await backtestResponse.json() : { summary: {}, worst_windows: [] };
    const calibration = calibrationResponse.ok ? await calibrationResponse.json() : { rows: [] };
    renderMetrics(payload.metadata ?? {}, backtest);
    renderReliability(calibration.rows ?? []);
    renderDiagnostics(backtest.worst_windows ?? []);
    statusEl.textContent = `Updated ${new Date().toLocaleTimeString()}`;
  } catch (error) {
    raceEl.innerHTML = `<span>Prediction data unavailable</span>`;
    metadataEl.innerHTML = `<span>Metadata unavailable</span>`;
    metricsEl.innerHTML = `<span>Metrics unavailable</span>`;
    reliabilityEl.innerHTML = `<span>Calibration unavailable</span>`;
    diagnosticsEl.innerHTML = `<span>Diagnostics unavailable</span>`;
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
