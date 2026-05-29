// JEM — Entity Detail View
// Independence risk hero + score breakdown + neighborhood graph + gaps + case volume.

import { State } from './state.js';
import { buildPanelHTML } from './panel.js';

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
        <td class="bd-factor">${factor}</td>
        <td class="bd-pts ${isPos ? 'bd-pts-pos' : 'bd-pts-neg'}">${isPos ? '+' : ''}${pts}</td>
      </tr>`;
    }).join('');

  return `<div class="bd-section">
    <div class="bd-title">${label} breakdown</div>
    <table class="bd-table"><tbody>${rows}</tbody></table>
  </div>`;
}

// ── Case volume ───────────────────────────────────────────────────────────────

function renderCaseVolume(cv) {
  if (!cv) return '';
  const stats = [];
  if (cv.pending_cases != null) stats.push(`<span class="cv-stat"><span class="cv-num">${fmtNum(cv.pending_cases)}</span><span class="cv-label"> pending</span></span>`);
  if (cv.disposal_rate != null) stats.push(`<span class="cv-stat"><span class="cv-num">${cv.disposal_rate.toFixed(2)}</span><span class="cv-label"> disposal rate</span></span>`);
  if (cv.clog_severity) stats.push(`<span class="cv-stat"><span class="cv-num" style="color:${clogColor(cv.clog_severity)}">${cv.clog_severity.toUpperCase()}</span><span class="cv-label"> clog</span></span>`);
  if (!stats.length) return '';
  const asOf = cv.data_as_of ? `<span class="cv-asof">Data as of ${cv.data_as_of}</span>` : '';
  return `<div class="cv-section"><div class="cv-row">${stats.join('')}${asOf}</div></div>`;
}

// ── Directed force-graph (ego-network) ───────────────────────────────────────

const GRAPH_LENSES = ['appellate_chain', 'supervisory', 'appointment', 'funding'];

// Which relationships each lens includes
function relMatchesLens(r, lenses) {
  if (lenses.has('appellate_chain') &&
      (r.relationship_category === 'appellate_chain' ||
       (r.relationship_category === 'statutory_ref' && r.relationship_type === 'BenchOf')))
    return true;
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
    if (body) renderNeighborhoodGraph(body, entityId, lenses);
  });
}

function renderNeighborhoodGraph(container, entityId, lenses) {
  if (!window.d3) { container.innerHTML = '<p class="nb-empty">D3 not loaded.</p>'; return; }
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
  const svg = d3.select(container).append('svg')
    .attr('width', W).attr('height', H)
    .style('font-family', 'Inter, sans-serif');

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
    .force('link',    d3.forceLink().id(d => d.id).distance(130).strength(0.45))
    .force('charge',  d3.forceManyBody().strength(-300))
    .force('collide', d3.forceCollide().radius(d => d.isFocus ? 34 : 26).iterations(3))
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
    sim.force('charge').strength(-300 - mNodes.length * 5);
    sim.alpha(0.35).restart();
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
  });

  // ── Initial render ─────────────────────────────────────────────────────────
  updateGraph();

  // Reset button
  const resetBtn = document.createElement('button');
  resetBtn.textContent = '⌂'; resetBtn.className = 'nb-reset-btn'; resetBtn.title = 'Reset view';
  resetBtn.onclick = () => svg.transition().duration(300).call(zoom.transform, d3.zoomIdentity);
  container.appendChild(resetBtn);
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
  const isScoreExcluded = score == null && dpScore == null;
  const isNotValidated = derived.scores_validated === false;

  const prevEntityId = _historyStack[_historyStack.length - 1];
  const prevEntity = prevEntityId ? State.getEntityById(prevEntityId) : null;

  const backLabel = prevEntity ? `← ${prevEntity.name}` : '← Back to overview';

  const lensToggleBtns = GRAPH_LENSES
    .map(l => `<button class="nb-lens-btn${_nbLenses.has(l) ? ' active' : ''}" data-lens="${l}" style="--lens-color:${REL_COLORS[l]}">${REL_LABELS[l]}</button>`)
    .join('');

  container.innerHTML = `
    <div class="dv-inner">
      <div class="dv-nav">
        <button class="dv-back-btn" id="dv-back">${backLabel}</button>
        <span class="dv-breadcrumb">${CLUSTER_LABELS[entity.cluster] || entity.cluster || ''}</span>
      </div>

      <div class="dv-layout">

        <!-- Left: scores, gaps, case volume -->
        <div class="dv-left">
          <div class="dv-header">
            <h1 class="dv-name">${entity.name}</h1>
            ${statusPill(entity)}
          </div>
          <div class="dv-meta">
            ${entity.abbreviation ? `<span class="dv-abbr">${entity.abbreviation}</span>` : ''}
            <span class="dv-cluster">${CLUSTER_LABELS[entity.cluster] || entity.cluster || ''}</span>
            ${entity.created_year ? `<span class="dv-year">Est. ${entity.created_year}</span>` : ''}
          </div>

          ${isScoreExcluded ? `
            <div class="dv-no-score">Independence risk score not computed for this entity type (governance anchor).</div>
          ` : `
            <div class="ir-hero" style="--ir-color:${RISK_COLORS[level] || '#888'}">
              <div class="ir-score-num">${score ?? '—'}</div>
              <div class="ir-level-label">${level ? level.toUpperCase() + ' INDEPENDENCE RISK' : 'INDEPENDENCE RISK'}</div>
              <div class="ir-explain">${RISK_EXPLAIN[level] || ''}</div>
              ${isNotValidated ? '<div class="ir-pending">⚐ Scores pending community review</div>' : ''}
            </div>
            ${renderBreakdown(derived.independence_risk_breakdown, 'Independence risk', 15)}

            ${dpScore != null ? `<div class="dp-section">
              <span class="dp-label">Discretionary Power</span>
              <span class="dp-score">${dpScore}</span>
              <div class="dp-bar-wrap"><div class="dp-bar" style="width:${Math.min(100, (dpScore / 20) * 100)}%"></div></div>
            </div>` : ''}
          `}

          ${renderCaseVolume(detail.case_volume)}

          <div class="dv-full-profile">
            <button class="dv-profile-toggle" id="dv-profile-toggle">
              Full structural profile ▾
              <span class="dv-profile-hint">appointment · funding · audit · complaint · sources</span>
            </button>
            <div class="dv-profile-body hidden" id="dv-profile-body"></div>
          </div>

          <div class="dv-actions">
            <button class="dv-open-map" id="dv-open-map">Open in full map →</button>
            <button class="dv-export-pdf" id="dv-export-pdf">↓ Export PDF</button>
          </div>
        </div>

        <!-- Right: neighborhood graph -->
        <div class="dv-right">
          <div class="nb-section-head">
            <span class="nb-section-title">Neighborhood</span>
            <div class="nb-lens-group" id="nb-lens-group" role="group" aria-label="Relationship lens filters">
              ${lensToggleBtns}
            </div>
          </div>
          <div class="nb-graph-wrap" id="nb-graph-wrap"></div>
          <p class="nb-hint">● filled = focus &nbsp;○ ring = neighbor · hover to highlight · click neighbor to open</p>
        </div>

      </div>
    </div>
  `;

  // ── Wire back button ────────────────────────────────────────────────────────
  container.querySelector('#dv-back')?.addEventListener('click', () => {
    if (prevEntityId) {
      _historyStack.pop();
      State.emit('navigateToDetail', prevEntityId);
    } else {
      State.emit('navigateToSummary', null);
    }
  });

  // ── Wire "open in full map" ─────────────────────────────────────────────────
  container.querySelector('#dv-open-map')?.addEventListener('click', () => {
    State.emit('navigateToMap', entityId);
  });

  // ── Wire full structural profile toggle ────────────────────────────────────
  container.querySelector('#dv-profile-toggle')?.addEventListener('click', () => {
    const body = container.querySelector('#dv-profile-body');
    const btn  = container.querySelector('#dv-profile-toggle');
    if (!body) return;
    const isHidden = body.classList.contains('hidden');
    if (isHidden) {
      // Lazy-render full profile on first open
      if (!body.dataset.rendered) {
        body.innerHTML = buildPanelHTML(entity);
        body.dataset.rendered = '1';
        // Wire connection rows inside the profile to navigate via detail view
        body.addEventListener('click', ev => {
          const btn2 = ev.target.closest('.detail-connection-row');
          if (!btn2) return;
          ev.preventDefault();
          const id = btn2.getAttribute('data-entity-id');
          if (id) State.emit('navigateToDetail', id);
        });
      }
      body.classList.remove('hidden');
      btn.innerHTML = `Full structural profile ▴ <span class="dv-profile-hint">appointment · funding · audit · complaint · sources</span>`;
    } else {
      body.classList.add('hidden');
      btn.innerHTML = `Full structural profile ▾ <span class="dv-profile-hint">appointment · funding · audit · complaint · sources</span>`;
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
    // 1. Ensure full structural profile is generated and visible
    const profileBody = container.querySelector('#dv-profile-body');
    let profileWasHidden = false;
    if (profileBody) {
      if (!profileBody.dataset.rendered) {
        profileBody.innerHTML = buildPanelHTML(entity);
        profileBody.dataset.rendered = '1';
        profileBody.addEventListener('click', ev => {
          const btn2 = ev.target.closest('.detail-connection-row');
          if (!btn2) return;
          ev.preventDefault();
          const id = btn2.getAttribute('data-entity-id');
          if (id) State.emit('navigateToDetail', id);
        });
      }
      profileWasHidden = profileBody.classList.contains('hidden');
      if (profileWasHidden) profileBody.classList.remove('hidden');
    }

    // 2. Fit the SVG viewBox to its actual content so the full tree prints
    const graphWrap = container.querySelector('#nb-graph-wrap');
    const svgEl = graphWrap?.querySelector('svg');
    let savedWidth = null, savedHeight = null, savedViewBox = null;
    if (svgEl) {
      try {
        const bbox = svgEl.getBBox();
        if (bbox.width > 0 && bbox.height > 0) {
          savedWidth   = svgEl.getAttribute('width');
          savedHeight  = svgEl.getAttribute('height');
          savedViewBox = svgEl.getAttribute('viewBox');
          const pad = 28;
          svgEl.setAttribute('viewBox',
            `${bbox.x - pad} ${bbox.y - pad} ${bbox.width + pad * 2} ${bbox.height + pad * 2}`);
          svgEl.setAttribute('width', '100%');
          svgEl.removeAttribute('height');
        }
      } catch (_) { /* getBBox may fail if element not rendered */ }
    }

    // 3. Print
    document.body.classList.add('jem-print-detail');

    const done = () => {
      document.body.classList.remove('jem-print-detail');
      // Restore profile state
      if (profileWasHidden && profileBody) profileBody.classList.add('hidden');
      // Restore SVG attributes
      if (svgEl) {
        if (savedWidth  != null) svgEl.setAttribute('width', savedWidth);
        else svgEl.removeAttribute('width');
        if (savedHeight != null) svgEl.setAttribute('height', savedHeight);
        else svgEl.removeAttribute('height');
        if (savedViewBox != null) svgEl.setAttribute('viewBox', savedViewBox);
        else svgEl.removeAttribute('viewBox');
      }
      window.removeEventListener('afterprint', done);
    };
    window.addEventListener('afterprint', done);
    window.print();
  });

  // ── Initial neighborhood render ─────────────────────────────────────────────
  requestAnimationFrame(() => {
    _redrawNeighborhood(container);
  });
}

function _redrawNeighborhood(container) {
  const wrap = container.querySelector('#nb-graph-wrap');
  if (!wrap) return;
  _miniGraphWrap = wrap;
  renderNeighborhoodGraph(wrap, _currentEntityId, _nbLenses);
  // Expand button lives inside the graph wrap (overlaid), added after render clears it
  const expandBtn = document.createElement('button');
  expandBtn.className = 'nb-expand-btn';
  expandBtn.title = 'Fullscreen';
  expandBtn.textContent = '⤢';
  expandBtn.onclick = () => openFullscreenGraph(_currentEntityId, _nbLenses);
  wrap.appendChild(expandBtn);
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
