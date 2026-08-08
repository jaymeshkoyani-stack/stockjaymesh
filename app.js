let allData = [];
let filteredData = [];
let strategy1Data = [];
let strategy2Data = [];
let sortCol = -1;
let sortAsc = true;
let currentView = "strategy2"; // Default to Strategy 2 View
let countdownSeconds = 180; // 3 minutes countdown

document.addEventListener("DOMContentLoaded", () => {
  loadDashboardData();
  startCountdownTimer();
  setInterval(loadDashboardData, 30000); // Poll data.json every 30s
});

async function loadDashboardData() {
  try {
    const response = await fetch("data.json?t=" + new Date().getTime());
    if (!response.ok) return;
    allData = await response.json();
    evaluateStrategy1();
    evaluateStrategy2();
    filterData();
    updateLastRefreshedTime();
  } catch (error) {
    console.error("Error loading dashboard data:", error);
  }
}

async function manualRefreshData() {
  const btn = document.getElementById("btn-sync-now");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "⌛ Logging in & Syncing...";
  }

  try {
    // Call server.py endpoint which re-authenticates login with iCharts
    const response = await fetch("/api/sync", { method: "POST" });
    const res = await response.json();
    
    if (res.status === "success") {
      await loadDashboardData();
      countdownSeconds = 180;
      alert(`[SUCCESS] Re-authenticated iCharts Login! Refreshed ${res.count} symbols successfully.`);
    } else {
      await loadDashboardData();
    }
  } catch (err) {
    console.log("Local sync endpoint call fallback to direct reload:", err);
    await loadDashboardData();
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "🔄 Sync Now";
    }
  }
}

function evaluateStrategy1() {
  strategy1Data = [];

  allData.forEach(item => {
    const t = item.totals;
    const c_oi = t.total_oi.calls_num || 0;
    const p_oi = t.total_oi.puts_num || 0;

    const c_oi_chg = t.total_oi_chg.calls_num || 0;
    const p_oi_chg = t.total_oi_chg.puts_num || 0;
    const net_oi_chg = t.total_oi_chg.net_num || 0;

    const rule1 = (net_oi_chg > c_oi) && (net_oi_chg > p_oi);
    const rule1_abs = (Math.abs(net_oi_chg) > c_oi) && (Math.abs(net_oi_chg) > p_oi);
    const rule2 = (c_oi_chg < 0) || (p_oi_chg < 0);

    if ((rule1 || rule1_abs) && rule2) {
      strategy1Data.push({
        ...item,
        rule1_pass: rule1 || rule1_abs,
        rule2_pass: rule2,
        rule2_calls_minus: c_oi_chg < 0,
        rule2_puts_minus: p_oi_chg < 0
      });
    }
  });

  const countScanned = document.getElementById("strat1-scanned-count");
  const countMatched = document.getElementById("strat1-matched-count");
  if (countScanned) countScanned.textContent = allData.length;
  if (countMatched) countMatched.textContent = strategy1Data.length;
}

function evaluateStrategy2() {
  strategy2Data = [];

  allData.forEach(item => {
    const futOI = item.future_oi || 0;
    const threshold = item.threshold_15pct || (futOI * 0.15);
    const otmCallsChg = item.otm_qty?.total_otm_oi_chg_calls_num || 0;
    const otmPutsChg = item.otm_qty?.total_otm_oi_chg_puts_num || 0;

    const callsPass = threshold > 0 && otmCallsChg > threshold;
    const putsPass = threshold > 0 && otmPutsChg > threshold;

    if (callsPass || putsPass || item.strategy2_match) {
      strategy2Data.push({
        ...item,
        callsPass,
        putsPass,
        threshold
      });
    }
  });

  const countScanned = document.getElementById("strat2-scanned-count");
  const countMatched = document.getElementById("strat2-matched-count");
  if (countScanned) countScanned.textContent = allData.length;
  if (countMatched) countMatched.textContent = strategy2Data.length;
}

