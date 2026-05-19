// JEM — Renderer
// Handles all SVG rendering across 4 semantic zoom levels.
// State-driven: re-renders when State emits relevant events.

import { State } from './state.js';
import { openDetailPanel } from './panel.js';
import {
  entityNodeShape,
  nodeShapePathForEntity,
  shapeLayoutRadius,
} from './nodeShapes.js';
import { PRINCIPAL_HC_BY_STATE_CODE } from './districtAggregates.js';

// ── Constants ─────────────────────────────────────────────────────────────────

const NODE_BASE_RADIUS = 22;
const NODE_MIN_RADIUS = 8;
const IR_RING_OFFSET = 6;    // Independence risk ring offset from node edge
const IR_RING_WIDTH = 4;

// ── Selections ────────────────────────────────────────────────────────────────

let svg, root, layerClusters, layerEdges, layerNodes, layerLabels;
let width, height;
/** Virtual drawing extent for org-chart (≥ viewport). Pan/zoom moves within this space. */
let layoutCanvasW = 0;
let layoutCanvasH = 0;
let lastGraphContentBounds = null;
let hoveredNodeId = null;
let simulation = null;
let simNodesById = new Map();
/** Populated during org-chart layout — used for hierarchy-scaled node radii & labels. */
let lastAppellateRanks = new Map();
let lastOrgBandById = new Map();

const FORCE_LAYOUT_MIN_NODES = 40;

/** Org-chart layout for full graph or progressive explorer (avoids build.py 2-row cluster strip). */
function shouldUseOrgChartLayout(entities) {
  if (entities.length >= FORCE_LAYOUT_MIN_NODES) return true;
  if (!State.useProgressiveExplorer || entities.length < 2) return false;
  return true;
}
const CLUSTER_PADDING = 120;
const HIERARCHY_Y_GAP = 90;
const BAND_GAP = 200;
const ORG_NODE_Y_GAP = 42;
/** Minimum center-to-center distance = NODE_SPACING_RADIUS_MULT × largest drawable node radius. */
const NODE_SPACING_RADIUS_MULT = 6.2;
/** Extra vertical budget per row for external labels under circles / rects. */
const ORG_LABEL_VERTICAL_CLEARANCE = 52;
const BAND_VERTICAL_GAP = 110;
/** Clear vertical gap between apex row (SC / President) and the HC cluster below. */
const APEX_TO_HC_GAP_MULT = 3.2;

/** Tier 0 = apex (SC / President); higher tiers = further down the tree / lower bands. */
const HIERARCHY_TIER_BASE_RADIUS = [52, 36, 28, 20, 14];

function hierarchyTierForSizing(d) {
  if (!d) return 4;
  if (!lastOrgBandById.size) return 2;
  const id = d.id || '';
  if (id === 'supreme_court_india' || id === 'president_india') return 0;

  const ar = lastAppellateRanks.get(id);
  if (typeof ar === 'number' && Number.isFinite(ar)) {
    if (ar <= 1) return 1;
    if (ar === 2) return 2;
    if (ar <= 5) return 3;
    return 4;
  }

  const band = lastOrgBandById.get(id);
  if (band === 0) return 0;
  if (d.type === 'HighCourtBench' || (d.type === 'ConstitutionalCourt' && id.startsWith('hc_'))) return 1;
  if (band === 1) return 2;
  if (band === 2) return 3;
  return 4;
}

function drawableNodeRadiusForEntity(d) {
  const tier = Math.min(
    HIERARCHY_TIER_BASE_RADIUS.length - 1,
    Math.max(0, hierarchyTierForSizing(d))
  );
  let base = HIERARCHY_TIER_BASE_RADIUS[tier] ?? NODE_BASE_RADIUS;
  if (State.showDiscretionaryPower) {
    const dp = (d.derived || {}).discretionary_power_score || 1;
    return Math.max(NODE_MIN_RADIUS, Math.min(base * 1.45, base + dp * 1.25));
  }
  return Math.max(NODE_MIN_RADIUS, base);
}

/** Judicial / quasi-judicial vs other institutions — drives colour & category, not shape (see renderNodes). */
function entityVisualKind(e) {
  if (!e) return 'stakeholder';
  const t = e.type;
  const c = e.cluster;
  if (
    t === 'ConstitutionalCourt'
    || t === 'HighCourtBench'
    || t === 'SubordinateCivilCourt'
    || t === 'CityCivilCourt'
    || t === 'SpecialCourt'
  ) {
    return 'court';
  }
  if (
    t === 'RegulatoryBodyQJ'
    || t === 'ADRBody'
    || t === 'ConsumerCommission'
    || c === 'tribunals_adr'
    || c === 'arbitration'
    || c === 'regulatory_bodies'
  ) {
    return 'allied';
  }
  return 'stakeholder';
}

function drawableRectHalfWidth(d) {
  return drawableNodeRadiusForEntity(d) * 1.45;
}

function drawableRectHalfHeight(d) {
  return drawableNodeRadiusForEntity(d) * 0.78;
}

/** Half-length of the diagonal of the node shape — used for spacing / collisions. */
function effectiveNodeLayoutRadius(d) {
  if (entityNodeShape(d) === 'rect') {
    return Math.hypot(drawableRectHalfWidth(d), drawableRectHalfHeight(d));
  }
  return shapeLayoutRadius(d, drawableNodeRadiusForEntity(d));
}

/** Full caption for apex / High Court nodes; abbreviation elsewhere when zoomed out. */
function nodeCaptionText(d, zoomScale) {
  const id = d.id || '';
  const isApex = id === 'president_india' || id === 'supreme_court_india';
  const isPrincipalHc = d.type === 'ConstitutionalCourt' && id.startsWith('hc_');
  const isHcBench = d.type === 'HighCourtBench';
  if (isApex || isPrincipalHc || isHcBench) {
    return d.name || d.abbreviation || id;
  }
  const abbr = d.abbreviation || d.name || id;
  if (zoomScale > 1.05) return d.name || abbr;
  if (zoomScale > 0.72) return abbr;
  return abbr.length > 22 ? `${abbr.slice(0, 20)}…` : abbr;
}

/** Vertical offset from node centre to external caption baseline (org chart). */
function externalLabelYOffset(d, labelFontPx) {
  const bump = labelFontPx > 18 ? 8 : labelFontPx > 14 ? 5 : 0;
  if (entityVisualKind(d) === 'stakeholder') {
    return drawableRectHalfHeight(d) + ORG_LABEL_VERTICAL_CLEARANCE * 0.7 + bump;
  }
  return drawableNodeRadiusForEntity(d) + ORG_LABEL_VERTICAL_CLEARANCE * 0.78 + bump;
}

function maxDrawableNodeRadius(entities) {
  let m = NODE_BASE_RADIUS;
  for (const d of entities) {
    m = Math.max(m, effectiveNodeLayoutRadius(d));
  }
  return m;
}

/** Hot-reload / legacy DOM: stakeholder groups need rect + in-box label children. */
function ensureUpgradedNodeShapes(mergedSelection) {
  const ns = 'http://www.w3.org/2000/svg';
  mergedSelection.each(function (d) {
    const g = d3.select(this);
    g.selectAll('.node-exception-overlay').remove();
    if (entityVisualKind(d) !== 'stakeholder') return;
    if (!g.select('.node-rect').empty()) return;

    const circle = g.select('.node-circle').node();
    const badge = g.select('.node-badge').node();
    if (!circle || !badge) return;

    function insertAfter(ref, tagName, className) {
      const el = document.createElementNS(ns, tagName);
      el.setAttribute('class', className);
      ref.parentNode.insertBefore(el, ref.nextSibling);
      return el;
    }

    if (g.select('.node-ir-ring-rect').empty()) {
      const el = document.createElementNS(ns, 'rect');
      el.setAttribute('class', 'node-ir-ring-rect');
      circle.parentNode.insertBefore(el, circle);
    }

    let ref = g.select('.node-circle').node();
    ref = insertAfter(ref, 'rect', 'node-rect');
    ref = insertAfter(ref, 'circle', 'node-exception-circle');
    ref = insertAfter(ref, 'rect', 'node-exception-rect');
    insertAfter(ref, 'text', 'node-inner-label');
  });
}

export function initRenderer() {
  svg = d3.select('#main-svg');
  root = d3.select('#graph-root');
  layerClusters = d3.select('#layer-clusters');
  layerEdges = d3.select('#layer-edges');
  layerNodes = d3.select('#layer-nodes');
  layerLabels = d3.select('#layer-labels');

  updateDimensions();
  window.addEventListener('resize', () => {
    updateDimensions();
    if (State.graph) {
      setupLayout();
      render();
    }
  });

  // Subscribe to state changes
  State.subscribe('graphLoaded', () => {
    setupLayout();
    render();
  });
  State.subscribe('yearChanged', () => { setupLayout(); render(); });
  State.subscribe('lensChanged', () => { setupLayout(); render(); });
  State.subscribe('viewModeChanged', () => { setupLayout(); render(); });
  State.subscribe('filterChanged', () => { setupLayout(); render(); });
  State.subscribe('collapseChanged', (entityId) => {
    setupLayout();
    render();
    requestAnimationFrame(() => {
      if (
        entityId
        && State.isPrincipalHighCourt(entityId)
        && State.expandedEntityIds?.has(entityId)
      ) {
        fitGraphToEntityFocus(entityId, { duration: 280, margin: 0.9 });
      } else {
        fitGraphToViewport({ duration: 0 });
      }
    });
  });
  State.subscribe('aggregateChanged', () => { setupLayout(); render(); });
  State.subscribe('derivedToggle', () => { setupLayout(); render(); });
  State.subscribe('zoomLevelChanged', () => render());
}

function updateDimensions() {
  const container = document.getElementById('canvas-container');
  width = container.clientWidth;
  height = container.clientHeight;
  svg.attr('width', width).attr('height', height);
  if (!layoutCanvasW || !layoutCanvasH) {
    layoutCanvasW = width;
    layoutCanvasH = height;
  }
}

// ── Main Render ───────────────────────────────────────────────────────────────

export function render() {
  if (!State.graph) return;

  const level = State.zoomLevel;

  if (level === 0) {
    layerClusters.style('display', null);
    layerClusters.selectAll('.hier-box').remove();
    layerEdges.style('display', 'none');
    layerNodes.style('display', 'none');
    layerLabels.style('display', 'none');
    _renderL0();
    return;
  }

  layerClusters.selectAll('.l0-cluster-card').remove();
  layerClusters.selectAll('.hier-box').remove();
  layerClusters.style('display', 'none');

  layerEdges.style('display', null);
  layerNodes.style('display', null);
  layerLabels.style('display', null);

  renderEdges();
  renderNodes();
  renderLabels();
}

