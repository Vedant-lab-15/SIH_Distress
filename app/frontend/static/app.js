/* ═══════════════════════════════════════════════════════════════════
   SurakshaMind — SIH 2026 Prototype Frontend
   All API calls go to the FastAPI backend at the same origin.
═══════════════════════════════════════════════════════════════════ */

'use strict';

// ─── Utilities ────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

async function api(path, opts = {}) {
  const r = await fetch(path, opts);
  if (!r.ok) {
    const txt = await r.text();
    throw new Error(`${r.status}: ${txt}`);
  }
  return r.json();
}

function riskClass(r) {
  return `risk-${String(r || '').toLowerCase()}`;
}

function riskLabel(r) {
  const map = { critical: '🔴 Critical', high: '🟠 High', moderate: '🟡 Moderate', low: '🟢 Low' };
  return map[String(r).toLowerCase()] || r;
}

function relativeTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  const diff = (Date.now() - d) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return d.toLocaleDateString('en-IN');
}

function kpiCard(num, label, cls = '') {
  return `<div class="kpi-card ${cls}"><div class="kpi-num">${num}</div><div class="kpi-label">${label}</div></div>`;
}

// ─── Navigation ───────────────────────────────────────────────────
let _currentScreen = 'home';
let _chartInstances = {};

function goTo(name) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  const s = $(`screen-${name}`);
  const b = document.querySelector(`[data-screen="${name}"]`);
  if (s) s.classList.add('active');
  if (b) b.classList.add('active');
  _currentScreen = name;
  window.scrollTo(0, 0);

  if (name === 'home')       loadHome();
  if (name === 'dashboard')  loadDashboard();
  if (name === 'alerts')     loadAlerts();
  if (name === 'analytics')  loadAnalytics();
}

document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => goTo(btn.dataset.screen));
});

// ─── System health check ──────────────────────────────────────────
async function checkHealth() {
  const pill = $('sysStatus');
  try {
    const h = await api('/health');
    pill.textContent = `● Online · ${h.model_version}`;
    pill.className = 'status-pill status-ok';
  } catch {
    pill.textContent = '● Offline';
    pill.className = 'status-pill status-error';
  }
}

// ─── SCREEN 1: HOME ──────────────────────────────────────────────
async function loadHome() {
  try {
    const an = await api('/demo/analytics');
    $('hs-victims').textContent = an.total_victims;
    $('hs-highrisk').textContent = an.high_risk_count;
    $('hs-alerts').textContent = an.total_alerts;
  } catch {
    $('hs-victims').textContent = '—';
  }
}

// ─── SCREEN 2: CHECK-IN ──────────────────────────────────────────

// Live slider labels
['ci-sentiment', 'ci-missed', 'ci-delay'].forEach(id => {
  const el = $(id);
  if (!el) return;
  el.addEventListener('input', () => {
    $(`${id}-val`).textContent = el.value;
  });
});

const PRESETS = {
  low: {
    text: 'Things are going better this week. I attended the hearing and the investigator was helpful. My family is supportive.',
    sentiment: 0.5, missed: 0, delay: 30,
  },
  moderate: {
    text: 'I am managing but the delays are frustrating. I had to appear in court twice this month. I feel a bit alone.',
    sentiment: -0.2, missed: 1, delay: 90,
  },
  high: {
    text: 'I am afraid and cannot sleep. There have been threats again and the case has been delayed for months. I have no money left.',
    sentiment: -0.6, missed: 3, delay: 200,
  },
  critical: {
    text: 'मैं बहुत डरा हुआ हूँ। दुश्मन ने धमकी दी है और मैं अकेला महसूस कर रहा हूँ। मन बहुत चिंतित है। मुझे नहीं पता क्या करूँ। bojh bahut zyada ho gaya hai.',
    sentiment: -0.9, missed: 5, delay: 365,
  },
};

function setPreset(level) {
  const p = PRESETS[level];
  $('ci-text').value = p.text;
  $('ci-sentiment').value = p.sentiment;
  $('ci-sentiment-val').textContent = p.sentiment.toFixed(2);
  $('ci-missed').value = p.missed;
  $('ci-missed-val').textContent = p.missed;
  $('ci-delay').value = p.delay;
  $('ci-delay-val').textContent = p.delay;
}

