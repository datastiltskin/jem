// JEM — Focused neighborhood graph (ego network only)
// Opens with the detail panel: parents, children, supervision, and every direct link.

import { State } from './state.js';
import { buildEntityConnectionSummary, formatCategoryLabel } from './entityConnections.js';
import { crescentPathD, isHighCourtBenchEntity } from './nodeShapes.js';

let sim = null;
let resizeObs = null;
let nbZoom = null;
let nbZoomTransform = null;
let lastNbNodes = null;
let currentFocusId = null;
let renderGeneration = 0;
let activeLinkFilter = 'all';

function relColor(cat) {
  const map = State.getRelationshipColors() || {};
  return map[cat] || '#64748b';
}

function nodeFill(e) {
  const lv = e.level_of_government || 'Central';
  if (lv === 'Central') return '#1e3d63';
  if (lv === 'State') return '#1d4a2e';
  if (lv === 'UT') return '#3a2850';
  if (lv === 'Shared_MultiState') return '#3a2418';
  if (lv === 'Shared_CentralState') return '#263818';
  return '#2d3436';
}

function labelLines(e) {
  const abbr = (e.abbreviation || '').trim();
  const name = (e.name || e.id || '').trim();
  if (abbr && abbr !== name) {
    return [abbr, name.length > 36 ? `${name.slice(0, 34)}…` : name];
  }
  if (name.length > 38) return [name.slice(0, 36) + '…'];
  return [name];
}

function linkMatchesFilter(rel, focusId, filter) {
  if (filter === 'all') return true;
  const cat = rel.relationship_category;
  if (filter === 'appellate_toward') {
    return cat === 'appellate_chain' && rel.source === focusId;
  }
  if (filter === 'appellate_from') {
    return cat === 'appellate_chain' && rel.target === focusId;
  }
  if (filter === 'supervises') {
    return cat === 'supervisory' && rel.source === focusId;
  }
  if (filter === 'supervised_by') {
    return cat === 'supervisory' && rel.target === focusId;
  }
  if (filter === 'other') {
    return cat !== 'appellate_chain' && cat !== 'supervisory';
  }
  return true;
}

function edgePath(x1, y1, x2, y2) {
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const dx = x2 - x1;
  const dy = y2 - y1;
  return `M${x1},${y1} Q${mx + dy * 0.15},${my - dx * 0.12} ${x2},${y2}`;
}

function getNeighborhoodViewSize() {
  const scrollEl = document.getElementById('neighborhood-graph-scroll');
  return {
    w: Math.max(280, scrollEl?.clientWidth || 480),
    h: Math.max(200, scrollEl?.clientHeight || 320),
  };
}

function computeNodeContentBounds(nodes, focusId, pad = 56) {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const n of nodes) {
    const r = n.id === focusId ? 28 : 22;
    const lines = labelLines(n.entity);
    const labelH = 12 * lines.length + 10;
    const labelBelow = n.id === focusId ? 38 : 28;
    minX = Math.min(minX, n.x - r - 12);
    maxX = Math.max(maxX, n.x + r + 12);
    minY = Math.min(minY, n.y - r - 12);
    maxY = Math.max(maxY, n.y + r + labelBelow + labelH);
  }
  if (!Number.isFinite(minX)) return null;
  return {
    minX: minX - pad,
    minY: minY - pad,
    maxX: maxX + pad,
    maxY: maxY + pad,
    cx: (minX + maxX) / 2,
    cy: (minY + maxY) / 2,
    width: Math.max(120, maxX - minX + pad * 2),
    height: Math.max(120, maxY - minY + pad * 2),
  };
}

function fitNeighborhoodTransform(nodes, focusId, viewW, viewH) {
  const b = computeNodeContentBounds(nodes, focusId);
  if (!b) return d3.zoomIdentity;
  const k = 0.9 * Math.min(viewW / b.width, viewH / b.height);
  const tx = viewW / 2 - k * b.cx;
  const ty = viewH / 2 - k * b.cy;
  return d3.zoomIdentity.translate(tx, ty).scale(k);
}

