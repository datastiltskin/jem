// JEM — Main Entry Point
// Loads graph.json, initialises all modules, wires events.

import { State } from './state.js';
import { initRenderer, render, fitGraphToViewport } from './renderer.js';
import { initTimeline } from './timeline.js';
import { initPanel, openDetailPanel } from './panel.js';
import { initNeighborhoodPanel } from './neighborhoodPanel.js';

const GRAPH_URL = './public/graph.json';

// ── KPI Strip (declared before boot so the symbol always exists at runtime) ───
// Four large action cards below the toolbar; each wires one view/filter action.

const FILTER_TO_CARD = {
  high_independence_risk: 'kpi-card-ir',
  blocked_or_absent: 'kpi-card-blocked',
};

let kpiCardsWired = false;

function syncKpiCardActive() {
  document.querySelectorAll('.kpi-card').forEach(c => c.classList.remove('active'));

  const cardIdForFilter = FILTER_TO_CARD[State.activeImpactFilter];
  if (cardIdForFilter) {
    document.getElementById(cardIdForFilter)?.classList.add('active');
  }

  if (State.viewMode === 'gaps') {
    document.getElementById('kpi-card-gaps')?.classList.add('active');
  }

  if (State.showCaseVolume) {
    document.getElementById('kpi-card-clog')?.classList.add('active');
  }

  const clearBtn = document.getElementById('btn-clear-filter');
  if (clearBtn) clearBtn.classList.toggle('hidden', !State.activeImpactFilter);
}

function populateKpiCards(metrics) {
  const setNum = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = (val !== undefined && val !== null) ? val : '—';
  };

  setNum('kpi-num-ir',      metrics.high_independence_risk_count);
  setNum('kpi-num-gaps',    metrics.structural_gaps_entity_count);
  setNum('kpi-num-blocked', (metrics.appellate_vacuum_count || 0) + (metrics.not_constituted_count || 0));
  setNum('kpi-num-clog',    metrics.critical_high_clog_count);

  if (!kpiCardsWired) {
    kpiCardsWired = true;

    const onCard = (id, fn) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.addEventListener('pointerdown', (e) => {
        e.preventDefault?.();
        e.stopPropagation?.();
        fn();
        syncKpiCardActive();
        render();
      });
    };

    onCard('kpi-card-ir', () => {
      if (State.viewMode !== 'risk') State.setViewMode('risk');
      State.setImpactFilter('high_independence_risk');
    });

    onCard('kpi-card-gaps', () => {
      if (State.viewMode !== 'gaps') State.setViewMode('gaps');
    });

    onCard('kpi-card-blocked', () => {
      State.setImpactFilter('blocked_or_absent');
    });

    onCard('kpi-card-clog', () => {
      State.toggleCaseVolume();
    });

    const clearBtn = document.getElementById('btn-clear-filter');
    if (clearBtn) {
      clearBtn.addEventListener('pointerdown', (e) => {
        e.preventDefault?.();
        e.stopPropagation?.();
        State.setImpactFilter(null);
        syncKpiCardActive();
        render();
      });
    }

    State.subscribe('filterChanged', syncKpiCardActive);
    State.subscribe('viewModeChanged', syncKpiCardActive);
    State.subscribe('derivedToggle', syncKpiCardActive);
  }

  syncKpiCardActive();
}

// ── Boot Sequence ─────────────────────────────────────────────────────────────

async function boot() {
  try {
    // 1. Load data
    const response = await fetch(GRAPH_URL);
    if (!response.ok) throw new Error(`Failed to load graph.json: ${response.status}`);
    const graph = await response.json();
    State.graph = graph;
    const cw = graph.meta?.canvas_width;
    const ch = graph.meta?.canvas_height;
    if (cw && ch) {
      document.documentElement.style.setProperty('--jem-canvas-width', `${cw}px`);
      document.documentElement.style.setProperty('--jem-canvas-height', `${ch}px`);
    }
    State.initExplorerDefaults();

    // 2. Populate KPI strip
    populateKpiCards(graph.impact_metrics || {});

    // 3. Initialise modules
    initRenderer();
    initTimeline();
    initPanel();
    initNeighborhoodPanel();
    initZoom();
    initToolbar();
    initSearch();
    initAboutModal();
    initDistrictLatticeHotkeys();

    State.emit('graphLoaded', graph);

    // 4. Hide loading overlay
    document.getElementById('loading-overlay').style.display = 'none';

    // 5. First render — default entity view (not cluster dashboard).
    State.setZoomLevel(1);
    render();
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        fitGraphToViewport({ duration: 0 });
      });
    });

  } catch (err) {
    console.error('JEM boot error:', err);
    document.getElementById('loading-overlay').innerHTML =
      `<div class="loading-error">
        <strong>Failed to load graph data</strong><br>
        ${err.message}<br><br>
        Run <code>python scripts/build.py</code> to generate <code>web/public/graph.json</code>
      </div>`;
  }
}