function setupLayout() {
  if (!State.graph) return;
  const entities = State.getVisibleEntities();
  const rels = State.getVisibleRelationships();

  // For larger datasets, default to an org-chart (hierarchical) layout:
  // fixed bands + columns, minimal cognitive load.
  const useOrgChart = shouldUseOrgChartLayout(entities);
  if (!useOrgChart) {
    teardownSimulation();
    layoutCanvasW = width;
    layoutCanvasH = height;
    lastGraphContentBounds = null;
    lastAppellateRanks = new Map();
    lastOrgBandById = new Map();
    return;
  }

  // --- Top-down hierarchy ranks (by appellate chain) ---
  // Data direction: lower --> higher (e.g. hc_delhi --> supreme_court_india).
  // We compute rank from the top node downwards by traversing incoming edges.
  const ranks = computeAppellateRanks(entities, rels);
  const maxRank = Math.max(0, ...Array.from(ranks.values()));
  const fallbackRank = maxRank + 2; // for nodes not in the appellate chain

  // --- Org-chart bands + state/HC grouping (for legibility) ---
  const bandIndexById = computeOrgBands(entities, ranks);
  const groups = computeHorizontalGroups(entities);
  const ext = computeOrgLayoutCanvas(width, height, entities.length);
  layoutCanvasW = ext.layoutW;
  layoutCanvasH = ext.layoutH;
  // Deterministic org-chart positions (no simulation).
  teardownSimulation();
  const layoutOut = computeOrgChartPositions({
    entities,
    relationships: rels,
    ranks,
    fallbackRank,
    bandIndexById,
    groups,
    layoutW: layoutCanvasW,
    layoutH: layoutCanvasH,
  });
  layoutCanvasW = layoutOut.layoutW;
  layoutCanvasH = layoutOut.layoutH;
  const positions = layoutOut.positions;
  simNodesById = new Map(Object.entries(positions).map(([id, pos]) => [id, { id, x: pos.x, y: pos.y }]));
  lastGraphContentBounds = computeEntityPositionsBounds(positions, entities);
}

function teardownSimulation() {
  if (simulation) simulation.stop();
  simulation = null;
  simNodesById = new Map();
}

function updateGeometryFromPositions() {
  // Update node transforms
  layerNodes.selectAll('.node')
    .attr('transform', d => {
      const n = simNodesById.get(d.id);
      const x = n?.x ?? d.position?.x ?? 0;
      const y = n?.y ?? d.position?.y ?? 0;
      return `translate(${x},${y})`;
    });

  // Update labels
  layerLabels.selectAll('.node-label')
    .attr('x', d => (simNodesById.get(d.id)?.x ?? d.position?.x ?? 0))
    .attr('y', d => (simNodesById.get(d.id)?.y ?? d.position?.y ?? 0) + 36);

  // Update edge paths
  layerEdges.selectAll('.edge-path')
    .attr('d', d => {
      const s = simNodesById.get(d.source);
      const t = simNodesById.get(d.target);
      if (!s || !t) return '';
      return curvePath(s.x, s.y, t.x, t.y);
    });
}

// ── Level 0: Institutional cluster cards only (no entity nodes / band boxes) ─

const STRUCTURAL_HEALTH_RANK = {
  healthy: 0,
  moderate: 1,
  concerning: 2,
  critical: 3,
};

const STRUCTURAL_HEALTH_COLOR = {
  critical: '#e74c3c',
  concerning: '#e67e22',
  moderate: '#f1c40f',
  healthy: '#27ae60',
};

function clusterFill12(hex) {
  const h = (hex || '#2d3436').replace('#', '');
  if (h.length !== 6) return 'rgba(45, 52, 54, 0.12)';
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r},${g},${b},0.12)`;
}

function worstStructuralHealthLevel(members) {
  let worst = 'healthy';
  let worstRank = -1;
  for (const e of members) {
    const lvl = (e.derived || {}).structural_health_level || 'healthy';
    const r = STRUCTURAL_HEALTH_RANK[lvl];
    if (r === undefined) continue;
    if (r > worstRank) {
      worstRank = r;
      worst = lvl;
    }
  }
  return worst;
}

function _renderL0() {
  const clusters = State.graph.clusters;
  const visibleEntities = State.getVisibleEntities();
  const visibleIds = new Set(visibleEntities.map(e => e.id));
  const meta = State.graph.meta;
  const scaleX = width / meta.canvas_width;
  const scaleY = height / meta.canvas_height;

  layerClusters.selectAll('.cluster-group').remove();
  layerClusters.selectAll('path.l0-subcluster-arc').remove();

  const clusterData = clusters.map(c => {
    const members = State.graph.entities.filter(
      e => e.cluster === c.id && visibleIds.has(e.id)
    );
    const gapSum = members.reduce((s, e) => s + (Number(e.gap_count) || 0), 0);
    const ncCount = members.filter(e => e.operational_status === 'Not_Constituted').length;
    const healthLevel = worstStructuralHealthLevel(members);
    return {
      ...c,
      _w: c.position.width * scaleX,
      _h: c.position.height * scaleY,
      _tx: c.position.x * scaleX,
      _ty: c.position.y * scaleY,
      _active: members.length,
      _gapSum: gapSum,
      _ncCount: ncCount,
      _healthLevel: healthLevel,
      _healthFill: STRUCTURAL_HEALTH_COLOR[healthLevel] || STRUCTURAL_HEALTH_COLOR.healthy,
    };
  });

  const cards = layerClusters.selectAll('g.l0-cluster-card')
    .data(clusterData, d => d.id);

  const enter = cards.enter().append('g')
    .attr('class', 'l0-cluster-card')
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation();
      zoomToCluster(d);
    });

  enter.append('ellipse').attr('class', 'l0-card-shape');
  enter.append('circle').attr('class', 'l0-health');
  enter.append('text').attr('class', 'l0-name');
  enter.append('text').attr('class', 'l0-count');
  enter.append('text').attr('class', 'l0-gaps');
  enter.append('text').attr('class', 'l0-nc');

  const merged = enter.merge(cards);

  merged.attr('transform', d => `translate(${d._tx},${d._ty})`);

  merged.select('.l0-card-shape')
    .attr('cx', d => d._w / 2)
    .attr('cy', d => d._h / 2)
    .attr('rx', d => Math.max(10, d._w / 2))
    .attr('ry', d => Math.max(10, d._h / 2))
    .attr('fill', d => clusterFill12(d.color))
    .attr('stroke', d => d.color)
    .attr('stroke-width', 2);

  merged.select('.l0-health')
    .attr('cx', d => d._w / 2)
    .attr('cy', d => d._h / 2)
    .attr('r', 30)
    .attr('fill', d => d._healthFill)
    .attr('stroke', 'rgba(0,0,0,0.18)')
    .attr('stroke-width', 1)
    .attr('pointer-events', 'none');

  merged.select('.l0-name')
    .attr('x', 10)
    .attr('y', 18)
    .attr('text-anchor', 'start')
    .attr('fill', '#fff')
    .attr('font-size', '14px')
    .attr('font-weight', '700')
    .attr('pointer-events', 'none')
    .text(d => d.name);

  merged.select('.l0-count')
    .attr('x', d => d._w - 10)
    .attr('y', 18)
    .attr('text-anchor', 'end')
    .attr('fill', '#9ca3af')
    .attr('font-size', '12px')
    .attr('font-weight', '400')
    .attr('pointer-events', 'none')
    .text(d => `${d._active} entities`);

  merged.select('.l0-gaps')
    .attr('x', 10)
    .attr('y', d => d._h - 8)
    .attr('text-anchor', 'start')
    .attr('fill', '#e67e22')
    .attr('font-size', '12px')
    .attr('font-weight', '600')
    .attr('pointer-events', 'none')
    .text(d => (d._gapSum > 0 ? `⚠ ${d._gapSum} gaps` : ''));

  merged.select('.l0-nc')
    .attr('x', d => d._w - 10)
    .attr('y', d => d._h - 8)
    .attr('text-anchor', 'end')
    .attr('fill', '#ca6f1e')
    .attr('font-size', '12px')
    .attr('font-weight', '600')
    .attr('pointer-events', 'none')
    .text(d => (d._ncCount > 0 ? `NC: ${d._ncCount}` : ''));

  cards.exit().remove();
}

// ── Level 1/2: Edges ──────────────────────────────────────────────────────────

function isBrokenAppellate(rel) {
  if (rel.relationship_category !== 'appellate_chain') return false;
  const src = State.getEntityById(rel.source);
  if (!src) return false;
  return (src.derived || {}).appellate_functional === false;
}

export function renderEdges() {
  if (State.zoomLevel === 0) return;
  const rels = State.getVisibleRelationships();
  const posMap = buildPositionMap();
  const colors = State.getRelationshipColors();
  const neighbors = hoveredNodeId ? buildNeighborSet(rels, hoveredNodeId) : null;
  const NAVY = '#2c3e50';

  const edgeKey = d => d.id ?? `${d.source}|${d.target}|${d.relationship_type || ''}`;

  const edges = layerEdges.selectAll('.edge')
    .data(rels, edgeKey);

  const enter = edges.enter().append('g').attr('class', 'edge');
  enter.append('path').attr('class', 'edge-path');

  const merged = enter.merge(edges);

  merged.select('.edge-path')
    .attr('d', d => {
      const s = posMap[d.source];
      const t = posMap[d.target];
      if (!s || !t) return '';
      return curvePath(s.x, s.y, t.x, t.y);
    })
    .attr('stroke', d => {
      if (d.relationship_category === 'appellate_chain') {
        if (State.viewMode === 'gaps' && isBrokenAppellate(d)) return '#e74c3c';
        return NAVY;
      }
      return colors[d.relationship_category] || '#999';
    })
    .attr('stroke-width', d => {
      if (State.viewMode === 'gaps' && d.relationship_category === 'appellate_chain' && isBrokenAppellate(d)) {
        return 3;
      }
      return d.is_binding ? 2 : 1;
    })
    .attr('stroke-dasharray', d => {
      if (State.viewMode === 'gaps' && d.relationship_category === 'appellate_chain' && isBrokenAppellate(d)) {
        return '10,6';
      }
      if (State.isRelationshipHistorical(d)) return '4,4';
      if (d.data_quality === 'unverified') return '2,3';
      if (d.data_quality === 'contested') return '6,2';
      return null;
    })
    .attr('fill', 'none')
    .attr('opacity', d => {
      // Readable at default zoom (~0.55); still dim non-hover paths when hovering a node.
      const base = State.isRelationshipHistorical(d) ? 0.22
        : d.data_quality === 'unverified' ? 0.28
        : 0.38;
      if (!neighbors) return base;
      const onPath = d.source === hoveredNodeId || d.target === hoveredNodeId;
      return onPath ? 0.95 : 0.12;
    })
    .attr('marker-end', d => {
      const cat = d.relationship_category;
      return `url(#arrow-${cat})`;
    })
    .on('mouseenter', function(event, d) {
      d3.select(this).attr('stroke-width', 3).attr('opacity', 1);
      showEdgeTooltip(event, d);
    })
    .on('mouseleave', function(event, d) {
      d3.select(this).attr('stroke-width', d.is_binding ? 2 : 1).attr('opacity', 0.75);
      hideTooltip();
    });

  // Edge-type labels: only at L2+. Always strip when leaving L2 or when endpoints vanish,
  // otherwise D3 leaves orphan <text> with stale transforms (mode / zoom / layout switches).
  if (State.zoomLevel < 2) {
    merged.selectAll('.edge-label').remove();
  } else {
    merged.each(function(d) {
      const g = d3.select(this);
      const s = posMap[d.source];
      const t = posMap[d.target];
      if (!s || !t) {
        g.selectAll('.edge-label').remove();
        return;
      }
      let lab = g.select('text.edge-label');
      if (lab.empty()) {
        lab = g.append('text').attr('class', 'edge-label');
      }
      const mx = (s.x + t.x) / 2;
      const my = (s.y + t.y) / 2;
      lab
        .attr('fill', colors[d.relationship_category] || '#999')
        .attr('font-size', '9px')
        .attr('dy', -4)
        .attr('text-anchor', 'middle')
        .text(formatRelType(d.relationship_type))
        .attr('transform', `translate(${mx},${my})`);
    });
  }

  edges.exit().remove();
}

