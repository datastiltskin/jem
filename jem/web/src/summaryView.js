// JEM — Summary View
// Landing page: stat band, risk-distribution small multiples, high-risk registry, all-entities table.

import { State } from './state.js';
import { buildAppellateHierarchy } from './entityConnections.js';

const RISK_COLORS = {
  low:      '#16a34a',
  moderate: '#d97706',
  high:     '#dc2626',
  severe:   '#7c3aed',
};

const RISK_ORDER = ['severe', 'high', 'moderate', 'low'];

const CLUSTER_LABELS = {
  constitutional_courts:   'Constitutional Courts',
  tribunals_adr:           'Tribunals & ADR',
  regulatory_bodies:       'Regulators',
  consumer_redressal:      'Consumer',
  arbitration:             'Arbitration',
  executive_interface:     'Executive Interface',
  digital_infrastructure:  'Digital Infrastructure',
  financing_audit:         'Finance & Audit',
  training_professional:   'Training & Professional',
  appointment_bodies:      'Appointment Bodies',
  legislative_executive:   'Legislative / Executive',
  subordinate_courts:      'Subordinate Courts',
  security:                'Security',
  people_roles:            'People / Roles',
};

// Clusters where IR scores are not computed
const SCORE_EXCLUDED_CLUSTERS = new Set(['legislative_executive', 'people_roles']);

// ── Helpers ───────────────────────────────────────────────────────────────────

function riskLevelLabel(level) {
  if (!level) return '—';
  return level.charAt(0).toUpperCase() + level.slice(1);
}

function statusPill(e) {
  if (e.operational_status === 'Not_Constituted') return '<span class="sum-pill sum-pill-nc">NC</span>';
  if (e.operational_status === 'Abolished') return '<span class="sum-pill sum-pill-abolished">Abolished</span>';
  if (e.operational_status === 'Partial_Operational') return '<span class="sum-pill sum-pill-partial">Partial</span>';
  return '';
}

function computeAvgDisposalRate(entities) {
  const withRate = entities.filter(e => e._detail?.case_volume?.disposal_rate != null);
  if (!withRate.length) return null;
  const avg = withRate.reduce((s, e) => s + e._detail.case_volume.disposal_rate, 0) / withRate.length;
  return avg.toFixed(2);
}

function typeLabel(type) {
  if (!type) return '—';
  return type.replace(/([A-Z])/g, ' $1').trim();
}

function govLevelLabel(level) {
  const MAP = {
    Central:             'Central',
    State:               'State',
    UT:                  'UT',
    Shared_MultiState:   'Multi-State',
    Shared_CentralState: 'Central–State',
  };
  return MAP[level] || level || '—';
}

function irScoreToLevel(score) {
  if (score >= 9) return 'severe';
  if (score >= 6) return 'high';
  if (score >= 3) return 'moderate';
  return 'low';
}

// ── Bubble strip plot ─────────────────────────────────────────────────────────
// One row per cluster. X = structural_health score (0.0–1.0, MASTER composite).
// Left = critical, right = healthy. Bubble area ∝ entity count at that health
// bucket. Color = health band. Click bubble → drill-down with IR + DP
// constituent breakdowns for the entities at that bucket.

const HEALTH_MAX  = 1.0;
const HEALTH_BUCKET = 0.05;    // group entities into 0.05-wide health buckets
const ROW_H       = 40;        // px per cluster row
const LABEL_W     = 148;       // px for left cluster label column
const AXIS_H      = 28;        // px for x-axis
const HEADER_H    = 18;        // px for column header
const PLOT_PAD_R  = 20;        // right padding
const MAX_BUBBLE_R = 15;       // max bubble radius in px

// Health bands (matching derive.py + ring legend)
const HEALTH_COLORS = {
  critical: '#e74c3c',
  at_risk:  '#f39c12',
  watch:    '#f1c40f',
  healthy:  '#27ae60',
};
// Zones listed left→right in display order (reversed: healthy on left, critical on right).
const HEALTH_ZONES = [
  { x0: 0.8, x1: 1.0, level: 'healthy',  fill: '#f0fdf4' },
  { x0: 0.6, x1: 0.8, level: 'watch',    fill: '#fefce8' },
  { x0: 0.3, x1: 0.6, level: 'at_risk',  fill: '#fff7ed' },
  { x0: 0.0, x1: 0.3, level: 'critical', fill: '#fef2f2' },
];

const HEALTH_LEVEL_LABELS = {
  critical: 'Critical',
  at_risk:  'At Risk',
  watch:    'Watch',
  healthy:  'Healthy',
};

function healthLevelLabel(level) {
  return HEALTH_LEVEL_LABELS[level] || (level || '—');
}

// Reversed axis: health=1.0 → left edge, health=0.0 → right edge.
function scoreToX(score, plotW) {
  return LABEL_W + ((HEALTH_MAX - score) / HEALTH_MAX) * plotW;
}

function healthBandFor(score) {
  if (score == null) return null;
  if (score < 0.3) return 'critical';
  if (score < 0.6) return 'at_risk';
  if (score < 0.8) return 'watch';
  return 'healthy';
}

function buildStripData(entities) {
  // For each cluster: Map of bucket → { count, level, entityIds, irAvg, dpAvg }
  const clusters = {};
  entities.forEach(e => {
    const cl = e.cluster;
    if (!cl || SCORE_EXCLUDED_CLUSTERS.has(cl)) return;
    const health = e.derived?.structural_health_score;
    if (health == null) return;
    const bucket = Math.round(health / HEALTH_BUCKET) * HEALTH_BUCKET;
    const key = bucket.toFixed(2);
    const level = healthBandFor(bucket);
    if (!clusters[cl]) clusters[cl] = {};
    if (!clusters[cl][key]) {
      clusters[cl][key] = { count: 0, level, ids: [], irSum: 0, dpSum: 0, bucket };
    }
    const slot = clusters[cl][key];
    slot.count++;
    slot.ids.push(e.id);
    slot.irSum += e.derived?.independence_risk_score || 0;
    slot.dpSum += e.derived?.discretionary_power_score || 0;
  });

  // Sort clusters by weighted avg health (worst — lowest health — first)
  return Object.entries(clusters)
    .filter(([, pts]) => Object.keys(pts).length > 0)
    .map(([cl, pts]) => {
      const entries = Object.entries(pts).map(([, d]) => ({
        score: d.bucket,
        count: d.count,
        level: d.level,
        ids: d.ids,
        irAvg: d.irSum / d.count,
        dpAvg: d.dpSum / d.count,
      }));
      const total = entries.reduce((s, d) => s + d.count, 0);
      const wavg = entries.reduce((s, d) => s + d.score * d.count, 0) / (total || 1);
      return { cl, entries, total, wavg };
    })
    .sort((a, b) => a.wavg - b.wavg);
}

function renderStripPlot(entities, svgWidth) {
  const plotW = svgWidth - LABEL_W - PLOT_PAD_R;
  const rows  = buildStripData(entities);
  const svgH  = HEADER_H + rows.length * ROW_H + AXIS_H;

  let svg = `<svg class="strip-svg" viewBox="0 0 ${svgWidth} ${svgH}"
    role="img" aria-label="Structural health distribution by cluster">`;

  // ── Background health zones ────────────────────────────────────────────────
  const zonesY = HEADER_H;
  const zonesH = rows.length * ROW_H;
  HEALTH_ZONES.forEach(z => {
    const xa = scoreToX(z.x0, plotW);
    const xb = scoreToX(z.x1, plotW);
    const zx = Math.min(xa, xb);
    const zw = Math.abs(xb - xa);
    svg += `<rect x="${zx}" y="${zonesY}" width="${zw}" height="${zonesH}"
      fill="${z.fill}" />`;
  });

  // ── Zone label row (header) ────────────────────────────────────────────────
  HEALTH_ZONES.forEach(z => {
    const zx = scoreToX((z.x0 + z.x1) / 2, plotW);
    svg += `<text x="${zx}" y="${HEADER_H - 5}" text-anchor="middle"
      font-size="9" fill="${HEALTH_COLORS[z.level]}" font-weight="600"
      opacity="0.85">${healthLevelLabel(z.level)}</text>`;
  });

  // ── Vertical grid lines at band boundaries ────────────────────────────────
  [0.0, 0.3, 0.6, 0.8, 1.0].forEach(tick => {
    const gx = scoreToX(tick, plotW);
    svg += `<line x1="${gx}" y1="${HEADER_H}" x2="${gx}" y2="${HEADER_H + zonesH}"
      stroke="#ddd" stroke-width="1" />`;
  });

  // ── Row dividers ───────────────────────────────────────────────────────────
  rows.forEach((_, i) => {
    const ry = HEADER_H + i * ROW_H;
    svg += `<line x1="0" y1="${ry}" x2="${svgWidth}" y2="${ry}"
      stroke="#ebebeb" stroke-width="1" />`;
  });

  // ── Row hover background rects (transparent; JS sets fill on hover) ────────
  rows.forEach(({ cl }, i) => {
    const ry = HEADER_H + i * ROW_H;
    svg += `<rect class="strip-row-bg" data-cluster-id="${cl}"
      x="0" y="${ry}" width="${svgWidth}" height="${ROW_H}"
      fill="transparent" pointer-events="none" />`;
  });

  // ── Center guide lines (baseline for each cluster row) ────────────────────
  rows.forEach((_, i) => {
    const cy = HEADER_H + i * ROW_H + ROW_H / 2;
    svg += `<line class="strip-guide"
      x1="${LABEL_W}" y1="${cy}" x2="${svgWidth - PLOT_PAD_R}" y2="${cy}"
      stroke="#d8d8d3" stroke-width="0.75" stroke-dasharray="3 4"
      pointer-events="none" />`;
  });

  // ── Cluster labels + bubbles ───────────────────────────────────────────────
  rows.forEach(({ cl, entries, total }, ri) => {
    const cy = HEADER_H + ri * ROW_H + ROW_H / 2;
    const label = CLUSTER_LABELS[cl] || cl;
    const shortLabel = label.length > 22 ? label.slice(0, 20) + '…' : label;

    // Cluster label (left column, clickable — opens drill-down for whole cluster)
    svg += `<text class="strip-cluster-label" data-cluster-id="${cl}"
      x="${LABEL_W - 8}" y="${cy + 4}" text-anchor="end"
      font-size="11" fill="#33332e" cursor="pointer">
      ${shortLabel}
      <title>Click to see all ${total} ${label} entities</title>
    </text>`;
    svg += `<text x="${LABEL_W - 8}" y="${cy + 15}" text-anchor="end"
      font-size="9" fill="#86857c">${total}</text>`;

    // Bubbles — one per health bucket in this cluster
    entries.forEach(({ score, count, level, ids, irAvg, dpAvg }) => {
      const bx = scoreToX(score, plotW);
      const r  = Math.min(MAX_BUBBLE_R, Math.max(3, Math.sqrt(count) * 2.8));
      const color = HEALTH_COLORS[level] || '#aaa';
      const encodedIds = encodeURIComponent(JSON.stringify(ids));
      const titleText = `${count} ${count === 1 ? 'entity' : 'entities'} · ${label}
Health ≈ ${score.toFixed(2)} (${healthLevelLabel(level)})
  ↳ IR avg ${irAvg.toFixed(1)} · DP avg ${dpAvg.toFixed(1)}`;

      svg += `<circle class="strip-bubble"
        cx="${bx}" cy="${cy}" r="${r}"
        fill="${color}" fill-opacity="0.75"
        stroke="${color}" stroke-width="1" stroke-opacity="0.9"
        data-cluster-id="${cl}" data-score="${score.toFixed(2)}" data-ids="${encodedIds}"
        cursor="pointer" style="transition:opacity .15s">
        <title>${titleText}</title>
      </circle>`;

      // Count label inside bubble if it fits
      if (r >= 10) {
        svg += `<text x="${bx}" y="${cy + 4}" text-anchor="middle"
          font-size="${Math.min(10, r * 0.85)}" fill="#fff" font-weight="600"
          pointer-events="none">${count}</text>`;
      }
    });
  });

  // ── X axis ────────────────────────────────────────────────────────────────
  const axisY = HEADER_H + zonesH + 4;
  svg += `<line x1="${LABEL_W}" y1="${axisY}" x2="${svgWidth - PLOT_PAD_R}" y2="${axisY}"
    stroke="#ccc" stroke-width="1" />`;
  [1.0, 0.8, 0.6, 0.4, 0.2, 0.0].forEach(tick => {
    const tx = scoreToX(tick, plotW);
    svg += `<text x="${tx}" y="${axisY + 13}" text-anchor="middle"
      font-size="9" fill="#86857c">${tick.toFixed(1)}</text>`;
  });
  svg += `<text x="${LABEL_W + plotW / 2}" y="${axisY + 24}" text-anchor="middle"
    font-size="9" fill="#86857c">← Healthy · Structural Health · Critical →</text>`;

  svg += `</svg>`;
  return svg;
}