async function runCheckin() {
  const text = $('ci-text').value.trim();
  if (!text) { alert('Please enter a check-in message.'); return; }

  const btn = document.querySelector('#screen-checkin .btn-primary.wide');
  btn.textContent = '⏳ Analysing…';
  btn.disabled = true;

  try {
    const payload = {
      text,
      language: $('ci-lang').value,
      sentiment_score: parseFloat($('ci-sentiment').value),
      missed_checkins: parseInt($('ci-missed').value),
      case_delay_days: parseInt($('ci-delay').value),
    };
    const r = await api('/demo/checkin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    renderCheckinResult(r);
  } catch (e) {
    alert('Check-in error: ' + e.message);
  } finally {
    btn.textContent = '🔍 Analyse Check-in';
    btn.disabled = false;
  }
}

function renderCheckinResult(r) {
  const result = $('ci-result');
  result.classList.remove('hidden');
  result.scrollIntoView({ behavior: 'smooth', block: 'start' });

  $('ci-dds-num').textContent = r.dds.toFixed(1);
  const badge = $('ci-risk-badge');
  badge.textContent = riskLabel(r.risk_level);
  badge.className = `risk-badge-large ${riskClass(r.risk_level)}`;

  drawDDSGauge(r.dds);

  const factors = $('ci-factors');
  factors.innerHTML = r.top_factors.map(f => `
    <div class="factor-row">
      <div class="factor-name">${f.factor}</div>
      <div class="factor-bar-wrap">
        <div class="factor-bar" style="width:${Math.min(f.contribution, 100)}%"></div>
      </div>
      <div class="factor-val">+${f.contribution.toFixed(1)} pts</div>
    </div>
  `).join('');

  $('ci-intervention').textContent = r.recommended_intervention;
}

function drawDDSGauge(dds) {
  const canvas = $('ddsGauge');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const cx = 100, cy = 110, r = 80;
  const startAngle = Math.PI;
  const endAngle = 2 * Math.PI;
  const valueAngle = startAngle + (dds / 100) * Math.PI;

  // Background arc
  ctx.beginPath();
  ctx.arc(cx, cy, r, startAngle, endAngle);
  ctx.lineWidth = 18;
  ctx.strokeStyle = '#1e293b';
  ctx.stroke();

  // Colored arc
  const color = dds >= 80 ? '#ef4444' : dds >= 65 ? '#f97316' : dds >= 40 ? '#eab308' : '#22c55e';
  ctx.beginPath();
  ctx.arc(cx, cy, r, startAngle, valueAngle);
  ctx.lineWidth = 18;
  ctx.strokeStyle = color;
  ctx.lineCap = 'round';
  ctx.stroke();

  // Needle
  const nx = cx + (r - 10) * Math.cos(valueAngle);
  const ny = cy + (r - 10) * Math.sin(valueAngle);
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(nx, ny);
  ctx.strokeStyle = '#f1f5f9';
  ctx.lineWidth = 3;
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(cx, cy, 6, 0, 2 * Math.PI);
  ctx.fillStyle = '#f1f5f9';
  ctx.fill();

  // Labels
  ctx.fillStyle = '#94a3b8';
  ctx.font = '11px Inter,sans-serif';
  ctx.fillText('0', cx - r - 4, cy + 14);
  ctx.fillText('100', cx + r - 18, cy + 14);
}

// ─── SCREEN 3: DASHBOARD ─────────────────────────────────────────
let _dashboardData = [];

async function loadDashboard() {
  $('db-tbody').innerHTML = '<tr><td colspan="8" class="loading-cell">Loading victims…</td></tr>';
  try {
    const d = await api('/demo/dashboard');
    _dashboardData = d.victims;
    renderDashboardKPIs(d);
    filterDashboard();
  } catch (e) {
    $('db-tbody').innerHTML = `<tr><td colspan="8" class="error-cell">${e.message}</td></tr>`;
  }
}

function renderDashboardKPIs(d) {
  const counts = { critical: 0, high: 0, moderate: 0, low: 0 };
  d.victims.forEach(v => { counts[v.risk_level] = (counts[v.risk_level] || 0) + 1; });
  $('db-kpis').innerHTML =
    kpiCard(d.count, 'Total Victims') +
    kpiCard(counts.critical || 0, 'Critical', 'kpi-critical') +
    kpiCard(counts.high || 0, 'High Risk', 'kpi-high') +
    kpiCard(counts.moderate || 0, 'Moderate', 'kpi-moderate') +
    kpiCard(counts.low || 0, 'Low Risk', 'kpi-low');
}

function filterDashboard() {
  const q = ($('db-search').value || '').toLowerCase();
  const risk = $('db-filter-risk').value;
  const sort = $('db-sort').value;

  let rows = _dashboardData.filter(v =>
    (!q || v.victim_id.toLowerCase().includes(q) || (v.state || '').toLowerCase().includes(q) || (v.offence_type || '').toLowerCase().includes(q)) &&
    (!risk || v.risk_level === risk)
  );

  if (sort === 'name') rows.sort((a, b) => a.victim_id.localeCompare(b.victim_id));
  else rows.sort((a, b) => b.dds - a.dds);

  const tbody = $('db-tbody');
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="loading-cell">No victims match the current filter.</td></tr>';
    return;
  }
  tbody.innerHTML = rows.map(v => `
    <tr class="clickable-row" onclick="openVictimDetail('${v.victim_id}')">
      <td><code>${v.victim_id}</code></td>
      <td>${v.state || '—'}</td>
      <td>${v.offence_type || '—'}</td>
      <td><span class="stage-chip">${v.case_stage || '—'}</span></td>
      <td><span class="dds-cell ${riskClass(v.risk_level)}">${v.dds.toFixed(1)}</span></td>
      <td><span class="risk-badge ${riskClass(v.risk_level)}">${riskLabel(v.risk_level)}</span></td>
      <td>${relativeTime(v.last_checkin)}</td>
      <td><button class="btn-xs" onclick="event.stopPropagation();openVictimDetail('${v.victim_id}')">View →</button></td>
    </tr>
  `).join('');
}