// ── Level 1/2: Nodes ──────────────────────────────────────────────────────────

export function renderNodes() {
  if (State.zoomLevel === 0) return;
  const entities = State.getVisibleEntities();
  const posMap = buildPositionMap();
  const irColors = State.getIndependenceRiskColors();
  const dqLegend = State.getDataQualityLegend();
  const osLegend = State.getOperationalStatusLegend();
  const rels = State.getVisibleRelationships();
  const neighborSet = hoveredNodeId ? buildNeighborSet(rels, hoveredNodeId) : null;

  const zoomScale = State.get('zoomScale') ?? State.zoomTransform?.k ?? 1;
  const kz = Math.max(0.18, Math.min(8, zoomScale || 1));
  function innerLabelFontPxFor(d) {
    const base = Math.max(4.2, Math.min(11.5, 8.2 / kz));
    const tier = hierarchyTierForSizing(d);
    const mul = tier <= 0 ? 1.32 : tier === 1 ? 1.12 : 1;
    return Math.min(12.5, base * mul);
  }

  const nodes = layerNodes.selectAll('.node')
    .data(entities, d => d.id);

  const enter = nodes.enter().append('g')
    .attr('class', 'node')
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation();
      State.selectEntity(d.id);
      openDetailPanel(d);
    })
    .on('mouseenter', function(event, d) {
      d3.select(this).selectAll('.node-shape, .node-circle, .node-rect').attr('filter', 'url(#glow)');
      hoveredNodeId = d.id;
      cancelTooltipHide();
      render(); // re-render with neighbor dimming + tooltips
      showNodeRelationshipsTooltip(event, d, rels);
    })
    .on('mouseleave', function(event, d) {
      d3.select(this).selectAll('.node-shape, .node-circle, .node-rect').attr('filter', null);
      hoveredNodeId = null;
      scheduleHideTooltip(300);
      render();
    });

  // Independence risk ring (court / allied circles)
  enter.append('circle').attr('class', 'node-ir-ring');
  // Independence risk ring (stakeholder rectangles)
  enter.append('rect').attr('class', 'node-ir-ring-rect');
  // Main shapes: path = SC/HC/tribunal/regulatory/arbitration/courts; rect = stakeholders
  enter.append('path').attr('class', 'node-shape');
  enter.append('circle').attr('class', 'node-circle');
  enter.append('rect').attr('class', 'node-rect');
  // Structural-exception diagonal stripe (Gaps mode)
  enter.append('path').attr('class', 'node-exception-shape');
  enter.append('circle').attr('class', 'node-exception-circle');
  enter.append('rect').attr('class', 'node-exception-rect');
  // In-box title on stakeholder (non-bench) rectangles
  enter.append('text').attr('class', 'node-inner-label');
  // Badge overlay (?, ⚑, "NC")
  enter.append('text').attr('class', 'node-badge');
  enter.append('text').attr('class', 'node-gap-marker');
  enter.append('text').attr('class', 'node-circ-marker');

  const merged = enter.merge(nodes);

  merged.attr('transform', d => {
    const pos = posMap[d.id] || d.position || { x: 0, y: 0 };
    return `translate(${pos.x},${pos.y})`;
  });

  ensureUpgradedNodeShapes(merged);

  const nodeRadius = drawableNodeRadiusForEntity;

  function innerLabelText(d) {
    const raw = d.abbreviation || d.name || d.id;
    const maxW = 2 * drawableRectHalfWidth(d) - 10;
    const fp = innerLabelFontPxFor(d);
    const approxChars = Math.max(6, Math.floor(maxW / (fp * 0.52)));
    return raw.length > approxChars ? `${raw.slice(0, approxChars - 1)}…` : raw;
  }

  function nodeStrokeAttrs(d) {
    if (State.viewMode === 'gaps' && d.operational_status === 'De_Facto_Blocked') {
      return { stroke: '#e67e22', strokeWidth: 3 };
    }
    if (State.showIndependenceRisk) {
      const level = (d.derived || {}).independence_risk_level || 'low';
      return { stroke: irColors[level] || '#27ae60', strokeWidth: 2 };
    }
    const kind = entityVisualKind(d);
    if (kind === 'court') return { stroke: '#94a3b8', strokeWidth: 2.5 };
    if (kind === 'allied') return { stroke: '#64748b', strokeWidth: 1.75 };
    return { stroke: '#444', strokeWidth: 2 };
  }

  // Historical / abolished opacity
  const nodeOpacity = d => {
    if (State.isEntityHistorical(d)) return 0.25;
    const osStyle = osLegend[d.operational_status] || {};
    return osStyle.node_opacity || 1.0;
  };

  const dimIfNotNeighbor = d => {
    const base = nodeOpacity(d);
    if (!neighborSet) return base;
    const isNeighbor = d.id === hoveredNodeId || neighborSet.has(d.id);
    return isNeighbor ? base : Math.min(base, 0.12);
  };

  function courtFill(d) {
    const kind = entityVisualKind(d);
    if (kind === 'court') return judicialBodyFill(d.level_of_government);
    if (kind === 'allied') return alliedBodyFill(d);
    return stakeholderNodeFill(d.level_of_government);
  }

  function courtStrokeDash(d) {
    if (d.operational_status === 'Not_Constituted') return '5,3';
    if (d.operational_status === 'Proposed') return '2,3';
    if (d.data_quality === 'unverified') return '3,3';
    return null;
  }

  function applyShapeAttrs(sel) {
    sel
      .attr('fill', courtFill)
      .attr('stroke', d => nodeStrokeAttrs(d).stroke)
      .attr('stroke-width', d => nodeStrokeAttrs(d).strokeWidth)
      .attr('stroke-dasharray', courtStrokeDash)
      .attr('opacity', dimIfNotNeighbor);
  }

  // Typed judicial shapes (hexagon, pentagon, crescent, diamond, triangle, square)
  merged.select('.node-shape')
    .style('display', d => {
      const shape = entityNodeShape(d);
      return shape !== 'rect' && shape !== 'circle' ? null : 'none';
    })
    .attr('fill-rule', d => (entityNodeShape(d) === 'crescent' ? 'evenodd' : null))
    .attr('d', d => nodeShapePathForEntity(d, nodeRadius(d)))
    .call(applyShapeAttrs);

  // Subordinate / city / special courts — circle
  merged.select('.node-circle')
    .style('display', d => (entityNodeShape(d) === 'circle' ? null : 'none'))
    .attr('r', nodeRadius)
    .call(applyShapeAttrs);

  // Executive, appointment, training, etc. — rectangles
  merged.select('.node-rect')
    .style('display', d => (entityNodeShape(d) === 'rect' ? null : 'none'))
    .attr('x', d => -drawableRectHalfWidth(d))
    .attr('y', d => -drawableRectHalfHeight(d))
    .attr('width', d => 2 * drawableRectHalfWidth(d))
    .attr('height', d => 2 * drawableRectHalfHeight(d))
    .attr('rx', 8)
    .attr('ry', 8)
    .attr('fill', d => stakeholderNodeFill(d.level_of_government))
    .attr('stroke', d => nodeStrokeAttrs(d).stroke)
    .attr('stroke-width', d => nodeStrokeAttrs(d).strokeWidth)
    .attr('stroke-dasharray', d => {
      if (d.operational_status === 'Not_Constituted') return '5,3';
      if (d.operational_status === 'Proposed') return '2,3';
      if (d.data_quality === 'unverified') return '3,3';
      return null;
    })
    .attr('opacity', dimIfNotNeighbor);

  // Independence risk ring — judicial / allied shapes (circle outline)
  merged.select('.node-ir-ring')
    .style('display', d => (entityNodeShape(d) !== 'rect' ? null : 'none'))
    .attr('r', d => {
      if (!State.showIndependenceRisk || entityNodeShape(d) === 'rect') return 0;
      return shapeLayoutRadius(d, nodeRadius(d)) + IR_RING_OFFSET;
    })
    .attr('fill', 'none')
    .attr('stroke', d => {
      const level = (d.derived || {}).independence_risk_level || 'low';
      return irColors[level] || '#27ae60';
    })
    .attr('stroke-width', IR_RING_WIDTH)
    .attr('opacity', d => (State.showIndependenceRisk && entityNodeShape(d) !== 'rect') ? 0.7 : 0);

  merged.select('.node-ir-ring-rect')
    .style('display', d => (entityNodeShape(d) === 'rect' ? null : 'none'))
    .attr('x', d => -drawableRectHalfWidth(d) - IR_RING_OFFSET)
    .attr('y', d => -drawableRectHalfHeight(d) - IR_RING_OFFSET)
    .attr('width', d => 2 * drawableRectHalfWidth(d) + 2 * IR_RING_OFFSET)
    .attr('height', d => 2 * drawableRectHalfHeight(d) + 2 * IR_RING_OFFSET)
    .attr('rx', 10)
    .attr('ry', 10)
    .attr('fill', 'none')
    .attr('stroke', d => {
      const level = (d.derived || {}).independence_risk_level || 'low';
      return irColors[level] || '#27ae60';
    })
    .attr('stroke-width', IR_RING_WIDTH)
    .attr('opacity', d => (State.showIndependenceRisk && entityNodeShape(d) === 'rect') ? 0.72 : 0);

  merged.select('.node-exception-shape')
    .style('display', d => {
      const shape = entityNodeShape(d);
      return shape !== 'rect' && shape !== 'circle' ? null : 'none';
    })
    .attr('fill-rule', d => (entityNodeShape(d) === 'crescent' ? 'evenodd' : null))
    .attr('d', d => nodeShapePathForEntity(d, nodeRadius(d)))
    .attr('fill', 'url(#pat-exception-stripes)')
    .attr('opacity', d => {
      const shape = entityNodeShape(d);
      return (State.showExceptions && d.structural_exception && shape !== 'rect' && shape !== 'circle') ? 0.52 : 0;
    })
    .attr('pointer-events', 'none');

  merged.select('.node-exception-circle')
    .style('display', d => (entityNodeShape(d) === 'circle' ? null : 'none'))
    .attr('r', d => {
      if (!State.showExceptions || !d.structural_exception || entityNodeShape(d) !== 'circle') return 0;
      return nodeRadius(d);
    })
    .attr('fill', 'url(#pat-exception-stripes)')
    .attr('opacity', d => (State.showExceptions && d.structural_exception && entityNodeShape(d) === 'circle') ? 0.52 : 0)
    .attr('pointer-events', 'none');

  merged.select('.node-exception-rect')
    .style('display', d => (entityNodeShape(d) === 'rect' ? null : 'none'))
    .attr('x', d => -drawableRectHalfWidth(d))
    .attr('y', d => -drawableRectHalfHeight(d))
    .attr('width', d => 2 * drawableRectHalfWidth(d))
    .attr('height', d => 2 * drawableRectHalfHeight(d))
    .attr('rx', 8)
    .attr('ry', 8)
    .attr('fill', 'url(#pat-exception-stripes)')
    .attr('opacity', d => (State.showExceptions && d.structural_exception && entityVisualKind(d) === 'stakeholder') ? 0.52 : 0)
    .attr('pointer-events', 'none');

  merged.select('.node-inner-label')
    .style('display', d => (entityVisualKind(d) === 'stakeholder' ? null : 'none'))
    .attr('text-anchor', 'middle')
    .attr('dominant-baseline', 'central')
    .attr('x', 0)
    .attr('y', 0)
    .attr('font-size', d => `${innerLabelFontPxFor(d)}px`)
    .attr('font-weight', d => (d.type === 'AppointmentBody' ? '650' : '560'))
    .attr('font-style', d => (d.type === 'ExecutiveBody' ? 'italic' : 'normal'))
    .attr('font-family', 'Inter, system-ui, -apple-system, sans-serif')
    .attr('fill', '#e8eef5')
    .attr('opacity', dimIfNotNeighbor)
    .text(innerLabelText);

  // Badge
  merged.select('.node-badge')
    .attr('text-anchor', 'middle')
    .attr('dominant-baseline', 'central')
    .attr('dy', d => (entityVisualKind(d) === 'stakeholder' ? -drawableRectHalfHeight(d) + 2 : -nodeRadius(d) + 2))
    .attr('dx', d => (entityVisualKind(d) === 'stakeholder' ? drawableRectHalfWidth(d) - 2 : nodeRadius(d) - 2))
    .attr('font-size', '10px')
    .attr('font-weight', d => (entityVisualKind(d) === 'stakeholder' ? '700' : '400'))
    .attr('fill', '#e74c3c')
    .text(d => {
      if (d.operational_status === 'Not_Constituted') return 'NC';
      if (d.data_quality === 'partial') return '?';
      if (d.data_quality === 'contested') return '⚑';
      return '';
    });

  merged.select('.node-gap-marker')
    .attr('text-anchor', 'middle')
    .attr('dominant-baseline', 'central')
    .attr('dy', d => (entityVisualKind(d) === 'stakeholder' ? -drawableRectHalfHeight(d) - 10 : -nodeRadius(d) - 10))
    .attr('dx', d => (entityVisualKind(d) === 'stakeholder' ? -drawableRectHalfWidth(d) + 4 : -nodeRadius(d) + 4))
    .attr('font-size', '18px')
    .attr('font-weight', '800')
    .attr('font-style', d => (entityVisualKind(d) === 'allied' ? 'italic' : 'normal'))
    .attr('fill', '#e74c3c')
    .attr('pointer-events', 'none')
    .text(d => ((State.showGaps && (d.gap_flag || (d.gap_count || 0) > 0)) ? '*' : ''));

  merged.select('.node-circ-marker')
    .attr('text-anchor', 'middle')
    .attr('dominant-baseline', 'central')
    .attr('dy', d => (entityVisualKind(d) === 'stakeholder' ? drawableRectHalfHeight(d) + 4 : nodeRadius(d) + 4))
    .attr('dx', d => (entityVisualKind(d) === 'stakeholder' ? drawableRectHalfWidth(d) - 2 : nodeRadius(d) - 2))
    .attr('font-size', '14px')
    .attr('fill', '#8e44ad')
    .attr('pointer-events', 'none')
    .text(d => {
      const c = d.circularity_score ?? d.derived?.circularity_score ?? 0;
      return (State.showCircularity && c > 0) ? '⟳' : '';
    });

  nodes.exit().remove();
}

