// JEM — Summary View
// Landing page: stat band, risk-distribution small multiples, high-risk registry, all-entities table.

import { State } from './state.js';

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

const TYPE_CATEGORY_MAP = {
  ConstitutionalCourt: 'Constitutional',
  HighCourtBench: 'Constitutional',
  CentralTribunal: 'Tribunal',
  StateTribunal: 'Tribunal',
  RegulatoryBodyQJ: 'Regulator',
  SharedRegulatoryBody: 'Regulator',
  BankingOmbudsman: 'Regulator',
  ConsumerCommission: 'Consumer',
  ArbitralInstitution: 'ADR',
  MediationBody: 'ADR',
  LokAdalat: 'ADR',
  ADRBody: 'ADR',
  AuditBody: 'Audit',
  AppointmentBody: 'Appointment',
  Lokayukta: 'Audit',
  SubordinateCivilCourt: 'Subordinate',
  SubordinateCriminalCourt: 'Subordinate',
  CityCivilCourt: 'Subordinate',
  SpecialCourt: 'Subordinate',
  FastTrackCourt: 'Subordinate',
  RevenueCourt: 'Subordinate',
  FamilyCourt: 'Subordinate',
  CommercialCourt: 'Subordinate',
  StatutoryBodyNotConstituted: 'Not Constituted',
  ExecutiveBody: 'Executive',
  Ministry: 'Executive',
  Department: 'Executive',
  LegislativeBody: 'Legislative',
  InvestigativeAgency: 'Investigative',
  ProsecutionBody: 'Investigative',
  DigitalInfraBody: 'Digital',
  SecurityBody: 'Security',
  TrainingBody: 'Training',
  ProfessionalBody: 'Professional',
};

const TYPE_CATEGORIES = ['All', 'Constitutional', 'Tribunal', 'Regulator', 'Consumer', 'ADR', 'Audit', 'Subordinate', 'Appointment', 'Investigative'];

// ── Helpers ───────────────────────────────────────────────────────────────────

function entityCategory(e) {
  return TYPE_CATEGORY_MAP[e.type] || 'Other';
}

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
// One row per cluster. X = IR score (0–15). Bubble area ∝ entity count at
// that score. Color = risk level. Click bubble → cluster drill-down filtered
// to that score bucket.

const SCORE_MAX   = 15;
const ROW_H       = 40;        // px per cluster row
const LABEL_W     = 148;       // px for left cluster label column
const AXIS_H      = 28;        // px for x-axis
const HEADER_H    = 18;        // px for column header
const PLOT_PAD_R  = 20;        // right padding
const MAX_BUBBLE_R = 15;       // max bubble radius in px

// Risk thresholds (matching derive.py: low 0-2, moderate 3-5, high 6-8, severe 9+)
const RISK_ZONES = [
  { x0: 0,   x1: 2.5,  level: 'low',      fill: '#f0fdf4' },
  { x0: 2.5, x1: 5.5,  level: 'moderate', fill: '#fff7ed' },
  { x0: 5.5, x1: 8.5,  level: 'high',     fill: '#fef2f2' },
  { x0: 8.5, x1: 15,   level: 'severe',   fill: '#faf5ff' },
];

function scoreToX(score, plotW) {
  return LABEL_W + (score / SCORE_MAX) * plotW;
}

function buildStripData(entities) {
  // For each cluster: Map of score → { count, level, entityIds }
  const clusters = {};
  entities.forEach(e => {
    const cl = e.cluster;
    if (!cl || SCORE_EXCLUDED_CLUSTERS.has(cl)) return;
    const score = e.derived?.independence_risk_score;
    const level = e.derived?.independence_risk_level;
    if (score == null || !level) return;
    if (!clusters[cl]) clusters[cl] = {};
    const key = score;
    if (!clusters[cl][key]) clusters[cl][key] = { count: 0, level, ids: [] };
    clusters[cl][key].count++;
    clusters[cl][key].ids.push(e.id);
  });

  // Sort clusters by weighted avg (worst first)
  return Object.entries(clusters)
    .filter(([, pts]) => Object.keys(pts).length > 0)
    .map(([cl, pts]) => {
      const entries = Object.entries(pts).map(([s, d]) => ({ score: +s, ...d }));
      const total = entries.reduce((s, d) => s + d.count, 0);
      const wavg = entries.reduce((s, d) => s + d.score * d.count, 0) / (total || 1);
      return { cl, entries, total, wavg };
    })
    .sort((a, b) => b.wavg - a.wavg);
}

