// JEM — Entity Detail View
// Independence risk hero + score breakdown + neighborhood graph + gaps + case volume.

import { State } from './state.js';
import { loadD3 } from './loadD3.js';
import { getProfileSections } from './panel.js';
import { balanceProfileColumns } from './profileLayout.js';
import { commentsHTML, wireComments } from './comments.js';

const SECTION_TAB_MAP = {
  lifecycle:   'setup',
  jurisdiction_scope: 'setup',
  jurisdiction_circuit: 'setup',
  jurisdiction_routing: 'setup',
  jurisdiction_routes: 'setup',
  parent_hc:   'setup',
  judges:      'setup',
  appointment: 'setup',
  funding:     'setup',
  audit:       'activity',
  complaint:   'activity',
  sources:     'activity',
  gaps:        'score',
};

function renderProfileWidget(s) {
  const tab = SECTION_TAB_MAP[s.key] || 'setup';
  const collapsed = s.key === 'jurisdiction_routes' || s.key === 'judges';
  const openAttr = collapsed ? '' : ' open';
  return `
    <details class="dv-section dv-tab-${tab}"${openAttr}>
      <summary><span>${s.title}</span></summary>
      <div class="dv-section-body">${s.body}</div>
    </details>
  `;
}
import { getAppellateChainForEntity } from './entityConnections.js';
import { printBrandBlock } from './brand.js';
import { scoreTip } from './scoreHelp.js';
import {
  shouldShowStructuralScores,
  structuralScoresHiddenMessage,
} from './scoreDisplay.js';

const RISK_COLORS = {
  low:      '#16a34a',
  moderate: '#d97706',
  high:     '#dc2626',
  severe:   '#7c3aed',
};

const RISK_EXPLAIN = {
  low:      'Structural design offers meaningful independence from executive influence.',
  moderate: 'Some structural vulnerabilities to executive influence; warrants monitoring.',
  high:     'Significant structural vulnerabilities — appointment, funding, or complaint mechanisms compromise independence.',
  severe:   'Critical structural independence risk — multiple compounding factors or entity not constituted.',
};

const HEALTH_EXPLAIN = {
  critical: 'Critical structural health — compounding independence and discretionary-power risks across the entity\'s design.',
  at_risk:  'Multiple structural vulnerabilities; the entity\'s design exposes it to executive influence or unbounded discretion.',
  watch:    'Functional but with notable structural weaknesses worth monitoring.',
  healthy:  'Structural design offers meaningful guardrails against executive influence and unchecked discretion.',
};

const HEALTH_LEVEL_LABELS = {
  critical: 'Critical',
  at_risk:  'At Risk',
  watch:    'Watch',
  healthy:  'Healthy',
};

const REL_COLORS = {
  appellate_chain: '#2c3e50',
  appointment:     '#e67e22',
  funding:         '#27ae60',
  supervisory:     '#8e44ad',
  audit:           '#7f8c8d',
  complaint:       '#e74c3c',
  digital:         '#2980b9',
  security:        '#6d4c41',
  training:        '#16a085',
  statutory_ref:   '#bdc3c7',
  investigative:   '#c0392b',
};

const REL_LABELS = {
  appellate_chain: 'Appellate',
  appointment:     'Appointment',
  funding:         'Funding',
  supervisory:     'Supervisory',
  audit:           'Audit',
  complaint:       'Complaint',
  digital:         'Digital',
  security:        'Security',
  training:        'Training',
  statutory_ref:   'Statutory',
  investigative:   'Investigative',
};

const DEFAULT_LENSES = new Set(['appellate_chain', 'appointment', 'funding']);

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

// ── State ─────────────────────────────────────────────────────────────────────

let _currentEntityId = null;
let _historyStack = [];          // for ← Previous entity
let _nbLenses = new Set(DEFAULT_LENSES);
let _fsOverlay = null;           // fullscreen tree overlay
// Persists graph topology (expanded nodes) across mini ↔ fullscreen transitions
let _graphState = null;          // { entityId, expandedOrder: string[] }
let _miniGraphWrap = null;       // ref to mini graph container for re-render on fs close

// ── Helpers ───────────────────────────────────────────────────────────────────

function statusPill(e) {
  if (e.operational_status === 'Not_Constituted')
    return '<span class="dv-pill dv-pill-nc">Not Constituted</span>';
  if (e.operational_status === 'Abolished')
    return '<span class="dv-pill dv-pill-abolished">Abolished</span>';
  if (e.operational_status === 'Partial_Operational')
    return '<span class="dv-pill dv-pill-partial">Partial</span>';
  if (e.operational_status === 'De_Facto_Blocked')
    return '<span class="dv-pill dv-pill-blocked">De Facto Blocked</span>';
  return '';
}

// Convert snake_case / Title_Case identifiers into human-readable labels for UI.
function humanize(str) {
  if (str == null) return '';
  return String(str)
    .replace(/_/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, c => c.toUpperCase());
}

function clogColor(severity) {
  const map = { critical: '#a32d2d', high: '#c2722b', moderate: '#8a7a2b', low: '#1d7a5a', unknown: '#888' };
  return map[severity] || '#888';
}

function fmtNum(n) {
  if (n == null) return '—';
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(0) + 'K';
  return String(n);
}

// ── Breakdown table ───────────────────────────────────────────────────────────

function renderBreakdown(breakdown, label, maxScore) {
  if (!breakdown || !Object.keys(breakdown).length) return '';
  const rows = Object.entries(breakdown)
    .filter(([, v]) => v !== 0)
    .sort((a, b) => b[1] - a[1])
    .map(([factor, pts]) => {
      const isPos = pts > 0;
      return `<tr>
        <td class="bd-factor">${humanize(factor)}</td>
        <td class="bd-pts ${isPos ? 'bd-pts-pos' : 'bd-pts-neg'}">${isPos ? '+' : ''}${pts}</td>
      </tr>`;
    }).join('');

  return `<div class="bd-section">
    <div class="bd-title">${label} breakdown</div>
    <table class="bd-table"><tbody>${rows}</tbody></table>
  </div>`;
}

// Fused IR + DP breakdown — single table with a source tag column so each factor
// is still traceable to its scoring stream.
function renderFusedBreakdown(irBd, dpBd, irColor) {
  const entries = [];
  if (irBd) for (const [k, v] of Object.entries(irBd)) if (v !== 0) entries.push({ source: 'IR', factor: k, pts: v, color: irColor });
  if (dpBd) for (const [k, v] of Object.entries(dpBd)) if (v !== 0) entries.push({ source: 'DP', factor: k, pts: v, color: '#6366f1' });
  if (!entries.length) return '<div class="bd-empty">No contributing factors recorded.</div>';

  entries.sort((a, b) => b.pts - a.pts);
  const rows = entries.map(e => {
    const isPos = e.pts > 0;
    return `<tr>
      <td class="bd-source"><span class="bd-source-tag" style="background:${e.color}1a;color:${e.color};border:1px solid ${e.color}55">${e.source}</span></td>
      <td class="bd-factor">${humanize(e.factor)}</td>
      <td class="bd-pts ${isPos ? 'bd-pts-pos' : 'bd-pts-neg'}">${isPos ? '+' : ''}${e.pts}</td>
    </tr>`;
  }).join('');

  return `<table class="bd-table bd-table-fused"><tbody>${rows}</tbody></table>`;
}

// ── Case volume ───────────────────────────────────────────────────────────────

// ── "Where this fits" — appellate chain strip ────────────────────────────────
// Renders upstream + downstream from the focal entity as a horizontal breadcrumb.
// Generic / aggregate / placeholder rows are excluded. Each node is clickable.
const APPELLATE_HIGHER_LABEL = 'higher courts or court-like';
const APPELLATE_LOWER_LABEL = 'lower courts or court-like';

function appellateCountSuffix(n) {
  return n > 2 ? ` (${n})` : '';
}

function appellateChainHint(upCount, downCount) {
  return `${APPELLATE_HIGHER_LABEL}${appellateCountSuffix(upCount)} ← → ${APPELLATE_LOWER_LABEL}${appellateCountSuffix(downCount)}`;
}