// ── Zoom ──────────────────────────────────────────────────────────────────────

function initZoom() {
  const svgEl = document.getElementById('main-svg');
  const root = document.getElementById('graph-root');

  const zoom = d3.zoom()
    .scaleExtent([0.02, 32])
    .translateExtent([[-28000, -24000], [28000, 24000]])
    .wheelDelta((event) => {
      const dy = event.deltaMode === 1 ? event.deltaY * 28
        : event.deltaMode === 2 ? event.deltaY * 900
        : event.deltaY;
      return -dy * 0.0016;
    })
    .on('zoom', (event) => {
      d3.select(root).attr('transform', event.transform);
      State.setTransform(event.transform);
      render();
    });

  d3.select(svgEl).call(zoom);

  // Store zoom behaviour for programmatic use
  State._zoom = zoom;
  State._zoomSvg = d3.select(svgEl);

  // Zoom buttons
  const zoomIn = (e) => {
    e.preventDefault?.();
    e.stopPropagation?.();
    State._zoomSvg.transition().duration(300).call(zoom.scaleBy, 1.5);
  };
  const zoomOut = (e) => {
    e.preventDefault?.();
    e.stopPropagation?.();
    State._zoomSvg.transition().duration(300).call(zoom.scaleBy, 0.67);
  };
  const zoomReset = (e) => {
    e.preventDefault?.();
    e.stopPropagation?.();
    fitGraphToViewport({ duration: 420 });
    State.setZoomLevel(1);
    render();
  };
  // Pointer events only to avoid double-firing.
  document.getElementById('btn-zoom-in').addEventListener('pointerdown', zoomIn);
  document.getElementById('btn-zoom-out').addEventListener('pointerdown', zoomOut);
  document.getElementById('btn-zoom-reset').addEventListener('pointerdown', zoomReset);

  d3.select(svgEl).call(zoom.transform, d3.zoomIdentity);
}

// ── Toolbar ───────────────────────────────────────────────────────────────────

function syncExplorerTreeActions() {
  const wrap = document.getElementById('explorer-tree-actions');
  if (!wrap) return;
  const hasDist = (State._districtAggregateIndex?.groups?.length || 0) > 0;
  wrap.classList.toggle('hidden', !State.useProgressiveExplorer && !hasDist);
  wrap.querySelector('.explorer-appellate-label')?.classList.toggle('hidden', !State.useProgressiveExplorer);
  document.getElementById('explorer-appellate-row')?.classList.toggle('hidden', !State.useProgressiveExplorer);
  document.getElementById('explorer-district-label')?.classList.toggle('hidden', !hasDist);
  document.getElementById('explorer-district-row')?.classList.toggle('hidden', !hasDist);
}

function syncLensToolbarButtons() {
  document.querySelectorAll('.lens-btn').forEach(btn => {
    const lens = btn.dataset.lens;
    if (lens === 'investigative') {
      btn.classList.toggle('investigative-active', State.showInvestigativeOverlay);
      btn.classList.remove('active');
      return;
    }
    btn.classList.toggle('active', State.activeLenses.has(lens));
  });
}

function syncDerivedToolbarButtons() {
  const irBtn = document.getElementById('toggle-ir');
  const dpBtn = document.getElementById('toggle-dp');
  if (irBtn) irBtn.classList.toggle('active', State.showIndependenceRisk);
  if (dpBtn) dpBtn.classList.toggle('active', State.showDiscretionaryPower);
}

function syncModeToolbarButtons() {
  document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.mode === State.viewMode);
  });
}