// ─── SCREEN 4: VICTIM DETAIL ─────────────────────────────────────
let _trendChart = null;

async function openVictimDetail(victimId) {
  goTo('detail');
  $('detail-header-info').innerHTML = `<h2>👤 Victim Detail: <code>${victimId}</code></h2>`;
  $('detail-stage-bar').innerHTML = '<div class="loading-cell">Loading…</div>';

  try {
    const d = await api(`/demo/victim/${encodeURIComponent(victimId)}`);
    renderVictimDetail(d);
  } catch (e) {
    $('detail-header-info').innerHTML += `<p class="error-cell">${e.message}</p>`;
  }
}

function renderVictimDetail(d) {
  // Header
  const v = d.victim;
  $('detail-header-info').innerHTML = `
    <div class="detail-hero">
      <div>
        <h2>👤 ${v.victim_id}</h2>
        <div class="victim-meta">
          <span>${v.state}</span><span>${v.gender}</span><span>Age ${v.age}</span>
          <span>${v.social_category}</span><span>${v.offence_type}</span>
          <span>Severity ${v.severity}/5</span>
        </div>
      </div>
      <div class="detail-badges">
        <span class="stage-chip large">${d.current_stage}</span>
        <span class="trend-chip">${d.trend}</span>
      </div>
    </div>
  `;

  // Trend chart
  const labels = d.timeline.map(t => `#${t.interaction_number}`);
  const scores = d.timeline.map(t => t.dds);
  const bgColors = scores.map(s => s >= 80 ? 'rgba(239,68,68,0.2)' : s >= 65 ? 'rgba(249,115,22,0.2)' : s >= 40 ? 'rgba(234,179,8,0.2)' : 'rgba(34,197,94,0.2)');
  const borderColors = scores.map(s => s >= 80 ? '#ef4444' : s >= 65 ? '#f97316' : s >= 40 ? '#eab308' : '#22c55e');

  if (_trendChart) { _trendChart.destroy(); _trendChart = null; }
  const ctx = $('trendChart').getContext('2d');
  _trendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'DDS',
        data: scores,
        borderColor: '#38bdf8',
        backgroundColor: 'rgba(56,189,248,0.08)',
        pointBackgroundColor: borderColors,
        pointRadius: 6,
        tension: 0.3,
        fill: true,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            afterLabel: ctx => {
              const t = d.timeline[ctx.dataIndex];
              return `Stage: ${t.case_stage}  |  ${t.channel}`;
            }
          }
        }
      },
      scales: {
        y: { min: 0, max: 100, grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } },
        x: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } },
      },
    },
  });
  $('detail-trend-label').innerHTML = `<span class="trend-chip">${d.trend}</span> over ${d.total_interactions} interactions`;

  // Case stage progress
  const STAGES = ['Investigation', 'Chargesheet', 'Trial', 'Judgment', 'Compensation', 'Rehabilitation'];
  const currentIdx = STAGES.findIndex(s => s.toLowerCase() === (d.current_stage || '').toLowerCase());
  $('detail-stage-bar').innerHTML = `
    <div class="stage-progress">
      ${STAGES.map((s, i) => `
        <div class="stage-step ${i < currentIdx ? 'done' : i === currentIdx ? 'current' : 'future'}">
          <div class="stage-dot">${i < currentIdx ? '✓' : i + 1}</div>
          <div class="stage-name">${s}</div>
        </div>
        ${i < STAGES.length - 1 ? '<div class="stage-connector ' + (i < currentIdx ? 'done' : '') + '"></div>' : ''}
      `).join('')}
    </div>
  `;

  // Recent summaries
  const recent = d.timeline.slice(-4).reverse();
  $('detail-summaries').innerHTML = recent.map(t => `
    <div class="summary-row">
      <div class="summary-meta">
        <span>Check-in #${t.interaction_number}</span>
        <span class="risk-badge ${riskClass(t.risk_level)}">${riskLabel(t.risk_level)}</span>
        ${t.threat_received ? '<span class="threat-badge">⚠️ Threat</span>' : ''}
      </div>
      <div class="summary-text">${t.summary || '(no text recorded)'}</div>
      <div class="summary-scores">
        Economic stress: ${t.economic_stress}/5 &nbsp;·&nbsp; Social support: ${t.social_support}/5
      </div>
    </div>
  `).join('');

  // SHAP factors
  const maxVal = Math.max(...d.shap_factors.map(f => f.value), 1);
  $('detail-shap').innerHTML = `
    <div class="shap-note">Model attributions — not causal evidence.</div>
    ${d.shap_factors.map(f => `
      <div class="factor-row">
        <div class="factor-name">${f.feature}</div>
        <div class="factor-bar-wrap">
          <div class="factor-bar shap-bar" style="width:${Math.min((f.value / maxVal) * 100, 100)}%"></div>
        </div>
        <div class="factor-val">${f.value > 0 ? '+' : ''}${f.value.toFixed(1)}</div>
        <div class="factor-dir ${f.direction.includes('↑') ? 'dir-up' : 'dir-neutral'}">${f.direction}</div>
      </div>
    `).join('')}
  `;

  // Intervention history
  $('detail-interventions').innerHTML = d.intervention_history.length
    ? d.intervention_history.map(h => `
      <div class="intervention-row">
        <div class="iv-meta">
          <span class="risk-badge ${riskClass(h.risk)}">${riskLabel(h.risk)}</span>
          <span class="iv-dds">DDS ${h.dds}</span>
          <span class="iv-date">${relativeTime(h.date)}</span>
          ${h.reviewed ? '<span class="reviewed-badge">✓ Reviewed</span>' : '<span class="pending-badge">Pending</span>'}
        </div>
        <div class="iv-action">${h.action}</div>
      </div>
    `).join('')
    : '<p class="empty-cell">No intervention records yet.</p>';

  // Profile
  $('detail-profile').innerHTML = `
    <div class="profile-grid">
      <div class="pf-row"><span>State</span><span>${v.state}</span></div>
      <div class="pf-row"><span>Age</span><span>${v.age}</span></div>
      <div class="pf-row"><span>Gender</span><span>${v.gender}</span></div>
      <div class="pf-row"><span>Social Category</span><span>${v.social_category}</span></div>
      <div class="pf-row"><span>Offence Type</span><span>${v.offence_type}</span></div>
      <div class="pf-row"><span>Severity</span><span>${v.severity}/5</span></div>
      <div class="pf-row"><span>Total Check-ins</span><span>${d.total_interactions}</span></div>
    </div>
  `;
}