function renderAppellateExportList(entity, upstream, downstream, upCount, downCount) {
  const item = (id) => {
    const e = State.getEntityById(id);
    if (!e) return '';
    const abbr = e.abbreviation && e.abbreviation !== e.name ? ` (${e.abbreviation})` : '';
    return `<li>${e.name}${abbr}</li>`;
  };
  const upFlat = [...upstream].reverse().flat();
  const downFlat = downstream.flat();

  const block = (title, count, ids) => {
    if (!ids.length) return '';
    return `
      <div class="wtf-export-block">
        <div class="wtf-export-title">${title} (${count})</div>
        <ol class="wtf-export-ol">${ids.map(item).join('')}</ol>
      </div>
    `;
  };

  const focalAbbr = entity.abbreviation && entity.abbreviation !== entity.name
    ? ` (${entity.abbreviation})`
    : '';

  return `
    <div class="wtf-export-list" aria-hidden="true">
      ${block(APPELLATE_HIGHER_LABEL, upCount, upFlat)}
      <div class="wtf-export-focal"><strong>${entity.name}</strong>${focalAbbr} — focal entity</div>
      ${block(APPELLATE_LOWER_LABEL, downCount, downFlat)}
    </div>
  `;
}

function renderAppellateChainStrip(entity) {
  const { upstream, downstream, upCount, downCount, hasEdges } = getAppellateChainForEntity(entity.id);
  if (!hasEdges) return '';

  const nodeChip = (id, focal = false) => {
    const e = State.getEntityById(id);
    if (!e) return '';
    const label = e.abbreviation || e.name;
    return `<button type="button" class="wtf-node${focal ? ' wtf-node-focal' : ''}" data-entity-id="${id}" title="${(e.name || '').replace(/"/g, '&quot;')}">${label}</button>`;
  };

  const tierGroup = (tier) => `<span class="wtf-tier">${tier.map((id) => nodeChip(id)).join('<span class="wtf-sib-sep">·</span>')}</span>`;

  const upChain = [...upstream].reverse().map(tierGroup);
  const downChain = downstream.map(tierGroup);

  const arrow = '<span class="wtf-arrow" aria-hidden="true">›</span>';
  const parts = [
    ...upChain,
    nodeChip(entity.id, true),
    ...downChain,
  ];

  return `
    <div class="wtf-card">
      <div class="wtf-head">
        <span class="wtf-label">Appellate chain — where this fits</span>
        <span class="wtf-hint">${appellateChainHint(upCount, downCount)}</span>
      </div>
      <div class="wtf-strip">
        ${parts.join(arrow)}
      </div>
      ${renderAppellateExportList(entity, upstream, downstream, upCount, downCount)}
    </div>
  `;
}

// Inline summary stats shown in the collapsed `<summary>` line of the Case Volume section.
function renderCaseVolumeSummary(cv) {
  if (!cv) return '';
  const parts = [];
  if (cv.clog_severity) parts.push(`<span class="dv-stat-chip" style="color:${clogColor(cv.clog_severity)};border-color:${clogColor(cv.clog_severity)}">${cv.clog_severity.toUpperCase()}</span>`);
  if (cv.pending_cases != null) parts.push(`<span class="dv-stat-mute">${fmtNum(cv.pending_cases)} pending</span>`);
  if (cv.disposal_rate != null) parts.push(`<span class="dv-stat-mute">${cv.disposal_rate.toFixed(2)} disposal</span>`);
  return parts.join(' · ');
}

function renderCaseVolume(cv) {
  if (!cv) return '';
  const stats = [];
  if (cv.pending_cases != null) stats.push(`<span class="cv-stat"><span class="cv-num">${fmtNum(cv.pending_cases)}</span><span class="cv-label"> pending</span></span>`);
  if (cv.disposal_rate != null) stats.push(`<span class="cv-stat"><span class="cv-num">${cv.disposal_rate.toFixed(2)}</span><span class="cv-label"> disposal rate</span></span>`);
  if (cv.clog_severity) stats.push(`<span class="cv-stat"><span class="cv-num" style="color:${clogColor(cv.clog_severity)}">${cv.clog_severity.toUpperCase()}</span><span class="cv-label"> clog</span></span>`);
  if (!stats.length) return '';
  const asOf = cv.data_as_of ? `<span class="cv-asof">Data as of ${cv.data_as_of}</span>` : '';
  const head = `<div class="cv-section"><div class="cv-row">${stats.join('')}${asOf}</div></div>`;

  // Detail rows (previously buried under the Profile widget).
  const rows = [];
  const row = (lbl, val) => val == null || val === '' ? '' : `<div class="detail-row"><span class="lbl">${lbl}</span><span>${val}</span></div>`;
  if (cv.pending_cases != null) rows.push(row('Pending cases', String(cv.pending_cases).replace(/\B(?=(\d{3})+(?!\d))/g, ',')));
  if (cv.filed_last_year != null) rows.push(row('Filed (last year)', String(cv.filed_last_year)));
  if (cv.disposed_last_year != null) rows.push(row('Disposed (last year)', String(cv.disposed_last_year)));
  if (cv.disposal_rate != null) rows.push(row('Disposal rate', String(cv.disposal_rate)));
  if (cv.avg_disposal_days != null) rows.push(row('Avg disposal days', String(cv.avg_disposal_days)));
  if (cv.sanctioned_strength != null) rows.push(row('Sanctioned strength', String(cv.sanctioned_strength)));
  if (cv.working_strength != null) rows.push(row('Working strength', String(cv.working_strength)));
  if (cv.clog_severity) rows.push(row('Clog severity', cv.clog_severity));
  if (cv.source_type) rows.push(row('Volume source type', cv.source_type));
  if (cv.source_url) rows.push(`<div class="detail-row"><span class="lbl">Volume source</span><span><a href="${cv.source_url}" target="_blank" rel="noopener noreferrer">${cv.source_url}</a></span></div>`);
  const detail = rows.length ? `<div class="cv-rows">${rows.join('')}</div>` : '';
  return head + detail;
}

// ── Directed force-graph (ego-network) ───────────────────────────────────────

const GRAPH_LENSES = ['appellate_chain', 'supervisory', 'appointment', 'funding'];

// Which relationships each lens includes.
// Note: BenchOf (statutory_ref category) is structural hierarchy — a bench is *part of*
// its parent court — not an appellate route. It is always shown regardless of lens so
// that toggling the Appellate lens never makes unrelated structural edges vanish.
function relMatchesLens(r, lenses) {
  if (r.relationship_category === 'statutory_ref' && r.relationship_type === 'BenchOf') return true;
  if (lenses.has('appellate_chain') && r.relationship_category === 'appellate_chain') return true;
  if (lenses.has('supervisory')  && r.relationship_category === 'supervisory')  return true;
  if (lenses.has('appointment')  && r.relationship_category === 'appointment')  return true;
  if (lenses.has('funding')      && r.relationship_category === 'funding')      return true;
  return false;
}

function openFullscreenGraph(entityId, lenses) {
  if (_fsOverlay) { _fsOverlay.remove(); _fsOverlay = null; }

  const entity = State.getEntityById(entityId);
  const overlay = document.createElement('div');
  overlay.className = 'nb-fs-overlay';
  overlay.innerHTML = `
    <div class="nb-fs-header">
      <span class="nb-fs-title">${entity?.name || ''} — structural neighborhood</span>
      <button class="nb-fs-close" title="Close (Esc)">×</button>
    </div>
    <div class="nb-fs-body" id="nb-fs-body"></div>
  `;
  document.body.appendChild(overlay);
  _fsOverlay = overlay;

  const close = () => {
    overlay.remove();
    _fsOverlay = null;
    document.removeEventListener('keydown', escHandler);
    // Sync expanded state back to mini graph
    if (_miniGraphWrap && _miniGraphWrap.isConnected) {
      renderNeighborhoodGraph(_miniGraphWrap, entityId, lenses);
      const expandBtn = document.createElement('button');
      expandBtn.className = 'nb-expand-btn';
      expandBtn.title = 'Fullscreen';
      expandBtn.textContent = '⤢';
      expandBtn.onclick = () => openFullscreenGraph(entityId, lenses);
      _miniGraphWrap.appendChild(expandBtn);
    }
  };
  const escHandler = e => { if (e.key === 'Escape') close(); };
  overlay.querySelector('.nb-fs-close').onclick = close;
  document.addEventListener('keydown', escHandler);

  requestAnimationFrame(() => {
    const body = overlay.querySelector('#nb-fs-body');
    if (body) void renderNeighborhoodGraph(body, entityId, lenses);
  });
}