function initToolbar() {
  const advToggle = document.getElementById('btn-advanced-toggle');
  const advDrawer = document.getElementById('advanced-drawer');
  const advSlot = document.getElementById('toolbar-advanced-slot');

  State.setViewMode('structure');

  syncExplorerTreeActions();
  syncLensToolbarButtons();
  syncDerivedToolbarButtons();
  syncModeToolbarButtons();
  const noteEl = document.getElementById('unvalidated-note');
  if (noteEl) {
    noteEl.style.visibility = (State.showIndependenceRisk || State.showDiscretionaryPower)
      ? 'visible' : 'hidden';
  }

  document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('pointerdown', (e) => {
      e.preventDefault?.();
      e.stopPropagation?.();
      const mode = btn.dataset.mode;
      State.setViewMode(mode);
      syncLensToolbarButtons();
      syncDerivedToolbarButtons();
      syncModeToolbarButtons();
      const drawer = document.getElementById('advanced-drawer');
      const advBtn = document.getElementById('btn-advanced-toggle');
      if (drawer && advBtn && !drawer.classList.contains('hidden')) {
        drawer.classList.add('hidden');
        advBtn.setAttribute('aria-expanded', 'false');
      }
      render();
    });
  });

  if (advToggle && advDrawer) {
    advToggle.addEventListener('pointerdown', (e) => {
      e.preventDefault?.();
      e.stopPropagation?.();
      const nowOpen = !advDrawer.classList.contains('hidden');
      if (nowOpen) {
        advDrawer.classList.add('hidden');
        advToggle.setAttribute('aria-expanded', 'false');
      } else {
        advDrawer.classList.remove('hidden');
        advToggle.setAttribute('aria-expanded', 'true');
      }
    });
  }

  document.querySelectorAll('.lens-btn').forEach(btn => {
    const handler = (e) => {
      e.preventDefault?.();
      e.stopPropagation?.();
      const lens = btn.dataset.lens;
      State.toggleLens(lens);
      if (lens !== 'investigative') btn.classList.toggle('active', State.activeLenses.has(lens));
      if (lens === 'investigative') {
        btn.classList.toggle('investigative-active', State.showInvestigativeOverlay);
      }
      render();
    };
    btn.addEventListener('pointerdown', handler);
  });

  const lensSelectAll = document.getElementById('lens-select-all');
  const lensClearAll = document.getElementById('lens-clear-all');
  const bulkLens = (e, fn) => {
    e.preventDefault?.();
    e.stopPropagation?.();
    fn();
    syncLensToolbarButtons();
    render();
  };
  lensSelectAll?.addEventListener('pointerdown', (e) => bulkLens(e, () => State.selectAllRelationshipLenses()));
  lensClearAll?.addEventListener('pointerdown', (e) => bulkLens(e, () => State.clearAllRelationshipLenses()));

  const explorerExpandTree = document.getElementById('explorer-expand-tree');
  const explorerCollapseTree = document.getElementById('explorer-collapse-tree');
  const explorerBulk = (e, fn) => {
    e.preventDefault?.();
    e.stopPropagation?.();
    fn();
    syncLensToolbarButtons();
    render();
  };
  explorerExpandTree?.addEventListener('pointerdown', (e) =>
    explorerBulk(e, () => State.expandAllAppellateInExplorer()));
  explorerCollapseTree?.addEventListener('pointerdown', (e) =>
    explorerBulk(e, () => State.collapseExplorerToRoots()));

  const explorerExpandDistricts = document.getElementById('explorer-expand-districts');
  const explorerCollapseDistricts = document.getElementById('explorer-collapse-districts');
  const districtBulk = (e, fn) => {
    e.preventDefault?.();
    e.stopPropagation?.();
    fn();
    render();
  };
  explorerExpandDistricts?.addEventListener('pointerdown', (e) =>
    districtBulk(e, () => State.expandAllDistrictAggregates()));
  explorerCollapseDistricts?.addEventListener('pointerdown', (e) =>
    districtBulk(e, () => State.collapseAllDistrictAggregates()));

  State.subscribe('graphLoaded', () => {
    syncExplorerTreeActions();
  });
  State.subscribe('collapseChanged', () => {
    syncExplorerTreeActions();
  });
  State.subscribe('aggregateChanged', () => {
    syncExplorerTreeActions();
  });

  const irBtn = document.getElementById('toggle-ir');
  const irHandler = (e) => {
    e.preventDefault?.();
    e.stopPropagation?.();
    State.toggleIR();
    irBtn.classList.toggle('active', State.showIndependenceRisk);
    render();
  };
  irBtn.addEventListener('pointerdown', irHandler);

  const dpBtn = document.getElementById('toggle-dp');
  const dpHandler = (e) => {
    e.preventDefault?.();
    e.stopPropagation?.();
    State.toggleDP();
    dpBtn.classList.toggle('active', State.showDiscretionaryPower);
    render();
  };
  dpBtn.addEventListener('pointerdown', dpHandler);

  State.subscribe('derivedToggle', () => {
    const note = document.getElementById('unvalidated-note');
    if (note) {
      note.style.visibility = (State.showIndependenceRisk || State.showDiscretionaryPower)
        ? 'visible' : 'hidden';
    }
    syncDerivedToolbarButtons();
  });

  State.subscribe('lensChanged', () => {
    syncLensToolbarButtons();
  });

  State.subscribe('viewModeChanged', () => {
    syncModeToolbarButtons();
    syncLensToolbarButtons();
    syncDerivedToolbarButtons();
    const note = document.getElementById('unvalidated-note');
    if (note) {
      note.style.visibility = (State.showIndependenceRisk || State.showDiscretionaryPower)
        ? 'visible' : 'hidden';
    }
  });

  document.addEventListener('pointerdown', (e) => {
    if (!advDrawer || !advToggle || advDrawer.classList.contains('hidden')) return;
    if (advSlot && advSlot.contains(e.target)) return;
    advDrawer.classList.add('hidden');
    advToggle.setAttribute('aria-expanded', 'false');
  });
}