function applyNeighborhoodZoomTransform(svgEl, _root, transform, animate = false) {
  const svgNode = d3.select(svgEl);
  const liveRoot = d3.select(svgEl).select('.nb-root');
  nbZoomTransform = transform;
  if (!nbZoom) {
    if (!liveRoot.empty()) liveRoot.attr('transform', transform);
    return;
  }
  if (animate) {
    svgNode.transition().duration(220).call(nbZoom.transform, transform);
  } else {
    svgNode.call(nbZoom.transform, transform);
  }
  if (!liveRoot.empty()) liveRoot.attr('transform', transform);
}

function resetNeighborhoodZoomFit() {
  const svg = document.getElementById('neighborhood-svg');
  if (!svg || !lastNbNodes?.length || !currentFocusId) return;
  const { w, h } = getNeighborhoodViewSize();
  const t = fitNeighborhoodTransform(lastNbNodes, currentFocusId, w, h);
  const root = d3.select(svg).select('.nb-root');
  applyNeighborhoodZoomTransform(svg, root, t, true);
}

function neighborhoodZoomBy(factor) {
  const svg = document.getElementById('neighborhood-svg');
  if (!svg || !nbZoom) return;
  d3.select(svg).transition().duration(180).call(nbZoom.scaleBy, factor);
}

function runLayout(svgEl, entities, rels, focusId, filter, { resetZoom = false } = {}) {
  if (sim) {
    sim.stop();
    sim = null;
  }
  d3.select(svgEl).selectAll('*').remove();

  const { w: viewW, h: viewH } = getNeighborhoodViewSize();
  svgEl.setAttribute('width', String(viewW));
  svgEl.setAttribute('height', String(viewH));
  svgEl.removeAttribute('viewBox');

  const W = viewW;
  const H = viewH;
  const cx = W / 2;
  const cy = H / 2;

  const root = d3.select(svgEl).append('g').attr('class', 'nb-root');

  root.append('defs')
    .append('marker')
    .attr('id', 'nb-arrow')
    .attr('viewBox', '0 0 10 10')
    .attr('refX', 9)
    .attr('refY', 5)
    .attr('markerWidth', 5)
    .attr('markerHeight', 5)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M 0 0 L 10 5 L 0 10 z')
    .attr('fill', '#94a3b8');

  const nodes = entities.map(e => ({
    id: e.id,
    entity: e,
    x: cx + (Math.random() - 0.5) * 30,
    y: cy + (Math.random() - 0.5) * 30,
  }));

  const nById = new Map(nodes.map(n => [n.id, n]));
  const links = rels
    .filter(r => nById.has(r.source) && nById.has(r.target))
    .filter(r => linkMatchesFilter(r, focusId, filter))
    .map(r => ({
      ...r,
      source: nById.get(r.source),
      target: nById.get(r.target),
    }));

  const focusNode = nById.get(focusId);
  if (focusNode) {
    focusNode.fx = cx;
    focusNode.fy = cy;
  }

  const linkPaths = root.append('g')
    .attr('class', 'nb-links')
    .selectAll('path')
    .data(links)
    .join('path')
    .attr('class', 'nb-edge')
    .attr('fill', 'none')
    .attr('stroke-width', 2)
    .attr('stroke-opacity', 0.92)
    .attr('marker-end', 'url(#nb-arrow)')
    .attr('stroke', d => relColor(d.relationship_category))
    .attr('d', d => edgePath(d.source.x, d.source.y, d.target.x, d.target.y))
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation();
      showLinkDetail(d);
    });

  linkPaths.append('title')
    .text(d => {
      const other = d.source.id === focusId ? d.target.entity : d.source.entity;
      const dir = d.source.id === focusId ? '→' : '←';
      return `${d.relationship_category} — ${d.relationship_type}\n${dir} ${other.name || other.id}${d.notes ? '\n' + String(d.notes).slice(0, 200) : ''}`;
    });

  const nodeG = root.append('g')
    .attr('class', 'nb-nodes')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .attr('class', d => `nb-node ${d.id === focusId ? 'nb-focus' : ''}`)
    .style('cursor', d => (d.id === focusId ? 'default' : 'pointer'))
    .on('click', (event, d) => {
      event.stopPropagation();
      if (d.id !== focusId) selectNeighborEntity(d.entity);
    });

  nodeG.each(function (d) {
    const g = d3.select(this);
    const r = d.id === focusId ? 24 : 15;
    const fill = nodeFill(d.entity);
    const stroke = d.id === focusId ? '#f1c40f' : '#94a3b8';
    const sw = d.id === focusId ? 2.5 : 1.2;
    if (isHighCourtBenchEntity(d.entity)) {
      g.append('path')
        .attr('class', 'nb-node-crescent')
        .attr('fill-rule', 'evenodd')
        .attr('d', crescentPathD(r))
        .attr('fill', fill)
        .attr('stroke', stroke)
        .attr('stroke-width', sw);
    } else {
      g.append('circle')
        .attr('r', r)
        .attr('fill', fill)
        .attr('stroke', stroke)
        .attr('stroke-width', sw);
    }
  });

  nodeG.each(function (d) {
    const g = d3.select(this);
    const lines = labelLines(d.entity);
    const lineHeight = 11;
    const startDy = d.id === focusId ? 38 : 28;
    const text = g.append('text')
      .attr('class', 'nb-label')
      .attr('text-anchor', 'middle')
      .attr('font-size', d.id === focusId ? 10.5 : 9.5)
      .attr('font-weight', d.id === focusId ? 700 : 500);
    lines.forEach((line, i) => {
      text.append('tspan')
        .attr('x', 0)
        .attr('dy', i === 0 ? startDy : lineHeight)
        .text(line);
    });
  });

  const n = nodes.length;
  const linkDist = Math.max(140, 118 + n * 4);
  const linkForce = d3.forceLink(links).id(d => d.id).distance(linkDist).strength(0.5);
  const charge = d3.forceManyBody().strength(-320 - n * 8);
  const collide = d3.forceCollide().radius(d => (d.id === focusId ? 38 : 28)).iterations(5);

  sim = d3.forceSimulation(nodes)
    .force('link', linkForce)
    .force('charge', charge)
    .force('collide', collide)
    .force('center', d3.forceCenter(cx, cy).strength(0.06))
    .alphaDecay(0.045)
    .velocityDecay(0.38);

  for (let i = 0; i < 360; i++) sim.tick();

  nodeG.attr('transform', d => `translate(${d.x},${d.y})`);
  linkPaths.attr('d', d => edgePath(d.source.x, d.source.y, d.target.x, d.target.y));

  sim.stop();
  sim = null;

  lastNbNodes = nodes;

  const svgNode = d3.select(svgEl);
  if (!nbZoom) {
    nbZoom = d3.zoom()
      .scaleExtent([0.15, 6])
      .filter((event) => {
        if (event.type === 'wheel') return true;
        if (event.type === 'mousedown') return event.button === 0;
        if (event.type === 'touchstart') return true;
        return false;
      })
      .on('zoom', (event) => {
        const liveRoot = d3.select(svgEl).select('.nb-root');
        if (!liveRoot.empty()) liveRoot.attr('transform', event.transform);
        nbZoomTransform = event.transform;
      });
    svgNode.call(nbZoom).on('dblclick.zoom', resetNeighborhoodZoomFit);
  }

  const t = resetZoom || !nbZoomTransform
    ? fitNeighborhoodTransform(nodes, focusId, viewW, viewH)
    : nbZoomTransform;
  applyNeighborhoodZoomTransform(svgEl, root, t, false);
}