async function renderNeighborhoodGraph(container, entityId, lenses) {
  try {
    await loadD3();
  } catch {
    container.innerHTML = '<p class="nb-empty">Could not load graph library.</p>';
    return;
  }
  const d3 = window.d3;
  container.innerHTML = '';

  const graph = State.graph;
  if (!graph) return;

  const allRels = graph.relationships || [];
  const entityById = {};
  (graph.entities || []).forEach(e => { entityById[e.id] = e; });

  // Build initial 1-hop ego-network
  const initNeighborIds = new Set();
  allRels.forEach(r => {
    if (r.source !== entityId && r.target !== entityId) return;
    if (!relMatchesLens(r, lenses)) return;
    if (!entityById[r.source] || !entityById[r.target]) return;
    initNeighborIds.add(r.source === entityId ? r.target : r.source);
  });

  if (!initNeighborIds.size) {
    container.innerHTML = '<p class="nb-empty">No direct relationships for the selected lenses.</p>';
    return;
  }

  const W = Math.max(440, container.clientWidth  || 440);
  const H = Math.max(340, container.clientHeight || 380);
  const cx = W / 2, cy = H / 2;

  // ── Mutable graph state ───────────────────────────────────────────────────
  const nodeSet = new Set([entityId, ...initNeighborIds]);
  const linkKeySet = new Set();
  const expandedIds = new Set();
  const expandedChildren = new Map(); // nodeId → Set of IDs it added
  // Ordered list of expansions — saved to _graphState so fullscreen ↔ mini transitions preserve topology
  const expandOrder = [];

  let mNodes = [
    { id: entityId, entity: entityById[entityId], isFocus: true,
      x: cx, y: cy, fx: cx, fy: cy },
    ...[...initNeighborIds].map(nid => ({
      id: nid, entity: entityById[nid], isFocus: false,
      x: cx + (Math.random() - 0.5) * 140,
      y: cy + (Math.random() - 0.5) * 140,
    })),
  ];
  const nById = new Map(mNodes.map(n => [n.id, n]));

  let mLinks = [];
  allRels.forEach(r => {
    if (!nById.has(r.source) || !nById.has(r.target)) return;
    if (!relMatchesLens(r, lenses)) return;
    const key = `${r.source}\x00${r.target}\x00${r.relationship_category}`;
    if (linkKeySet.has(key)) return;
    linkKeySet.add(key);
    mLinks.push({ source: nById.get(r.source), target: nById.get(r.target),
                  category: r.relationship_category,
                  type: r.relationship_type || r.relationship_category, _key: key });
  });

  // ── Restore previously expanded nodes (fullscreen ↔ mini transition) ────────
  if (_graphState?.entityId === entityId && _graphState.expandOrder.length) {
    _graphState.expandOrder.forEach(nodeId => {
      if (!nodeSet.has(nodeId)) return; // node not in current 1-hop graph, skip
      const addedIds = new Set();
      const newLinks = [];
      allRels.forEach(r => {
        if (r.source !== nodeId && r.target !== nodeId) return;
        if (!relMatchesLens(r, lenses)) return;
        const otherId = r.source === nodeId ? r.target : r.source;
        if (!entityById[otherId]) return;
        if (!nodeSet.has(otherId)) {
          const src = nById.get(nodeId);
          const nn = { id: otherId, entity: entityById[otherId], isFocus: false,
                       x: src.x + (Math.random() - 0.5) * 80,
                       y: src.y + (Math.random() - 0.5) * 80 };
          mNodes.push(nn); nById.set(otherId, nn);
          nodeSet.add(otherId); addedIds.add(otherId);
        }
        const key = `${r.source}\x00${r.target}\x00${r.relationship_category}`;
        if (!linkKeySet.has(key)) {
          linkKeySet.add(key);
          newLinks.push({ source: nById.get(r.source), target: nById.get(r.target),
                          category: r.relationship_category,
                          type: r.relationship_type || r.relationship_category, _key: key });
        }
      });
      mLinks = [...mLinks, ...newLinks];
      expandedIds.add(nodeId);
      expandedChildren.set(nodeId, addedIds);
      expandOrder.push(nodeId);
    });
  }

  // ── SVG scaffold ──────────────────────────────────────────────────────────
  // viewBox + 100% sizing → SVG rescales with the container on window resize,
  // so the graph stays fully visible at all breakpoints without re-rendering.
  const svg = d3.select(container).append('svg')
    .attr('viewBox', `0 0 ${W} ${H}`)
    .attr('preserveAspectRatio', 'xMidYMid meet')
    .attr('width', '100%').attr('height', '100%')
    .style('font-family', 'Inter, sans-serif')
    .style('display', 'block');

  const defs = svg.append('defs');
  // Pre-create all category markers so newly added edges always find theirs
  Object.entries(REL_COLORS).forEach(([cat, color]) => {
    defs.append('marker')
      .attr('id', 'arr-' + cat.replace(/\W/g, '_'))
      .attr('viewBox', '0 0 10 10').attr('refX', 9).attr('refY', 5)
      .attr('markerWidth', 5).attr('markerHeight', 5).attr('orient', 'auto')
      .append('path').attr('d', 'M0,0 L10,5 L0,10 z').attr('fill', color);
  });

  const zoom = d3.zoom().scaleExtent([0.18, 3])
    .on('zoom', ev => gMain.attr('transform', ev.transform));
  svg.call(zoom).on('dblclick.zoom', null);
  svg.on('click', () => hidePopover());

  const gMain   = svg.append('g');
  const gLinks  = gMain.append('g');
  const gLabels = gMain.append('g');
  const gNodes  = gMain.append('g');

  // ── Live force simulation ─────────────────────────────────────────────────
  const sim = d3.forceSimulation()
    .force('link',    d3.forceLink().id(d => d.id).distance(170).strength(0.45))
    .force('charge',  d3.forceManyBody().strength(-450))
    .force('collide', d3.forceCollide().radius(d => d.isFocus ? 40 : 32).iterations(3))
    .force('center',  d3.forceCenter(cx, cy).strength(0.05))
    .alphaDecay(0.028).velocityDecay(0.42);

  // ── Drag ──────────────────────────────────────────────────────────────────
  const drag = d3.drag()
    .on('start', (ev, d) => {
      if (!ev.active) sim.alphaTarget(0.3).restart();
      d.fx = d.x; d.fy = d.y;
    })
    .on('drag',  (ev, d) => { d.fx = ev.x; d.fy = ev.y; })
    .on('end',   (ev, d) => {
      if (!ev.active) sim.alphaTarget(0);
      // keep d.fx / d.fy set — node stays pinned where dropped
    });

  // ── Popover ───────────────────────────────────────────────────────────────
  const pop = document.createElement('div');
  pop.className = 'tt-popover';
  pop.style.display = 'none';
  container.appendChild(pop);

  function hidePopover() { pop.style.display = 'none'; }

  function showPopover(d, event) {
    const e = State.getEntityById(d.id);
    if (!e) return;
    const lv    = e.derived?.independence_risk_level;
    const score = e.derived?.independence_risk_score ?? '—';
    const color = RISK_COLORS[lv] || '#86857c';
    const isExp = expandedIds.has(d.id);
    const canExp = allRels.some(r => {
      if (r.source !== d.id && r.target !== d.id) return false;
      if (!relMatchesLens(r, lenses)) return false;
      const other = r.source === d.id ? r.target : r.source;
      return entityById[other] && !nodeSet.has(other);
    });

    pop.innerHTML = `
      <button class="tt-pop-close">×</button>
      <div class="tt-pop-name">${e.name}</div>
      <div class="tt-pop-meta">${(e.type || '').replace(/([A-Z])/g, ' $1').trim()}</div>
      <div class="tt-pop-ir" style="color:${color}">
        ${lv ? `<b>${lv.toUpperCase()}</b> · ${score}` : 'Score not computed'}
      </div>
      <div class="tt-pop-actions">
        ${(canExp || isExp) ? `<button class="tt-pop-expand">${isExp ? '− Collapse' : '+ Expand neighbors'}</button>` : ''}
        <button class="tt-pop-open" data-entity-id="${d.id}">Open full profile →</button>
      </div>`;

    const cRect = container.getBoundingClientRect();
    const px = Math.min(event.clientX - cRect.left + 14, W - 220);
    const py = Math.max(6, event.clientY - cRect.top - 16);
    pop.style.cssText = `display:block;left:${px}px;top:${py}px`;

    pop.querySelector('.tt-pop-close').onclick  = e2 => { e2.stopPropagation(); hidePopover(); };
    pop.querySelector('.tt-pop-open').onclick   = e2 => { e2.stopPropagation(); hidePopover(); State.emit('navigateToDetail', d.id); };
    pop.querySelector('.tt-pop-expand')?.addEventListener('click', e2 => {
      e2.stopPropagation(); hidePopover();
      isExp ? collapseNode(d.id) : expandNode(d.id);
    });
  }

  // ── Expand / collapse ─────────────────────────────────────────────────────
  function expandNode(nodeId) {
    const addedIds = new Set();
    const newLinks = [];
    allRels.forEach(r => {
      if (r.source !== nodeId && r.target !== nodeId) return;
      if (!relMatchesLens(r, lenses)) return;
      const otherId = r.source === nodeId ? r.target : r.source;
      if (!entityById[otherId]) return;
      if (!nodeSet.has(otherId)) {
        const src = nById.get(nodeId);
        const nn = { id: otherId, entity: entityById[otherId], isFocus: false,
                     x: src.x + (Math.random() - 0.5) * 80,
                     y: src.y + (Math.random() - 0.5) * 80 };
        mNodes.push(nn); nById.set(otherId, nn);
        nodeSet.add(otherId); addedIds.add(otherId);
      }
      const key = `${r.source}\x00${r.target}\x00${r.relationship_category}`;
      if (!linkKeySet.has(key)) {
        linkKeySet.add(key);
        newLinks.push({ source: nById.get(r.source), target: nById.get(r.target),
                        category: r.relationship_category,
                        type: r.relationship_type || r.relationship_category, _key: key });
      }
    });
    mLinks = [...mLinks, ...newLinks];
    expandedIds.add(nodeId);
    expandedChildren.set(nodeId, addedIds);
    if (!expandOrder.includes(nodeId)) expandOrder.push(nodeId);
    _graphState = { entityId, expandOrder: [...expandOrder] };
    updateGraph();
  }

  function collapseNode(nodeId) {
    const added = expandedChildren.get(nodeId) || new Set();
    const remove = new Set();
    added.forEach(id => {
      // keep if connected to any node other than nodeId
      const hasOther = mLinks.some(l => {
        if (l.source.id !== id && l.target.id !== id) return false;
        const other = l.source.id === id ? l.target.id : l.source.id;
        return other !== nodeId;
      });
      if (!hasOther) remove.add(id);
    });
    mNodes = mNodes.filter(n => !remove.has(n.id));
    mLinks = mLinks.filter(l => !remove.has(l.source.id) && !remove.has(l.target.id));
    // also remove the direct links from nodeId to added nodes still present but now hidden
    mLinks = mLinks.filter(l => {
      if (l.source.id !== nodeId && l.target.id !== nodeId) return true;
      const other = l.source.id === nodeId ? l.target.id : l.source.id;
      return initNeighborIds.has(other) || other === entityId;
    });
    remove.forEach(id => { nodeSet.delete(id); nById.delete(id); });
    expandedIds.delete(nodeId);
    expandedChildren.delete(nodeId);
    const idx = expandOrder.indexOf(nodeId);
    if (idx !== -1) expandOrder.splice(idx, 1);
    _graphState = { entityId, expandOrder: [...expandOrder] };
    updateGraph();
  }

  // ── Helpers ───────────────────────────────────────────────────────────────
  function edgeD(s, t) {
    const tR = t.isFocus ? 22 : 14, sR = s.isFocus ? 22 : 14;
    const dx = t.x - s.x, dy = t.y - s.y, dist = Math.hypot(dx, dy) || 1;
    const sx = s.x + dx / dist * (sR + 2), sy = s.y + dy / dist * (sR + 2);
    const ex = t.x - dx / dist * (tR + 9), ey = t.y - dy / dist * (tR + 9);
    const ox = (ey - sy) * 0.14, oy = -(ex - sx) * 0.14;
    return `M${sx},${sy} Q${(sx+ex)/2+ox},${(sy+ey)/2+oy} ${ex},${ey}`;
  }

  function labelPos(d) {
    const mx = (d.source.x + d.target.x) / 2, my = (d.source.y + d.target.y) / 2;
    let angle = Math.atan2(d.target.y - d.source.y, d.target.x - d.source.x) * 180 / Math.PI;
    if (angle > 90 || angle < -90) angle += 180;
    return { mx, my: my - 6, angle };
  }

  function highlight(d, on) {
    if (!on) {
      gNodes.selectAll('g.nb-node').style('opacity', 1);
      gLinks.selectAll('path.nb-edge').style('opacity', 0.72);
      gLabels.selectAll('text.nb-elbl').style('opacity', 1);
      return;
    }
    const rel = new Set([d.id]);
    mLinks.forEach(l => { if (l.source.id === d.id || l.target.id === d.id) { rel.add(l.source.id); rel.add(l.target.id); } });
    gNodes.selectAll('g.nb-node').style('opacity', n => rel.has(n.id) ? 1 : 0.13);
    gLinks.selectAll('path.nb-edge').style('opacity', l => rel.has(l.source.id) && rel.has(l.target.id) ? 0.88 : 0.04);
    gLabels.selectAll('text.nb-elbl').style('opacity', l => rel.has(l.source.id) && rel.has(l.target.id) ? 1 : 0.04);
  }

  // ── Render update (called on init and after expand/collapse) ──────────────
  let edgeSel, lblSel, nodeGSel;
  let _pendingFit = true;

  function updateGraph() {
    edgeSel = gLinks.selectAll('path.nb-edge')
      .data(mLinks, d => d._key)
      .join(
        e => e.append('path').attr('class', 'nb-edge').attr('fill', 'none')
              .attr('stroke-width', 1.8).attr('stroke-opacity', 0.72)
              .attr('stroke', d => REL_COLORS[d.category] || '#94a3b8')
              .attr('marker-end', d => `url(#arr-${d.category.replace(/\W/g, '_')})`),
        u => u,
        x => x.remove()
      );

    lblSel = gLabels.selectAll('text.nb-elbl')
      .data(mLinks, d => d._key)
      .join(
        e => e.append('text').attr('class', 'nb-elbl')
              .attr('text-anchor', 'middle').attr('dominant-baseline', 'central')
              .attr('font-size', 9).attr('pointer-events', 'none')
              .attr('fill', d => REL_COLORS[d.category] || '#94a3b8')
              .style('paint-order', 'stroke').style('stroke', '#fff')
              .style('stroke-width', '3px').style('stroke-linejoin', 'round')
              .text(d => d.type),
        u => u,
        x => x.remove()
      );

    nodeGSel = gNodes.selectAll('g.nb-node')
      .data(mNodes, d => d.id)
      .join(
        e => {
          const g = e.append('g').attr('class', 'nb-node')
            .style('cursor', d => d.isFocus ? 'default' : 'pointer');

          g.each(function(d) {
            const r = d.isFocus ? 20 : 12;
            const lv = d.entity?.derived?.independence_risk_level;
            const rc = RISK_COLORS[lv] || '#86857c';
            d3.select(this).append('circle').attr('r', r)
              .attr('fill', d.isFocus ? rc : '#fff')
              .attr('stroke', rc).attr('stroke-width', d.isFocus ? 0 : 2);
          });

          g.each(function(d) {
            const r = d.isFocus ? 20 : 12;
            const name = d.entity?.name || d.id, abbr = d.entity?.abbreviation;
            const l1 = abbr || (name.length > 22 ? name.slice(0,20)+'…' : name);
            const l2 = abbr ? (name.length > 28 ? name.slice(0,26)+'…' : name) : null;
            const t = d3.select(this).append('text').attr('text-anchor', 'middle')
              .attr('font-size', d.isFocus ? 10 : 9).attr('font-weight', d.isFocus ? 700 : 400)
              .attr('fill', '#33332e').style('paint-order','stroke')
              .style('stroke','#fbfbf8').style('stroke-width','2.5px').style('stroke-linejoin','round');
            t.append('tspan').attr('x', 0).attr('dy', r + 13).text(l1);
            if (l2) t.append('tspan').attr('x', 0).attr('dy', 11).text(l2);
          });

          g.filter(d => !d.isFocus).call(drag);
          g.on('mouseover', (ev, d) => highlight(d, true))
           .on('mouseout',  () => highlight(null, false))
           .on('click', (ev, d) => { if (!d.isFocus) { ev.stopPropagation(); showPopover(d, ev); } });
          return g;
        },
        u => u,
        x => x.remove()
      );

    // Visual indicator: dashed ring on expanded nodes
    nodeGSel.select('circle')
      .attr('stroke-dasharray', d => expandedIds.has(d.id) ? '5 3' : null);

    sim.nodes(mNodes);
    sim.force('link').links(mLinks);
    sim.alpha(0.35).restart();
    _pendingFit = true;
  }

  // ── Zoom-to-fit ────────────────────────────────────────────────────────────
  function zoomToFit(animate = true) {
    if (!mNodes.length) return;
    const pad = 40;
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const n of mNodes) {
      if (n.x < minX) minX = n.x;
      if (n.y < minY) minY = n.y;
      if (n.x > maxX) maxX = n.x;
      if (n.y > maxY) maxY = n.y;
    }
    const bboxW = (maxX - minX) + pad * 2;
    const bboxH = (maxY - minY) + pad * 2;
    const scale = Math.min(W / bboxW, H / bboxH, 1);
    const tx = W / 2 - ((minX + maxX) / 2) * scale;
    const ty = H / 2 - ((minY + maxY) / 2) * scale;
    const t = d3.zoomIdentity.translate(tx, ty).scale(scale);
    const sel = animate ? svg.transition().duration(400) : svg;
    sel.call(zoom.transform, t);
  }

  // ── Tick: update positions ────────────────────────────────────────────────
  sim.on('tick', () => {
    if (edgeSel) edgeSel.attr('d', d => edgeD(d.source, d.target));
    if (lblSel) lblSel.each(function(d) {
      const { mx, my, angle } = labelPos(d);
      d3.select(this).attr('x', mx).attr('y', my)
        .attr('transform', `rotate(${angle},${mx},${my})`);
    });
    if (nodeGSel) nodeGSel.attr('transform', d => `translate(${d.x},${d.y})`);

    // Fit once per (re)layout, after the simulation has roughly settled.
    if (_pendingFit && sim.alpha() < 0.08) {
      _pendingFit = false;
      zoomToFit(true);
    }
  });

  // ── Initial render ─────────────────────────────────────────────────────────
  updateGraph();

  // Reset button — clears drag pins, refits to current layout.
  const resetBtn = document.createElement('button');
  resetBtn.textContent = '⌂'; resetBtn.className = 'nb-reset-btn'; resetBtn.title = 'Reset view';
  resetBtn.onclick = () => {
    mNodes.forEach(n => { if (!n.isFocus) { n.fx = null; n.fy = null; } });
    sim.alpha(0.4).restart();
    _pendingFit = true;
  };
  container.appendChild(resetBtn);
}