// ── High-risk entity registry ─────────────────────────────────────────────────

// ── Spotlight carousel ────────────────────────────────────────────────────────
// Featured set: critical + at_risk entities, worst-first. One large card per slide.

function spotlightSet(entities) {
  return entities
    .filter(e => {
      const lvl = e.derived?.structural_health_level;
      return lvl === 'critical' || lvl === 'at_risk';
    })
    .sort((a, b) =>
      (a.derived?.structural_health_score ?? 999) - (b.derived?.structural_health_score ?? 999)
    );
}

function topFactors(breakdown, n = 3) {
  if (!breakdown) return [];
  return Object.entries(breakdown)
    .filter(([, v]) => v > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, n);
}

function renderSpotlightCard(e) {
  const d = e.derived || {};
  const health = d.structural_health_score;
  const healthLvl = d.structural_health_level || healthBandFor(health);
  const healthColor = HEALTH_COLORS[healthLvl] || '#aaa';
  const healthPct = health != null ? Math.max(0, Math.min(100, health * 100)) : 0;

  const irLvl = d.independence_risk_level;
  const irColor = RISK_COLORS[irLvl] || '#6b7280';
  const ir = d.independence_risk_score;
  const dp = d.discretionary_power_score;

  const irFactors = topFactors(d.independence_risk_breakdown, 3);
  const dpFactors = topFactors(d.discretionary_power_breakdown, 3);

  const factorList = (rows, color) => rows.length
    ? rows.map(([reason, pts]) => `
        <div class="dr-bd-row">
          <span class="dr-bd-pts" style="color:${color}">+${pts}</span>
          <span class="dr-bd-reason">${reason}</span>
        </div>`).join('')
    : '<div class="dr-empty">No leaf factors recorded.</div>';

  const meta = [
    e.created_year ? `Est. ${e.created_year}` : null,
    govLevelLabel(e.level_of_government),
    typeLabel(e.type),
  ].filter(Boolean).join(' · ');

  return `<article class="sp-card" data-entity-id="${e.id}">
    <header class="sp-card-head">
      <div class="sp-card-name">${e.name}${statusPill(e)}</div>
      <div class="sp-card-band" style="background:${healthColor}1a;color:${healthColor};border:1px solid ${healthColor}66">
        ${healthLevelLabel(healthLvl).toUpperCase()}
      </div>
    </header>

    <div class="sp-card-master">
      <div class="sp-card-master-row">
        <span class="sp-card-master-label">Structural Health</span>
        <span class="sp-card-master-number" style="color:${healthColor}">${health != null ? health.toFixed(2) : '—'}</span>
      </div>
      <div class="sp-card-master-bar">
        <div class="sp-card-master-fill" style="width:${healthPct}%;background:${healthColor}"></div>
      </div>
    </div>

    <div class="sp-card-constituents">
      <div class="sp-card-const-col">
        <div class="sp-card-const-head" style="color:${irColor}">
          ↳ Independence Risk · ${ir ?? '—'}${irLvl ? ' · ' + irLvl.toUpperCase() : ''}
        </div>
        ${factorList(irFactors, irColor)}
      </div>
      <div class="sp-card-const-col">
        <div class="sp-card-const-head" style="color:#6366f1">
          ↳ Discretionary Power · ${dp ?? '—'}
        </div>
        ${factorList(dpFactors, '#6366f1')}
      </div>
    </div>

    <div class="sp-card-meta">${meta}</div>

    <div class="sp-card-actions">
      <button class="sp-action sp-open" data-entity-id="${e.id}">Open profile →</button>
      <button class="sp-action sp-report" data-entity-id="${e.id}">↓ Report</button>
    </div>
  </article>`;
}

function renderSpotlightCarousel(featured, totalEntities) {
  if (!featured.length) {
    return `<div class="sp-empty">
      <p>No entities are currently in critical or at-risk health bands.</p>
      <button class="sp-browse-all" id="sp-browse-all">Browse all ${totalEntities} entities →</button>
    </div>`;
  }
  const cards = featured.map(renderSpotlightCard).join('');
  const useDots = featured.length <= 10;
  const dots = useDots
    ? featured.map((_, i) => `<button class="sp-dot${i === 0 ? ' active' : ''}" data-i="${i}" aria-label="Go to card ${i + 1}"></button>`).join('')
    : '';
  return `<div class="sp-carousel" tabindex="0">
    <button class="sp-arrow sp-arrow-prev" aria-label="Previous">‹</button>
    <div class="sp-viewport">
      <div class="sp-track" id="sp-track" style="transform:translateX(0%)">${cards}</div>
    </div>
    <button class="sp-arrow sp-arrow-next" aria-label="Next">›</button>
    <div class="sp-footer">
      <div class="sp-progress">
        ${useDots
          ? `<div class="sp-dots">${dots}</div>`
          : `<span class="sp-counter"><span id="sp-counter-i">1</span> / ${featured.length}</span>`}
      </div>
      <div class="sp-footer-right">
        <span class="sp-footer-label"><span id="sp-counter-label">${featured.length}</span> critical &amp; at-risk</span>
        <button class="sp-browse-all" id="sp-browse-all">Browse all ${totalEntities} →</button>
      </div>
    </div>
  </div>`;
}

// ── Catalog drawer (full entity list, slide-in) ───────────────────────────────

const _drawerState = { rendered: false, search: '', band: 'all' };

function entityMatchesSearch(e, q) {
  if (!q) return true;
  const needle = q.toLowerCase();
  return (e.name || '').toLowerCase().includes(needle)
    || (e.abbreviation || '').toLowerCase().includes(needle);
}

function renderDrawerList(entities) {
  const filtered = entities
    .filter(e => {
      if (_drawerState.band !== 'all') {
        const lvl = e.derived?.structural_health_level;
        if (_drawerState.band === 'unscored') {
          if (lvl) return false;
        } else if (lvl !== _drawerState.band) return false;
      }
      return entityMatchesSearch(e, _drawerState.search);
    });

  if (!filtered.length) {
    return '<p class="cat-drawer-empty">No entities match the current filter.</p>';
  }

  // Group by cluster
  const grouped = {};
  filtered.forEach(e => {
    const cl = e.cluster || '_unknown';
    (grouped[cl] ||= []).push(e);
  });

  const clusterIds = Object.keys(grouped).sort((a, b) => {
    const aw = grouped[a].reduce((s, e) => s + (e.derived?.structural_health_score ?? 1), 0) / grouped[a].length;
    const bw = grouped[b].reduce((s, e) => s + (e.derived?.structural_health_score ?? 1), 0) / grouped[b].length;
    return aw - bw;
  });

  return clusterIds.map(cl => {
    const members = grouped[cl].slice().sort((a, b) =>
      (a.derived?.structural_health_score ?? 999) - (b.derived?.structural_health_score ?? 999)
    );
    const rows = members.map(e => {
      const d = e.derived || {};
      const lvl = d.structural_health_level || healthBandFor(d.structural_health_score);
      const color = lvl ? (HEALTH_COLORS[lvl] || '#aaa') : '#aaa';
      const health = d.structural_health_score;
      return `<button class="cat-row" data-entity-id="${e.id}" data-report="0">
        <span class="cat-row-health" style="color:${color}">${health != null ? health.toFixed(2) : '—'}</span>
        <span class="cat-row-name">${e.name}${statusPill(e)}</span>
        <span class="cat-row-ir">IR ${d.independence_risk_score ?? '—'}</span>
        <span class="cat-row-dp">DP ${d.discretionary_power_score ?? '—'}</span>
        <span class="cat-row-report" data-report="1" data-entity-id="${e.id}" title="Jump to entity report">↓</span>
      </button>`;
    }).join('');
    return `<section class="cat-drawer-cluster">
      <header class="cat-drawer-cluster-head">
        <span>${CLUSTER_LABELS[cl] || cl}</span>
        <span class="cat-drawer-cluster-count">${members.length}</span>
      </header>
      <div class="cat-drawer-rows">${rows}</div>
    </section>`;
  }).join('');
}

function renderCatalogDrawer(entities) {
  const bands = ['all', 'critical', 'at_risk', 'watch', 'healthy', 'unscored'];
  const bandLabel = {
    all: 'All',
    critical: 'Critical',
    at_risk: 'At Risk',
    watch: 'Watch',
    healthy: 'Healthy',
    unscored: 'Unscored',
  };
  const chips = bands.map(b => `
    <button class="cat-drawer-chip${b === _drawerState.band ? ' active' : ''}" data-band="${b}">${bandLabel[b]}</button>
  `).join('');

  return `<header class="cat-drawer-head">
      <div class="cat-drawer-title">Browse all ${entities.length} entities</div>
      <button class="cat-drawer-close" id="cat-drawer-close" aria-label="Close">✕</button>
    </header>
    <div class="cat-drawer-controls">
      <input type="search" class="cat-drawer-search" id="cat-drawer-search"
        placeholder="Search by name or abbreviation…" value="${_drawerState.search}">
      <div class="cat-drawer-chips" role="group" aria-label="Health band filter">${chips}</div>
    </div>
    <div class="cat-drawer-list" id="cat-drawer-list">${renderDrawerList(entities)}</div>`;
}

// ── Cluster drill-down overlay ────────────────────────────────────────────────

function buildFactorFrequency(members, breakdownKey) {
  const counts = new Map();
  members.forEach(e => {
    const bd = (e.derived || {})[breakdownKey];
    if (!bd) return;
    for (const [reason, pts] of Object.entries(bd)) {
      if (!counts.has(reason)) counts.set(reason, { count: 0, total: 0 });
      const slot = counts.get(reason);
      slot.count++;
      slot.total += pts;
    }
  });
  return [...counts.entries()]
    .map(([reason, v]) => ({ reason, count: v.count, total: v.total }))
    .sort((a, b) => b.count - a.count || b.total - a.total);
}

function renderPatternTab(members) {
  const healthValues = members.map(e => e.derived?.structural_health_score).filter(v => v != null);
  const irValues = members.map(e => e.derived?.independence_risk_score).filter(v => v != null);
  const dpValues = members.map(e => e.derived?.discretionary_power_score).filter(v => v != null);

  const avgHealth = healthValues.length ? healthValues.reduce((s, v) => s + v, 0) / healthValues.length : null;
  const avgIR = irValues.length ? irValues.reduce((s, v) => s + v, 0) / irValues.length : null;
  const avgDP = dpValues.length ? dpValues.reduce((s, v) => s + v, 0) / dpValues.length : null;

  const irFactors = buildFactorFrequency(members, 'independence_risk_breakdown').slice(0, 6);
  const dpFactors = buildFactorFrequency(members, 'discretionary_power_breakdown').slice(0, 6);

  const factorRow = (f, n) => `
    <div class="dr-factor-row">
      <span class="dr-factor-reason">${f.reason}</span>
      <span class="dr-factor-count">${f.count}/${n}</span>
      <span class="dr-factor-points">+${f.total} pts</span>
    </div>`;

  const avgHealthColor = avgHealth != null ? (HEALTH_COLORS[healthBandFor(avgHealth)] || '#aaa') : '#aaa';

  return `
    <div class="dr-pattern">
      <div class="dr-stat-band">
        <div class="dr-stat">
          <div class="dr-stat-lbl">Avg Health</div>
          <div class="dr-stat-num" style="color:${avgHealthColor}">${avgHealth != null ? avgHealth.toFixed(2) : '—'}</div>
        </div>
        <div class="dr-stat">
          <div class="dr-stat-lbl">Avg IR</div>
          <div class="dr-stat-num">${avgIR != null ? avgIR.toFixed(1) : '—'}</div>
        </div>
        <div class="dr-stat">
          <div class="dr-stat-lbl">Avg DP</div>
          <div class="dr-stat-num">${avgDP != null ? avgDP.toFixed(1) : '—'}</div>
        </div>
      </div>

      <div class="dr-section">
        <div class="dr-section-title">Recurring IR factors</div>
        <p class="dr-section-hint">Each row: how many entities in this bucket share the factor, and total points contributed.</p>
        ${irFactors.length
          ? irFactors.map(f => factorRow(f, members.length)).join('')
          : '<p class="dr-empty">No IR breakdown data.</p>'}
      </div>

      <div class="dr-section">
        <div class="dr-section-title">Recurring DP factors</div>
        ${dpFactors.length
          ? dpFactors.map(f => factorRow(f, members.length)).join('')
          : '<p class="dr-empty">No DP breakdown data.</p>'}
      </div>
    </div>`;
}