// ── Level 1/2: Labels (semantic zoom L1/L2; scale-driven via State.get('zoomScale')) ─

function renderLabels() {
  if (State.zoomLevel === 0) return;
  const entities = State.getVisibleEntities();
  const posMap = buildPositionMap();
  const dqLegend = State.getDataQualityLegend();
  const textPrimary = getComputedStyle(document.documentElement).getPropertyValue('--text-primary').trim() || '#111827';
  const textDim = getComputedStyle(document.documentElement).getPropertyValue('--text-dim').trim() || '#6b7280';
  const isLightTheme = (getComputedStyle(document.documentElement).getPropertyValue('--bg').trim() || '').toLowerCase() !== '#0d0d1a';
  const rels = State.getVisibleRelationships();
  const neighborSet = hoveredNodeId ? buildNeighborSet(rels, hoveredNodeId) : null;
  const zoomScale = State.get('zoomScale') ?? State.zoomTransform?.k ?? 1;
  // Labels are inside the zoomed #graph-root. Font in user units: F×k ≈ constant screen px.
  // Never use a minimum F≥12 here — at large k that explodes on-screen (was the huge-label bug).
  const k = Math.max(0.18, Math.min(8, zoomScale || 1));
  function benchLabelFontPx(d) {
    const tier = hierarchyTierForSizing(d);
    const tierMul = tier <= 0 ? 2.1 : tier === 1 ? 1.75 : tier === 2 ? 1.1 : 1;
    const basePx = tier <= 0 ? 14.5 : tier === 1 ? 12.5 : 10.5;
    return Math.max(4.5, Math.min(32, (basePx / k) * tierMul));
  }

  const benchLabelEntities = entities.filter(e => entityVisualKind(e) !== 'stakeholder');

  const labels = layerLabels.selectAll('.node-label')
    .data(benchLabelEntities, d => d.id);

  const enter = labels.enter().append('text').attr('class', 'node-label');
  const merged = enter.merge(labels);

  merged
    .attr('x', d => (posMap[d.id] || d.position || {x:0}).x)
    .attr('y', d => (posMap[d.id] || d.position || {y:0}).y + externalLabelYOffset(d, benchLabelFontPx(d)))
    .attr('text-anchor', 'middle')
    .attr('font-size', d => `${benchLabelFontPx(d)}px`)
    .attr('font-weight', d => {
      const dq = d.data_quality;
      if (entityVisualKind(d) === 'court') {
        if (dq === 'verified') return '780';
        return '520';
      }
      if (entityVisualKind(d) === 'allied') {
        if (dq === 'verified') return '660';
        return '430';
      }
      return '400';
    })
    .attr('fill', d => {
      if (State.isEntityHistorical(d)) return textDim;
      if (isLightTheme) return textPrimary; // override dark-theme legend colors
      const dq = d.data_quality;
      const style = dqLegend[dq] || {};
      return style.color || textPrimary;
    })
    .attr('font-style', d => {
      if (entityVisualKind(d) === 'allied') return 'italic';
      const dq = d.data_quality;
      const dqStyle = dqLegend[dq] || {};
      if (dqStyle.italic) return 'italic';
      if (d.operational_status === 'Not_Constituted') return 'italic';
      if (State.isEntityHistorical(d)) return 'italic';
      return 'normal';
    })
    .attr('text-decoration', d => {
      if (State.isEntityHistorical(d)) return 'line-through';
      const dq = d.data_quality;
      const dqStyle = dqLegend[dq] || {};
      if (dqStyle.underline) return `underline ${dqStyle.underline}`;
      return null;
    })
    .attr('opacity', d => {
      if (State.isEntityHistorical(d)) return 0.45;
      if (!neighborSet) return 0.94;
      const isNeighbor = d.id === hoveredNodeId || neighborSet.has(d.id);
      return isNeighbor ? 1.0 : 0.22;
    })
    .text(d => nodeCaptionText(d, zoomScale));

  labels.exit().remove();
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function buildNeighborSet(rels, id) {
  const set = new Set();
  rels.forEach(r => {
    if (r.source === id) set.add(r.target);
    else if (r.target === id) set.add(r.source);
  });
  return set;
}

function computeAppellateRanks(entities, rels) {
  const ids = new Set(entities.map(e => e.id));
  const edges = rels
    .filter(r => r.relationship_category === 'appellate_chain')
    .filter(r => ids.has(r.source) && ids.has(r.target));

  // Build reverse adjacency: higher -> [lower...]
  const incomingFrom = new Map(); // key: higher, value: lowers that appeal to it
  edges.forEach(r => {
    const higher = r.target;
    const lower = r.source;
    if (!incomingFrom.has(higher)) incomingFrom.set(higher, []);
    incomingFrom.get(higher).push(lower);
  });

  const rank = new Map();
  const root = 'supreme_court_india';
  rank.set(root, 0);

  const q = [root];
  while (q.length) {
    const cur = q.shift();
    const curRank = rank.get(cur) ?? 0;
    const lowers = incomingFrom.get(cur) || [];
    for (const low of lowers) {
      const nextRank = curRank + 1;
      const prev = rank.get(low);
      if (prev === undefined || nextRank < prev) {
        rank.set(low, nextRank);
        q.push(low);
      }
    }
  }

  return rank;
}

function computeOrgBands(entities, appellateRanks) {
  // Bands (top -> bottom):
  // 0: Apex constitutional + head-of-state
  // 1: High Courts + core appointment bodies
  // 2: Tribunals / regulators / oversight infrastructure
  // 3: State bodies + subordinate courts + roles/people
  const band = new Map();

  for (const e of entities) {
    const id = e.id;
    const type = e.type;
    const cluster = e.cluster;

    if (id === 'supreme_court_india' || id === 'president_india') {
      band.set(id, 0);
      continue;
    }

    if (type === 'HighCourtBench' || (type === 'ConstitutionalCourt' && id.startsWith('hc_'))) {
      band.set(id, 1);
      continue;
    }

    if (cluster === 'appointment_bodies' || type === 'AppointmentBody') {
      band.set(id, 1);
      continue;
    }

    if (cluster === 'tribunals_adr' || type === 'CentralTribunal' || type === 'StateTribunal') {
      band.set(id, 2);
      continue;
    }

    if (cluster === 'regulatory_bodies' || type === 'RegulatoryBodyQJ') {
      band.set(id, 2);
      continue;
    }

    if (cluster === 'digital_infrastructure' || cluster === 'financing_audit' || cluster === 'training_professional') {
      band.set(id, 2);
      continue;
    }

    if (cluster === 'constitutional_courts' && type === 'ConstitutionalCourt') {
      // Other constitutional courts (SC already handled)
      band.set(id, 1);
      continue;
    }

    // Default bottom band
    band.set(id, 3);
  }

  return band;
}

function computeHorizontalGroups(entities) {
  // Prefer state/UT from jurisdiction_scope.states_covered/uts_covered.
  // For TN sample entities (ids like tn_*), use id prefix.
  // Else group as Central.
  const map = new Map();
  for (const e of entities) {
    const id = e.id || '';
    const js = e.jurisdiction_scope || e._detail?.jurisdiction_scope || {};
    const states = Array.isArray(js.states_covered) ? js.states_covered : [];
    const uts = Array.isArray(js.uts_covered) ? js.uts_covered : [];

    if (id.startsWith('tn_') || id === 'tnerc' || id === 'tn_rera') {
      map.set(id, 'TN');
      continue;
    }

    if (states.length === 1) {
      map.set(id, states[0]);
      continue;
    }
    if (uts.length === 1) {
      map.set(id, uts[0]);
      continue;
    }

    // High Courts: use the first state code if multi, else label as MultiState.
    if (id.startsWith('hc_') && states.length > 1) {
      map.set(id, 'MultiState_HC');
      continue;
    }

    if (e.level_of_government === 'State') {
      map.set(id, 'State');
      continue;
    }

    map.set(id, 'Central');
  }
  return map;
}

/** Bands at this index and below use a narrow vertical ribbon instead of one X column per state. */
const COMPACT_LAYOUT_MIN_BAND = 2;

/** Virtual canvas — width driven by upper bands + compact ribbons, not entity count alone. */
function computeOrgLayoutCanvas(viewW, viewH, entityCount, widthHint) {
  const n = Math.max(0, entityCount);
  const spread = Math.sqrt(n);
  const layoutW = Math.min(
    20000,
    Math.max(
      widthHint || 0,
      viewW * 2.4,
      viewW + spread * 72 + 720
    )
  );
  const layoutH = Math.min(
    19000,
    Math.max(viewH * 4.2, viewH + spread * 95 + 1180)
  );
  return { layoutW: Math.round(layoutW), layoutH: Math.round(layoutH) };
}

function jitterFromId(id, amp) {
  let h = 0;
  for (let i = 0; i < (id || '').length; i++) {
    h = (Math.imul(31, h) + id.charCodeAt(i)) | 0;
  }
  const a = ((h & 255) / 255) * 2 - 1;
  const b = (((h >> 8) & 255) / 255) * 2 - 1;
  return { dx: a * amp, dy: b * amp * 0.62 };
}

function compactGridShape(n) {
  const cols = Math.max(4, Math.ceil(Math.sqrt(n * 1.12)));
  const rows = Math.ceil(n / cols);
  return { cols, rows };
}

function computeCompactRibbonWidth(n, minCenterDist) {
  if (n <= 0) return 0;
  const cellW = minCenterDist * 1.18;
  const { cols } = compactGridShape(n);
  return cols * cellW + cellW * 0.55 + CLUSTER_PADDING * 2;
}

function computeCompactBandVerticalHalf(n, minCenterDist, layoutH) {
  if (n <= 0) return minCenterDist;
  const rowPitch = minCenterDist * 0.92;
  const { rows } = compactGridShape(n);
  const need = (rows * rowPitch) / 2 + minCenterDist * 0.55;
  return Math.min(layoutH * 0.44, Math.max(minCenterDist * 1.15, need));
}

/**
 * Sparse non-linear packing for dense lower bands: brick-offset grid in a narrow
 * ribbon centred on the canvas (not one column per jurisdiction).
 */
function layoutCompactBand({
  bandEntities,
  bandBaseY,
  centerX,
  minCenterDist,
  bandClamp,
  getGroup,
}) {
  const n = bandEntities.length;
  const cellW = minCenterDist * 1.18;
  const rowPitch = minCenterDist * 0.92;
  const { cols, rows } = compactGridShape(n);
  const ribbonW = cols * cellW + cellW * 0.55;
  const xLo = centerX - ribbonW / 2;
  const xHi = centerX + ribbonW / 2;

  const sorted = [...bandEntities].sort((a, b) => {
    const ga = getGroup(a) || '';
    const gb = getGroup(b) || '';
    if (ga !== gb) return ga.localeCompare(gb);
    return (a.id || '').localeCompare(b.id || '');
  });

  const positions = {};
  const xStart = centerX - ribbonW / 2 + cellW / 2;

  sorted.forEach((e, idx) => {
    const col = idx % cols;
    const row = Math.floor(idx / cols);
    const brick = (row % 2) * cellW * 0.42;
    const waveY = Math.sin((col / Math.max(1, cols - 1)) * Math.PI) * rowPitch * 0.22;
    const j = jitterFromId(e.id, minCenterDist * 0.14);
    let x = xStart + col * cellW + brick + j.dx;
    let y = bandBaseY + (row - (rows - 1) / 2) * rowPitch + waveY + j.dy;
    x = Math.max(xLo + minCenterDist * 0.35, Math.min(xHi - minCenterDist * 0.35, x));
    y = Math.max(bandBaseY - bandClamp, Math.min(bandBaseY + bandClamp, y));
    positions[e.id] = { x, y };
  });

  return { positions, ribbonW, xLo, xHi };
}

/** Sort key: principal HC then its benches (Madurai after hc_madras, etc.). */
function judiciarySortKey(e) {
  const parent = e.parent_hc || e._detail?.parent_hc;
  if (e.type === 'HighCourtBench' && parent) return `${parent}~${e.id}`;
  if (e.id?.startsWith('hc_')) return `${e.id}~`;
  return e.id || '';
}

/**
 * Band 1 — HCs + permanent benches: 3-row grid centred under the Supreme Court.
 * Avoids one-X-column-per-jurisdiction (all MultiState HCs stacked in one pile).
 */
function layoutJudiciaryScatterBand({
  bandEntities,
  clusterTopY,
  centerX,
  minCenterDist,
}) {
  const judiciary = bandEntities.filter(
    e => e.type === 'HighCourtBench'
      || (e.type === 'ConstitutionalCourt' && e.id?.startsWith('hc_'))
  );
  const appointment = bandEntities.filter(
    e => e.type === 'AppointmentBody' || e.cluster === 'appointment_bodies'
  );
  const other = bandEntities.filter(
    e => !judiciary.includes(e) && !appointment.includes(e)
  );

  const positions = {};
  const dist = minCenterDist * 1.48;
  const cellW = dist * 1.22;
  const rowPitch = dist * 1.08;

  function scatterPack(entities, clusterTopY, cx, preferRows, topAnchored = true, tightGrid = false) {
    if (!entities.length) return { xLo: cx, xHi: cx, yMax: clusterTopY };
    const n = entities.length;
    let cols;
    let rows;
    if (preferRows) {
      rows = preferRows;
      cols = Math.ceil(n / rows);
    } else {
      cols = Math.max(5, Math.ceil(Math.sqrt(n * 1.05)));
      rows = Math.ceil(n / cols);
    }
    const ribbonW = cols * cellW + cellW * 0.65;
    const xLo = cx - ribbonW / 2;
    const xHi = cx + ribbonW / 2;
    const sorted = [...entities].sort((a, b) => judiciarySortKey(a).localeCompare(judiciarySortKey(b)));
    const xStart = cx - ribbonW / 2 + cellW / 2;
    let yMax = clusterTopY;
    const jitterAmp = tightGrid ? dist * 0.02 : dist * 0.1;

    sorted.forEach((e, idx) => {
      const col = idx % cols;
      const row = Math.floor(idx / cols);
      const brick = tightGrid ? 0 : (row % 2) * cellW * 0.48;
      const waveY = tightGrid ? 0 : Math.sin((col / Math.max(1, cols - 1)) * Math.PI) * rowPitch * 0.28;
      const j = jitterFromId(e.id, jitterAmp);
      let x = xStart + col * cellW + brick + j.dx;
      let y = topAnchored
        ? clusterTopY + row * rowPitch + waveY + (tightGrid ? 0 : Math.max(0, j.dy))
        : clusterTopY + (row - (rows - 1) / 2) * rowPitch + waveY + j.dy;
      x = Math.max(xLo + dist * 0.4, Math.min(xHi - dist * 0.4, x));
      y = Math.max(clusterTopY, y);
      positions[e.id] = { x, y };
      yMax = Math.max(yMax, y);
    });
    return { xLo, xHi, yMax: yMax + rowPitch * 0.65 };
  }

  const scX = centerX;
  let xLo = scX;
  let xHi = scX;

  let yMax = clusterTopY;

  if (judiciary.length) {
    const pack = scatterPack(judiciary, clusterTopY, scX, 3, true, true);
    xLo = Math.min(xLo, pack.xLo);
    xHi = Math.max(xHi, pack.xHi);
    yMax = Math.max(yMax, pack.yMax);
  }

  if (appointment.length) {
    const apptTopY = clusterTopY - rowPitch * 1.85;
    const apptCx = scX - Math.max(300, cellW * 3.5);
    const pack = scatterPack(appointment, apptTopY, apptCx, 2, true);
    xLo = Math.min(xLo, pack.xLo);
    xHi = Math.max(xHi, pack.xHi);
    yMax = Math.max(yMax, pack.yMax);
  }

  if (other.length) {
    const pack = scatterPack(other, clusterTopY + rowPitch * 0.4, scX + cellW * 2.8, 2, true);
    xLo = Math.min(xLo, pack.xLo);
    xHi = Math.max(xHi, pack.xHi);
    yMax = Math.max(yMax, pack.yMax);
  }

  return { positions, xLo, xHi, yMin: clusterTopY, yMax };
}

function principalHcIdForDistrictGroup(g) {
  return PRINCIPAL_HC_BY_STATE_CODE[g.stateCode] || g.hcTargetId;
}

/** Expanded district lattices (and collapsed summaries) pack under their principal HC. */
function collectDistrictLatticePinnedIds(entities) {
  const pinned = new Set();
  const index = State._districtAggregateIndex;
  if (!index?.groups) return pinned;
  const ids = new Set(entities.map(e => e.id));
  for (const g of index.groups) {
    const parentId = principalHcIdForDistrictGroup(g);
    const parentVisible = parentId && ids.has(parentId);
    if (!parentVisible) continue;
    const latticeOpen = State.expandedDistrictAggregateIds?.has(g.groupId);
    const synthId = g.synthetic ? `__jem_agg_${g.stateCode}_district_courts` : null;
    if (latticeOpen) {
      for (const mid of g.memberIds) if (ids.has(mid)) pinned.add(mid);
    } else if (g.proxyId && ids.has(g.proxyId)) {
      pinned.add(g.proxyId);
    } else if (synthId && ids.has(synthId)) {
      pinned.add(synthId);
    }
  }
  return pinned;
}

/**
 * Place expanded district lattices in a dedicated band below all High Courts
 * (not directly under one HC node, which overlaps lower HC rows).
 * @returns {number} bottom Y of the district band, or districtBandTopY if empty
 */
function layoutDistrictCourtsUnderParentHc({ entities, positions, minCenterDist, districtBandTopY }) {
  const index = State._districtAggregateIndex;
  if (!index?.groups) return districtBandTopY ?? 0;
  const byId = new Map(entities.map(e => [e.id, e]));
  const cellW = minCenterDist * 1.12;
  const rowPitch = minCenterDist * 0.92;
  const fixedRows = 3;
  const bandGap = minCenterDist * 1.6 + ORG_LABEL_VERTICAL_CLEARANCE;
  let yCursor = districtBandTopY + bandGap;

  for (const g of index.groups) {
    const parentId = principalHcIdForDistrictGroup(g);
    const parent = byId.get(parentId);
    const parentPos = positions[parentId];
    if (!parent || !parentPos) continue;

    const latticeOpen = State.expandedDistrictAggregateIds?.has(g.groupId);

    if (latticeOpen) {
      const members = [...g.memberIds]
        .filter(id => byId.has(id))
        .map(id => byId.get(id))
        .sort((a, b) => (a.id || '').localeCompare(b.id || ''));
      if (!members.length) continue;

      const cols = Math.ceil(members.length / fixedRows);
      const ribbonW = cols * cellW;
      const xStart = parentPos.x - ribbonW / 2 + cellW / 2;
      const topY = yCursor;

      members.forEach((e, idx) => {
        const col = idx % cols;
        const row = Math.floor(idx / cols);
        positions[e.id] = {
          x: xStart + col * cellW,
          y: topY + row * rowPitch,
        };
      });
      yCursor = topY + fixedRows * rowPitch + ORG_LABEL_VERTICAL_CLEARANCE + minCenterDist * 0.8;
      continue;
    }

    const synthId = g.synthetic ? `__jem_agg_${g.stateCode}_district_courts` : null;
    if (g.proxyId && byId.has(g.proxyId)) {
      positions[g.proxyId] = { x: parentPos.x, y: yCursor };
      yCursor += minCenterDist * 1.8;
    } else if (synthId && byId.has(synthId)) {
      positions[synthId] = { x: parentPos.x, y: yCursor };
      yCursor += minCenterDist * 1.8;
    }
  }

  return yCursor;
}

/**
 * Minimum vertical half-height for a band so we can fit a 5/7/9-row zig-zag
 * (several steps above & below the band centre).
 */
function computeBandZigZagVerticalHalf(nBand, minCenterDist, layoutH) {
  if (nBand <= 8) return minCenterDist * 1.0;
  const halfZig = nBand > 200 ? 4 : nBand > 55 ? 3 : 2;
  const rowCount = halfZig * 2 + 1;
  const rowPitch = minCenterDist * 0.54;
  const span = ((rowCount - 1) / 2) * rowPitch + minCenterDist * 0.45;
  return Math.min(layoutH * 0.38, Math.max(minCenterDist * 1.2, span));
}

/**
 * Rows within a hierarchy band: 3–4 steps above and below centre (5, 7, or 9 rows).
 * Row pitch is shrunk if needed to stay inside the band’s vertical clamp.
 */
function computeBandZigZagLayout(nBand, minCenterDist, bandVerticalHalf) {
  if (nBand <= 8) {
    return { rowCount: 1, rowPitch: 0, halfZig: 0 };
  }
  const halfZig = nBand > 200 ? 4 : nBand > 55 ? 3 : 2;
  const rowCount = halfZig * 2 + 1;
  let rowPitch = minCenterDist * 0.52;
  let span = ((rowCount - 1) / 2) * rowPitch;
  const maxSpan = Math.max(minCenterDist * 1.25, bandVerticalHalf * 0.96);
  if (span > maxSpan && rowCount > 1) {
    rowPitch = maxSpan / ((rowCount - 1) / 2);
    span = ((rowCount - 1) / 2) * rowPitch;
  }
  return { rowCount, rowPitch, halfZig };
}

function computeEntityPositionsBounds(positions, entities) {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  const padX = 150;
  const padTop = 120;
  const padBottom = 130;
  for (const e of entities) {
    const p = positions[e.id];
    if (!p) continue;
    const rr = effectiveNodeLayoutRadius(e);
    const tier = hierarchyTierForSizing(e);
    const lbl = entityVisualKind(e) !== 'stakeholder'
      ? 58 + tier * 10
      : 28 + tier * 4;
    minX = Math.min(minX, p.x - rr);
    maxX = Math.max(maxX, p.x + rr);
    minY = Math.min(minY, p.y - rr);
    maxY = Math.max(maxY, p.y + rr + lbl);
  }
  if (!Number.isFinite(minX)) return null;
  return {
    minX: minX - padX,
    maxX: maxX + padX,
    minY: minY - padTop,
    maxY: maxY + padBottom,
  };
}

function computeOrgChartPositions({
  entities,
  relationships,
  ranks,
  fallbackRank,
  bandIndexById,
  groups,
  layoutW: initialLayoutW,
  layoutH,
}) {
  // Drive hierarchy-sized radii during this layout pass.
  lastAppellateRanks = ranks;
  lastOrgBandById = bandIndexById;

  // Hybrid layout:
  // - Y is banded (hierarchy)
  // - Band 0: SC + President pinned at top
  // - Band 1: HCs + benches — zig-zag scatter centred under SC (not one column per state)
  // - Bands 2+: narrow brick grid ribbon (no state-wide horizontal sprawl)
  const getBand = (e) => bandIndexById.get(e.id) ?? 3;
  const getGroup = (e) => groups.get(e.id) ?? 'Central';
  const getRank = (e) => ranks.get(e.id) ?? fallbackRank;

  const ids = new Set(entities.map(e => e.id));
  const rMax = maxDrawableNodeRadius(entities);
  const minCenterDist = NODE_SPACING_RADIUS_MULT * rMax;
  const districtLatticePinned = collectDistrictLatticePinnedIds(entities);

  const bandToEntities = new Map();
  for (const e of entities) {
    if (districtLatticePinned.has(e.id)) continue;
    const b = getBand(e);
    if (!bandToEntities.has(b)) bandToEntities.set(b, []);
    bandToEntities.get(b).push(e);
  }

  const upperBandGroups = new Set();
  for (const e of entities) {
    if (getBand(e) < COMPACT_LAYOUT_MIN_BAND) upperBandGroups.add(getGroup(e));
  }
  const groupKeys = Array.from(upperBandGroups);
  groupKeys.sort((a, b) => (a === 'Central' ? -1 : b === 'Central' ? 1 : a.localeCompare(b)));

  const rawColPitch = minCenterDist * 2.35;
  let minColPitch = rawColPitch;
  const LAYOUT_W_CAP = 16000;
  let upperBandW = CLUSTER_PADDING * 2 + Math.max(1, groupKeys.length) * minColPitch;
  if (upperBandW > LAYOUT_W_CAP) {
    minColPitch = Math.max(
      minCenterDist * 1.32,
      (LAYOUT_W_CAP - CLUSTER_PADDING * 2) / Math.max(1, groupKeys.length)
    );
    upperBandW = CLUSTER_PADDING * 2 + groupKeys.length * minColPitch;
  }

  let maxCompactRibbonW = 0;
  for (let b = COMPACT_LAYOUT_MIN_BAND; b <= 4; b++) {
    const arr = bandToEntities.get(b);
    if (arr?.length) {
      maxCompactRibbonW = Math.max(maxCompactRibbonW, computeCompactRibbonWidth(arr.length, minCenterDist));
    }
  }

  let layoutW = Math.min(
    LAYOUT_W_CAP,
    Math.max(initialLayoutW, upperBandW, maxCompactRibbonW)
  );
  const usableW = Math.max(240, layoutW - CLUSTER_PADDING * 2);
  const bandXClampByIndex = new Map();

  function verticalHalfClampForBand(nInBand) {
    if (nInBand <= 1) return Math.max(130, minCenterDist * 1.2);
    const cols = Math.max(4, Math.floor(usableW / (minCenterDist * 1.08)));
    const rows = Math.ceil(nInBand / cols);
    const rowPitch = minCenterDist * 1.12 + ORG_LABEL_VERTICAL_CLEARANCE * 0.42;
    const need = (rows * rowPitch) / 2 + minCenterDist * 0.65;
    return Math.min(layoutH * 0.42, Math.max(140, need));
  }

  let maxVerticalHalf = 0;
  for (const arr of bandToEntities.values()) {
    maxVerticalHalf = Math.max(maxVerticalHalf, verticalHalfClampForBand(arr.length));
  }

  const bandPitch = Math.max(
    BAND_GAP + BAND_VERTICAL_GAP,
    minCenterDist * 2.45,
    maxVerticalHalf * 2 + BAND_VERTICAL_GAP
  );
  const bandClampFloor = Math.max(100, BAND_GAP * 0.36, minCenterDist * 0.52);

  const bandHalfClampByIndex = new Map();
  for (const [b, arr] of bandToEntities) {
    const n = arr.length;
    const base = Math.max(bandClampFloor, verticalHalfClampForBand(n));
    const extra = b === 1
      ? computeCompactBandVerticalHalf(n, minCenterDist * 1.35, layoutH)
      : b >= COMPACT_LAYOUT_MIN_BAND
        ? computeCompactBandVerticalHalf(n, minCenterDist, layoutH)
        : computeBandZigZagVerticalHalf(n, minCenterDist, layoutH);
    bandHalfClampByIndex.set(b, Math.max(base, extra));
  }

  const groupX = new Map();
  groupKeys.forEach((gk, i) => {
    const cx = CLUSTER_PADDING + minColPitch * (i + 0.5);
    groupX.set(gk, cx);
  });

  const positions = {};

  const rels = (relationships || [])
    .filter(r => ids.has(r.source) && ids.has(r.target));

  const topY = CLUSTER_PADDING;
  const pinSep = Math.max(240, minCenterDist * 1.25, rMax * 2.4);
  const apexClearance = rMax * 2.2 + ORG_LABEL_VERTICAL_CLEARANCE + 36;
  positions['president_india'] = { x: layoutW / 2 - pinSep / 2, y: topY };
  positions['supreme_court_india'] = { x: layoutW / 2 + pinSep / 2, y: topY };

  const bandLayoutMeta = new Map();
  bandLayoutMeta.set(0, {
    yMin: topY - rMax,
    yMax: topY + apexClearance,
    xLo: layoutW / 2 - pinSep,
    xHi: layoutW / 2 + pinSep,
  });

  const bandKeys = Array.from(bandToEntities.keys()).sort((a, b) => a - b);
  const centerX = layoutW / 2;
  let cursorY = topY + apexClearance + minCenterDist * APEX_TO_HC_GAP_MULT;

  for (const band of bandKeys) {
    if (band === 0) continue;

    const bandEntities = bandToEntities.get(band) || [];
    const bandClamp = bandHalfClampByIndex.get(band) ?? bandClampFloor;
    const bandBaseY = cursorY;
    const nBand = bandEntities.length;
    if (!nBand) continue;

    if (band === 1) {
      const scCenter = positions['supreme_court_india']?.x ?? centerX;
      const jud = layoutJudiciaryScatterBand({
        bandEntities,
        clusterTopY: cursorY,
        centerX: scCenter,
        minCenterDist,
      });
      bandXClampByIndex.set(band, { lo: jud.xLo, hi: jud.xHi });
      bandLayoutMeta.set(band, {
        yMin: jud.yMin,
        yMax: jud.yMax + ORG_LABEL_VERTICAL_CLEARANCE,
        xLo: jud.xLo,
        xHi: jud.xHi,
      });
      for (const [id, pos] of Object.entries(jud.positions)) {
        if (!positions[id]) positions[id] = pos;
      }
      cursorY = jud.yMax + minCenterDist * 2.4 + BAND_VERTICAL_GAP;
      const districtBottom = layoutDistrictCourtsUnderParentHc({
        entities,
        positions,
        minCenterDist,
        districtBandTopY: cursorY,
      });
      cursorY = Math.max(cursorY, districtBottom) + BAND_VERTICAL_GAP;
      continue;
    }

    if (band >= COMPACT_LAYOUT_MIN_BAND) {
      const compact = layoutCompactBand({
        bandEntities,
        bandBaseY,
        centerX,
        minCenterDist,
        bandClamp,
        getGroup,
      });
      bandXClampByIndex.set(band, { lo: compact.xLo, hi: compact.xHi });
      let yMax = bandBaseY;
      for (const [id, pos] of Object.entries(compact.positions)) {
        if (!positions[id]) positions[id] = pos;
        yMax = Math.max(yMax, pos.y);
      }
      bandLayoutMeta.set(band, {
        yMin: bandBaseY - bandClamp,
        yMax: yMax + ORG_LABEL_VERTICAL_CLEARANCE,
        xLo: compact.xLo,
        xHi: compact.xHi,
      });
      cursorY = yMax + minCenterDist * 1.8 + BAND_VERTICAL_GAP;
      continue;
    }

    const { rowCount, rowPitch } = computeBandZigZagLayout(nBand, minCenterDist, bandClamp);
    const spreadY = Math.min(bandClamp * 1.85, bandClamp + Math.sqrt(Math.max(0, nBand)) * 14);
    const xJitter = nBand > 80 ? 36 : 58;

    const orderedBand = [...bandEntities].sort((a, b) => {
      const ga = getGroup(a) || '';
      const gb = getGroup(b) || '';
      if (ga !== gb) return ga.localeCompare(gb);
      if (getRank(a) !== getRank(b)) return getRank(a) - getRank(b);
      return (a.id || '').localeCompare(b.id || '');
    });

    const nodes = orderedBand.map((e, idx) => {
      const pinned = positions[e.id];
      const gx = groupX.get(getGroup(e)) ?? centerX;
      let yTarget = bandBaseY;
      let xNudge = 0;
      if (rowCount > 1 && rowPitch > 0) {
        const zigRow = idx % rowCount;
        yTarget = bandBaseY + (zigRow - (rowCount - 1) / 2) * rowPitch;
        xNudge = ((zigRow % 2) * 2 - 1) * minCenterDist * 0.28;
      }
      const x0 = pinned?.x ?? gx + xNudge + (Math.random() - 0.5) * xJitter * 0.55;
      const yJ = rowCount > 1 ? rowPitch * 0.38 : spreadY;
      const y0 = pinned?.y ?? (yTarget + (Math.random() - 0.5) * yJ);
      return {
        id: e.id,
        ref: e,
        x: x0,
        y: y0,
        _group: getGroup(e),
        _rank: getRank(e),
        _yTarget: yTarget,
        _xNudge: xNudge,
      };
    });
    const byId = new Map(nodes.map(n => [n.id, n]));

    const links = rels
      .filter(r => (byId.has(r.source) && byId.has(r.target)))
      .map(r => ({ ...r, source: byId.get(r.source), target: byId.get(r.target) }));

    const linkDist = Math.max(112, minCenterDist * 1.08);
    const charge = -Math.max(520, minCenterDist * 14);
    const collideR = minCenterDist * 0.58;
    const yStrength = nBand > 80 ? 0.055 : nBand > 35 ? 0.075 : 0.1;
    const linkStrength = nBand > 120 ? 0.34 : 0.5;
    const sim = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(linkDist).strength(linkStrength))
      .force('charge', d3.forceManyBody().strength(charge))
      .force('collide', d3.forceCollide().radius(() => collideR).iterations(7))
      .force('x', d3.forceX(d => (groupX.get(d._group) ?? centerX) + (d._xNudge || 0)).strength(0.2))
      .force('y', d3.forceY(d => d._yTarget).strength(yStrength))
      .stop();

    const simTicks = nBand > 120 ? 520 : nBand > 70 ? 400 : 300;
    for (let i = 0; i < simTicks; i++) sim.tick();

    for (const n of nodes) {
      if (positions[n.id]) continue;
      const y = Math.max(bandBaseY - bandClamp, Math.min(bandBaseY + bandClamp, n.y));
      positions[n.id] = { x: n.x, y };
    }
  }

  const overlapEntities = entities.filter(e => !districtLatticePinned.has(e.id));
  resolveOverlapsByBand({
    entities: overlapEntities,
    positions,
    bandIndexById,
    layoutW,
    layoutH,
    minDist: minCenterDist,
    bandPitch,
    bandHalfClampByIndex,
    bandClampFloor,
    bandXClampByIndex,
    bandLayoutMeta,
  });

  return { positions, layoutW, layoutH };
}