function showLinkDetail(rel) {
  const el = document.getElementById('neighborhood-link-detail');
  if (!el || !rel) return;
  const focus = State.getEntityById(currentFocusId);
  const other = rel.source.id === currentFocusId ? rel.target.entity : rel.source.entity;
  const dir = rel.source.id === currentFocusId ? 'Outgoing' : 'Incoming';
  el.innerHTML = `
    <strong>${formatCategoryLabel(rel.relationship_category)}</strong> · ${rel.relationship_type || 'link'}
    <span class="nb-link-detail-dir">${dir}</span>
    <button type="button" class="nb-link-jump" data-entity-id="${other.id}">${other.name || other.id}</button>
    ${rel.notes ? `<p class="nb-link-note">${String(rel.notes).slice(0, 280)}</p>` : ''}
  `;
  el.classList.remove('hidden');
  el.querySelector('.nb-link-jump')?.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    selectNeighborEntity(other);
  });
}

async function selectNeighborEntity(entity) {
  if (!entity?.id) return;
  const { openDetailPanel } = await import('./panel.js');
  State.selectEntity(entity.id);
  openDetailPanel(entity);
}

function renderLinksList(summary, focusEntity) {
  const el = document.getElementById('neighborhood-links');
  if (!el) return;

  const groups = [
    { key: 'appellate_toward', title: 'Appellate toward (higher court / body)', rows: summary.appellateToward },
    { key: 'appellate_from', title: 'Appellate from (lower court / body)', rows: summary.appellateFrom },
    { key: 'supervises', title: 'Supervises', rows: summary.supervises },
    { key: 'supervised_by', title: 'Supervised by', rows: summary.supervisedBy },
  ];

  let html = `<div id="neighborhood-link-detail" class="neighborhood-link-detail hidden"></div>`;

  for (const g of groups) {
    if (!g.rows.length) continue;
    html += `<div class="nb-links-group"><div class="nb-links-group-title">${g.title}</div>`;
    for (const row of g.rows) {
      html += `<button type="button" class="nb-link-row" data-entity-id="${row.entityId}" data-filter="${g.key}">
        <span class="nb-link-row-name">${row.entityName}</span>
        <span class="nb-link-row-meta">${row.type} · ${formatCategoryLabel(row.category)}</span>
      </button>`;
    }
    html += '</div>';
  }

  const otherCats = [...summary.byCategory.entries()];
  if (otherCats.length) {
    html += '<div class="nb-links-group"><div class="nb-links-group-title">Other relationships</div>';
    for (const [cat, rows] of otherCats) {
      for (const row of rows) {
        html += `<button type="button" class="nb-link-row" data-entity-id="${row.entityId}" data-filter="other">
          <span class="nb-link-row-name">${row.entityName}</span>
          <span class="nb-link-row-meta">${row.directionLabel} · ${row.type}</span>
        </button>`;
      }
    }
    html += '</div>';
  }

  if (!summary.all.length) {
    html += '<p class="nb-links-empty">No direct relationships in graph data for this entity.</p>';
  }

  el.innerHTML = html;

  el.querySelectorAll('.nb-link-row').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const id = btn.getAttribute('data-entity-id');
      const ent = State.getEntityById(id);
      if (ent) selectNeighborEntity(ent);
    });
  });
}