function renderEntityBreakdown(e) {
  const d = e.derived || {};
  const irBd = d.independence_risk_breakdown || {};
  const dpBd = d.discretionary_power_breakdown || {};
  const irRows = Object.entries(irBd).sort((a, b) => b[1] - a[1]);
  const dpRows = Object.entries(dpBd).sort((a, b) => b[1] - a[1]);
  const factorList = (rows, color) => rows.length
    ? rows.map(([reason, pts]) => `
        <div class="dr-bd-row">
          <span class="dr-bd-pts" style="color:${pts >= 0 ? color : '#16a34a'}">${pts >= 0 ? '+' : ''}${pts}</span>
          <span class="dr-bd-reason">${reason}</span>
        </div>`).join('')
    : '<div class="dr-empty">No breakdown.</div>';

  return `<div class="dr-expand-body">
    <div class="dr-expand-col">
      <div class="dr-expand-head">↳ Independence Risk · ${d.independence_risk_score ?? '—'} ${(d.independence_risk_level || '').toUpperCase()}</div>
      ${factorList(irRows, '#dc2626')}
    </div>
    <div class="dr-expand-col">
      <div class="dr-expand-head">↳ Discretionary Power · ${d.discretionary_power_score ?? '—'}</div>
      ${factorList(dpRows, '#6366f1')}
    </div>
    <div class="dr-expand-footer">
      <button class="dr-open-full" data-entity-id="${e.id}">Open full entity panel →</button>
    </div>
  </div>`;
}

function renderEntitiesTab(members) {
  if (!members.length) return `<p class="sum-empty">No entities in this bucket.</p>`;
  const rows = members.map((e) => {
    const d = e.derived || {};
    const health = d.structural_health_score;
    const healthLvl = d.structural_health_level || healthBandFor(health);
    const healthColor = HEALTH_COLORS[healthLvl] || '#aaa';
    const irLvl = d.independence_risk_level;
    const irColor = RISK_COLORS[irLvl] || '#aaa';
    return `<div class="dr-row" data-entity-row="${e.id}">
      <button class="dr-row-head" data-toggle-id="${e.id}" aria-expanded="false">
        <span class="dr-row-caret">▸</span>
        <span class="dr-row-health" style="color:${healthColor}">${health != null ? health.toFixed(2) : '—'}</span>
        <span class="dr-row-name">${e.name}${statusPill(e)}</span>
        <span class="dr-row-chips">
          <span class="reg-const-chip" style="color:${irColor};border-color:${irColor}66">IR ${d.independence_risk_score ?? '—'}${irLvl ? ' · ' + irLvl.charAt(0).toUpperCase() + irLvl.slice(1) : ''}</span>
          <span class="reg-const-chip reg-const-chip-dp">DP ${d.discretionary_power_score ?? '—'}</span>
        </span>
        <span class="dr-row-type">${e.type?.replace(/([A-Z])/g, ' $1').trim() || ''}</span>
      </button>
      <div class="dr-row-expand" data-expand-id="${e.id}" hidden>
        ${renderEntityBreakdown(e)}
      </div>
    </div>`;
  }).join('');
  return `<div class="dr-entities">${rows}</div>`;
}

// ── Temporal structure (decade mirror chart + slider) ────────────────────────
// Births up, deaths down. Constitutional events overlaid as vertical markers.
// A draggable year scrubber focuses a year — chart highlights the decade, and
// an inline list shows entities created or abolished within a window.

const TEMPORAL_DECADE_START = 1950;
const TEMPORAL_DECADE_END = Math.floor(new Date().getFullYear() / 10) * 10; // current decade start
const FOCUS_WINDOW_YEARS = 3; // ±3 yr window when scrubbing

// Pick bucket size based on visible span: decade > 40yr, 5yr 15–40, yearly < 15.
function _pickBucketSize(span) {
  if (span > 40) return 10;
  if (span > 15) return 5;
  return 1;
}

function _bucketLabel(start, size) {
  if (size === 10) return `${String(start).slice(2)}s`;
  if (size === 5)  return `${start}`;
  return String(start);
}

function _buildBuckets(entities, rangeStart, rangeEnd) {
  const size = _pickBucketSize(rangeEnd - rangeStart);
  const aligned = Math.floor(rangeStart / size) * size;
  const buckets = [];
  for (let y = aligned; y < rangeEnd; y += size) {
    buckets.push({ start: y, size, label: _bucketLabel(y, size), births: [], deaths: [] });
  }
  const bucketOf = (yr) => {
    if (yr == null) return null;
    const idx = Math.floor((yr - aligned) / size);
    if (idx < 0 || idx >= buckets.length) return null;
    return buckets[idx];
  };
  for (const e of entities) {
    const b1 = bucketOf(e.created_year);
    if (b1) b1.births.push(e);
    const b2 = bucketOf(e.abolished_year);
    if (b2) b2.deaths.push(e);
  }
  return { buckets, size };
}

function _eventTypeColor(type) {
  return {
    constitutional: '#7c3aed',
    institutional:  '#0891b2',
    reform:         '#16a34a',
    judgment:       '#dc2626',
  }[type] || '#6b7280';
}

function renderTemporalStructure(opts = {}) {
  const entities = State.graph?.entities || [];
  const events = (State.graph?.timeline_events || []).slice().sort((a, b) => a.year - b.year);
  const fullStart = TEMPORAL_DECADE_START;
  const fullEnd = TEMPORAL_DECADE_END + 10;
  const rangeStart = opts.rangeStart ?? fullStart;
  const rangeEnd = opts.rangeEnd ?? fullEnd;
  const brushMode = !!opts.brushMode;
  const isZoomed = rangeStart !== fullStart || rangeEnd !== fullEnd;
  const { buckets, size: bucketSize } = _buildBuckets(entities, rangeStart, rangeEnd);

  const maxBirths = Math.max(1, ...buckets.map(b => b.births.length));
  const maxDeaths = Math.max(1, ...buckets.map(b => b.deaths.length));
  const yMax = Math.max(maxBirths, maxDeaths);

  // Layout
  const W = 760, H = 300, PAD_L = 64, PAD_R = 20, PAD_T = 36, PAD_B = 64;
  const plotW = W - PAD_L - PAD_R;
  const plotH = H - PAD_T - PAD_B;
  const midY = PAD_T + plotH / 2;
  const halfH = plotH / 2;
  const barW = plotW / buckets.length;
  const barGap = Math.max(4, barW * 0.18);
  const usableBarW = barW - barGap;

  const yearToX = (yr) => PAD_L + ((yr - rangeStart) / (rangeEnd - rangeStart)) * plotW;

  // Bars — labels thin out when bucketSize=1 to avoid label collisions.
  const labelEvery = bucketSize === 1 ? Math.max(1, Math.ceil(buckets.length / 12)) : 1;
  const barsSVG = buckets.map((b, i) => {
    const x = PAD_L + i * barW + barGap / 2;
    const bH = (b.births.length / yMax) * halfH;
    const dH = (b.deaths.length / yMax) * halfH;
    const showLabel = i % labelEvery === 0;
    return `
      <g class="ts-bar-group" data-bucket-start="${b.start}" data-bucket-size="${b.size}">
        ${bH > 0 ? `<rect class="ts-bar ts-bar-birth" x="${x}" y="${midY - bH}" width="${usableBarW}" height="${bH}" data-kind="birth" data-bucket-start="${b.start}" data-bucket-size="${b.size}"><title>${b.births.length} created in ${b.label}${b.size > 1 ? ` (${b.start}–${b.start + b.size - 1})` : ''}</title></rect>` : ''}
        ${dH > 0 ? `<rect class="ts-bar ts-bar-death" x="${x}" y="${midY}" width="${usableBarW}" height="${dH}" data-kind="death" data-bucket-start="${b.start}" data-bucket-size="${b.size}"><title>${b.deaths.length} abolished in ${b.label}${b.size > 1 ? ` (${b.start}–${b.start + b.size - 1})` : ''}</title></rect>` : ''}
        ${showLabel ? `<text class="ts-bar-label" x="${x + usableBarW / 2}" y="${H - PAD_B + 16}" text-anchor="middle">${b.label}</text>` : ''}
        ${b.births.length ? `<text class="ts-bar-count ts-bar-count-birth" x="${x + usableBarW / 2}" y="${midY - bH - 3}" text-anchor="middle">${b.births.length}</text>` : ''}
        ${b.deaths.length ? `<text class="ts-bar-count ts-bar-count-death" x="${x + usableBarW / 2}" y="${midY + dH + 10}" text-anchor="middle">${b.deaths.length}</text>` : ''}
      </g>
    `;
  }).join('');

  // Constitutional event markers (only those in visible range)
  const eventsSVG = events.map((ev, i) => {
    if (ev.year < rangeStart || ev.year > rangeEnd) return '';
    const x = yearToX(ev.year);
    const color = _eventTypeColor(ev.type);
    return `
      <g class="ts-event" data-event-index="${i}">
        <line x1="${x}" x2="${x}" y1="${PAD_T - 6}" y2="${H - PAD_B}" stroke="${color}" stroke-dasharray="3 3" stroke-width="1" />
        <circle cx="${x}" cy="${PAD_T - 6}" r="4" fill="${color}" />
        <title>${ev.year} — ${ev.label}</title>
      </g>
    `;
  }).join('');

  // Mid axis (zero baseline)
  const midAxis = `<line x1="${PAD_L}" x2="${W - PAD_R}" y1="${midY}" y2="${midY}" stroke="#111827" stroke-width="1" />`;

  // Y labels — direction header + max-count ticks.
  // Direction labels sit at the SVG's very left edge (anchor start at x=2),
  // so they stay confined to the left gutter and never collide with bars.
  const yLabels = `
    <text class="ts-axis-dir ts-axis-dir-up"   x="2" y="${PAD_T - 14}"      text-anchor="start">↑ Created</text>
    <text class="ts-axis-dir ts-axis-dir-down" x="2" y="${H - PAD_B + 18}" text-anchor="start">↓ Abolished</text>
    <text class="ts-axis-tick" x="${PAD_L - 8}" y="${midY - halfH + 4}" text-anchor="end">${yMax}</text>
    <text class="ts-axis-tick" x="${PAD_L - 8}" y="${midY + 4}" text-anchor="end">0</text>
    <text class="ts-axis-tick" x="${PAD_L - 8}" y="${midY + halfH + 4}" text-anchor="end">${yMax}</text>
    <line class="ts-axis-line" x1="${PAD_L}" x2="${PAD_L}" y1="${PAD_T}" y2="${H - PAD_B}" />
  `;

  // Range rail at the bottom — two handles for zoom + one thumb for focus.
  const scrubY = H - PAD_B + 30;
  const scrubX1 = PAD_L;
  const scrubX2 = W - PAD_R;
  const proposedFocus = opts.focusYear ?? Math.round(rangeStart + (rangeEnd - rangeStart) * 0.5);
  const initialFocusYear = Math.max(rangeStart, Math.min(rangeEnd, proposedFocus));

  // ALL three rail elements (handles + focus thumb) share the SAME coordinate
  // system: the full-rail axis (1950 → fullEnd). This is what makes them
  // visually consistent — the focus thumb always sits between the handles.
  const fullRailYearToX = (yr) =>
    PAD_L + ((yr - fullStart) / (fullEnd - fullStart)) * plotW;
  const leftHandleX  = fullRailYearToX(rangeStart);
  const rightHandleX = fullRailYearToX(rangeEnd);
  const focusX       = fullRailYearToX(initialFocusYear);

  const railSVG = `
    <g class="ts-rail">
      <line class="ts-rail-line ts-rail-full" x1="${scrubX1}" x2="${scrubX2}" y1="${scrubY}" y2="${scrubY}" />
      <line class="ts-rail-line ts-rail-range" x1="${leftHandleX}" x2="${rightHandleX}" y1="${scrubY}" y2="${scrubY}" />
      <text class="ts-rail-end ts-rail-end-l" x="${scrubX1}" y="${scrubY + 20}" text-anchor="start">${fullStart}</text>
      <text class="ts-rail-end ts-rail-end-r" x="${scrubX2}" y="${scrubY + 20}" text-anchor="end">${fullEnd}</text>
      <circle class="ts-handle ts-handle-left"  cx="${leftHandleX}"  cy="${scrubY}" r="6" data-role="handle-left"  />
      <circle class="ts-handle ts-handle-right" cx="${rightHandleX}" cy="${scrubY}" r="6" data-role="handle-right" />
      <circle class="ts-scrub-thumb" cx="${focusX}" cy="${scrubY}" r="7" data-role="thumb" />
      <text class="ts-scrub-year" x="${focusX}" y="${scrubY + 20}" text-anchor="middle">${initialFocusYear}</text>
    </g>
    <g class="ts-tip" style="display:none" pointer-events="none">
      <rect class="ts-tip-bg" rx="4" ry="4" width="120" height="30" />
      <text class="ts-tip-text" x="60" y="19" text-anchor="middle"></text>
    </g>
  `;

  const eventLegend = ['constitutional', 'institutional', 'reform', 'judgment'].map(t =>
    `<span class="ts-evl"><span class="ts-evl-dot" style="background:${_eventTypeColor(t)}"></span>${t}</span>`
  ).join('');

  const bucketLabel = bucketSize === 10 ? 'decade' : bucketSize === 5 ? '5-yr' : 'year';
  const span = rangeEnd - rangeStart;

  // Preset eras — policy-researcher language. Each renders as a clickable pill.
  const currentYear = new Date().getFullYear();
  const presets = [
    { label: 'All',                          s: fullStart, e: fullEnd },
    { label: 'Pre-tribunalisation 1950–85',  s: 1950,      e: 1985 },
    { label: 'Liberalisation 1991–2010',     s: 1991,      e: 2010 },
    { label: 'Tribunals Reforms era 2017+',  s: 2017,      e: fullEnd },
    { label: 'Last 25 yr',                   s: currentYear - 25, e: fullEnd },
  ];
  const presetsHTML = presets.map(p => {
    const active = p.s === rangeStart && p.e === rangeEnd;
    return `<button type="button" class="ts-preset${active ? ' ts-preset-active' : ''}" data-start="${p.s}" data-end="${p.e}">${p.label}</button>`;
  }).join('');

  return `
    <div class="ts-wrap" data-focus-year="${initialFocusYear}" data-range-start="${rangeStart}" data-range-end="${rangeEnd}">
      <div class="ts-meta">
        <span><span class="ts-meta-num">${entities.filter(e => e.created_year).length}</span> entities with creation year ·
        <span class="ts-meta-num">${entities.filter(e => e.abolished_year).length}</span> with abolition year ·
        <span class="ts-meta-num">${events.length}</span> constitutional moments</span>
        <span class="ts-status">
          <span class="ts-bucket-info">${buckets.length} ${bucketLabel} bucket${buckets.length === 1 ? '' : 's'} · ${span} yr span</span>
        </span>
      </div>
      <div class="ts-presets">${presetsHTML}</div>
      <div class="ts-svg-wrap">
        <svg class="ts-svg" viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
          ${midAxis}
          ${yLabels}
          ${barsSVG}
          ${eventsSVG}
          ${railSVG}
        </svg>
      </div>
      <div class="ts-legend">${eventLegend}<span class="ts-legend-hint">click event = focus · double-click = zoom ±15 yr</span></div>
      <div class="ts-focus-panel" id="ts-focus-panel"></div>
    </div>
  `;
}
// "Spine + anomalies" — researcher-grade overview rather than a 600-node graph.
//   Left:  the canonical 5-tier appellate structure with curated reference
//          entities at each tier (the rest is available via the catalog drawer
//          and per-entity profiles).
//   Right: structural anomalies in the appellate chain — entities flagged as
//          Not Constituted, Partial Operational, or carrying documented
//          structural gaps. These are the editorial story.
//
// Why this shape: a policy researcher already knows there is a Supreme Court
// and 25 High Courts; the value of an "appellate hierarchy" overview is to
// surface *what is structurally broken*, not enumerate names already familiar.