// ── XLSX export ───────────────────────────────────────────────────────────────
// Multi-sheet workbook: each concern (identity, scores, factors, appointment, …)
// becomes its own sheet. SheetJS is lazy-loaded from a CDN on first click so it
// doesn't impact initial page load.

const SHEETJS_CDN = 'https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js';

function loadSheetJS() {
  if (window.XLSX) return Promise.resolve(window.XLSX);
  if (window._sheetjsLoading) return window._sheetjsLoading;
  window._sheetjsLoading = new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = SHEETJS_CDN;
    s.async = true;
    s.onload = () => resolve(window.XLSX);
    s.onerror = () => reject(new Error('Failed to load XLSX library'));
    document.head.appendChild(s);
  });
  return window._sheetjsLoading;
}

// Sheet names: ≤31 chars, none of  : \ / ? * [ ]
function safeSheetName(name) {
  return name.replace(/[:\\/?*[\]]/g, ' ').slice(0, 31);
}

function buildEntityWorkbookSheets(entity) {
  const d = entity.derived || {};
  const det = entity._detail || {};
  const sheets = []; // [{ name, aoa: [[...rows]] }]

  // ── Identity ──
  sheets.push({
    name: 'Identity',
    aoa: [
      ['Field', 'Value'],
      ['id', entity.id],
      ['name', entity.name],
      ['abbreviation', entity.abbreviation || ''],
      ['type', entity.type],
      ['cluster', entity.cluster],
      ['level_of_government', entity.level_of_government],
      ['created_year', entity.created_year ?? ''],
      ['abolished_year', entity.abolished_year ?? ''],
      ['operational_status', entity.operational_status],
      ['constitutional_basis', entity.constitutional_basis || ''],
      ['statutory_basis', entity.statutory_basis || ''],
      ['data_quality', entity.data_quality],
    ],
  });

  const js = det.jurisdiction_scope || entity.jurisdiction_scope;
  if (js && typeof js === 'object') {
    const rows = [
      ['is_all_india', js.is_all_india ?? ''],
      ['states_covered', Array.isArray(js.states_covered) ? js.states_covered.join(', ') : ''],
      ['uts_covered', Array.isArray(js.uts_covered) ? js.uts_covered.join(', ') : ''],
      ['is_shared_multi', js.is_shared_multi ?? ''],
      ['shared_appointer', js.shared_appointer || ''],
      ['jurisdiction_types', Array.isArray(js.jurisdiction_types) ? js.jurisdiction_types.join(', ') : ''],
    ].filter(([, v]) => v !== '' && v !== undefined && v !== null);
    if (rows.length) sheets.push({ name: 'Jurisdiction', aoa: [['Field', 'Value'], ...rows] });
  }

  // ── Scores ──
  if (shouldShowStructuralScores(entity)) {
    sheets.push({
      name: 'Scores',
      aoa: [
        ['Score', 'Value', 'Level'],
        ['Structural Health', d.structural_health_score ?? '', d.structural_health_level || ''],
        ['Independence Risk', d.independence_risk_score ?? '', d.independence_risk_level || ''],
        ['Discretionary Power', d.discretionary_power_score ?? '', ''],
        ['scores_validated', d.scores_validated ?? '', ''],
      ],
    });
  }

  // ── Health contributions ──
  if (shouldShowStructuralScores(entity)) {
    const hBd = d.structural_health_breakdown;
    if (hBd && Object.keys(hBd).length) {
      sheets.push({
        name: 'Health Contributions',
        aoa: [
          ['Contribution', 'Risk weight (subtracted from 1.0)'],
          ...Object.entries(hBd).map(([k, v]) => [k, typeof v === 'number' ? +v.toFixed(3) : v]),
        ],
      });
    }

    const irBd = d.independence_risk_breakdown;
    if (irBd && Object.keys(irBd).length) {
      sheets.push({
        name: 'IR Factors',
        aoa: [
          ['Factor', 'Points'],
          ...Object.entries(irBd).sort((a, b) => b[1] - a[1]),
        ],
      });
    }

    const dpBd = d.discretionary_power_breakdown;
    if (dpBd && Object.keys(dpBd).length) {
      sheets.push({
        name: 'DP Factors',
        aoa: [
          ['Factor', 'Points'],
          ...Object.entries(dpBd).sort((a, b) => b[1] - a[1]),
        ],
      });
    }
  }

  // ── Appointment ──
  if (det.appointment) {
    const a = det.appointment;
    const rows = [
      ['nominates', a.nominates || ''],
      ['recommends', a.recommends || ''],
      ['consulted', Array.isArray(a.consulted) ? a.consulted.join('; ') : (a.consulted || '')],
      ['consultation_binding', a.consultation_binding ?? ''],
      ['formally_appoints', a.formally_appoints || ''],
      ['criteria_public', a.criteria_public ?? ''],
      ['tenure', a.tenure || ''],
      ['reappointment_possible', a.reappointment_possible ?? ''],
      ['removal_authority', a.removal_authority || ''],
      ['removal_requires_parliament', a.removal_requires_parliament ?? ''],
    ].filter(([, v]) => v !== '' && v !== undefined && v !== null);
    if (rows.length) sheets.push({ name: 'Appointment', aoa: [['Field', 'Value'], ...rows] });
  }

  // ── Funding ──
  if (det.funding) {
    const f = det.funding;
    const rows = [
      ['primary_source', f.primary_source || ''],
      ['ministry_responsible', f.ministry_responsible || ''],
      ['state_contribution_percent', f.state_contribution_percent ?? ''],
      ['budget_figure_crore', f.budget_figure_crore ?? ''],
      ['budget_year', f.budget_year ?? ''],
    ].filter(([, v]) => v !== '' && v !== undefined && v !== null);
    if (rows.length) sheets.push({ name: 'Funding', aoa: [['Field', 'Value'], ...rows] });
  }

  // ── Audit ──
  if (det.audit) {
    const au = det.audit;
    const rows = [
      ['audited_by', au.audited_by || ''],
      ['audit_type', au.audit_type || ''],
      ['audit_report_public', au.audit_report_public ?? ''],
      ['conduct_oversight_body', au.conduct_oversight_body || ''],
    ].filter(([, v]) => v !== '' && v !== undefined && v !== null);
    if (rows.length) sheets.push({ name: 'Audit', aoa: [['Field', 'Value'], ...rows] });
  }

  // ── Complaint mechanism ──
  if (det.complaint_mechanism) {
    const c = det.complaint_mechanism;
    const complaintRows = (c.bias_complaint_to || []).map((b, i) => [
      i + 1,
      b.body || '',
      b.mechanism || '',
      b.external_to_judiciary ?? '',
      b.is_public_process ?? '',
      b.complainant_has_locus ?? '',
      b.timeframe_defined ?? '',
    ]);
    if (complaintRows.length) {
      sheets.push({
        name: 'Complaint — Bias',
        aoa: [
          ['#', 'Body', 'Mechanism', 'External', 'Public process', 'Locus', 'Timeframe defined'],
          ...complaintRows,
        ],
      });
    }
    const otherRows = [];
    if (c.criminal_prosecution) {
      const cp = c.criminal_prosecution;
      otherRows.push(['criminal_prosecution.requires_sanction_from', cp.requires_sanction_from || '']);
      otherRows.push(['criminal_prosecution.consultation_required_with', cp.consultation_required_with || '']);
      otherRows.push(['criminal_prosecution.consultation_binding', cp.consultation_binding ?? '']);
    }
    if (c.lokpal_jurisdiction) {
      otherRows.push(['lokpal_jurisdiction', c.lokpal_jurisdiction]);
      if (c.lokpal_jurisdiction_note) otherRows.push(['lokpal_jurisdiction_note', c.lokpal_jurisdiction_note]);
    }
    if (otherRows.length) {
      sheets.push({ name: 'Complaint — Other', aoa: [['Field', 'Value'], ...otherRows] });
    }
  }

  // ── Case volume ──
  if (det.case_volume && typeof det.case_volume === 'object') {
    const cv = det.case_volume;
    const rows = [
      ['data_as_of', cv.data_as_of || ''],
      ['pending_cases', cv.pending_cases ?? ''],
      ['filed_last_year', cv.filed_last_year ?? ''],
      ['disposed_last_year', cv.disposed_last_year ?? ''],
      ['disposal_rate', cv.disposal_rate ?? ''],
      ['avg_disposal_days', cv.avg_disposal_days ?? ''],
      ['clog_severity', cv.clog_severity || ''],
      ['source_type', cv.source_type || ''],
      ['source_url', cv.source_url || ''],
    ].filter(([, v]) => v !== '' && v !== undefined && v !== null);
    if (rows.length) sheets.push({ name: 'Case Volume', aoa: [['Field', 'Value'], ...rows] });
  }

  // ── Judge strength ──
  if (det.judge_strength && typeof det.judge_strength === 'object') {
    const rows = Object.entries(det.judge_strength)
      .filter(([, v]) => v !== '' && v !== undefined && v !== null);
    if (rows.length) sheets.push({ name: 'Judge Strength', aoa: [['Field', 'Value'], ...rows] });
  }

  // ── Sources ──
  if (entity.sources && entity.sources.length) {
    const rows = entity.sources.map((s, i) => [
      i + 1,
      s.title || s.label || '',
      s.url || (typeof s === 'string' ? s : ''),
    ]);
    sheets.push({ name: 'Sources', aoa: [['#', 'Title', 'URL'], ...rows] });
  }

  // ── README / metadata first sheet ──
  const meta = [
    ['JEM — Structural Report'],
    ['Entity', entity.name],
    ['ID', entity.id],
    ['Generated', new Date().toISOString()],
    [],
    ['Sheets in this workbook:'],
    ...sheets.map(s => ['', s.name]),
  ];
  sheets.unshift({ name: 'README', aoa: meta });

  return sheets;
}