function resolveOverlapsByBand({
  entities,
  positions,
  bandIndexById,
  layoutW,
  layoutH,
  minDist,
  bandPitch,
  bandHalfClampByIndex,
  bandClampFloor,
  bandXClampByIndex,
  bandLayoutMeta,
}) {
  const pitch = bandPitch ?? (BAND_GAP + 40);
  const bands = new Map();
  const byEntity = new Map(entities.map(e => [e.id, e]));
  for (const e of entities) {
    const b = bandIndexById.get(e.id) ?? 3;
    if (!positions[e.id]) continue;
    if (!bands.has(b)) bands.set(b, []);
    bands.get(b).push(e.id);
  }

  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

  for (const [band, ids] of bands.entries()) {
    if (ids.length < 2) continue;
    const meta = bandLayoutMeta?.get(band);
    const bandBaseY = CLUSTER_PADDING + band * pitch;
    const bandClamp = bandHalfClampByIndex?.get(band)
      ?? Math.max(bandClampFloor ?? 120, pitch * 0.38, minDist * 0.55);
    const yMin = meta?.yMin ?? bandBaseY - bandClamp;
    const yMax = meta?.yMax ?? Math.min(bandBaseY + bandClamp, layoutH - 80);

    for (let iter = 0; iter < 380; iter++) {
      let moved = 0;
      for (let i = 0; i < ids.length; i++) {
        for (let j = i + 1; j < ids.length; j++) {
          const aId = ids[i], bId = ids[j];
          const a = positions[aId], bpos = positions[bId];
          if (!a || !bpos) continue;
          const ea = byEntity.get(aId);
          const eb = byEntity.get(bId);
          if (!ea || !eb) continue;
          const need = effectiveNodeLayoutRadius(ea) + effectiveNodeLayoutRadius(eb) + 14;
          let dx = bpos.x - a.x;
          let dy = bpos.y - a.y;
          const dist = Math.hypot(dx, dy) || 0.0001;
          if (dist >= need) continue;

          const push = (need - dist) * 0.5;
          dx /= dist; dy /= dist;
          a.x -= dx * push; a.y -= dy * push;
          bpos.x += dx * push; bpos.y += dy * push;
          moved++;
        }
      }

      const xClamp = bandXClampByIndex?.get(band);
      const xLo = meta?.xLo ?? xClamp?.lo ?? 56;
      const xHi = meta?.xHi ?? xClamp?.hi ?? layoutW - 56;

      for (const id of ids) {
        const p = positions[id];
        if (!p) continue;
        if (band === 0) continue;
        p.x = clamp(p.x, xLo, xHi);
        p.y = clamp(p.y, yMin, yMax);
      }

      if (moved === 0) break;
    }
  }
}