const TIER_DEFS = [
  { key: 0, name: 'Constitutional apex',                 note: 'Final appellate jurisdiction under Article 136 (SLP).' },
  { key: 1, name: 'Constitutional courts & central tribunals', note: 'High Courts under Article 214; central tribunals under their parent statutes.' },
  { key: 2, name: 'Permanent benches & state tribunals', note: 'Permanent HC benches; state-level appellate tribunals.' },
  { key: 3, name: 'Subordinate appellate & regional',    note: 'District & sessions courts; regional tribunal benches.' },
  { key: 4, name: 'First-instance & quasi-judicial',     note: 'Trial-level courts and original-jurisdiction quasi-judicial bodies.' },
];

function _entitiesInAppellateGraph() {
  const set = new Set();
  for (const r of State.graph?.relationships || []) {
    if (r.relationship_category === 'appellate_chain') {
      set.add(r.source); set.add(r.target);
    }
  }
  return set;
}

// Structural anomaly register — every category a legal-policy researcher would
// consider materially anomalous. Project-wide, not restricted to the appellate
// graph (Not Constituted entities by definition have no edges).
//
// Severity order (informs default-open state + colour):
//   critical → Not Constituted, De Facto Blocked, Abolished
//   high     → Suspended, Partial Operational, Merged
//   moderate → Structural exception, Contested data, Structural gaps
function _appellateAnomalyGroups() {
  const entities = State.graph?.entities || [];
  const now = new Date().getFullYear();

  // Per-row fact: the single most relevant datum for a researcher (year + context).
  const fact = (e, cat) => {
    if (cat === 'Not Constituted' && e.created_year) {
      return `${e.created_year} · ${now - e.created_year} yr pending`;
    }
    if (cat === 'Abolished' && e.abolished_year) {
      return `Abolished ${e.abolished_year}`;
    }
    if (cat === 'Suspended' && e.suspended_year) return `Suspended ${e.suspended_year}`;
    if (cat === 'Merged') {
      const into = e.merged_into || e._detail?.merged_into;
      return into ? `→ ${into}` : 'Merged';
    }
    if (cat === 'De Facto Blocked') return 'Non-operational in practice';
    if (cat === 'Partial Operational') return 'Partial coverage';
    if (cat === 'Structural exception') return 'Deviates from statutory template';
    if (cat === 'Contested data') return e.data_quality_notes ? 'Sources disagree' : 'Data contested';
    if (cat === 'Structural gaps') {
      const n = Number(e.gap_count) || (e.gaps?.length || 0);
      return `${n} gap${n === 1 ? '' : 's'}`;
    }
    return '';
  };

  const groups = {
    'Not Constituted':      { severity: 'critical',  entities: [] },
    'Abolished':            { severity: 'abolished', entities: [] },
    'De Facto Blocked':     { severity: 'critical',  entities: [] },
    'Suspended':            { severity: 'high',     entities: [] },
    'Partial Operational':  { severity: 'high',     entities: [] },
    'Merged':               { severity: 'high',     entities: [] },
    'Structural exception': { severity: 'moderate', entities: [] },
    'Contested data':       { severity: 'moderate', entities: [] },
    'Structural gaps':      { severity: 'moderate', entities: [] },
  };

  // First pass: assign by primary operational_status. An entity sits in exactly
  // one status bucket so the count tallies cleanly with the stat band.
  for (const e of entities) {
    const status = e.operational_status;
    const row = { id: e.id, name: e.name, abbr: e.abbreviation };
    let placed = null;
    if      (status === 'Not_Constituted')      placed = 'Not Constituted';
    else if (status === 'Abolished')            placed = 'Abolished';
    else if (status === 'De_Facto_Blocked')     placed = 'De Facto Blocked';
    else if (status === 'Suspended')            placed = 'Suspended';
    else if (status === 'Partial_Operational')  placed = 'Partial Operational';
    else if (status === 'Merged')               placed = 'Merged';
    if (placed) {
      row.fact = fact(e, placed);
      groups[placed].entities.push(row);
    }
  }

  // Second pass: structural-exception, contested data quality, and documented
  // gaps for *active* entities only (we don't want to double-count an Abolished
  // entity into a gaps bucket — the abolition IS the anomaly).
  for (const e of entities) {
    if (['Not_Constituted', 'Abolished', 'De_Facto_Blocked', 'Suspended', 'Partial_Operational', 'Merged']
        .includes(e.operational_status)) continue;
    const row = { id: e.id, name: e.name, abbr: e.abbreviation };
    if (e.structural_exception) {
      row.fact = fact(e, 'Structural exception');
      groups['Structural exception'].entities.push(row);
      continue;
    }
    if (e.data_quality === 'contested') {
      row.fact = fact(e, 'Contested data');
      groups['Contested data'].entities.push(row);
      continue;
    }
    const gapCount = Number(e.gap_count) || (e.gaps?.length || 0);
    if (gapCount > 0) {
      row.fact = fact({ ...e, gap_count: gapCount }, 'Structural gaps');
      groups['Structural gaps'].entities.push(row);
    }
  }

  // Sort within group: by name (researcher scan-pattern).
  for (const k of Object.keys(groups)) {
    groups[k].entities.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
  }

  return Object.entries(groups)
    .filter(([, g]) => g.entities.length)
    .map(([tag, g]) => ({ tag, severity: g.severity, entities: g.entities }));
}