// ─── SCREEN 5: ALERTS ────────────────────────────────────────────
let _allAlerts = [];
let _ackVictimId = null;

async function loadAlerts() {
  $('alert-list').innerHTML = '<div class="loading-cell">Loading alerts…</div>';
  try {
    const d = await api('/demo/alerts');
    _allAlerts = d.alerts;
    $('al-kpis').innerHTML =
      kpiCard(d.total, 'Total Alerts') +
      kpiCard(d.open, 'Open', 'kpi-high') +
      kpiCard(d.total - d.open, 'Acknowledged', 'kpi-low') +
      kpiCard(d.alerts.filter(a => a.priority === 'critical').length, 'Critical', 'kpi-critical');
    filterAlerts();
  } catch (e) {
    $('alert-list').innerHTML = `<div class="error-cell">${e.message}</div>`;
  }
}

function filterAlerts() {
  const f = $('al-filter').value;
  let alerts = _allAlerts.filter(a =>
    !f || a.status === f || a.priority === f
  );
  if (!alerts.length) {
    $('alert-list').innerHTML = '<div class="empty-state">No alerts match the filter.</div>';
    return;
  }
  $('alert-list').innerHTML = alerts.map(a => `
    <div class="alert-card ${riskClass(a.priority)} ${a.status === 'acknowledged' ? 'ack' : ''}">
      <div class="alert-top">
        <div class="alert-id">
          <span class="risk-badge ${riskClass(a.priority)}">${riskLabel(a.priority)}</span>
          <code>${a.victim_id}</code>
          ${a.dds != null ? `<span class="alert-dds">DDS: ${a.dds}</span>` : ''}
        </div>
        <div class="alert-time">${relativeTime(a.created_at)}</div>
      </div>
      <div class="alert-action">${a.recommended_action}</div>
      <div class="alert-notif">
        ${a.notification_log.map(n => `
          <span class="notif-chip ${n.status}">${n.channel} ${n.status === 'delivered' ? '✓' : '✗'}</span>
        `).join('')}
      </div>
      <div class="alert-footer">
        ${a.status === 'open'
          ? `<button class="btn-primary sm" onclick="openAckModal('${a.victim_id}')">✅ Acknowledge</button>`
          : `<span class="ack-label">✓ Acknowledged</span>`
        }
        <button class="btn-outline sm" onclick="openVictimDetail('${a.victim_id}')">View Profile →</button>
      </div>
    </div>
  `).join('');
}