function renderStripPlot(entities, svgWidth) {
  const plotW = svgWidth - LABEL_W - PLOT_PAD_R;
  const rows  = buildStripData(entities);
  const svgH  = HEADER_H + rows.length * ROW_H + AXIS_H;

  let svg = `<svg class="strip-svg" viewBox="0 0 ${svgWidth} ${svgH}"
    role="img" aria-label="Independence risk distribution by cluster">`;

  // ── Background risk zones ──────────────────────────────────────────────────
  const zonesY = HEADER_H;
  const zonesH = rows.length * ROW_H;
  RISK_ZONES.forEach(z => {
    const zx = scoreToX(z.x0, plotW);
    const zw = scoreToX(z.x1, plotW) - zx;
    svg += `<rect x="${zx}" y="${zonesY}" width="${zw}" height="${zonesH}"
      fill="${z.fill}" />`;
  });

  // ── Zone label row (header) ────────────────────────────────────────────────
  RISK_ZONES.forEach(z => {
    const zx = scoreToX((z.x0 + z.x1) / 2, plotW);
    svg += `<text x="${zx}" y="${HEADER_H - 5}" text-anchor="middle"
      font-size="9" fill="${RISK_COLORS[z.level]}" font-weight="600"
      opacity="0.8">${riskLevelLabel(z.level)}</text>`;
  });

  // ── Vertical grid lines at whole-number tick marks ────────────────────────
  [0, 3, 6, 9, 12, 15].forEach(tick => {
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

    // Bubbles — one per distinct score value in this cluster
    entries.forEach(({ score, count, level, ids }) => {
      const bx = scoreToX(score, plotW);
      const r  = Math.min(MAX_BUBBLE_R, Math.max(3, Math.sqrt(count) * 2.8));
      const color = RISK_COLORS[level] || '#aaa';
      const encodedIds = encodeURIComponent(JSON.stringify(ids));

      svg += `<circle class="strip-bubble"
        cx="${bx}" cy="${cy}" r="${r}"
        fill="${color}" fill-opacity="0.75"
        stroke="${color}" stroke-width="1" stroke-opacity="0.9"
        data-cluster-id="${cl}" data-score="${score}" data-ids="${encodedIds}"
        cursor="pointer" style="transition:opacity .15s">
        <title>${count} ${count === 1 ? 'entity' : 'entities'} · ${label} · score ${score} (${riskLevelLabel(level)})</title>
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
  [0, 3, 6, 9, 12, 15].forEach(tick => {
    const tx = scoreToX(tick, plotW);
    svg += `<text x="${tx}" y="${axisY + 13}" text-anchor="middle"
      font-size="9" fill="#86857c">${tick}</text>`;
  });
  svg += `<text x="${LABEL_W + plotW / 2}" y="${axisY + 24}" text-anchor="middle"
    font-size="9" fill="#86857c">Independence Risk Score →</text>`;

  svg += `</svg>`;
  return svg;
}

// ── High-risk entity registry ─────────────────────────────────────────────────

function renderRiskRegistry(entities) {
  const highRisk = entities
    .filter(e => e.derived?.independence_risk_level === 'high' || e.derived?.independence_risk_level === 'severe')
    .sort((a, b) => (b.derived?.independence_risk_score || 0) - (a.derived?.independence_risk_score || 0));

  if (!highRisk.length) return '<p class="sum-empty">No high-risk entities found in this build.</p>';

  const rows = highRisk.map(e => {
    const level = e.derived?.independence_risk_level || '';
    const score = e.derived?.independence_risk_score ?? '—';
    const breakdown = e.derived?.independence_risk_breakdown || {};
    // Pick the top contributing factor as the short description
    const topFactor = Object.entries(breakdown)
      .filter(([, v]) => v > 0)
      .sort((a, b) => b[1] - a[1])[0];
    const desc = topFactor ? topFactor[0] : '';

    return `<div class="reg-row" role="row">
      <span class="reg-score" style="color:${RISK_COLORS[level] || '#333'}">${score}</span>
      <span class="reg-name">
        <button class="reg-entity-link" data-entity-id="${e.id}">${e.name}</button>
        ${statusPill(e)}
      </span>
      <span class="reg-desc">${desc}</span>
    </div>`;
  }).join('');

  return `<div class="reg-header reg-row" role="columnheader">
    <span class="reg-score">Score</span>
    <span class="reg-name">Entity</span>
    <span class="reg-desc">Top structural factor</span>
  </div>
  <div class="reg-body">${rows}</div>`;
}

// ── All-entities table ────────────────────────────────────────────────────────

function buildHierarchyMaps(rels) {
  const childrenOf = {};
  const parentOf   = {};
  // AppealableTo: source appeals to target → target is the parent
  rels.forEach(r => {
    if (r.relationship_category === 'appellate_chain') {
      const parent = r.target, child = r.source;
      if (parent && child) {
        (childrenOf[parent] ||= []).push(child);
        if (!parentOf[child]) parentOf[child] = parent;
      }
    }
  });
  // BenchOf: source is a bench of target → target is the parent
  rels.forEach(r => {
    if (r.relationship_type === 'BenchOf') {
      const parent = r.target, child = r.source;
      if (parent && child && !parentOf[child]) {
        (childrenOf[parent] ||= []).push(child);
        parentOf[child] = parent;
      }
    }
  });
  return { childrenOf, parentOf };
}

// Renders appellate tree rows recursively; returns { html, visited }
function renderTreeRows(rootIds, entityById, childrenOf, sortKey) {
  const visited = new Set();
  let html = '';

  function walk(id, depth, ancestors) {
    if (visited.has(id)) return;
    visited.add(id);
    const e = entityById[id];
    if (!e) return;

    const rawChildren = (childrenOf[id] || []).filter(c => entityById[c] && !visited.has(c));
    const hasChildren = rawChildren.length > 0;
    const sortedChildren = [...rawChildren].sort((a, b) => {
      const ea = entityById[a], eb = entityById[b];
      return sortKey === 'risk'
        ? (eb?.derived?.independence_risk_score ?? -1) - (ea?.derived?.independence_risk_score ?? -1)
        : (ea?.name || a).localeCompare(eb?.name || b);
    });

    const level        = e.derived?.independence_risk_level;
    const score        = e.derived?.independence_risk_score;
    const isAbols      = e.operational_status === 'Abolished';
    const govLvl       = govLevelLabel(e.level_of_government);
    const ancestorsStr = ancestors.join(',');
    const isCollapsed  = _collapsedTreeNodes.has(id);
    const rowCls       = ['tree-row', isAbols && 'all-row-abolished'].filter(Boolean).join(' ');

    html += `<tr class="${rowCls}" data-id="${id}" data-depth="${depth}" data-ancestors="${ancestorsStr}">
      <td class="tree-toggle-cell">
        ${hasChildren
          ? `<button class="tree-toggle" data-id="${id}" title="${isCollapsed ? 'Expand' : 'Collapse'}">${isCollapsed ? '▶' : '▼'}</button>`
          : `<span class="tree-leaf"></span>`}
      </td>
      <td class="tree-name-cell" style="padding-left:${depth * 18 + 2}px">
        <button class="reg-entity-link" data-entity-id="${id}">${e.name}</button>
        ${statusPill(e)}
        <span class="tree-type-lbl">${typeLabel(e.type)}</span>
      </td>
      <td class="all-gov"><span class="gov-pill">${govLvl}</span></td>
      <td class="all-risk">
        ${level
          ? `<span class="risk-badge risk-${level}" style="color:${RISK_COLORS[level]}">${riskLevelLabel(level)}</span><span class="risk-num"> ${score}</span>`
          : '<span class="risk-none">—</span>'}
      </td>
    </tr>`;

    if (!isCollapsed) {
      sortedChildren.forEach(child => walk(child, depth + 1, [...ancestors, id]));
    }
  }

  rootIds.forEach(id => walk(id, 0, []));
  return { html, visited };
}

// Renders cluster-grouped rows for a given entity list (used for orphans + filtered views)
function renderClusterRows(members, childrenOf, parentOf, entityById, sortKey) {
  const clustersRaw = State.graph?.clusters || {};
  const clusterMeta = {};
  Object.values(clustersRaw).forEach(cl => { clusterMeta[cl.id] = cl; });

  const byCluster = {};
  members.forEach(e => { (byCluster[e.cluster || '_unknown'] ||= []).push(e); });

  const clusterOrder = Object.keys(byCluster).sort((a, b) => {
    const aAvg = clusterMeta[a]?.avg_independence_risk
      ?? byCluster[a].reduce((s, e) => s + (e.derived?.independence_risk_score ?? 0), 0) / byCluster[a].length;
    const bAvg = clusterMeta[b]?.avg_independence_risk
      ?? byCluster[b].reduce((s, e) => s + (e.derived?.independence_risk_score ?? 0), 0) / byCluster[b].length;
    return bAvg - aAvg;
  });

  function clusterEntityRow(e, rank, isChild = false) {
    const level   = e.derived?.independence_risk_level;
    const score   = e.derived?.independence_risk_score;
    const isAbols = e.operational_status === 'Abolished';
    const cls     = ['all-row', isChild && 'all-row-child', isAbols && 'all-row-abolished'].filter(Boolean).join(' ');
    return `<tr class="${cls}" data-cat="${entityCategory(e)}">
      <td class="all-rank">${isChild ? '' : rank}</td>
      <td class="all-name">
        ${isChild ? '<span class="tree-connector">└</span>' : ''}
        <button class="reg-entity-link" data-entity-id="${e.id}">${e.name}</button>
        ${statusPill(e)}
      </td>
      <td class="all-gov"><span class="gov-pill">${govLevelLabel(e.level_of_government)}</span></td>
      <td class="all-risk">
        ${level
          ? `<span class="risk-badge risk-${level}" style="color:${RISK_COLORS[level]}">${riskLevelLabel(level)}</span><span class="risk-num"> ${score}</span>`
          : '<span class="risk-none">—</span>'}
      </td>
    </tr>`;
  }

  let html = '';
  const memberIdSet = new Set(members.map(e => e.id));

  clusterOrder.forEach(clusterId => {
    const clMembers = byCluster[clusterId] || [];
    if (!clMembers.length) return;

    const meta       = clusterMeta[clusterId];
    const clColor    = meta?.color || '#888';
    const clLabel    = CLUSTER_LABELS[clusterId] || clusterId;
    const isExcluded = SCORE_EXCLUDED_CLUSTERS.has(clusterId);
    const scored     = clMembers.filter(e => e.derived?.independence_risk_score != null);
    const avgIR      = scored.length
      ? (scored.reduce((s, e) => s + e.derived.independence_risk_score, 0) / scored.length).toFixed(1)
      : null;
    const avgLevel = avgIR != null ? irScoreToLevel(+avgIR) : null;

    html += `<tr class="cl-header-row">
      <td colspan="4" class="cl-header-cell">
        <span class="cl-header-dot" style="background:${clColor}"></span>
        <span class="cl-header-name">${clLabel}</span>
        <span class="cl-header-count">${clMembers.length} entities</span>
        ${avgLevel ? `<span class="cl-header-ir" style="color:${RISK_COLORS[avgLevel]}">avg IR ${avgIR}</span>` : ''}
        ${isExcluded ? '<span class="cl-header-excl">scores not computed</span>' : ''}
      </td>
    </tr>`;

    // Top-level = not a child of another entity in this same set
    const topLevel = clMembers.filter(e => !parentOf[e.id] || !memberIdSet.has(parentOf[e.id]));

    const byType = {};
    topLevel.forEach(e => { (byType[e.type || '_unknown'] ||= []).push(e); });

    const typeOrder = Object.keys(byType).sort((a, b) => {
      if (sortKey === 'risk') {
        const aA = byType[a].reduce((s, e) => s + (e.derived?.independence_risk_score ?? -1), 0) / byType[a].length;
        const bA = byType[b].reduce((s, e) => s + (e.derived?.independence_risk_score ?? -1), 0) / byType[b].length;
        return bA - aA;
      }
      return a.localeCompare(b);
    });

    typeOrder.forEach(typeName => {
      let typeMembers = [...byType[typeName]];
      typeMembers = sortKey === 'risk'
        ? typeMembers.sort((a, b) => (b.derived?.independence_risk_score ?? -1) - (a.derived?.independence_risk_score ?? -1))
        : typeMembers.sort((a, b) => a.name.localeCompare(b.name));

      const childCount = typeMembers.reduce((n, e) =>
        n + (childrenOf[e.id] || []).filter(c => memberIdSet.has(c)).length, 0);

      html += `<tr class="type-header-row">
        <td colspan="4" class="type-header-cell">
          <span class="type-header-name">${typeLabel(typeName)}</span>
          <span class="type-header-count">${typeMembers.length}${childCount ? ` + ${childCount}` : ''}</span>
        </td>
      </tr>`;

      typeMembers.forEach((e, i) => {
        html += clusterEntityRow(e, i + 1);
        const children = (childrenOf[e.id] || [])
          .filter(c => memberIdSet.has(c))
          .map(c => entityById[c])
          .filter(Boolean);
        if (children.length) {
          const sorted = sortKey === 'risk'
            ? [...children].sort((a, b) => (b.derived?.independence_risk_score ?? -1) - (a.derived?.independence_risk_score ?? -1))
            : [...children].sort((a, b) => a.name.localeCompare(b.name));
          sorted.forEach(child => { html += clusterEntityRow(child, 0, true); });
        }
      });
    });
  });

  return html;
}

function renderClusteredEntitiesTable(entities, filter = 'All', sortKey = 'risk') {
  const rels = State.graph?.relationships || [];
  const { childrenOf, parentOf } = buildHierarchyMaps(rels);
  const entityById = {};
  entities.forEach(e => { entityById[e.id] = e; });

  // Filter mode: skip the appellate tree, show only matching cluster rows
  if (filter !== 'All') {
    const filtered = entities.filter(e => entityCategory(e) === filter);
    const clHtml = renderClusterRows(filtered, childrenOf, parentOf, entityById, sortKey);
    return `<table class="all-table all-table-clustered">
      <thead><tr>
        <th class="all-rank">#</th><th>Entity</th><th>Level</th><th>Independence Risk</th>
      </tr></thead>
      <tbody>${clHtml}</tbody>
    </table>`;
  }

  // All mode: appellate tree on top + orphan cluster groups below
  const ROOTS = ['supreme_court_india', 'president_india'].filter(id => entityById[id]);
  const { html: treeHtml, visited: inTree } = renderTreeRows(ROOTS, entityById, childrenOf, sortKey);
  const orphans  = entities.filter(e => !inTree.has(e.id));
  const orphanHtml = renderClusterRows(orphans, childrenOf, parentOf, entityById, sortKey);

  const tbody = `
    <tr class="section-divider-row">
      <td colspan="4" class="section-divider-cell">
        <span class="section-divider-title">Appellate hierarchy</span>
        <span class="section-divider-count">${inTree.size} entities · rooted at Supreme Court &amp; President</span>
      </td>
    </tr>
    ${treeHtml}
    <tr class="section-divider-row">
      <td colspan="4" class="section-divider-cell">
        <span class="section-divider-title">Outside appellate chain</span>
        <span class="section-divider-count">${orphans.length} entities · grouped by cluster</span>
        <span class="section-divider-note">Regulators, tribunals &amp; legislative bodies without documented appellate connections</span>
      </td>
    </tr>
    ${orphanHtml}
  `;

  return `<table class="all-table all-table-clustered" id="all-entities-tree-table">
    <thead><tr>
      <th class="tree-toggle-col"></th><th>Entity</th><th>Level</th><th>Independence Risk</th>
    </tr></thead>
    <tbody>${tbody}</tbody>
  </table>`;
}

// ── Cluster drill-down overlay ────────────────────────────────────────────────

function buildClusterDrillHTML(clusterId, entities, filterIds = null) {
  const label = CLUSTER_LABELS[clusterId] || clusterId;
  const idSet = filterIds ? new Set(filterIds) : null;
  const members = entities
    .filter(e => e.cluster === clusterId && (!idSet || idSet.has(e.id)))
    .sort((a, b) => (b.derived?.independence_risk_score ?? -1) - (a.derived?.independence_risk_score ?? -1));

  if (!members.length) return `<p class="sum-empty">No entities in this cluster.</p>`;

  const rows = members.map((e, i) => {
    const level = e.derived?.independence_risk_level;
    const score = e.derived?.independence_risk_score;
    const color = level ? RISK_COLORS[level] : '#aaa';
    return `<div class="reg-row" role="row">
      <span class="reg-score" style="color:${color}">${score ?? '—'}</span>
      <span class="reg-name">
        <button class="reg-entity-link" data-entity-id="${e.id}">${e.name}</button>
        ${statusPill(e)}
      </span>
      <span class="reg-desc" style="color:var(--jem-mute);font-size:11px">${e.type?.replace(/([A-Z])/g,' $1').trim() || ''}</span>
    </div>`;
  }).join('');

  return `<div class="cl-drill-header">
    <span class="cl-drill-title">${label}</span>
    <span class="cl-drill-count">${members.length} entities</span>
  </div>
  <div class="reg-header reg-row" role="columnheader">
    <span class="reg-score">Score</span>
    <span class="reg-name">Entity</span>
    <span class="reg-desc">Type</span>
  </div>
  <div class="reg-body">${rows}</div>`;
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
    const link = e.target.closest('[data-entity-id]');
    if (link) {
      e.preventDefault();
      overlay.classList.add('cl-drill-hidden');
      State.emit('navigateToDetail', link.dataset.entityId);
    }
  });
}

// ── Main render ───────────────────────────────────────────────────────────────

let _currentTab = 'risks';
let _currentCatFilter = 'All';
let _currentSort = 'risk';
let _collapsedTreeNodes = new Set();

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

  const catFilterBtns = TYPE_CATEGORIES.map(cat =>
    `<button class="cat-filter-btn${cat === 'All' ? ' active' : ''}" data-cat="${cat}">${cat}</button>`
  ).join('');

  container.innerHTML = `
    <div class="sum-inner">

      <div class="sum-masthead">
        <h1 class="sum-title">Judiciary Entity Map — India</h1>
        <p class="sum-subtitle">Structural map of appointment chains, funding flows, independence risk, and systemic gaps across India's judicial ecosystem.</p>
      </div>

      <div class="stat-band">
        <div class="stat-item">
          <span class="stat-num">${entities.length}<span class="stat-denom"> / ~1,500</span></span>
          <span class="stat-lbl">Entities mapped</span>
        </div>
        <div class="stat-item stat-item-risk">
          <span class="stat-num">${highRiskCount}</span>
          <span class="stat-lbl">High or severe independence risk</span>
        </div>
        <div class="stat-item stat-item-nc">
          <span class="stat-num">${notConstitutedCount}</span>
          <span class="stat-lbl">Legislated but not constituted</span>
        </div>
        ${avgDisposal ? `<div class="stat-item">
          <span class="stat-num">${avgDisposal}</span>
          <span class="stat-lbl">Avg disposal rate (of entities with NJDG data)</span>
        </div>` : ''}
      </div>

      <div class="sm-section">
        <div class="sm-section-head">
          <span class="sm-section-title">Independence risk distribution</span>
        </div>
        <p class="sm-note-global">Each bubble = entities at that score. Bubble area ∝ count. Click any bubble or label to see those entities. Legislative/executive bodies excluded (governance anchors).</p>
        <div class="strip-wrap" id="strip-plot-wrap"></div>
      </div>

      <div class="sum-tabs" role="tablist">
        <button class="sum-tab active" id="sum-tab-risks" data-tab="risks" role="tab" aria-selected="true">High-risk entities (${highRiskCount})</button>
        <button class="sum-tab" id="sum-tab-all" data-tab="all" role="tab" aria-selected="false">All ${entities.length} entities</button>
      </div>

      <div id="sum-pane-risks" class="sum-pane" role="tabpanel">
        <p class="sum-pane-note">Entities with high or severe independence risk, ranked by score. Click an entity to see its full structural profile.</p>
        <div class="reg-table" id="risk-registry">${renderRiskRegistry(entities)}</div>
      </div>

      <div id="sum-pane-all" class="sum-pane sum-pane-hidden" role="tabpanel">
        <p class="sum-pane-note">All ${entities.length} entities, sorted by independence risk. ⚐ Scores for legislative/executive bodies not computed — governance anchors only.</p>
        <div class="all-controls">
          <div class="cat-filter-group" role="group" aria-label="Filter by category">${catFilterBtns}</div>
          <div class="sort-group">
            <span class="sort-lbl">Sort:</span>
            <button class="sort-btn active" id="sort-by-risk">By risk</button>
            <button class="sort-btn" id="sort-by-alpha">A–Z</button>
          </div>
        </div>
        <div id="all-entities-table">${renderClusteredEntitiesTable(entities, 'All', 'risk')}</div>
      </div>

      <div class="sum-footer">
        <button class="btn-explore-map" id="btn-explore-map">Explore full map →</button>
      </div>

    </div>
  `;

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

  // ── Wire tabs ──────────────────────────────────────────────────────────────
  container.querySelectorAll('.sum-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      _currentTab = btn.dataset.tab;
      container.querySelectorAll('.sum-tab').forEach(b => {
        b.classList.toggle('active', b === btn);
        b.setAttribute('aria-selected', b === btn ? 'true' : 'false');
      });
      container.querySelectorAll('.sum-pane').forEach(p => p.classList.add('sum-pane-hidden'));
      const pane = container.querySelector(`#sum-pane-${_currentTab}`);
      if (pane) pane.classList.remove('sum-pane-hidden');
    });
  });

  // ── Wire category filter buttons + tree collapse ──────────────────────────
  container.addEventListener('click', e => {
    // Tree collapse/expand toggle
    const treeToggle = e.target.closest('.tree-toggle');
    if (treeToggle) {
      const id = treeToggle.dataset.id;
      if (_collapsedTreeNodes.has(id)) _collapsedTreeNodes.delete(id);
      else _collapsedTreeNodes.add(id);
      _rerenderAllTable(container, entities);
      return;
    }

    const catBtn = e.target.closest('.cat-filter-btn');
    if (catBtn) {
      _currentCatFilter = catBtn.dataset.cat;
      container.querySelectorAll('.cat-filter-btn').forEach(b => b.classList.toggle('active', b === catBtn));
      _rerenderAllTable(container, entities);
      return;
    }

    const sortBtn = e.target.closest('.sort-btn');
    if (sortBtn) {
      _currentSort = sortBtn.id === 'sort-by-alpha' ? 'alpha' : 'risk';
      container.querySelectorAll('.sort-btn').forEach(b => b.classList.toggle('active', b === sortBtn));
      _rerenderAllTable(container, entities);
      return;
    }

    const entityLink = e.target.closest('[data-entity-id]');
    if (entityLink) {
      e.preventDefault();
      State.emit('navigateToDetail', entityLink.dataset.entityId);
    }
  });

  // ── Wire "Explore full map" ────────────────────────────────────────────────
  container.querySelector('#btn-explore-map')?.addEventListener('click', () => {
    State.emit('navigateToMap', null);
  });
}

function _rerenderAllTable(container, entities) {
  const el = container.querySelector('#all-entities-table');
  if (el) el.innerHTML = renderClusteredEntitiesTable(entities, _currentCatFilter, _currentSort);
}

// Called externally to reset the view (e.g. when returning from detail)
export function resetSummaryView() {
  _currentTab = 'risks';
  _currentCatFilter = 'All';
  _currentSort = 'risk';
  _collapsedTreeNodes.clear();
}