function _wireTemporalStructure(tsWrap, entities) {
  const events = (State.graph?.timeline_events || []).slice().sort((a, b) => a.year - b.year);
  const W = 760, PAD_L = 64, PAD_R = 20;
  const plotW = W - PAD_L - PAD_R;
  const fullStart = TEMPORAL_DECADE_START;
  const fullEnd = TEMPORAL_DECADE_END + 10;
  const MIN_SPAN = 5; // smallest zoom span in years

  const getState = () => {
    const wrap = tsWrap.querySelector('.ts-wrap');
    return {
      wrap,
      svg: tsWrap.querySelector('.ts-svg'),
      focusPanel: tsWrap.querySelector('#ts-focus-panel'),
      tip: tsWrap.querySelector('.ts-tip'),
      tipBg: tsWrap.querySelector('.ts-tip-bg'),
      tipText: tsWrap.querySelector('.ts-tip-text'),
      handleL: tsWrap.querySelector('.ts-handle-left'),
      handleR: tsWrap.querySelector('.ts-handle-right'),
      railRange: tsWrap.querySelector('.ts-rail-range'),
      thumb: tsWrap.querySelector('.ts-scrub-thumb'),
      focusLine: tsWrap.querySelector('.ts-scrub-focus-line'),
      yearText: tsWrap.querySelector('.ts-scrub-year'),
      rangeStart: parseInt(wrap.dataset.rangeStart, 10),
      rangeEnd: parseInt(wrap.dataset.rangeEnd, 10),
      focusYear: parseInt(wrap.dataset.focusYear, 10),
    };
  };

  const rerender = (overrides = {}) => {
    const s = getState();
    tsWrap.innerHTML = renderTemporalStructure({
      rangeStart: overrides.rangeStart ?? s.rangeStart,
      rangeEnd:   overrides.rangeEnd   ?? s.rangeEnd,
      focusYear:  overrides.focusYear  ?? s.focusYear,
    });
    refreshFocusPanel();
  };

  // Coordinate helpers
  // Visible-range x ↔ year (for the focus thumb / chart plot).
  const visibleXToYear = (clientX) => {
    const { svg, rangeStart, rangeEnd } = getState();
    const rect = svg.getBoundingClientRect();
    const scale = rect.width / W;
    const localX = (clientX - rect.left) / scale;
    const px = Math.max(PAD_L, Math.min(W - PAD_R, localX));
    const yr = rangeStart + ((px - PAD_L) / plotW) * (rangeEnd - rangeStart);
    return Math.round(yr);
  };
  const yearToVisibleLocalX = (yr, rangeStart, rangeEnd) =>
    PAD_L + ((yr - rangeStart) / (rangeEnd - rangeStart)) * plotW;
  // Full-rail x ↔ year (for the range handles, which span the entire timeline regardless of zoom).
  const fullRailXToYear = (clientX) => {
    const { svg } = getState();
    const rect = svg.getBoundingClientRect();
    const scale = rect.width / W;
    const localX = (clientX - rect.left) / scale;
    const px = Math.max(PAD_L, Math.min(W - PAD_R, localX));
    const yr = fullStart + ((px - PAD_L) / plotW) * (fullEnd - fullStart);
    return Math.round(yr);
  };
  const yearToFullRailX = (yr) =>
    PAD_L + ((yr - fullStart) / (fullEnd - fullStart)) * plotW;

  const refreshFocusPanel = () => {
    const { wrap, focusPanel } = getState();
    const year = parseInt(wrap.dataset.focusYear, 10);
    const lo = year - FOCUS_WINDOW_YEARS;
    const hi = year + FOCUS_WINDOW_YEARS;
    const created = entities.filter(e => e.created_year != null && e.created_year >= lo && e.created_year <= hi);
    const abolished = entities.filter(e => e.abolished_year != null && e.abolished_year >= lo && e.abolished_year <= hi);
    const nearEvents = events.filter(ev => ev.year >= lo && ev.year <= hi);
    const chip = (e, kind) => `<button type="button" class="ts-chip ts-chip-${kind}" data-entity-id="${e.id}" title="${(e.name || '').replace(/"/g, '&quot;')}">${e.abbreviation || e.name} <span class="ts-chip-yr">${kind === 'birth' ? e.created_year : e.abolished_year}</span></button>`;
    const eventRow = nearEvents.length ? `
      <div class="ts-focus-events">
        ${nearEvents.map(ev => `<span class="ts-focus-event" style="border-left-color:${_eventTypeColor(ev.type)}"><strong>${ev.year}</strong> · ${ev.label}</span>`).join('')}
      </div>` : '';
    if (!created.length && !abolished.length && !nearEvents.length) {
      focusPanel.innerHTML = `<p class="ts-focus-empty">Nothing within ±${FOCUS_WINDOW_YEARS} years of ${year}.</p>`;
      return;
    }
    focusPanel.innerHTML = `
      <div class="ts-focus-head">
        <span class="ts-focus-year">${year}</span>
        <span class="ts-focus-window">within ±${FOCUS_WINDOW_YEARS} yr</span>
        <span class="ts-focus-counts">
          <span class="ts-focus-count ts-focus-count-birth">${created.length} created</span>
          <span class="ts-focus-count ts-focus-count-death">${abolished.length} abolished</span>
        </span>
      </div>
      ${eventRow}
      ${created.length ? `<div class="ts-focus-row"><span class="ts-focus-row-label">Born</span><div class="ts-focus-chips">${created.map(e => chip(e, 'birth')).join('')}</div></div>` : ''}
      ${abolished.length ? `<div class="ts-focus-row"><span class="ts-focus-row-label">Abolished</span><div class="ts-focus-chips">${abolished.map(e => chip(e, 'death')).join('')}</div></div>` : ''}
    `;
  };

  refreshFocusPanel();

  // ── Move focus thumb (always at full-rail x for consistency with handles) ─
  const moveScrubberTo = (year) => {
    const { wrap, rangeStart, rangeEnd, thumb, yearText } = getState();
    year = Math.max(rangeStart, Math.min(rangeEnd, year));
    wrap.dataset.focusYear = year;
    const x = yearToFullRailX(year);
    thumb?.setAttribute('cx', x);
    if (yearText) { yearText.setAttribute('x', x); yearText.textContent = year; }
    refreshFocusPanel();
  };
  // Visual-only thumb update (no panel refresh — used during handle drag).
  const syncThumbVisual = () => {
    const { wrap, thumb, yearText } = getState();
    const yr = parseInt(wrap.dataset.focusYear, 10);
    const x = yearToFullRailX(yr);
    thumb?.setAttribute('cx', x);
    if (yearText) { yearText.setAttribute('x', x); yearText.textContent = yr; }
  };

  // ── Tooltip ───────────────────────────────────────────────────
  const showTip = (anchorX, anchorY, text) => {
    const { tip, tipBg, tipText } = getState();
    if (!tip) return;
    // Measure: monospace text — estimate width by char count.
    const w = Math.max(80, text.length * 7 + 16);
    tipBg.setAttribute('width', w);
    tip.setAttribute('transform', `translate(${anchorX - w / 2}, ${anchorY - 42})`);
    tipText.setAttribute('x', w / 2);
    tipText.textContent = text;
    tip.style.display = '';
  };
  const hideTip = () => {
    const { tip } = getState();
    if (tip) tip.style.display = 'none';
  };

  // ── Drag dispatcher ───────────────────────────────────────────
  // dragRole: 'handle-left' | 'handle-right' | 'thumb' | 'plot' | null
  let dragRole = null;
  let pendingRangeStart = null;
  let pendingRangeEnd = null;

  const startDrag = (target, clientX) => {
    const role = target.closest('[data-role]')?.dataset.role;
    if (role === 'handle-left' || role === 'handle-right' || role === 'thumb') {
      dragRole = role;
      const s = getState();
      pendingRangeStart = s.rangeStart;
      pendingRangeEnd = s.rangeEnd;
      updateDrag(clientX);
      return true;
    }
    if (target.closest('.ts-svg') && !target.closest('.ts-bar, .ts-event circle, .ts-rail')) {
      // Clicking on the chart plot area scrubs focus along the visible axis.
      dragRole = 'plot';
      moveScrubberTo(visibleXToYear(clientX));
      return true;
    }
    return false;
  };

  const updateDrag = (clientX) => {
    const s = getState();
    if (dragRole === 'handle-left') {
      // Use the THUMB radius as the floor so the handle can never overlap the focus thumb
      // visually — focus year auto-clamps in lockstep.
      const yr = fullRailXToYear(clientX);
      const clamped = Math.max(fullStart, Math.min(pendingRangeEnd - MIN_SPAN, yr));
      pendingRangeStart = clamped;
      const x = yearToFullRailX(clamped);
      s.handleL?.setAttribute('cx', x);
      s.railRange?.setAttribute('x1', x);
      showTip(x, parseFloat(s.handleL?.getAttribute('cy') || 0),
        `From ${clamped} · span ${pendingRangeEnd - clamped}`);
      // Live-clamp focus year if it now falls outside pending range.
      const curFocus = parseInt(s.wrap.dataset.focusYear, 10);
      if (curFocus < pendingRangeStart) {
        s.wrap.dataset.focusYear = pendingRangeStart;
        syncThumbVisual();
      }
    } else if (dragRole === 'handle-right') {
      const yr = fullRailXToYear(clientX);
      const clamped = Math.max(pendingRangeStart + MIN_SPAN, Math.min(fullEnd, yr));
      pendingRangeEnd = clamped;
      const x = yearToFullRailX(clamped);
      s.handleR?.setAttribute('cx', x);
      s.railRange?.setAttribute('x2', x);
      showTip(x, parseFloat(s.handleR?.getAttribute('cy') || 0),
        `To ${clamped} · span ${clamped - pendingRangeStart}`);
      const curFocus = parseInt(s.wrap.dataset.focusYear, 10);
      if (curFocus > pendingRangeEnd) {
        s.wrap.dataset.focusYear = pendingRangeEnd;
        syncThumbVisual();
      }
    } else if (dragRole === 'thumb') {
      // Thumb is on the full-rail axis — use the same conversion.
      moveScrubberTo(fullRailXToYear(clientX));
    } else if (dragRole === 'plot') {
      // Plot-area drag uses the visible (zoomed) axis.
      moveScrubberTo(visibleXToYear(clientX));
    }
  };

  const endDrag = () => {
    if (!dragRole) return;
    if (dragRole === 'handle-left' || dragRole === 'handle-right') {
      hideTip();
      const s = getState();
      if (pendingRangeStart !== s.rangeStart || pendingRangeEnd !== s.rangeEnd) {
        const curFocus = parseInt(s.wrap.dataset.focusYear, 10);
        const newFocus = Math.max(pendingRangeStart, Math.min(pendingRangeEnd, curFocus));
        rerender({ rangeStart: pendingRangeStart, rangeEnd: pendingRangeEnd, focusYear: newFocus });
      }
    }
    dragRole = null;
    pendingRangeStart = null;
    pendingRangeEnd = null;
  };

  tsWrap.addEventListener('mousedown', (ev) => {
    if (ev.target.closest('.ts-preset, .ts-chip, .ts-bar, .ts-event circle')) return;
    if (startDrag(ev.target, ev.clientX)) ev.preventDefault();
  });
  document.addEventListener('mousemove', (ev) => { if (dragRole) updateDrag(ev.clientX); });
  document.addEventListener('mouseup', endDrag);

  tsWrap.addEventListener('touchstart', (ev) => {
    if (ev.target.closest('.ts-preset, .ts-chip, .ts-bar, .ts-event circle')) return;
    if (ev.touches[0]) startDrag(ev.target, ev.touches[0].clientX);
  }, { passive: true });
  document.addEventListener('touchmove', (ev) => { if (dragRole && ev.touches[0]) updateDrag(ev.touches[0].clientX); }, { passive: true });
  document.addEventListener('touchend', endDrag);

  // ── Click delegation (presets, bars, event single-click, chips) ──────
  tsWrap.addEventListener('click', (ev) => {
    const preset = ev.target.closest('.ts-preset');
    if (preset) {
      const s = parseInt(preset.dataset.start, 10);
      const e = parseInt(preset.dataset.end, 10);
      rerender({ rangeStart: s, rangeEnd: e, focusYear: Math.round((s + e) / 2) });
      return;
    }
    const bar = ev.target.closest('.ts-bar');
    if (bar) {
      const start = parseInt(bar.dataset.bucketStart, 10);
      const size = parseInt(bar.dataset.bucketSize, 10);
      moveScrubberTo(start + Math.floor(size / 2));
      return;
    }
    const evt = ev.target.closest('.ts-event');
    if (evt) {
      const idx = parseInt(evt.dataset.eventIndex, 10);
      const e = events[idx];
      if (e) moveScrubberTo(e.year);
      return;
    }
    const chipBtn = ev.target.closest('.ts-chip');
    if (chipBtn) State.emit('navigateToDetail', chipBtn.dataset.entityId);
  });

  // ── Double-click an event marker → zoom ±15 yr around it ─────
  tsWrap.addEventListener('dblclick', (ev) => {
    const evt = ev.target.closest('.ts-event');
    if (!evt) return;
    const idx = parseInt(evt.dataset.eventIndex, 10);
    const e = events[idx];
    if (!e) return;
    const s = Math.max(fullStart, e.year - 15);
    const ee = Math.min(fullEnd, e.year + 15);
    rerender({ rangeStart: s, rangeEnd: ee, focusYear: e.year });
  });
}