/**
 * Fit the org-chart content into the visible canvas (map-style “whole map” view).
 * No-op when not using org layout or bounds unknown.
 */
/** Pan/zoom to a principal HC plus its district lattice (after blue + expand). */
export function fitGraphToEntityFocus(entityId, opts = {}) {
  if (!State._zoomSvg?.node || !State._zoom) return;
  const posMap = buildPositionMap();
  const focusIds = new Set([entityId]);
  const dg = State.districtGroupForPrincipalHc?.(entityId);
  if (dg) {
    if (State.expandedDistrictAggregateIds?.has(dg.groupId)) {
      for (const mid of dg.memberIds) focusIds.add(mid);
    } else if (dg.proxyId) {
      focusIds.add(dg.proxyId);
    } else {
      focusIds.add(`__jem_agg_${dg.stateCode}_district_courts`);
    }
  }
  for (const kid of State._childrenByParent?.[entityId] || []) focusIds.add(kid);

  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const id of focusIds) {
    const p = posMap[id];
    if (!p) continue;
    const e = State.getEntityById(id);
    const pad = (e ? effectiveNodeLayoutRadius(e) : 36) + ORG_LABEL_VERTICAL_CLEARANCE + 24;
    minX = Math.min(minX, p.x - pad);
    maxX = Math.max(maxX, p.x + pad);
    minY = Math.min(minY, p.y - pad);
    maxY = Math.max(maxY, p.y + pad);
  }
  if (!Number.isFinite(minX)) {
    fitGraphToViewport(opts);
    return;
  }

  const dur = opts.duration ?? 280;
  const margin = opts.margin ?? 0.9;
  const container = document.getElementById('canvas-container');
  const vw = container?.clientWidth || width || 800;
  const vh = container?.clientHeight || height || 600;
  const bw = Math.max(220, maxX - minX);
  const bh = Math.max(220, maxY - minY);
  const cx = (minX + maxX) / 2;
  const cy = (minY + maxY) / 2;
  const scale0 = margin * Math.min(vw / bw, vh / bh);
  const ext = State._zoom.scaleExtent();
  const k = Math.max(ext[0], Math.min(ext[1], scale0));
  const tx = vw / 2 - k * cx;
  const ty = vh / 2 - k * cy;
  const t = d3.zoomIdentity.translate(tx, ty).scale(k);
  const svgNode = State._zoomSvg.node();
  if (dur <= 0) {
    State._zoomSvg.call(State._zoom.transform, t);
    State.setTransform(d3.zoomTransform(svgNode));
  } else {
    State._zoomSvg.transition().duration(dur).call(State._zoom.transform, t)
      .on('end', () => State.setTransform(d3.zoomTransform(svgNode)));
  }
}