function openAckModal(victimId) {
  _ackVictimId = victimId;
  $('ack-victim-id').textContent = victimId;
  $('ack-note').value = '';
  $('ack-modal').classList.remove('hidden');
}

function closeAckModal() {
  $('ack-modal').classList.add('hidden');
  _ackVictimId = null;
}

async function submitAcknowledge() {
  if (!_ackVictimId) return;
  try {
    await api('/demo/acknowledge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ victim_id: _ackVictimId, counsellor_note: $('ack-note').value }),
    });
    closeAckModal();
    await loadAlerts();
  } catch (e) {
    alert('Error: ' + e.message);
  }
}

// ─── SCREEN 6: ANALYTICS ─────────────────────────────────────────
let _pieChart = null;
let _stageChart = null;

async function loadAnalytics() {
  try {
    const d = await api('/demo/analytics');
    renderAnalytics(d);
  } catch (e) {
    $('an-kpis').innerHTML = `<div class="error-cell">${e.message}</div>`;
  }
}

function renderAnalytics(d) {
  $('an-kpis').innerHTML =
    kpiCard(d.total_victims, 'Total Victims') +
    kpiCard(d.high_risk_count, 'High-Risk Cases', 'kpi-high') +
    kpiCard(`${d.intervention_success_rate}%`, 'Intervention Success Rate', 'kpi-low') +
    kpiCard(d.total_alerts, 'Total Alerts Generated');

  // State heatmap table
  const hm = d.state_heatmap;
  $('an-heatmap').innerHTML = `
    <table class="heatmap-table">
      <thead><tr><th>State</th><th>Victims</th><th>Avg DDS</th><th>High/Critical</th><th>Risk Rate</th><th>Level</th></tr></thead>
      <tbody>
        ${hm.map(s => {
          const riskRate = s.risk_rate;
          const level = riskRate >= 50 ? 'critical' : riskRate >= 30 ? 'high' : riskRate >= 15 ? 'moderate' : 'low';
          return `<tr>
            <td><strong>${s.state}</strong></td>
            <td>${s.total_victims}</td>
            <td><span class="${riskClass(level)}">${s.avg_dds}</span></td>
            <td>${s.high_critical_count}</td>
            <td>
              <div class="heat-bar-wrap">
                <div class="heat-bar ${riskClass(level)}" style="width:${Math.min(riskRate, 100)}%"></div>
                <span>${riskRate}%</span>
              </div>
            </td>
            <td><span class="risk-badge ${riskClass(level)}">${riskLabel(level)}</span></td>
          </tr>`;
        }).join('')}
      </tbody>
    </table>
  `;

  // Risk pie
  const riskDist = d.risk_distribution;
  if (_pieChart) { _pieChart.destroy(); _pieChart = null; }
  _pieChart = new Chart($('riskPieChart').getContext('2d'), {
    type: 'doughnut',
    data: {
      labels: ['Low', 'Moderate', 'High', 'Critical'],
      datasets: [{
        data: [riskDist.low || 0, riskDist.moderate || 0, riskDist.high || 0, riskDist.critical || 0],
        backgroundColor: ['#22c55e', '#eab308', '#f97316', '#ef4444'],
        borderColor: '#0f172a',
        borderWidth: 3,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#cbd5e1', padding: 16 } },
      },
    },
  });

  // Case stage bar
  const stages = d.case_stage_breakdown;
  const stageKeys = Object.keys(stages);
  if (_stageChart) { _stageChart.destroy(); _stageChart = null; }
  _stageChart = new Chart($('stageBarChart').getContext('2d'), {
    type: 'bar',
    data: {
      labels: stageKeys,
      datasets: [{
        label: 'Victims',
        data: stageKeys.map(k => stages[k]),
        backgroundColor: '#38bdf8',
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } },
        x: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } },
      },
    },
  });

  // Intervention panel
  $('an-intervention').innerHTML = `
    <div class="iv-stat-grid">
      <div class="iv-stat"><div class="iv-num">${d.total_alerts}</div><div class="iv-lbl">Alerts Generated</div></div>
      <div class="iv-stat"><div class="iv-num">${d.acknowledged_alerts}</div><div class="iv-lbl">Acknowledged</div></div>
      <div class="iv-stat"><div class="iv-num iv-green">${d.intervention_success_rate}%</div><div class="iv-lbl">Success Rate</div></div>
    </div>
    <div class="iv-progress-wrap">
      <div class="iv-progress-bar" style="width:${d.intervention_success_rate}%"></div>
    </div>
    <p class="iv-note">Success = alert acknowledged by a counsellor before crisis escalation (synthetic metric).</p>
  `;
}