function renderAppellateHierarchy() {
  const { tiers } = buildAppellateHierarchy();
  if (!tiers.length || tiers.every(t => !t.length)) {
    return '<p class="sum-empty">No appellate-chain relationships in the dataset yet.</p>';
  }

  // Curate each tier: surface 4 reference entities. Sort by structural salience —
  // anomaly status first (so a Not Constituted entity at tier 1 is visible),
  // then by entity name length (shorter ≈ more canonical) as a stable secondary.
  const inGraph = _entitiesInAppellateGraph();
  const salience = (id) => {
    const e = State.getEntityById(id);
    if (!e) return 99;
    if (e.operational_status === 'Not_Constituted') return 0;
    if (e.operational_status === 'De_Facto_Blocked') return 1;
    if (e.operational_status === 'Partial_Operational') return 2;
    return 10;
  };

  const referenceChip = (id) => {
    const e = State.getEntityById(id);
    if (!e) return '';
    const label = e.abbreviation || e.name;
    const full = (e.name || id).replace(/"/g, '&quot;');
    const flag = e.operational_status === 'Not_Constituted' ? '<span class="ah-flag" title="Not Constituted">NOT CONSTITUTED</span>'
               : e.operational_status === 'De_Facto_Blocked' ? '<span class="ah-flag ah-flag-blocked" title="De Facto Blocked">DE FACTO BLOCKED</span>'
               : e.operational_status === 'Abolished'        ? `<span class="ah-flag ah-flag-abolished" title="Abolished${e.abolished_year ? ' ' + e.abolished_year : ''}">ABOLISHED${e.abolished_year ? ' ' + e.abolished_year : ''}</span>`
               : '';
    const chipClass = e.operational_status === 'Abolished' ? 'ah-chip ah-chip-abolished' : 'ah-chip';
    return `<button type="button" class="${chipClass}" data-entity-id="${id}" title="${full}"><span class="ah-chip-label">${label}</span>${flag}</button>`;
  };

  const tierRow = (tier, ti) => {
    const def = TIER_DEFS[ti] || { name: `Tier ${ti + 1}`, note: '' };
    const sorted = [...tier].sort((a, b) => salience(a) - salience(b) || (State.getEntityById(a)?.name || a).length - (State.getEntityById(b)?.name || b).length);
    const refs = sorted.slice(0, 4).map(referenceChip).join('');
    const moreCount = tier.length - 4;
    const rest = sorted.slice(4).map(referenceChip).join('');
    return `
      <div class="ah-tier-row">
        <div class="ah-tier-num">${ti + 1}</div>
        <div class="ah-tier-body">
          <div class="ah-tier-head">
            <span class="ah-tier-name">${def.name}</span>
            <span class="ah-tier-count">${tier.length} ${tier.length === 1 ? 'entity' : 'entities'}</span>
          </div>
          ${def.note ? `<div class="ah-tier-note">${def.note}</div>` : ''}
          <div class="ah-tier-refs">
            ${refs}
            ${moreCount > 0 ? `<details class="ah-tier-more-wrap"><summary class="ah-tier-more">+ ${moreCount} more</summary><div class="ah-tier-rest">${rest}</div></details>` : ''}
          </div>
        </div>
      </div>
    `;
  };

  const anomalyGroups = _appellateAnomalyGroups();
  const anomalyTotal = anomalyGroups.reduce((acc, g) => acc + g.entities.length, 0);
  const anomalyHTML = anomalyGroups.length ? anomalyGroups.map(g => `
    <details class="ah-anom-group ah-anom-sev-${g.severity}" ${g.tag === 'Not Constituted' ? 'open' : ''}>
      <summary class="ah-anom-group-head">
        <span class="ah-anom-group-tag">${g.tag}</span>
        <span class="ah-anom-group-count">${g.entities.length}</span>
      </summary>
      <div class="ah-anom-list">
        ${g.entities.map(a => `
          <button type="button" class="ah-anom" data-entity-id="${a.id}">
            <span class="ah-anom-name">${a.name}</span>
            ${a.fact ? `<span class="ah-anom-fact">${a.fact}</span>` : ''}
          </button>
        `).join('')}
      </div>
    </details>
  `).join('') : '<p class="ah-anom-empty">No structural anomalies flagged in appellate graph.</p>';

  const totalEntities = tiers.reduce((acc, t) => acc + t.length, 0);

  return `
    <div class="ah-wrap">
      <div class="ah-meta">
        <span class="ah-meta-num">${totalEntities}</span> entities across
        <span class="ah-meta-num">${tiers.length}</span> appellate tiers ·
        <span class="ah-meta-num">${anomalyTotal}</span> structural anomalies
      </div>
      <div class="ah-grid">
        <section class="ah-spine" aria-label="Appellate spine">
          <header class="ah-col-head">The spine</header>
          ${tiers.map(tierRow).join('')}
        </section>
        <aside class="ah-anomalies" aria-label="Structural anomalies">
          <header class="ah-col-head">Structural anomaly register</header>
          <p class="ah-col-sub">Every materially anomalous entity across the map — by operational status (Not Constituted, Abolished, Suspended, Merged, etc.), structural exception, contested data quality, or documented gap. One row per entity, single primary category.</p>
          ${anomalyHTML}
        </aside>
      </div>
    </div>
  `;
}

function buildClusterDrillHTML(clusterId, entities, filterIds = null) {
  const label = CLUSTER_LABELS[clusterId] || clusterId;
  const idSet = filterIds ? new Set(filterIds) : null;
  const members = entities
    .filter(e => e.cluster === clusterId && (!idSet || idSet.has(e.id)))
    .sort((a, b) => (a.derived?.structural_health_score ?? 999) - (b.derived?.structural_health_score ?? 999));

  if (!members.length) return `<p class="sum-empty">No entities in this cluster.</p>`;

  return `<div class="cl-drill-header">
      <span class="cl-drill-title">${label}</span>
      <span class="cl-drill-count">${members.length} entities · sorted by worst health</span>
    </div>
    <div class="dr-tabs" role="tablist">
      <button class="dr-tab active" data-dr-tab="pattern" role="tab" aria-selected="true">Pattern</button>
      <button class="dr-tab" data-dr-tab="entities" role="tab" aria-selected="false">Entities (${members.length})</button>
    </div>
    <div class="dr-pane" data-dr-pane="pattern">${renderPatternTab(members)}</div>
    <div class="dr-pane dr-pane-hidden" data-dr-pane="entities">${renderEntitiesTab(members)}</div>`;
}

function showClusterDrill(clusterId, entities, container, filterIds = null) {
  let overlay = container.querySelector('#cluster-drill-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'cluster-drill-overlay';
    overlay.className = 'cl-drill-overlay';
    container.querySelector('.sum-inner').appendChild(overlay);
  }

  overlay.innerHTML = `
    <div class="cl-drill-card">
      <button class="cl-drill-close" id="cl-drill-close" aria-label="Close">✕</button>
      <div class="cl-drill-body" id="cl-drill-body">
        ${buildClusterDrillHTML(clusterId, entities, filterIds)}
      </div>
    </div>
    <div class="cl-drill-backdrop" id="cl-drill-backdrop"></div>
  `;

  overlay.classList.remove('cl-drill-hidden');

  overlay.querySelector('#cl-drill-close')?.addEventListener('click', () => {
    overlay.classList.add('cl-drill-hidden');
  });
  overlay.querySelector('#cl-drill-backdrop')?.addEventListener('click', () => {
    overlay.classList.add('cl-drill-hidden');
  });
  overlay.querySelector('.cl-drill-body')?.addEventListener('click', e => {
    // Tab switch
    const tabBtn = e.target.closest('.dr-tab');
    if (tabBtn) {
      const tab = tabBtn.dataset.drTab;
      overlay.querySelectorAll('.dr-tab').forEach(t => {
        const active = t.dataset.drTab === tab;
        t.classList.toggle('active', active);
        t.setAttribute('aria-selected', active ? 'true' : 'false');
      });
      overlay.querySelectorAll('.dr-pane').forEach(p => {
        p.classList.toggle('dr-pane-hidden', p.dataset.drPane !== tab);
      });
      return;
    }

    // Inline row expand
    const rowHead = e.target.closest('.dr-row-head');
    if (rowHead) {
      const id = rowHead.dataset.toggleId;
      const expand = overlay.querySelector(`[data-expand-id="${CSS.escape(id)}"]`);
      const caret = rowHead.querySelector('.dr-row-caret');
      if (expand) {
        const willOpen = expand.hasAttribute('hidden');
        if (willOpen) expand.removeAttribute('hidden'); else expand.setAttribute('hidden', '');
        rowHead.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
        if (caret) caret.textContent = willOpen ? '▾' : '▸';
      }
      return;
    }

    // "Open full entity panel" button
    const openFull = e.target.closest('.dr-open-full');
    if (openFull) {
      e.preventDefault();
      overlay.classList.add('cl-drill-hidden');
      State.emit('navigateToDetail', openFull.dataset.entityId);
      return;
    }

    // Existing entity link (legacy / future)
    const link = e.target.closest('[data-entity-id]:not(.dr-open-full):not(.dr-row-head)');
    if (link) {
      e.preventDefault();
      overlay.classList.add('cl-drill-hidden');
      State.emit('navigateToDetail', link.dataset.entityId);
    }
  });
}

// ── Main render ───────────────────────────────────────────────────────────────

// ── Stat-band detail panels (researcher hat: dense, sourced, one-line-per-row) ─
const CURRENT_YEAR = new Date().getFullYear();

function _statPanelEntities(stat, entities) {
  if (stat === 'risk') {
    return entities
      .filter(e => ['high', 'severe'].includes(e.derived?.independence_risk_level))
      .sort((a, b) => (b.derived?.independence_risk_score ?? 0) - (a.derived?.independence_risk_score ?? 0));
  }
  if (stat === 'nc') {
    return entities
      .filter(e => e.operational_status === 'Not_Constituted')
      .sort((a, b) => (a.created_year ?? 9999) - (b.created_year ?? 9999));
  }
  if (stat === 'abolished') {
    return entities
      .filter(e => e.operational_status === 'Abolished')
      .sort((a, b) => (b.abolished_year ?? 0) - (a.abolished_year ?? 0));
  }
  if (stat === 'disposal') {
    return entities
      .filter(e => e._detail?.case_volume?.disposal_rate != null)
      .sort((a, b) => (a._detail.case_volume.disposal_rate) - (b._detail.case_volume.disposal_rate));
  }
  return entities;
}

function _statPanelMeta(stat, list, totalEntities) {
  if (stat === 'coverage') return {
    title: 'Coverage',
    blurb: `${totalEntities} entities mapped against the ~1,500-entity universe (Constitution + central + state + UT). Coverage is sparse for state-level subordinate courts; central and constitutional layers are substantially complete.`,
    column: 'By govt level · count · share',
  };
  if (stat === 'risk') return {
    title: 'High or severe independence risk',
    blurb: 'Algorithmic indicator of structural design — not findings of conduct. Drivers include appointer-litigant conflict, executive removal authority without judicial concurrence, opaque appointment criteria, and reappointment dependency.',
    column: 'IR score · level',
  };
  if (stat === 'nc') return {
    title: 'Legislated but not constituted',
    blurb: 'Entities created by statute but not yet operationalised — appellate vacuums where the legislated remedy does not exist in practice. Litigants typically route through writ jurisdiction (HC under Article 226) instead.',
    column: 'Legislated · years pending',
  };
  if (stat === 'abolished') return {
    title: 'Abolished',
    blurb: 'Entities formally dissolved by statute, gazette notification, or judicial order. Their dissolution typically routed caseload to successor courts (e.g. IPAB → HCs after 2021 Tribunals Reforms Act). Transitional provisions are often the structural research question.',
    column: 'Abolished · years since',
  };
  if (stat === 'disposal') return {
    title: 'Case-volume tracked entities · worst disposal first',
    blurb: 'Ratio of cases disposed to cases filed in the most recent NJDG snapshot. Below 1.0 means backlog is growing. Coverage limited to entities with NJDG data published in this build.',
    column: 'Disposal · pending',
  };
  return { title: '', blurb: '', column: '' };
}

function _statRow(stat, e) {
  const meta = [];
  if (stat === 'risk') {
    const lvl = e.derived?.independence_risk_level || '—';
    const sc = e.derived?.independence_risk_score ?? '—';
    meta.push(`<span class="sp-row-score">${sc}</span><span class="sp-row-lvl sp-lvl-${lvl}">${lvl.toUpperCase()}</span>`);
  } else if (stat === 'nc') {
    const yr = e.created_year;
    const yrsPending = yr ? (CURRENT_YEAR - yr) : null;
    meta.push(`<span class="sp-row-yr">${yr || '—'}</span>${yrsPending != null ? `<span class="sp-row-pending">${yrsPending} yr unconstituted</span>` : ''}`);
  } else if (stat === 'abolished') {
    const yr = e.abolished_year;
    const yrsSince = yr ? (CURRENT_YEAR - yr) : null;
    meta.push(`<span class="sp-row-yr">${yr || '—'}</span>${yrsSince != null ? `<span class="sp-row-pending">${yrsSince} yr ago</span>` : ''}`);
  } else if (stat === 'disposal') {
    const cv = e._detail?.case_volume || {};
    const rate = cv.disposal_rate != null ? cv.disposal_rate.toFixed(2) : '—';
    const pending = cv.pending_cases != null ? cv.pending_cases.toLocaleString() : '—';
    meta.push(`<span class="sp-row-score">${rate}</span><span class="sp-row-pending">${pending} pending</span>`);
  } else if (stat === 'coverage') {
    meta.push(`<span class="sp-row-cluster">${(e.cluster || '').replace(/_/g, ' ')}</span><span class="sp-row-gov">${(e.level_of_government || '').replace(/_/g, ' ')}</span>`);
  }
  return `<button type="button" class="sp-row" data-entity-id="${e.id}">
    <span class="sp-row-name">${e.name}${e.abbreviation && e.abbreviation !== e.name ? ` <span class="sp-row-abbr">(${e.abbreviation})</span>` : ''}</span>
    <span class="sp-row-meta">${meta.join('')}</span>
  </button>`;
}

// Govt-level segmentation for the coverage panel. Order matters: it drives
// stack order in the segmented bar and the legend.
const GOV_LEVELS = [
  { key: 'Central',             short: 'C',   label: 'Central' },
  { key: 'Shared_CentralState', short: 'C/S', label: 'Shared' },
  { key: 'Shared_MultiState',   short: 'M/S', label: 'Multi-state' },
  { key: 'State',               short: 'S',   label: 'State' },
  { key: 'UT',                  short: 'UT',  label: 'UT' },
];

// Coverage filter state — set of selected govt-level keys, or null for "all".
// Lives on the DOM (data-filter-levels) so it survives focus across re-renders
// without needing global state.
function _coverageActiveSet(scope) {
  const raw = scope?.dataset?.filterLevels;
  if (raw == null || raw === '') return null;
  return new Set(raw.split(',').filter(Boolean));
}

function _renderCoveragePanel(entities, selected) {
  // If `selected` is null we treat all levels as active.
  const isActive = (key) => !selected || selected.has(key);
  const filtered = entities.filter(e => isActive(e.level_of_government || 'unknown'));
  const filteredTotal = filtered.length || 1; // avoid /0 in pct

  // Group filtered entities by cluster.
  const byCluster = new Map();
  for (const e of filtered) {
    const c = e.cluster || 'unknown';
    if (!byCluster.has(c)) byCluster.set(c, []);
    byCluster.get(c).push(e);
  }

  const rows = [...byCluster.entries()]
    .sort((a, b) => b[1].length - a[1].length)
    .map(([clusterId, list]) => {
      const total = list.length;
      const pct = ((total / filteredTotal) * 100).toFixed(1);
      const label = CLUSTER_LABELS[clusterId] || clusterId.replace(/_/g, ' ');

      const counts = {};
      for (const e of list) {
        const lv = e.level_of_government || 'unknown';
        counts[lv] = (counts[lv] || 0) + 1;
      }
      const orderedLevels = GOV_LEVELS.filter(l => counts[l.key]);
      const otherCount = total - orderedLevels.reduce((s, l) => s + counts[l.key], 0);
      const segments = orderedLevels.map(l => {
        const w = (counts[l.key] / total) * 100;
        return `<span class="sp-seg sp-seg-${l.key.toLowerCase().replace('_','-')}" style="width:${w}%" title="${l.label}: ${counts[l.key]}"></span>`;
      }).join('') + (otherCount > 0
        ? `<span class="sp-seg sp-seg-unknown" style="width:${(otherCount / total) * 100}%" title="Unspecified: ${otherCount}"></span>`
        : '');

      const breakdown = orderedLevels.map(l =>
        `<span class="sp-gov-tag sp-gov-${l.key.toLowerCase().replace('_','-')}">${l.short} ${counts[l.key]}</span>`
      ).join('');

      return `<button type="button" class="sp-row sp-row-cluster-bar" data-cluster-id="${clusterId}">
        <span class="sp-row-name">${label}</span>
        <span class="sp-row-meta">
          <span class="sp-gov-breakdown">${breakdown}</span>
          <span class="sp-row-score">${total}</span>
          <span class="sp-bar sp-bar-stacked">${segments}</span>
          <span class="sp-row-pending">${pct}%</span>
        </span>
      </button>`;
    }).join('');

  // Legend doubles as filter UI. Inactive levels are visibly muted.
  const legend = GOV_LEVELS.map(l => {
    const active = isActive(l.key);
    return `<button type="button" class="sp-legend-item${active ? ' sp-legend-active' : ' sp-legend-inactive'}" data-level-key="${l.key}" aria-pressed="${active}">
      <span class="sp-legend-swatch sp-seg-${l.key.toLowerCase().replace('_','-')}"></span>${l.label}
    </button>`;
  }).join('');

  // Filter summary: count of entities in current selection vs total.
  const filterNote = selected
    ? `<span class="sp-filter-note">${filtered.length} of ${entities.length} shown · <button type="button" class="sp-filter-reset">reset</button></span>`
    : `<span class="sp-filter-note sp-filter-note-mute">Click a level to filter</span>`;

  return `<div class="sp-legend-row">
    <div class="sp-legend">${legend}</div>
    ${filterNote}
  </div>${rows || '<p class="sp-empty">No entities match the current filter.</p>'}`;
}

function renderStatPanel(stat, entities, opts = {}) {
  const meta = _statPanelMeta(stat, null, entities.length);
  let body;
  if (stat === 'coverage') {
    body = _renderCoveragePanel(entities, opts.coverageFilter || null);
  } else {
    const list = _statPanelEntities(stat, entities);
    if (!list.length) {
      body = '<p class="sp-empty">No matching entities in the current dataset.</p>';
    } else {
      body = list.map(e => _statRow(stat, e)).join('');
    }
  }
  return `
    <div class="sp-card" data-stat="${stat}">
      <div class="sp-head">
        <div>
          <h3 class="sp-title">${meta.title}</h3>
          <p class="sp-blurb">${meta.blurb}</p>
        </div>
        <button type="button" class="sp-close" aria-label="Close" title="Close">✕</button>
      </div>
      <div class="sp-col-head">
        <span class="sp-col-name">Entity</span>
        <span class="sp-col-meta">${meta.column}</span>
      </div>
      <div class="sp-list">${body}</div>
    </div>
  `;
}

export function initSummaryView() {
  const graph = State.graph;
  if (!graph) return;

  const container = document.getElementById('summary-view');
  if (!container) return;

  const entities = graph.entities || [];
  const metrics = graph.impact_metrics || {};
  const avgDisposal = computeAvgDisposalRate(entities);

  const notConstitutedCount = metrics.not_constituted_count
    ?? entities.filter(e => e.operational_status === 'Not_Constituted').length;
  const highRiskCount = metrics.high_independence_risk_count
    ?? entities.filter(e => ['high', 'severe'].includes(e.derived?.independence_risk_level)).length;
  const abolishedCount = metrics.abolished_count
    ?? entities.filter(e => e.operational_status === 'Abolished').length;

  container.innerHTML = `
    <div class="sum-inner">

      <div class="sum-masthead">
        <h1 class="sum-title">Judiciary Entity Map — India</h1>
        <p class="sum-subtitle">Structural map of appointment chains, funding flows, independence risk, and systemic gaps across India's judicial ecosystem.</p>
      </div>

      <div class="stat-band" id="stat-band" role="tablist">
        <button type="button" class="stat-item" data-stat="coverage" aria-expanded="false">
          <span class="stat-num">${entities.length}<span class="stat-denom"> / ~1,500</span></span>
          <span class="stat-lbl">Entities mapped</span>
        </button>
        <button type="button" class="stat-item stat-item-risk" data-stat="risk" aria-expanded="false">
          <span class="stat-num">${highRiskCount}</span>
          <span class="stat-lbl">High or severe independence risk</span>
        </button>
        <button type="button" class="stat-item stat-item-nc" data-stat="nc" aria-expanded="false">
          <span class="stat-num">${notConstitutedCount}</span>
          <span class="stat-lbl">Legislated but not constituted</span>
        </button>
        <button type="button" class="stat-item stat-item-abolished" data-stat="abolished" aria-expanded="false">
          <span class="stat-num">${abolishedCount}</span>
          <span class="stat-lbl">Abolished</span>
        </button>
        ${avgDisposal ? `<button type="button" class="stat-item" data-stat="disposal" aria-expanded="false">
          <span class="stat-num">${avgDisposal}</span>
          <span class="stat-lbl">Avg disposal rate (NJDG-tracked entities)</span>
        </button>` : ''}
      </div>
      <div class="stat-panel" id="stat-panel" hidden></div>

      <div class="sm-section sp-section">
        <div class="sm-section-head">
          <span class="sm-section-title">Spotlight · critical &amp; at-risk entities</span>
        </div>
        <p class="sm-note-global">Each card is a preview of the entity's structural report. Step through with arrows or swipe.</p>
        ${renderSpotlightCarousel(spotlightSet(entities), entities.length)}
      </div>

      <div class="sm-section">
        <div class="sm-section-head">
          <span class="sm-section-title">Appellate hierarchy</span>
        </div>
        <p class="sm-note-global">The five-tier appellate spine on the left; a project-wide structural anomaly register on the right — every entity flagged by operational status, structural exception, contested data, or documented gap. Click any reference entity or anomaly to open its structural profile.</p>
        <div class="ah-section-wrap" id="appellate-hierarchy-wrap"></div>
      </div>

      <div class="sm-section">
        <div class="sm-section-head">
          <span class="sm-section-title">Structural health distribution</span>
        </div>
        <p class="sm-note-global">Master composite of independence risk + discretionary power.
        Each bubble = entities at that health band; bubble area ∝ count.
        Click a bubble to drill into the constituent IR + DP scores for those entities.
        Legislative/executive bodies excluded (governance anchors).</p>
        <div class="strip-wrap" id="strip-plot-wrap"></div>
      </div>

      <div class="sm-section sm-section-timeline">
        <div class="sm-section-head">
          <span class="sm-section-title">Timeline · how we got here</span>
        </div>
        <p class="sm-note-global">Three quarters of a century of judicial institution-building, decade by decade. Creations rise above the line, abolitions fall below; constitutional moments are dotted in. Drag the focus year to see what was born or dissolved near any moment — or jump to a policy era.</p>
        <div class="ts-section-wrap" id="temporal-structure-wrap"></div>
      </div>

    </div>
  `;

  // ── Render temporal structure ─────────────────────────────────────────────
  requestAnimationFrame(() => {
    const tsWrap = container.querySelector('#temporal-structure-wrap');
    if (!tsWrap) return;
    tsWrap.innerHTML = renderTemporalStructure();
    _wireTemporalStructure(tsWrap, entities);
  });

  // ── Render appellate hierarchy ─────────────────────────────────────────────
  requestAnimationFrame(() => {
    const ahWrap = container.querySelector('#appellate-hierarchy-wrap');
    if (ahWrap) {
      ahWrap.innerHTML = renderAppellateHierarchy();
      ahWrap.addEventListener('click', ev => {
        const target = ev.target.closest('.ah-chip, .ah-anom');
        if (!target) return;
        const id = target.dataset.entityId;
        if (id) State.emit('navigateToDetail', id);
      });
    }
  });

  // ── Render strip plot (sized to container after DOM paint) ───────────────
  requestAnimationFrame(() => {
    const wrap = container.querySelector('#strip-plot-wrap');
    if (wrap) {
      const w = Math.max(480, wrap.clientWidth || 560);
      wrap.innerHTML = renderStripPlot(entities, w);

      // Wire bubble clicks → drill-down filtered to that score
      wrap.addEventListener('click', ev => {
        const bubble = ev.target.closest('.strip-bubble');
        if (bubble) {
          const clusterId = bubble.dataset.clusterId;
          const score = +bubble.dataset.score;
          const ids = JSON.parse(decodeURIComponent(bubble.dataset.ids || '[]'));
          showClusterDrill(clusterId, entities, container, ids);
          return;
        }
        // Cluster label text → drill all entities in that cluster
        const labelText = ev.target.closest('.strip-cluster-label');
        if (labelText) {
          showClusterDrill(labelText.dataset.clusterId, entities, container);
        }
      });

      // Wire row hover highlighting
      const svgEl = wrap.querySelector('svg');
      if (svgEl) {
        const highlightCluster = (clusterId) => {
          svgEl.querySelectorAll('.strip-bubble').forEach(b => {
            const active = b.dataset.clusterId === clusterId;
            b.style.fillOpacity = active ? '0.9' : '0.1';
            b.style.strokeOpacity = active ? '1' : '0.1';
          });
          svgEl.querySelectorAll('.strip-cluster-label').forEach(t => {
            t.style.opacity = t.dataset.clusterId === clusterId ? '1' : '0.25';
            t.style.fontWeight = t.dataset.clusterId === clusterId ? '700' : '';
          });
          svgEl.querySelectorAll('.strip-guide').forEach((line, i) => {
            const rowCl = svgEl.querySelectorAll('.strip-row-bg')[i]?.dataset.clusterId;
            line.style.strokeOpacity = rowCl === clusterId ? '1' : '0.2';
          });
          svgEl.querySelectorAll('.strip-row-bg').forEach(r => {
            r.style.fill = r.dataset.clusterId === clusterId ? 'rgba(51,51,46,0.04)' : 'transparent';
          });
        };
        const resetHighlight = () => {
          svgEl.querySelectorAll('.strip-bubble').forEach(b => {
            b.style.fillOpacity = '';
            b.style.strokeOpacity = '';
          });
          svgEl.querySelectorAll('.strip-cluster-label').forEach(t => {
            t.style.opacity = '';
            t.style.fontWeight = '';
          });
          svgEl.querySelectorAll('.strip-guide').forEach(l => { l.style.strokeOpacity = ''; });
          svgEl.querySelectorAll('.strip-row-bg').forEach(r => { r.style.fill = 'transparent'; });
        };

        svgEl.addEventListener('mouseover', ev => {
          const el = ev.target.closest('[data-cluster-id]');
          if (el) highlightCluster(el.dataset.clusterId);
        });
        svgEl.addEventListener('mouseleave', resetHighlight);
      }
    }
  });

  // ── Wire spotlight carousel ────────────────────────────────────────────────
  const featured = spotlightSet(entities);
  wireSpotlightCarousel(container, featured);

  // ── Wire stat-band tiles → toggle detail panel ─────────────────────────────
  const statBand = container.querySelector('#stat-band');
  const statPanel = container.querySelector('#stat-panel');
  let openStat = null;
  const closeStatPanel = () => {
    statPanel.hidden = true;
    statPanel.innerHTML = '';
    statBand?.querySelectorAll('.stat-item').forEach(b => {
      b.setAttribute('aria-expanded', 'false');
      b.classList.remove('stat-item-active');
    });
    openStat = null;
  };
  statBand?.addEventListener('click', e => {
    const btn = e.target.closest('.stat-item');
    if (!btn) return;
    const stat = btn.dataset.stat;
    if (stat === openStat) { closeStatPanel(); return; }
    statPanel.innerHTML = renderStatPanel(stat, entities);
    statPanel.hidden = false;
    statBand.querySelectorAll('.stat-item').forEach(b => {
      const isActive = b === btn;
      b.setAttribute('aria-expanded', isActive ? 'true' : 'false');
      b.classList.toggle('stat-item-active', isActive);
    });
    openStat = stat;
    // Scroll the panel into view if it ends up offscreen.
    requestAnimationFrame(() => {
      const r = statPanel.getBoundingClientRect();
      if (r.bottom > window.innerHeight) {
        statPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    });
  });
  // Coverage-panel-local filter state, kept on the .sp-card dataset for resilience.
  const _rerenderCoverage = (card) => {
    const selectedRaw = card.dataset.coverageFilter || '';
    const selected = selectedRaw ? new Set(selectedRaw.split(',')) : null;
    const fresh = renderStatPanel('coverage', entities, { coverageFilter: selected });
    statPanel.innerHTML = fresh;
    // Re-apply dataset to the new card (innerHTML wipes prior dataset).
    const newCard = statPanel.querySelector('.sp-card');
    if (newCard) newCard.dataset.coverageFilter = selectedRaw;
  };

  statPanel.addEventListener('click', e => {
    if (e.target.closest('.sp-close')) { closeStatPanel(); return; }

    const card = e.target.closest('.sp-card');
    const isCoverage = card?.dataset.stat === 'coverage';

    // Legend filter toggle
    const legendBtn = e.target.closest('.sp-legend-item');
    if (legendBtn && isCoverage) {
      e.preventDefault();
      e.stopPropagation();
      const key = legendBtn.dataset.levelKey;
      const currentRaw = card.dataset.coverageFilter || '';
      const all = GOV_LEVELS.map(l => l.key);
      let selected;
      if (!currentRaw) {
        // First click: deselect the one clicked = keep all others.
        selected = new Set(all.filter(k => k !== key));
      } else {
        selected = new Set(currentRaw.split(','));
        if (selected.has(key)) selected.delete(key); else selected.add(key);
      }
      // If everything is back in: clear filter (null state). If nothing: keep empty set but show empty.
      if (selected.size === all.length) {
        card.dataset.coverageFilter = '';
      } else {
        card.dataset.coverageFilter = [...selected].join(',');
      }
      _rerenderCoverage(card);
      return;
    }

    // Reset filter
    if (e.target.closest('.sp-filter-reset') && isCoverage) {
      e.preventDefault();
      e.stopPropagation();
      card.dataset.coverageFilter = '';
      _rerenderCoverage(card);
      return;
    }

    // Cluster row → drill overlay, respecting active filter when set
    const clusterRow = e.target.closest('.sp-row-cluster-bar');
    if (clusterRow) {
      e.preventDefault();
      e.stopPropagation();
      const cid = clusterRow.dataset.clusterId;
      const selectedRaw = isCoverage ? (card.dataset.coverageFilter || '') : '';
      if (selectedRaw) {
        const sel = new Set(selectedRaw.split(','));
        const ids = entities
          .filter(en => en.cluster === cid && sel.has(en.level_of_government || 'unknown'))
          .map(en => en.id);
        showClusterDrill(cid, entities, container, ids);
      } else {
        showClusterDrill(cid, entities, container);
      }
    }
  });

  // ── Wire card actions, browse-all, generic entity links ───────────────────
  container.addEventListener('click', e => {
    const reportBtn = e.target.closest('.sp-report');
    if (reportBtn) {
      e.preventDefault();
      const id = reportBtn.dataset.entityId;
      try { sessionStorage.setItem('jem.autoExport', id); } catch (_) {}
      State.emit('navigateToDetail', id);
      return;
    }

    const openBtn = e.target.closest('.sp-open');
    if (openBtn) {
      e.preventDefault();
      State.emit('navigateToDetail', openBtn.dataset.entityId);
      return;
    }

    const browseBtn = e.target.closest('#sp-browse-all');
    if (browseBtn) {
      e.preventDefault();
      openCatalogDrawer(entities);
      return;
    }

    const entityLink = e.target.closest('[data-entity-id]');
    if (entityLink && !entityLink.closest('.sp-card-head')) {
      e.preventDefault();
      State.emit('navigateToDetail', entityLink.dataset.entityId);
    }
  });

}

// ── Spotlight carousel state + interaction ───────────────────────────────────

let _spotlightIndex = 0;
let _spotlightTimer = null;
const SPOTLIGHT_INTERVAL_MS = 6000;

function wireSpotlightCarousel(container, featured) {
  const carousel = container.querySelector('.sp-carousel');
  if (!carousel || !featured.length) return;

  const track = carousel.querySelector('#sp-track');
  const dots = [...carousel.querySelectorAll('.sp-dot')];
  const counterI = carousel.querySelector('#sp-counter-i');
  const total = featured.length;
  _spotlightIndex = 0;

  function goTo(i, opts = {}) {
    // Loop: wrap around at edges so auto-advance never gets stuck
    _spotlightIndex = ((i % total) + total) % total;
    track.style.transform = `translateX(-${_spotlightIndex * 100}%)`;
    dots.forEach((d, di) => d.classList.toggle('active', di === _spotlightIndex));
    if (counterI) counterI.textContent = String(_spotlightIndex + 1);
    if (opts.userInitiated !== false) restartTimer();
  }

  function startTimer() {
    if (total <= 1) return;
    stopTimer();
    _spotlightTimer = setInterval(() => {
      goTo(_spotlightIndex + 1, { userInitiated: false });
    }, SPOTLIGHT_INTERVAL_MS);
  }
  function stopTimer() {
    if (_spotlightTimer) { clearInterval(_spotlightTimer); _spotlightTimer = null; }
  }
  function restartTimer() { stopTimer(); startTimer(); }

  carousel.querySelector('.sp-arrow-prev')?.addEventListener('click', e => {
    e.preventDefault();
    goTo(_spotlightIndex - 1);
  });
  carousel.querySelector('.sp-arrow-next')?.addEventListener('click', e => {
    e.preventDefault();
    goTo(_spotlightIndex + 1);
  });
  dots.forEach(dot => {
    dot.addEventListener('click', e => {
      e.preventDefault();
      goTo(+dot.dataset.i);
    });
  });

  carousel.addEventListener('keydown', e => {
    if (e.key === 'ArrowLeft') { e.preventDefault(); goTo(_spotlightIndex - 1); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); goTo(_spotlightIndex + 1); }
  });

  // Pointer/touch swipe
  let startX = null;
  const viewport = carousel.querySelector('.sp-viewport');
  viewport?.addEventListener('pointerdown', e => { startX = e.clientX; stopTimer(); });
  viewport?.addEventListener('pointerup', e => {
    if (startX == null) return;
    const dx = e.clientX - startX;
    startX = null;
    if (Math.abs(dx) < 40) { startTimer(); return; }
    goTo(_spotlightIndex + (dx < 0 ? 1 : -1));
  });
  viewport?.addEventListener('pointercancel', () => { startX = null; startTimer(); });

  // Pause on hover/focus, resume on leave/blur
  carousel.addEventListener('mouseenter', stopTimer);
  carousel.addEventListener('mouseleave', startTimer);
  carousel.addEventListener('focusin', stopTimer);
  carousel.addEventListener('focusout', startTimer);
  // Pause when the tab is hidden
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stopTimer();
    else startTimer();
  });

  startTimer();
}