export function fitGraphToViewport(opts = {}) {
  if (!lastGraphContentBounds || !State._zoomSvg?.node || !State._zoom) return;
  const dur = opts.duration ?? 0;
  const margin = opts.margin ?? 0.9;
  const container = document.getElementById('canvas-container');
  const vw = container?.clientWidth || width || 800;
  const vh = container?.clientHeight || height || 600;
  const b = lastGraphContentBounds;
  const bw = Math.max(180, b.maxX - b.minX);
  const bh = Math.max(180, b.maxY - b.minY);
  const cx = (b.minX + b.maxX) / 2;
  const cy = (b.minY + b.maxY) / 2;
  const scale0 = margin * Math.min(vw / bw, vh / bh);
  const ext = State._zoom.scaleExtent();
  const k = Math.max(ext[0], Math.min(ext[1], scale0));
  const tx = vw / 2 - k * cx;
  const ty = vh / 2 - k * cy;
  const t = d3.zoomIdentity.translate(tx, ty).scale(k);
  const svgNode = State._zoomSvg.node();
  if (dur <= 0) {
    State._zoomSvg.call(State._zoom.transform, t);
    State.setTransform(d3.zoomTransform(svgNode));
  } else {
    State._zoomSvg.transition().duration(dur).call(State._zoom.transform, t)
      .on('end', () => {
        State.setTransform(d3.zoomTransform(svgNode));
      });
  }
}