function applyColumnWidths(ws) {
  const ref = ws['!ref'];
  if (!ref || !window.XLSX) return;
  const range = window.XLSX.utils.decode_range(ref);
  const widths = [];
  for (let C = range.s.c; C <= range.e.c; C++) {
    let max = 10;
    for (let R = range.s.r; R <= range.e.r; R++) {
      const cell = ws[window.XLSX.utils.encode_cell({ r: R, c: C })];
      if (!cell || cell.v == null) continue;
      const len = String(cell.v).length;
      if (len > max) max = len;
    }
    widths.push({ wch: Math.min(max + 2, 60) });
  }
  ws['!cols'] = widths;
}

async function downloadEntityXLSX(entity) {
  let XLSX;
  try {
    XLSX = await loadSheetJS();
  } catch (err) {
    console.error(err);
    alert('Could not load spreadsheet library. Check your internet connection.');
    return;
  }
  const wb = XLSX.utils.book_new();
  const sheets = buildEntityWorkbookSheets(entity);
  for (const s of sheets) {
    const ws = XLSX.utils.aoa_to_sheet(s.aoa);
    applyColumnWidths(ws);
    XLSX.utils.book_append_sheet(wb, ws, safeSheetName(s.name));
  }
  const filename = `${(entity.id || 'entity').replace(/[^a-z0-9_-]+/gi, '_')}.xlsx`;
  XLSX.writeFile(wb, filename);
}