// ── Catalog drawer (open/close, search, filter) ──────────────────────────────

function openCatalogDrawer(entities) {
  let drawer = document.getElementById('catalog-drawer');
  if (!drawer) {
    drawer = document.createElement('aside');
    drawer.id = 'catalog-drawer';
    drawer.className = 'catalog-drawer hidden';
    drawer.setAttribute('aria-hidden', 'true');
    drawer.innerHTML = `
      <div class="cat-drawer-backdrop"></div>
      <div class="cat-drawer-panel" role="dialog" aria-label="Browse all entities"></div>
    `;
    document.body.appendChild(drawer);
  }

  const panel = drawer.querySelector('.cat-drawer-panel');
  panel.innerHTML = renderCatalogDrawer(entities);
  _drawerState.rendered = true;

  // Show drawer
  drawer.classList.remove('hidden');
  drawer.setAttribute('aria-hidden', 'false');
  requestAnimationFrame(() => drawer.classList.add('open'));

  // Focus search
  setTimeout(() => drawer.querySelector('#cat-drawer-search')?.focus(), 50);

  // Wire interactions once
  if (!drawer.dataset.wired) {
    drawer.dataset.wired = '1';

    drawer.addEventListener('click', e => {
      if (e.target.classList.contains('cat-drawer-backdrop')
          || e.target.closest('#cat-drawer-close')) {
        closeCatalogDrawer(drawer);
        return;
      }
      const chip = e.target.closest('.cat-drawer-chip');
      if (chip) {
        _drawerState.band = chip.dataset.band;
        drawer.querySelectorAll('.cat-drawer-chip').forEach(c =>
          c.classList.toggle('active', c === chip));
        rerenderDrawerList(drawer, entities);
        return;
      }
      const reportIcon = e.target.closest('[data-report="1"]');
      if (reportIcon) {
        e.preventDefault();
        e.stopPropagation();
        const id = reportIcon.dataset.entityId;
        try { sessionStorage.setItem('jem.autoExport', id); } catch (_) {}
        closeCatalogDrawer(drawer);
        State.emit('navigateToDetail', id);
        return;
      }
      const row = e.target.closest('.cat-row');
      if (row) {
        e.preventDefault();
        closeCatalogDrawer(drawer);
        State.emit('navigateToDetail', row.dataset.entityId);
      }
    });

    drawer.addEventListener('input', e => {
      if (e.target.id === 'cat-drawer-search') {
        _drawerState.search = e.target.value || '';
        rerenderDrawerList(drawer, entities);
      }
    });

    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && !drawer.classList.contains('hidden')) {
        closeCatalogDrawer(drawer);
      }
    });
  }
}

function rerenderDrawerList(drawer, entities) {
  const list = drawer.querySelector('#cat-drawer-list');
  if (list) list.innerHTML = renderDrawerList(entities);
}

function closeCatalogDrawer(drawer) {
  drawer.classList.remove('open');
  drawer.setAttribute('aria-hidden', 'true');
  setTimeout(() => drawer.classList.add('hidden'), 220);
}

// Called externally to reset the view (e.g. when returning from detail)
export function resetSummaryView() {
  _spotlightIndex = 0;
  _drawerState.search = '';
  _drawerState.band = 'all';
}