function buildPositionMap() {
  const map = {};
  if (!State.graph) return map;
  for (const e of State.getVisibleEntities()) {
    const n = simNodesById.get(e.id);
    if (n) map[e.id] = { x: n.x, y: n.y };
    else if (e.position) map[e.id] = { ...e.position };
  }
  return map;
}

function curvePath(x1, y1, x2, y2) {
  // Cubic bezier — offset control points perpendicular to the line
  const dx = x2 - x1;
  const dy = y2 - y1;
  const dr = Math.sqrt(dx * dx + dy * dy) * 0.4;
  // Slight arc
  return `M${x1},${y1} Q${(x1+x2)/2 + dy*0.2},${(y1+y2)/2 - dx*0.2} ${x2},${y2}`;
}

function govLevelFill(level) {
  switch(level) {
    case 'Central': return '#1a3a5c';
    case 'State': return '#1a4a2a';
    case 'UT': return '#3a2a4a';
    case 'Shared_MultiState': return '#3a2a1a';
    case 'Shared_CentralState': return '#2a3a1a';
    default: return '#2d2d2d';
  }
}

/** Fills for constitutional / civil court rectangles (slightly lifted from gov circles for in-box labels). */
function judicialBodyFill(level) {
  switch (level) {
    case 'Central': return '#1e3d63';
    case 'State': return '#1d4a2e';
    case 'UT': return '#3a2850';
    case 'Shared_MultiState': return '#3a2418';
    case 'Shared_CentralState': return '#263818';
    default: return '#2a2a2a';
  }
}

/** Tribunals, regulators, arbitration — distinct muted tones by cluster. */
function alliedBodyFill(d) {
  if (d.cluster === 'arbitration') return '#243448';
  if (d.cluster === 'regulatory_bodies') return '#352d40';
  if (d.cluster === 'tribunals_adr') return '#1a4550';
  return '#2c3542';
}

function stakeholderNodeFill(level) {
  const base = govLevelFill(level);
  // Softer than bench nodes so circles read as “actors / institutions” not courts.
  return base === '#2d2d2d' ? '#353545' : base;
}

function irLevel(score) {
  if (score <= 2) return 'low';
  if (score <= 5) return 'moderate';
  if (score <= 8) return 'high';
  return 'severe';
}

function irColor(score) {
  const colors = State.graph ? State.getIndependenceRiskColors() : {};
  return colors[irLevel(score)] || '#27ae60';
}

function formatRelType(type) {
  return type.replace(/_/g, ' ').toLowerCase();
}

function zoomToCluster(cluster) {
  // Programmatically zoom so the cluster fills the viewport
  // This transitions from L0 to L1
  const svgEl = document.getElementById('main-svg');
  const zoom = d3.zoom().on('zoom', (event) => {
    root.attr('transform', event.transform);
    State.setTransform(event.transform);
  });
  d3.select(svgEl).call(
    zoom.transform,
    d3.zoomIdentity.translate(width/2, height/2).scale(0.6)
  );
  State.setZoomLevel(1);
  render();
}

function showEdgeTooltip(event, d) {
  // Simple tooltip — could be enhanced
  const existing = document.getElementById('edge-tooltip');
  if (existing) existing.remove();
  const t = document.createElement('div');
  t.id = 'edge-tooltip';
  t.style.cssText = `position:fixed;left:${event.clientX+12}px;top:${event.clientY-20}px;
    background:#1a1a2e;color:#eee;padding:6px 10px;border-radius:6px;
    font-size:11px;pointer-events:none;z-index:1000;max-width:260px;
    border:1px solid #444;`;
  t.innerHTML = `<strong>${formatRelType(d.relationship_type)}</strong>
    ${d.is_constitutional ? '<span style="color:#27ae60"> ⊕ Constitutional</span>' : ''}
    ${d.is_binding ? '<span style="color:#e67e22"> ⊕ Binding</span>' : ''}
    ${d.notes ? `<br><small style="color:#aaa">${d.notes.slice(0,120)}…</small>` : ''}
    ${d.year_abolished ? `<br><small style="color:#e74c3c">Abolished ${d.year_abolished}</small>` : ''}`;
  document.body.appendChild(t);
}

let tooltipHideTimer = null;

function cancelTooltipHide() {
  if (tooltipHideTimer) {
    clearTimeout(tooltipHideTimer);
    tooltipHideTimer = null;
  }
}

/** Lets the cursor move onto the tooltip to scroll before it closes. */
function scheduleHideTooltip(ms = 220) {
  cancelTooltipHide();
  tooltipHideTimer = setTimeout(() => {
    tooltipHideTimer = null;
    hideTooltip();
  }, ms);
}

function clampTooltipToViewport(el, event) {
  const margin = 10;
  const w = el.offsetWidth || 320;
  const h = el.offsetHeight || 200;
  let left = event.clientX + 14;
  let top = event.clientY - 18;
  if (left + w > window.innerWidth - margin) left = window.innerWidth - w - margin;
  if (left < margin) left = margin;
  if (top + h > window.innerHeight - margin) top = window.innerHeight - h - margin;
  if (top < margin) top = margin;
  el.style.left = `${left}px`;
  el.style.top = `${top}px`;
}

function wireTooltipPointerHold(el) {
  el.addEventListener('mouseenter', cancelTooltipHide);
  el.addEventListener('mouseleave', () => scheduleHideTooltip(200));
}

function hideTooltip() {
  cancelTooltipHide();
  const t = document.getElementById('edge-tooltip');
  if (t) t.remove();
}

function htmlIndependenceRiskBreakdown(breakdown) {
  if (!breakdown || typeof breakdown !== 'object') return '';
  const rows = Object.entries(breakdown)
    .sort((a, b) => b[1] - a[1])
    .map(([reason, pts]) => {
      const sign = pts >= 0 ? '+' : '';
      const cls = pts > 0 ? '#e74c3c' : '#16a34a';
      return `<div style="display:flex;gap:8px;font-size:11px;padding:2px 0">
        <span style="font-family:var(--font-mono,monospace);min-width:32px;font-weight:700;color:${cls}">${sign}${pts}</span>
        <span style="color:#4b5563;line-height:1.35">${reason}</span>
      </div>`;
    })
    .join('');
  return `<div style="margin-top:8px;padding:8px;border-radius:6px;background:rgba(17,24,39,0.04)">${rows}</div>`;
}

function showNodeRelationshipsTooltip(event, node, rels) {
  hideTooltip();

  const t = document.createElement('div');
  t.id = 'edge-tooltip';
  t.className = 'graph-hover-tooltip';
  t.style.cssText = [
    'position:fixed',
    'left:0',
    'top:0',
    'background:#ffffff',
    'color:#111827',
    'padding:0',
    'border-radius:10px',
    'font-size:12px',
    'pointer-events:auto',
    'z-index:1200',
    'max-width:min(440px,calc(100vw - 24px))',
    'max-height:min(78vh,640px)',
    'border:1px solid rgba(17,24,39,0.12)',
    'box-shadow:0 12px 30px rgba(17,24,39,0.14)',
    'display:flex',
    'flex-direction:column',
    'overflow:hidden',
  ].join(';');

  if (State.viewMode === 'risk') {
    const derived = node.derived || {};
    const irColors = State.getIndependenceRiskColors();
    const level = derived.independence_risk_level || 'unknown';
    const score = derived.independence_risk_score;
    const levelColor = irColors[level] || '#6b7280';
    let html = `<div style="flex-shrink:0;padding:10px 12px 0;font-weight:700">${node.abbreviation || node.name}</div>`;
    html += `<div style="flex-shrink:0;font-size:11px;color:#6b7280;margin-bottom:4px;padding:0 12px">Independence risk</div>`;
    html += `<div style="flex-shrink:0;display:flex;align-items:baseline;gap:10px;margin-bottom:4px;padding:0 12px">
      <span style="font-size:20px;font-weight:800;font-family:var(--font-mono,monospace)">${score ?? '—'}</span>
      <span style="font-size:11px;font-weight:700;color:${levelColor}">${(level || '').toUpperCase()}</span>
    </div>`;
    html += `<div class="graph-hover-tooltip-body" style="flex:1;min-height:0;overflow-y:auto;overflow-x:hidden;overscroll-behavior:contain;padding:0 12px 12px">`;
    html += htmlIndependenceRiskBreakdown(derived.independence_risk_breakdown);
    html += '</div>';
    t.innerHTML = html;
    document.body.appendChild(t);
    wireTooltipPointerHold(t);
    requestAnimationFrame(() => {
      clampTooltipToViewport(t, event);
      requestAnimationFrame(() => clampTooltipToViewport(t, event));
    });
    return;
  }

  const connected = rels.filter(r => r.source === node.id || r.target === node.id);
  if (!connected.length) return;

  const byCat = new Map();
  connected.forEach(r => {
    const cat = r.relationship_category || 'other';
    if (!byCat.has(cat)) byCat.set(cat, []);
    byCat.get(cat).push(r);
  });

  const lookupName = (id) => (State.getEntityById(id)?.abbreviation || State.getEntityById(id)?.name || id);
  const catTitle = (c) => (c || '').replace(/_/g, ' ');
  const relTitle = (r) => (r.relationship_type || '').replace(/_/g, ' ');

  let html = `<div style="flex-shrink:0;padding:10px 12px 0;font-weight:700">${node.abbreviation || node.name}</div>`;
  html += `<div style="flex-shrink:0;color:#6b7280;font-size:11px;margin-bottom:6px;padding:0 12px">${connected.length} relationship(s)</div>`;
  html += '<div class="graph-hover-tooltip-body" style="flex:1;min-height:0;overflow-y:auto;overflow-x:hidden;overscroll-behavior:contain;padding:0 10px 12px 12px">';
  for (const [cat, items] of byCat.entries()) {
    html += `<div style="margin:8px 0 4px 0;font-size:11px;color:#374151;font-weight:700">${catTitle(cat)}</div>`;
    for (const r of items) {
      const other = r.source === node.id ? r.target : r.source;
      html += `<div style="font-size:11px;color:#111827;line-height:1.45;padding:2px 0">
        <span style="color:#6b7280">${relTitle(r)}</span> → <span style="font-weight:600">${lookupName(other)}</span>
      </div>`;
    }
  }
  html += '</div>';
  t.innerHTML = html;
  document.body.appendChild(t);
  wireTooltipPointerHold(t);
  requestAnimationFrame(() => {
    clampTooltipToViewport(t, event);
    requestAnimationFrame(() => clampTooltipToViewport(t, event));
  });
}

// Click on background: deselect
document.addEventListener('click', (e) => {
  if (e.target.id === 'main-svg' || e.target === document.getElementById('canvas-container')) {
    State.clearEntity();
  }
});