// ── Search ────────────────────────────────────────────────────────────────────

function initSearch() {
  const input = document.getElementById('search-input');
  const results = document.getElementById('search-results');
  let fuse = null;

  State.subscribe('graphLoaded', (graph) => {
    fuse = new Fuse(graph.entities, {
      keys: ['name', 'abbreviation', 'aliases', 'constitutional_basis', 'statutory_basis'],
      threshold: 0.35,
      includeScore: true,
    });
  });

  input.addEventListener('input', () => {
    const q = input.value.trim();
    if (!q || !fuse) {
      results.classList.add('hidden');
      return;
    }
    const hits = fuse.search(q).slice(0, 8);
    if (!hits.length) {
      results.classList.add('hidden');
      return;
    }
    results.innerHTML = hits.map(h => {
      const e = h.item;
      return `<div class="search-result" data-id="${e.id}">
        <span class="sr-name ${e.data_quality}">${e.name}</span>
        <span class="sr-type">${formatType(e.type)}</span>
        ${e.operational_status === 'Not_Constituted' ? '<span class="sr-badge nc">NC</span>' : ''}
      </div>`;
    }).join('');
    results.classList.remove('hidden');

    results.querySelectorAll('.search-result').forEach(el => {
      el.addEventListener('click', () => {
        const id = el.dataset.id;
        const entity = State.getEntityById(id);
        if (entity) {
          State.selectEntity(id);
          openDetailPanel(entity);
          input.value = '';
          results.classList.add('hidden');
        }
      });
    });
  });

  document.addEventListener('click', (e) => {
    if (!input.contains(e.target) && !results.contains(e.target)) {
      results.classList.add('hidden');
    }
  });
}

function formatType(type) {
  return (type || '').replace(/([A-Z])/g, ' $1').trim();
}

function initDistrictLatticeHotkeys() {
  document.addEventListener('keydown', (e) => {
    if (e.defaultPrevented) return;
    const el = e.target;
    if (el && (el.closest?.('input, textarea, select') || el.isContentEditable)) return;
    if (!State._districtAggregateIndex?.groups?.length) return;
    if (e.code === 'Minus' || e.code === 'NumpadSubtract' || e.key === '-') {
      e.preventDefault();
      State.collapseAllDistrictAggregates();
      render();
      return;
    }
    if (e.code === 'Equal' || e.code === 'NumpadAdd' || e.key === '=' || (e.key === '+' && e.shiftKey)) {
      e.preventDefault();
      State.expandAllDistrictAggregates();
      render();
    }
  });
}

// ── About panel (slide-over) ──────────────────────────────────────────────────

function initAboutModal() {
  const panel = document.getElementById('about-panel');
  const open = (e) => {
    e.preventDefault?.();
    e.stopPropagation?.();
    panel.classList.remove('hidden');
  };
  const close = (e) => {
    e.preventDefault?.();
    e.stopPropagation?.();
    panel.classList.add('hidden');
  };
  document.getElementById('btn-about').addEventListener('pointerdown', open);
  document.getElementById('about-close').addEventListener('pointerdown', close);
}

// ── Start ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', boot);