// ── Main render ───────────────────────────────────────────────────────────────

export function renderDetailView(entityId, fromEntityId = null) {
  const entity = State.getEntityById(entityId);
  if (!entity) return;

  // Push history
  if (fromEntityId && fromEntityId !== entityId) {
    _historyStack = [fromEntityId];
  }
  _currentEntityId = entityId;
  _nbLenses = new Set(DEFAULT_LENSES);

  const container = document.getElementById('detail-view');
  if (!container) return;

  const derived = entity.derived || {};
  const detail = entity._detail || {};
  const level = derived.independence_risk_level;
  const score = derived.independence_risk_score;
  const dpScore = derived.discretionary_power_score;
  const healthScore = derived.structural_health_score;
  const healthLevel = derived.structural_health_level || State.structuralHealthBand?.(healthScore);
  const healthColors = State.getStructuralHealthColors?.() || {};
  const healthColor = healthLevel ? (healthColors[healthLevel] || '#888') : '#888';
  const showScores = shouldShowStructuralScores(entity);
  const isNotValidated = derived.scores_validated === false;

  const prevEntityId = _historyStack[_historyStack.length - 1];
  const prevEntity = prevEntityId ? State.getEntityById(prevEntityId) : null;

  const backLabel = prevEntity ? `← ${prevEntity.name}` : '← Back to overview';

  const lensToggleBtns = GRAPH_LENSES
    .map(l => `<button class="nb-lens-btn${_nbLenses.has(l) ? ' active' : ''}" data-lens="${l}" style="--lens-color:${REL_COLORS[l]}">${REL_LABELS[l]}</button>`)
    .join('');

  const healthPct = healthScore != null ? Math.max(0, Math.min(100, healthScore * 100)) : 0;
  const healthLabel = healthLevel ? HEALTH_LEVEL_LABELS[healthLevel] || healthLevel : null;

  const profileSections = getProfileSections(entity);
  const { left: leftSections, right: rightSections } = balanceProfileColumns(profileSections);
  const leftProfileHTML  = leftSections.map(renderProfileWidget).join('');
  const rightProfileHTML = rightSections.map(renderProfileWidget).join('');

  container.innerHTML = `
    <div class="dv-inner">
      ${printBrandBlock()}
      <div class="dv-nav">
        <button class="dv-back-btn" id="dv-back">${backLabel}</button>
        <span class="dv-breadcrumb">${CLUSTER_LABELS[entity.cluster] || entity.cluster || ''}</span>
        <div class="dv-actions-top">
          <button class="dv-action-btn dv-copy-link" id="dv-copy-link" title="Copy shareable link to this entity profile">
            <svg class="dv-link-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M10 13a5 5 0 0 0 7.07 0l3-3a5 5 0 0 0-7.07-7.07l-1.5 1.5"/>
              <path d="M14 11a5 5 0 0 0-7.07 0l-3 3a5 5 0 0 0 7.07 7.07l1.5-1.5"/>
            </svg>
            <span class="dv-action-label">Share</span>
          </button>
          <button class="dv-action-btn dv-export-xlsx" id="dv-export-xlsx" title="Download per-entity raw data as multi-sheet Excel file">↓ XLSX</button>
          <button class="dv-action-btn dv-export-pdf" id="dv-export-pdf" title="Print / save as PDF">↓ Export PDF</button>
        </div>
      </div>

      <div class="dv-mobile-sticky-wrap">
        <div class="dv-mobile-identity">
          <h1 class="dv-name dv-name-mobile">${entity.name}</h1>
          ${statusPill(entity)}
          ${showScores ? `
            <div class="dv-mobile-health" style="--h-color:${healthColor}">
              <div class="dv-mobile-health-num">${healthScore != null ? healthScore.toFixed(2) : '—'}</div>
              <div class="dv-mobile-health-meta">
                <div class="dv-mobile-health-label">Structural health ${scoreTip('structural_health')}</div>
                ${healthLabel ? `<div class="dv-mobile-health-band">${healthLabel.toUpperCase()}</div>` : ''}
              </div>
            </div>
          ` : ''}
        </div>

        <nav class="dv-tab-strip" role="tablist" aria-label="Entity profile sections">
          <button type="button" class="dv-tab-btn active" role="tab" data-dv-tab="activity" aria-selected="true">Activity</button>
          <button type="button" class="dv-tab-btn" role="tab" data-dv-tab="setup" aria-selected="false">Profile</button>
          <button type="button" class="dv-tab-btn" role="tab" data-dv-tab="network" aria-selected="false">Relationships</button>
          ${showScores ? '<button type="button" class="dv-tab-btn" role="tab" data-dv-tab="score" aria-selected="false">Score</button>' : ''}
        </nav>
      </div>

      <div class="dv-tab-network">${renderAppellateChainStrip(entity)}</div>

      <div class="dv-layout">

        <!-- Left: scores, gaps -->
        <div class="dv-left">
          <div class="dv-header dv-tab-score">
            <h1 class="dv-name">${entity.name}</h1>
            ${statusPill(entity)}
          </div>
          <div class="dv-meta dv-tab-score">
            ${entity.abbreviation ? `<span class="dv-abbr">${entity.abbreviation}</span>` : ''}
            <span class="dv-cluster">${CLUSTER_LABELS[entity.cluster] || entity.cluster || ''}</span>
            ${entity.created_year ? `<span class="dv-year">Est. ${entity.created_year}</span>` : ''}
          </div>

          ${!showScores ? `
            <div class="dv-no-score dv-tab-score">${structuralScoresHiddenMessage(entity)}</div>
          ` : `
            <!-- 1. Summary score card (sticky, not collapsible) -->
            <div class="summary-score-card dv-tab-score" style="--h-color:${healthColor}">
              <div class="health-hero-top">
                <div class="health-hero-num">${healthScore != null ? healthScore.toFixed(2) : '—'}</div>
                <div class="health-hero-meta">
                  <div class="health-hero-label">STRUCTURAL HEALTH INDICATOR ${scoreTip('structural_health')}</div>
                  ${healthLabel ? `<div class="health-hero-band">${healthLabel.toUpperCase()}</div>` : ''}
                </div>
              </div>
              <div class="health-hero-bar"><div class="health-hero-fill" style="width:${healthPct}%"></div></div>
              <div class="health-hero-explain">${HEALTH_EXPLAIN[healthLevel] || 'Composite of independence risk and discretionary power.'}</div>
              ${isNotValidated ? '<div class="ir-pending">⚐ Scores pending community review</div>' : ''}
            </div>

            ${(score != null || dpScore != null) ? `
              <!-- 2. Constituent score breakdown (open by default) -->
              <details class="dv-section dv-section-constituents dv-tab-score" open>
                <summary>Constituent score breakdown</summary>
                <div class="dv-section-body">
                  ${score != null ? `
                    <div class="constituent-block">
                      <div class="constituent-head">
                        <span class="constituent-name">Independence Risk ${scoreTip('independence_risk')}</span>
                        <span class="constituent-score" style="color:${RISK_COLORS[level] || '#888'}">${score} · ${(level || '').toUpperCase()}</span>
                      </div>
                      <div class="constituent-bar"><div class="constituent-fill" style="width:${Math.min(100, (score / 15) * 100)}%;background:${RISK_COLORS[level] || '#888'}"></div></div>
                      <div class="constituent-explain">${RISK_EXPLAIN[level] || ''}</div>
                      <details class="constituent-bd">
                        <summary>Factor breakdown</summary>
                        ${renderBreakdown(derived.independence_risk_breakdown, 'Independence risk', 15)}
                      </details>
                    </div>
                  ` : ''}
                  ${dpScore != null ? `
                    <div class="constituent-block">
                      <div class="constituent-head">
                        <span class="constituent-name">Discretionary Power ${scoreTip('discretionary_power')}</span>
                        <span class="constituent-score" style="color:#6366f1">${dpScore}</span>
                      </div>
                      <div class="constituent-bar"><div class="constituent-fill" style="width:${Math.min(100, (dpScore / 20) * 100)}%;background:#6366f1"></div></div>
                      <details class="constituent-bd">
                        <summary>Factor breakdown</summary>
                        ${renderBreakdown(derived.discretionary_power_breakdown, 'Discretionary power', 15)}
                      </details>
                    </div>
                  ` : ''}
                </div>
              </details>
            ` : ''}
          `}

          <!-- Themed profile widgets (governance / structural setup) -->
          ${leftProfileHTML}
        </div>

        <!-- Right: neighborhood graph -->
        <div class="dv-right">
          <div class="nb-section-head dv-tab-network">
            <span class="nb-section-title">Neighborhood</span>
            <div class="nb-lens-group" id="nb-lens-group" role="group" aria-label="Relationship lens filters">
              ${lensToggleBtns}
            </div>
          </div>
          <div class="nb-graph-wrap dv-tab-network" id="nb-graph-wrap"></div>
          <p class="nb-hint dv-tab-network">● filled = focus &nbsp;○ ring = neighbor · hover to highlight · click neighbor to open</p>

          ${renderCaseVolume(detail.case_volume) ? `
            <details class="dv-section dv-tab-activity" open>
              <summary>
                <span>Case volume &amp; clog ${scoreTip('clog_severity')}</span>
                <span class="dv-section-summary-stats">${renderCaseVolumeSummary(detail.case_volume)}</span>
              </summary>
              <div class="dv-section-body">${renderCaseVolume(detail.case_volume)}</div>
            </details>
          ` : ''}

          <!-- Themed profile widgets (evidence / accountability) -->
          ${rightProfileHTML}
        </div>

      </div>

      <div class="dv-tab-activity">${commentsHTML('entity:' + entity.id, { title: 'Comments' })}</div>
    </div>
  `;

  wireComments(container);

  // Any .detail-connection-row inside a themed widget should navigate.
  container.querySelector('.dv-layout')?.addEventListener('click', ev => {
    const lnk = ev.target.closest('.detail-connection-row');
    if (!lnk) return;
    ev.preventDefault();
    const id = lnk.getAttribute('data-entity-id');
    if (id) State.emit('navigateToDetail', id);
  });

  // ── Mobile tab strip (≤900px only, hidden on desktop via CSS) ──────────────
  // Default active tab is "score". When the Network tab is activated for the
  // first time the neighborhood graph must be re-measured because it was
  // initially painted while hidden (display: none → zero size).
  container.setAttribute('data-dv-tab', 'activity');
  let _nbDrawnAtSize = '';
  container.querySelector('.dv-tab-strip')?.addEventListener('click', ev => {
    const btn = ev.target.closest('.dv-tab-btn');
    if (!btn) return;
    const tab = btn.getAttribute('data-dv-tab');
    if (!tab) return;
    container.setAttribute('data-dv-tab', tab);
    container.querySelectorAll('.dv-tab-btn').forEach(b => {
      const isActive = b === btn;
      b.classList.toggle('active', isActive);
      b.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });
    if (tab === 'network') {
      const wrap = container.querySelector('#nb-graph-wrap');
      const size = wrap ? `${wrap.clientWidth}x${wrap.clientHeight}` : '';
      if (size && size !== _nbDrawnAtSize) {
        _redrawNeighborhood(container);
        _nbDrawnAtSize = size;
      }
    }
    // Scroll the body to the top so the user lands at the start of the tab.
    const dv = document.getElementById('detail-view');
    if (dv) dv.scrollTop = 0;
  });

  // ── Wire back button ────────────────────────────────────────────────────────
  container.querySelector('#dv-back')?.addEventListener('click', () => {
    if (prevEntityId) {
      _historyStack.pop();
      State.emit('navigateToDetail', prevEntityId);
    } else {
      State.emit('navigateToSummary', null);
    }
  });

  // ── Wire XLSX export ────────────────────────────────────────────────────────
  container.querySelector('#dv-export-xlsx')?.addEventListener('click', () => {
    downloadEntityXLSX(entity);
  });

  // ── Wire "Where this fits" chips → navigate to that entity ─────────────────
  container.querySelector('.wtf-card')?.addEventListener('click', (ev) => {
    const btn = ev.target.closest('.wtf-node');
    if (!btn) return;
    const id = btn.dataset.entityId;
    if (id && id !== entity.id) State.emit('navigateToDetail', id);
  });

  // ── Wire Copy-link ─────────────────────────────────────────────────────────
  // Builds a fresh URL from window.location so it works regardless of how the
  // user arrived (deep-link, search, navigation history).
  container.querySelector('#dv-copy-link')?.addEventListener('click', async (ev) => {
    const btn = ev.currentTarget;
    const labelEl = btn.querySelector('.dv-action-label');
    const shareUrl = `${location.origin}${location.pathname}${location.search}#/entity/${encodeURIComponent(entity.id)}`;
    const flash = (label, cls) => {
      const prev = labelEl ? labelEl.textContent : btn.textContent;
      if (labelEl) labelEl.textContent = label; else btn.textContent = label;
      btn.classList.add(cls);
      setTimeout(() => {
        if (labelEl) labelEl.textContent = prev; else btn.textContent = prev;
        btn.classList.remove(cls);
      }, 1500);
    };
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(shareUrl);
      } else {
        // Fallback for non-secure contexts (file://, http://) where Clipboard API is gated.
        const ta = document.createElement('textarea');
        ta.value = shareUrl;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        ta.remove();
      }
      flash('Copied ✓', 'dv-copy-ok');
    } catch (err) {
      console.error('Copy link failed:', err);
      flash('Copy failed', 'dv-copy-err');
    }
  });

  // ── Wire lens toggles ───────────────────────────────────────────────────────
  container.querySelector('#nb-lens-group')?.addEventListener('click', e => {
    const btn = e.target.closest('.nb-lens-btn');
    if (!btn) return;
    const lens = btn.dataset.lens;
    if (_nbLenses.has(lens)) _nbLenses.delete(lens);
    else _nbLenses.add(lens);
    btn.classList.toggle('active', _nbLenses.has(lens));
    _redrawNeighborhood(container);
  });

  // ── Wire PDF export ─────────────────────────────────────────────────────────
  container.querySelector('#dv-export-pdf')?.addEventListener('click', () => {
    const detailView = document.getElementById('detail-view');
    const reopened = [];
    // Expand profile sections only — not score ? tooltips (details.score-tip).
    detailView?.querySelectorAll('details.dv-section, details.constituent-bd').forEach((el) => {
      if (!el.open) reopened.push(el);
      el.setAttribute('open', '');
    });
    detailView?.querySelectorAll('details.score-tip[open]').forEach((el) => {
      el.removeAttribute('open');
    });

    document.body.classList.add('jem-print-detail');
    const cleanup = () => {
      document.body.classList.remove('jem-print-detail');
      reopened.forEach((el) => el.removeAttribute('open'));
      window.removeEventListener('afterprint', cleanup);
      window.removeEventListener('beforeprint', ensurePrintClass);
    };
    const ensurePrintClass = () => document.body.classList.add('jem-print-detail');
    window.addEventListener('beforeprint', ensurePrintClass);
    window.addEventListener('afterprint', cleanup);
    window.print();
  });

  // ── Initial neighborhood render ─────────────────────────────────────────────
  requestAnimationFrame(() => {
    void _redrawNeighborhood(container);
  });

  // ── Auto-scroll to export action when arrived via "↓ Report" from summary ──
  try {
    if (sessionStorage.getItem('jem.autoExport') === entity.id) {
      sessionStorage.removeItem('jem.autoExport');
      requestAnimationFrame(() => {
        const btn = container.querySelector('#dv-export-pdf');
        if (btn) {
          btn.scrollIntoView({ behavior: 'smooth', block: 'center' });
          btn.classList.add('dv-export-pulse');
          setTimeout(() => btn.classList.remove('dv-export-pulse'), 1800);
        }
      });
    }
  } catch (_) { /* sessionStorage unavailable */ }
}

function _redrawNeighborhood(container) {
  const wrap = container.querySelector('#nb-graph-wrap');
  if (!wrap) return;
  _miniGraphWrap = wrap;
  return renderNeighborhoodGraph(wrap, _currentEntityId, _nbLenses).then(() => {
    // Expand button lives inside the graph wrap (overlaid), added after render clears it
    const expandBtn = document.createElement('button');
    expandBtn.className = 'nb-expand-btn';
    expandBtn.title = 'Fullscreen';
    expandBtn.textContent = '⤢';
    expandBtn.onclick = () => openFullscreenGraph(_currentEntityId, _nbLenses);
    wrap.appendChild(expandBtn);
  });
}

export function clearDetailView() {
  _currentEntityId = null;
  _historyStack = [];
  _graphState = null;
  _miniGraphWrap = null;
  if (_fsOverlay) { _fsOverlay.remove(); _fsOverlay = null; }
  const container = document.getElementById('detail-view');
  if (container) container.innerHTML = '';
}