// ─── INIT ────────────────────────────────────────────────────────
checkHealth();
setInterval(checkHealth, 30000);
loadHome();

// ═══════════════════════════════════════════════════════════════════
// ADDITIVE: GAP 4 — Voice / IVRS tab + Channel chips
// ═══════════════════════════════════════════════════════════════════

// ─── Check-in Tab Switching ───────────────────────────────────────
function switchCheckinTab(tab) {
  // Toggle tab buttons
  document.querySelectorAll('.ci-tab').forEach(b => b.classList.remove('active'));
  const activeBtn = $(`tab-${tab}`);
  if (activeBtn) activeBtn.classList.add('active');

  // Toggle panes
  document.querySelectorAll('.ci-pane').forEach(p => p.classList.add('hidden'));
  const pane = $(`ci-pane-${tab}`);
  if (pane) pane.classList.remove('hidden');
}

// ─── IVRS Simulation ─────────────────────────────────────────────
const IVRS_TRANSCRIPT = 'I feel afraid. The threats have not stopped. I cannot sleep.';

async function simulateIVRS() {
  const btn = $('ivrs-btn');
  const dot = $('voice-dot');
  const label = $('waveform-label');
  const polyline = $('wavePolyline');

  // 1. Show connecting state
  btn.disabled = true;
  btn.textContent = '⏳ Connecting to IVRS…';
  if (dot) dot.classList.add('dot-active');

  // Animate waveform — bump opacity and jitter points
  if (polyline) {
    polyline.style.opacity = '1';
    polyline.style.transition = 'opacity 0.3s';
  }
  if (label) label.textContent = 'Connecting to IVRS…';

  await _sleep(1000);
  if (label) label.textContent = 'Call in progress…';
  btn.textContent = '🎙️ Recording…';

  // Animate waveform points during "call"
  let animFrame = 0;
  const waveInterval = setInterval(() => {
    if (!polyline) return;
    animFrame++;
    const pts = [];
    for (let x = 0; x <= 500; x += 10) {
      const base = 40;
      const amp = 18 + Math.random() * 14;
      const y = base + (Math.sin((x + animFrame * 8) * 0.06) * amp) + (Math.random() - 0.5) * 6;
      pts.push(`${x},${Math.max(8, Math.min(72, y)).toFixed(1)}`);
    }
    polyline.setAttribute('points', pts.join(' '));
  }, 80);

  await _sleep(2200);
  clearInterval(waveInterval);

  // 2. Show transcript
  if (label) label.textContent = 'Call ended — transcribing…';
  await _sleep(400);

  const transcript = $('voice-transcript');
  if (transcript) transcript.classList.remove('hidden');
  if (label) label.textContent = 'Extracting acoustic features…';

  await _sleep(600);

  // 3. Show feature table
  const features = $('voice-features');
  if (features) features.classList.remove('hidden');
  if (label) label.textContent = 'Analysis complete';

  if (dot) dot.classList.remove('dot-active');
  if (dot) dot.classList.add('dot-done');

  btn.textContent = '✅ IVRS Call Simulated';

  // 4. Run DDS scoring on the transcript text
  try {
    const r = await api('/demo/checkin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: IVRS_TRANSCRIPT,
        language: 'en',
        sentiment_score: -0.75,   // derived from MFCC2 elevation
        missed_checkins: 2,
        case_delay_days: 180,
      }),
    });
    renderVoiceResult(r);
  } catch (e) {
    const vr = $('voice-result');
    if (vr) { vr.classList.remove('hidden'); vr.innerHTML = `<p class="error-cell">Scoring error: ${e.message}</p>`; }
  }
}