function updateLegend(summary) {
  const el = document.getElementById('neighborhood-legend');
  if (!el) return;

  const items = [
    { id: 'all', label: 'All', count: summary.all.length },
    { id: 'appellate_toward', label: 'Appellate toward', count: summary.appellateToward.length, dot: 'nb-leg-parent' },
    { id: 'appellate_from', label: 'Appellate from', count: summary.appellateFrom.length, dot: 'nb-leg-child' },
    { id: 'supervises', label: 'Supervises', count: summary.supervises.length, dot: 'nb-leg-supervise' },
    { id: 'supervised_by', label: 'Supervised by', count: summary.supervisedBy.length, dot: 'nb-leg-supervised' },
    { id: 'other', label: 'Other', count: [...summary.byCategory.values()].reduce((s, a) => s + a.length, 0), dot: 'nb-leg-other' },
  ];

  el.innerHTML = items.map(it => `
    <button type="button" class="nb-leg-btn ${activeLinkFilter === it.id ? 'active' : ''}" data-filter="${it.id}">
      ${it.dot ? `<span class="nb-dot ${it.dot}"></span>` : ''}
      ${it.label} (${it.count})
    </button>
  `).join('');

  el.querySelectorAll('.nb-leg-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      activeLinkFilter = btn.getAttribute('data-filter') || 'all';
      scheduleNeighborhoodRender({ resetZoom: true });
    });
  });
}

function buildEgoEntities(summary, focusId) {
  const ids = new Set([focusId]);
  for (const row of summary.all) ids.add(row.entityId);
  const entities = [];
  for (const id of ids) {
    const e = State.getEntityById(id);
    if (e) entities.push(e);
  }
  return entities;
}

function updateNeighborhoodChrome(entity, summary) {
  const title = document.getElementById('neighborhood-title');
  const sub = document.getElementById('neighborhood-subtitle');
  if (title) title.textContent = 'Neighborhood';
  if (sub) {
    if (!summary.all.length) {
      sub.textContent = `${entity.name || entity.id} — no direct neighbors in graph data yet; only this entity appears in the mini-map. Links will show here as relationships are added.`;
    } else {
      sub.textContent = `${entity.name || entity.id} — direct links only. Drag to pan; scroll wheel or +/− to zoom; click a node or row, or use legend filters.`;
    }
  }
  updateLegend(summary);
  renderLinksList(summary, entity);
}