function startCountdownTimer() {
  setInterval(() => {
    countdownSeconds--;
    if (countdownSeconds <= 0) {
      countdownSeconds = 180;
      loadDashboardData();
    }
    const mins = Math.floor(countdownSeconds / 60);
    const secs = countdownSeconds % 60;
    const timerElem = document.getElementById("countdown-timer");
    if (timerElem) {
      timerElem.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
  }, 1000);
}

function filterData() {
  const searchTerm = (document.getElementById("symbol-search")?.value || "").toUpperCase().trim();
  const sentiment = document.getElementById("sentiment-filter")?.value || "ALL";

  filteredData = allData.filter(item => {
    const matchesSearch = item.symbol.toUpperCase().includes(searchTerm);
    const netOIChg = item.totals.total_oi_chg.net_num || 0;
    let matchesSentiment = true;
    if (sentiment === "BULLISH") matchesSentiment = netOIChg > 0;
    if (sentiment === "BEARISH") matchesSentiment = netOIChg < 0;

    return matchesSearch && matchesSentiment;
  });

  renderDashboard();
}

function renderDashboard() {
  renderKPICards(allData);
  document.getElementById("total-count").textContent = allData.length;
  document.getElementById("visible-count").textContent = filteredData.length;

  if (currentView === "strategy2") {
    renderStrategy2Grid(strategy2Data);
  } else if (currentView === "strategy1") {
    renderStrategy1Grid(strategy1Data);
  } else if (currentView === "excel") {
    renderExcelGrid(filteredData);
  } else {
    renderSymbolCards(filteredData);
  }
}

function renderKPICards(data) {
  let netOITotal = 0;
  let bullishCount = 0;
  let bearishCount = 0;

  data.forEach(item => {
    const netOIChg = item.totals.total_oi_chg.net_num || 0;
    netOITotal += netOIChg;
    if (netOIChg > 0) bullishCount++;
    else if (netOIChg < 0) bearishCount++;
  });

  const kpiContainer = document.getElementById("kpi-grid");
  if (!kpiContainer) return;

  const netOIFormatted = formatCurrencyCr(netOITotal);

  kpiContainer.innerHTML = `
    <div class="kpi-card">
      <div class="kpi-info">
        <p>Strategy 2 Matches (QTY OTM)</p>
        <h2 style="color: #38bdf8;">${strategy2Data.length} Symbols</h2>
      </div>
      <div class="kpi-icon" style="background: rgba(2, 132, 199, 0.2); color: #38bdf8;">🚀</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-info">
        <p>Strategy 1 Matches</p>
        <h2 style="color: #a78bfa;">${strategy1Data.length} Symbols</h2>
      </div>
      <div class="kpi-icon" style="background: rgba(139, 92, 246, 0.2); color: #a78bfa;">🎯</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-info">
        <p>Bullish Symbols (Net OI Chg > 0)</p>
        <h2 style="color: #34d399;">${bullishCount} Symbols</h2>
      </div>
      <div class="kpi-icon" style="background: rgba(16, 185, 129, 0.2); color: #34d399;">📈</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-info">
        <p>Bearish Symbols (Net OI Chg < 0)</p>
        <h2 style="color: #f87171;">${bearishCount} Symbols</h2>
      </div>
      <div class="kpi-icon" style="background: rgba(239, 68, 68, 0.2); color: #f87171;">📉</div>
    </div>
  `;
}

function renderStrategy2Grid(data) {
  const tbody = document.getElementById("strategy2-grid-body");
  const visibleCountElem = document.getElementById("strat2-visible-count");
  if (!tbody) return;

  if (visibleCountElem) visibleCountElem.textContent = data.length;
  tbody.innerHTML = "";

  if (data.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="11" style="text-align: center; padding: 24px; color: var(--text-muted);">
          No symbols currently match Strategy 2 rules. Live scanner checking every 3 minutes...
        </td>
      </tr>
    `;
    return;
  }

  data.forEach((item, idx) => {
    const otm = item.otm_qty || {};
    const rowHTML = `
      <tr>
        <td style="color: var(--text-muted);">${idx + 1}</td>
        <td class="col-sticky">${item.symbol}</td>
        <td style="color: #cbd5e1;">${item.expiry || '-'}</td>
        <td style="font-weight: 700; color: #f1f5f9;">${item.future_oi_str}</td>
        <td style="color: #fbbf24; font-weight: 700;">${item.threshold_15pct_str}</td>
        
        <!-- OTM Calls & Puts OI Chg (QTY Mode) -->
        <td style="color: ${item.callsPass ? '#34d399' : '#38bdf8'}; font-weight: ${item.callsPass ? '800' : '400'};">
          ${otm.total_otm_oi_chg_calls} ${item.callsPass ? '🔥 (>15%)' : ''}
        </td>
        <td style="color: ${item.putsPass ? '#34d399' : '#f472b6'}; font-weight: ${item.putsPass ? '800' : '400'};">
          ${otm.total_otm_oi_chg_puts} ${item.putsPass ? '🔥 (>15%)' : ''}
        </td>
        <td style="color: #a78bfa; font-weight: 700;">${otm.total_otm_oi_chg_net}</td>
        
        <!-- Rule Pass Status -->
        <td><span style="color: ${item.callsPass ? '#34d399' : 'var(--text-muted)'}; font-weight: 700;">${item.callsPass ? 'PASS ✅' : 'NO'}</span></td>
        <td><span style="color: ${item.putsPass ? '#34d399' : 'var(--text-muted)'}; font-weight: 700;">${item.putsPass ? 'PASS ✅' : 'NO'}</span></td>
        
        <td>
          <span style="padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 800; background: rgba(2, 132, 199, 0.25); color: #38bdf8; border: 1px solid rgba(2, 132, 199, 0.5);">
            STRATEGY 2 MATCH 🚀
          </span>
        </td>
      </tr>
    `;

    tbody.insertAdjacentHTML("beforeend", rowHTML);
  });
}

function renderStrategy1Grid(data) {
  const tbody = document.getElementById("strategy1-grid-body");
  const visibleCountElem = document.getElementById("strat1-visible-count");
  if (!tbody) return;

  if (visibleCountElem) visibleCountElem.textContent = data.length;
  tbody.innerHTML = "";

  if (data.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="13" style="text-align: center; padding: 24px; color: var(--text-muted);">
          No symbols currently match Strategy 1 rules. Live scanner checking every 3 minutes...
        </td>
      </tr>
    `;
    return;
  }

  data.forEach((item, idx) => {
    const t = item.totals;
    const netOIChgVal = t.total_oi_chg.net_num || 0;
    const cOIChgVal = t.total_oi_chg.calls_num || 0;
    const pOIChgVal = t.total_oi_chg.puts_num || 0;

    const rowHTML = `
      <tr>
        <td style="color: var(--text-muted);">${idx + 1}</td>
        <td class="col-sticky">${item.symbol}</td>
        <td style="color: #cbd5e1;">${item.expiry || '-'}</td>
        <td style="font-weight: 600; color: #f1f5f9;">${item.strike_atm}</td>
        <td style="color: #fbbf24; font-weight: 600;">${item.pcr_oi}</td>
        
        <td class="${netOIChgVal >= 0 ? 'val-green' : 'val-red'}" style="font-size: 13px; font-weight: 800;">${t.total_oi_chg.net}</td>
        <td style="color: #38bdf8;">${t.total_oi.calls}</td>
        <td style="color: #f472b6;">${t.total_oi.puts}</td>
        
        <td style="color: ${cOIChgVal < 0 ? '#f87171' : '#34d399'}; font-weight: ${cOIChgVal < 0 ? '800' : '400'};">
          ${t.total_oi_chg.calls} ${cOIChgVal < 0 ? '🔻 (Minus)' : ''}
        </td>
        <td style="color: ${pOIChgVal < 0 ? '#f87171' : '#34d399'}; font-weight: ${pOIChgVal < 0 ? '800' : '400'};">
          ${t.total_oi_chg.puts} ${pOIChgVal < 0 ? '🔻 (Minus)' : ''}
        </td>
        
        <td><span style="color: #34d399; font-weight: 700;">PASS (Net Chg > OI)</span></td>
        <td><span style="color: #34d399; font-weight: 700;">PASS (${item.rule2_calls_minus ? 'Calls < 0' : 'Puts < 0'})</span></td>
        
        <td>
          <span style="padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 800; background: rgba(139, 92, 246, 0.25); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.5);">
            STRATEGY 1 MATCH ✅
          </span>
        </td>
      </tr>
    `;

    tbody.insertAdjacentHTML("beforeend", rowHTML);
  });
}

function renderExcelGrid(data) {
  const tbody = document.getElementById("excel-grid-body");
  if (!tbody) return;

  tbody.innerHTML = "";

  data.forEach((item, idx) => {
    const t = item.totals;
    const netOIChgVal = t.total_oi_chg.net_num || 0;
    const netOIVal = t.total_oi.net_num || 0;
    const netVolVal = t.total_vol.net_num || 0;
    const isBullish = netOIChgVal > 0;

    const oiChgHighlight = netOIChgVal < 0 ? "row-net-chg-red" : "row-net-chg-green";

    const rowHTML = `
      <tr>
        <td style="color: var(--text-muted);">${idx + 1}</td>
        <td class="col-sticky">${item.symbol}</td>
        <td style="color: #cbd5e1;">${item.expiry || '-'}</td>
        <td style="font-weight: 600; color: #f1f5f9;">${item.strike_atm}</td>
        <td style="color: #fbbf24; font-weight: 600;">${item.pcr_oi}</td>
        
        <td style="color: #38bdf8;">${t.total_oi.calls}</td>
        <td style="color: #f472b6;">${t.total_oi.puts}</td>
        <td class="${netOIVal >= 0 ? 'val-green' : 'val-red'}">${t.total_oi.net}</td>
        
        <td style="color: #38bdf8;">${t.total_oi_chg.calls}</td>
        <td style="color: #f472b6;">${t.total_oi_chg.puts}</td>
        <td class="${oiChgHighlight}">${t.total_oi_chg.net}</td>
        
        <td style="color: #38bdf8;">${t.total_vol.calls}</td>
        <td style="color: #f472b6;">${t.total_vol.puts}</td>
        <td class="${netVolVal >= 0 ? 'val-green' : 'val-red'}">${t.total_vol.net}</td>
        
        <td>
          <span style="padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; background: ${isBullish ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}; color: ${isBullish ? '#34d399' : '#f87171'}; border: 1px solid ${isBullish ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'};">
            ${isBullish ? 'BULLISH ▲' : 'BEARISH ▼'}
          </span>
        </td>
      </tr>
    `;

    tbody.insertAdjacentHTML("beforeend", rowHTML);
  });
}

function renderSymbolCards(data) {
  const container = document.getElementById("symbol-cards-container");
  if (!container) return;

  container.innerHTML = "";

  data.forEach(item => {
    const t = item.totals;
    const netOIChgVal = t.total_oi_chg.net_num || 0;
    const oiChgRowClass = netOIChgVal < 0 ? "row-highlight-red" : "row-highlight-green";

    const cardHTML = `
      <div class="icharts-card">
        <div class="card-header">
          <div class="symbol-badge">${item.symbol}</div>
          <div class="expiry-tag">EXP: ${item.expiry || 'CURRENT'}</div>
        </div>
        <div class="meta-row">
          <div class="meta-item">ATM Strike: <span>${item.strike_atm}</span></div>
          <div class="meta-item">PCR (OI): <span>${item.pcr_oi}</span></div>
        </div>

        <table class="icharts-totals-table">
          <thead>
            <tr>
              <th colspan="4" style="background-color: #f8fafc; font-size: 13px; font-weight: 700; color: #334155; padding: 4px;">Totals</th>
            </tr>
            <tr>
              <th style="width: 28%;">Stat</th>
              <th style="width: 24%;">Calls</th>
              <th style="width: 24%;">Puts</th>
              <th style="width: 24%;">Net</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style="text-align: left; font-weight: 600;">Total OI</td>
              <td>${t.total_oi.calls}</td>
              <td>${t.total_oi.puts}</td>
              <td class="${(t.total_oi.net_num || 0) >= 0 ? 'val-green' : 'val-red'}">${t.total_oi.net}</td>
            </tr>
            <tr class="${oiChgRowClass}">
              <td style="text-align: left; font-weight: 600;">Total OI Chg</td>
              <td>${t.total_oi_chg.calls}</td>
              <td>${t.total_oi_chg.puts}</td>
              <td class="${netOIChgVal >= 0 ? 'val-green' : 'val-red'}">${t.total_oi_chg.net}</td>
            </tr>
            <tr>
              <td style="text-align: left; font-weight: 600;">Total Volume</td>
              <td>${t.total_vol.calls}</td>
              <td>${t.total_vol.puts}</td>
              <td class="${(t.total_vol.net_num || 0) >= 0 ? 'val-green' : 'val-red'}">${t.total_vol.net}</td>
            </tr>
          </tbody>
        </table>
      </div>
    `;

    container.insertAdjacentHTML("beforeend", cardHTML);
  });
}

function sortTable(colIdx) {
  if (sortCol === colIdx) {
    sortAsc = !sortAsc;
  } else {
    sortCol = colIdx;
    sortAsc = true;
  }

  filteredData.sort((a, b) => {
    let valA, valB;
    switch(colIdx) {
      case 1: valA = a.symbol; valB = b.symbol; break;
      case 2: valA = a.expiry; valB = b.expiry; break;
      case 3: valA = parseFloat(a.strike_atm) || 0; valB = parseFloat(b.strike_atm) || 0; break;
      case 4: valA = parseFloat(a.pcr_oi) || 0; valB = parseFloat(b.pcr_oi) || 0; break;
      case 5: valA = a.totals.total_oi.calls_num || 0; valB = b.totals.total_oi.calls_num || 0; break;
      case 6: valA = a.totals.total_oi.puts_num || 0; valB = b.totals.total_oi.puts_num || 0; break;
      case 7: valA = a.totals.total_oi.net_num || 0; valB = b.totals.total_oi.net_num || 0; break;
      case 8: valA = a.totals.total_oi_chg.calls_num || 0; valB = b.totals.total_oi_chg.calls_num || 0; break;
      case 9: valA = a.totals.total_oi_chg.puts_num || 0; valB = b.totals.total_oi_chg.puts_num || 0; break;
      case 10: valA = a.totals.total_oi_chg.net_num || 0; valB = b.totals.total_oi_chg.net_num || 0; break;
      case 11: valA = a.totals.total_vol.calls_num || 0; valB = b.totals.total_vol.calls_num || 0; break;
      case 12: valA = a.totals.total_vol.puts_num || 0; valB = b.totals.total_vol.puts_num || 0; break;
      case 13: valA = a.totals.total_vol.net_num || 0; valB = b.totals.total_vol.net_num || 0; break;
      default: valA = a.symbol; valB = b.symbol;
    }

    if (typeof valA === "string") {
      return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
    }
    return sortAsc ? valA - valB : valB - valA;
  });

  renderDashboard();
}

function switchView(viewName) {
  currentView = viewName;
  const strat2Sec = document.getElementById("strategy2-view-section");
  const strat1Sec = document.getElementById("strategy1-view-section");
  const excelSec = document.getElementById("excel-view-section");
  const cardsSec = document.getElementById("cards-view-section");
  
  const btnStrat2 = document.getElementById("btn-view-strategy2");
  const btnStrat1 = document.getElementById("btn-view-strategy1");
  const btnExcel = document.getElementById("btn-view-excel");
  const btnCards = document.getElementById("btn-view-cards");

  strat2Sec.style.display = viewName === "strategy2" ? "block" : "none";
  strat1Sec.style.display = viewName === "strategy1" ? "block" : "none";
  excelSec.style.display = viewName === "excel" ? "block" : "none";
  cardsSec.style.display = viewName === "cards" ? "block" : "none";

  btnStrat2.classList.toggle("active", viewName === "strategy2");
  btnStrat1.classList.toggle("active", viewName === "strategy1");
  btnExcel.classList.toggle("active", viewName === "excel");
  btnCards.classList.toggle("active", viewName === "cards");

  renderDashboard();
}

function exportToCSV() {
  let dataToExport = filteredData;
  if (currentView === "strategy2") dataToExport = strategy2Data;
  if (currentView === "strategy1") dataToExport = strategy1Data;

  if (dataToExport.length === 0) return;

  const headers = ["Symbol", "Expiry", "Future OI", "15% Threshold", "Total OTM OI Chg (Calls QTY)", "Total OTM OI Chg (Puts QTY)", "Total OI Net", "Total OI Chg (Calls Value)", "Total OI Chg (Puts Value)", "Total OI Chg Net"];
  const rows = [headers];

  dataToExport.forEach(item => {
    const t = item.totals;
    const otm = item.otm_qty || {};
    rows.push([
      item.symbol,
      item.expiry || '',
      item.future_oi_str || '',
      item.threshold_15pct_str || '',
      otm.total_otm_oi_chg_calls || '',
      otm.total_otm_oi_chg_puts || '',
      t.total_oi.net,
      t.total_oi_chg.calls,
      t.total_oi_chg.puts,
      t.total_oi_chg.net
    ]);
  });

  let csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\n");
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `iCharts_${currentView.toUpperCase()}_Export_${new Date().toISOString().slice(0,10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function formatCurrencyCr(val) {
  const absVal = Math.abs(val);
  if (absVal >= 10000000) {
    return `${(val / 10000000).toFixed(2)} Cr`;
  } else if (absVal >= 100000) {
    return `${(val / 100000).toFixed(2)} L`;
  } else {
    return val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
}

function updateLastRefreshedTime() {
  const timeElem = document.getElementById("last-refreshed-time");
  if (timeElem) {
    const now = new Date();
    timeElem.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
}