function _sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function renderVoiceResult(r) {
  const result = $('voice-result');
  if (!result) return;
  result.classList.remove('hidden');
  result.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

  $('voice-dds-num').textContent = r.dds.toFixed(1);

  const badge = $('voice-risk-badge');
  badge.textContent = riskLabel(r.risk_level);
  badge.className = `risk-badge-large ${riskClass(r.risk_level)}`;

  // Reuse the same drawDDSGauge logic with a different canvas
  const canvas = $('ddsGaugeVoice');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const cx = 100, cy = 110, rad = 80;
    const startAngle = Math.PI;
    const valueAngle = startAngle + (r.dds / 100) * Math.PI;
    ctx.beginPath();
    ctx.arc(cx, cy, rad, startAngle, 2 * Math.PI);
    ctx.lineWidth = 18; ctx.strokeStyle = '#1e293b'; ctx.stroke();
    const color = r.dds >= 80 ? '#ef4444' : r.dds >= 65 ? '#f97316' : r.dds >= 40 ? '#eab308' : '#22c55e';
    ctx.beginPath();
    ctx.arc(cx, cy, rad, startAngle, valueAngle);
    ctx.lineWidth = 18; ctx.strokeStyle = color; ctx.lineCap = 'round'; ctx.stroke();
    const nx = cx + (rad - 10) * Math.cos(valueAngle);
    const ny = cy + (rad - 10) * Math.sin(valueAngle);
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(nx, ny);
    ctx.strokeStyle = '#f1f5f9'; ctx.lineWidth = 3; ctx.stroke();
    ctx.beginPath(); ctx.arc(cx, cy, 6, 0, 2 * Math.PI);
    ctx.fillStyle = '#f1f5f9'; ctx.fill();
    ctx.fillStyle = '#94a3b8'; ctx.font = '11px Inter,sans-serif';
    ctx.fillText('0', cx - rad - 4, cy + 14);
    ctx.fillText('100', cx + rad - 18, cy + 14);
  }

  $('voice-factors').innerHTML = r.top_factors.map(f => `
    <div class="factor-row">
      <div class="factor-name">${f.factor}</div>
      <div class="factor-bar-wrap">
        <div class="factor-bar" style="width:${Math.min(f.contribution, 100)}%"></div>
      </div>
      <div class="factor-val">+${f.contribution.toFixed(1)} pts</div>
    </div>
  `).join('');

  $('voice-intervention').textContent = r.recommended_intervention;
}