function renderNeighborhoodGraph(generation, options = {}) {
  const panel = document.getElementById('neighborhood-panel');
  const svg = document.getElementById('neighborhood-svg');
  const focusId = currentFocusId;
  if (!panel || !svg || !focusId || panel.classList.contains('hidden')) return false;
  if (generation != null && generation !== renderGeneration) return false;

  const summary = buildEntityConnectionSummary(focusId);
  const entities = buildEgoEntities(summary, focusId);
  const rels = State.graph.relationships.filter(
    r => entities.some(e => e.id === r.source) && entities.some(e => e.id === r.target)
  );

  runLayout(svg, entities, rels, focusId, activeLinkFilter, {
    resetZoom: options.resetZoom === true,
  });
  updateLegend(summary);
  return true;
}

function scheduleNeighborhoodRender(options = {}) {
  const gen = renderGeneration;
  requestAnimationFrame(() => {
    renderNeighborhoodGraph(gen, options);
  });
}

function attachResizeObserver() {
  const panel = document.getElementById('neighborhood-panel');
  const scrollEl = document.getElementById('neighborhood-graph-scroll');
  if (!scrollEl || !panel) return;

  if (resizeObs) {
    resizeObs.disconnect();
    resizeObs = null;
  }

  resizeObs = new ResizeObserver(() => {
    if (panel.classList.contains('hidden') || !currentFocusId) return;
    renderNeighborhoodGraph(renderGeneration, { resetZoom: false });
  });
  resizeObs.observe(scrollEl);
}

export function openNeighborhoodPanel(entity) {
  if (!entity?.id || entity._jemSyntheticAggregate) return;

  const panel = document.getElementById('neighborhood-panel');
  const svg = document.getElementById('neighborhood-svg');
  if (!panel || !svg) return;

  currentFocusId = entity.id;
  activeLinkFilter = 'all';
  nbZoomTransform = d3.zoomIdentity;
  renderGeneration += 1;

  const summary = buildEntityConnectionSummary(entity.id);
  updateNeighborhoodChrome(entity, summary);

  panel.classList.remove('hidden');
  document.body.classList.add('neighborhood-open');

  attachResizeObserver();
  scheduleNeighborhoodRender({ resetZoom: true });
}

export function closeNeighborhoodPanel() {
  const panel = document.getElementById('neighborhood-panel');
  const svg = document.getElementById('neighborhood-svg');
  currentFocusId = null;
  activeLinkFilter = 'all';
  renderGeneration += 1;

  if (sim) {
    sim.stop();
    sim = null;
  }
  if (resizeObs) {
    resizeObs.disconnect();
    resizeObs = null;
  }
  nbZoom = null;
  nbZoomTransform = d3.zoomIdentity;
  lastNbNodes = null;
  if (panel) panel.classList.add('hidden');
  document.body.classList.remove('neighborhood-open');
  if (svg) {
    d3.select(svg).selectAll('*').remove();
    svg.removeAttribute('width');
    svg.removeAttribute('height');
  }
}

export function initNeighborhoodPanel() {
  const panel = document.getElementById('neighborhood-panel');
  const closeBtn = document.getElementById('neighborhood-close');
  const backdrop = panel?.querySelector('.neighborhood-backdrop');

  const stopBubble = (e) => {
    e.preventDefault?.();
    e.stopPropagation?.();
  };

  const bindZoomBtn = (id, handler) => {
    const btn = document.getElementById(id);
    if (!btn) return;
    btn.addEventListener('click', (e) => {
      stopBubble(e);
      handler();
    });
  };
  bindZoomBtn('nb-zoom-in', () => neighborhoodZoomBy(1.35));
  bindZoomBtn('nb-zoom-out', () => neighborhoodZoomBy(1 / 1.35));
  bindZoomBtn('nb-zoom-reset', resetNeighborhoodZoomFit);

  const onClose = (e) => {
    e?.preventDefault?.();
    e?.stopPropagation?.();
    closeNeighborhoodPanel();
  };

  closeBtn?.addEventListener('click', onClose);
  backdrop?.addEventListener('click', onClose);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && panel && !panel.classList.contains('hidden')) {
      closeNeighborhoodPanel();
    }
  });
}