// ─── Expander toggle ─────────────────────────────────────────────
function toggleExpander(btn) {
  const body = btn.nextElementSibling;
  const arrow = btn.querySelector('.expander-arrow');
  if (!body) return;
  body.classList.toggle('hidden');
  if (arrow) arrow.textContent = body.classList.contains('hidden') ? '▼' : '▲';
}

// ─── Alert channel chips (patch filterAlerts rendering) ──────────
// MOCK channel assignment: deterministic from victim_id hash
const _CHANNELS = ['Chatbot', 'IVRS', 'SMS', 'App'];
const _CHANNEL_ICONS = { Chatbot: '💬', IVRS: '📞', SMS: '📱', App: '📲' };

function _alertChannel(victimId) {
  let h = 0;
  for (let i = 0; i < victimId.length; i++) h = (h * 31 + victimId.charCodeAt(i)) & 0xffff;
  return _CHANNELS[h % _CHANNELS.length];
}

function channelChip(victimId) {
  const ch = _alertChannel(victimId);
  const icon = _CHANNEL_ICONS[ch] || '📡';
  const isVoice = ch === 'IVRS';
  return `<span class="channel-chip ${isVoice ? 'chip-voice' : ''}">${icon} ${ch}${isVoice ? ' 〜' : ''}</span>`;
}

// Override filterAlerts to inject channel chip — keeps all existing logic intact
const _origFilterAlerts = filterAlerts;
// Redefine filterAlerts to inject channel chips into each alert card
function filterAlerts() {
  const f = $('al-filter').value;
  let alerts = _allAlerts.filter(a =>
    !f || a.status === f || a.priority === f
  );
  if (!alerts.length) {
    $('alert-list').innerHTML = '<div class="empty-state">No alerts match the filter.</div>';
    return;
  }
  $('alert-list').innerHTML = alerts.map(a => `
    <div class="alert-card ${riskClass(a.priority)} ${a.status === 'acknowledged' ? 'ack' : ''}">
      <div class="alert-top">
        <div class="alert-id">
          <span class="risk-badge ${riskClass(a.priority)}">${riskLabel(a.priority)}</span>
          <code>${a.victim_id}</code>
          ${a.dds != null ? `<span class="alert-dds">DDS: ${a.dds}</span>` : ''}
          ${channelChip(a.victim_id)}
        </div>
        <div class="alert-time">${relativeTime(a.created_at)}</div>
      </div>
      <div class="alert-action">${a.recommended_action}</div>
      <div class="alert-notif">
        ${a.notification_log.map(n => `
          <span class="notif-chip ${n.status}">${n.channel} ${n.status === 'delivered' ? '✓' : '✗'}</span>
        `).join('')}
      </div>
      <div class="alert-footer">
        ${a.status === 'open'
          ? `<button class="btn-primary sm" onclick="openAckModal('${a.victim_id}')">✅ Acknowledge</button>`
          : `<span class="ack-label">✓ Acknowledged</span>`
        }
        <button class="btn-outline sm" onclick="openVictimDetail('${a.victim_id}')">View Profile →</button>
      </div>
    </div>
  `).join('');
}
