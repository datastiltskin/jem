// JEM — Main Entry Point
// Loads graph.json, initialises all modules, wires events.

import { State } from './state.js';
import { initFocusCanvas, render, fitFocusToView } from './focusCanvas.js';
import { initNavigatorTree, expandPathToEntity } from './navigatorTree.js';
import { initGroupReport } from './groupReport.js';
import { initTimeline } from './timeline.js';
import { initPanel } from './panel.js';
import { initNeighborhoodPanel } from './neighborhoodPanel.js';
import { initViewStatus, getGapStats, primeGapStats } from './viewStatus.js';
import { selectAndOpenEntity } from './entitySelection.js';
import { initSummaryView } from './summaryView.js';
import { renderDetailView, clearDetailView } from './detailView.js';
import { initSmartSearch, entityDisplayName } from './smartSearch.js';
import { renderAboutPage } from './aboutContent.js';
import { initToolbarAuth } from './auth.js';
import { mountMapShell } from './mapShell.js';
import { loadD3 } from './loadD3.js';
import { loadFuse } from './loadFuse.js';

const GRAPH_URL = './public/graph.json';

/** Keep app chrome below site header + toolbar when search chips wrap to a second row. */
function syncChromeTop() {
  const siteHeader = document.querySelector('.site-header');
  const toolbar = document.getElementById('toolbar');
  if (!toolbar) return;
  const headerH = siteHeader ? Math.ceil(siteHeader.getBoundingClientRect().height) : 0;
  const toolbarH = Math.ceil(toolbar.getBoundingClientRect().height);
  document.documentElement.style.setProperty('--jem-site-header-height', `${headerH}px`);
  document.documentElement.style.setProperty('--jem-chrome-top', `${headerH + toolbarH}px`);
}

function initChromeTopSync() {
  const siteHeader = document.querySelector('.site-header');
  const toolbar = document.getElementById('toolbar');
  if (!toolbar) return;
  syncChromeTop();
  if (typeof ResizeObserver !== 'undefined') {
    const ro = new ResizeObserver(() => syncChromeTop());
    ro.observe(toolbar);
    if (siteHeader) ro.observe(siteHeader);
  }
  window.addEventListener('resize', syncChromeTop);
}

// ── Lazy map boot (option C — hybrid gate) ────────────────────────────────────
// Cold #/map: gate defers graph.json fetch until the user clicks.
// Overview/detail: graph loads on boot; map workspace inits on first map visit.
// Graph already in memory: spinner only (auto-approved).

let _mapLoadApproved = false;
let _appDataBooted = false;
let _searchPatchWired = false;

let _resolveMapLoad;
const _mapLoadPromise = new Promise((resolve) => { _resolveMapLoad = resolve; });

function approveMapLoad() {
  if (_mapLoadApproved) return;
  _mapLoadApproved = true;
  _resolveMapLoad();
}

function setMapLoadPane(gate, spinner) {
  document.getElementById('map-load-gate')?.classList.toggle('hidden', !gate);
  document.getElementById('map-load-spinner')?.classList.toggle('hidden', !spinner);
}

function showMapBootError(err) {
  const stage = document.getElementById('map-load-stage');
  if (!stage) return;
  stage.classList.remove('hidden');
  setMapLoadPane(false, false);
  stage.innerHTML =
    `<div class="loading-error map-load-error">
      <strong>Failed to load map</strong><br>
      ${err.message}
    </div>`;
}

function applyGraph(graph) {
  State.graph = graph;
  const cw = graph.meta?.canvas_width;
  const ch = graph.meta?.canvas_height;
  if (cw && ch) {
    document.documentElement.style.setProperty('--jem-canvas-width', `${cw}px`);
    document.documentElement.style.setProperty('--jem-canvas-height', `${ch}px`);
  }
  State.initExplorerDefaults();
  State.initFocusDefaults();
  primeGapStats(graph);
  State.emit('graphLoaded', graph);
}

async function loadGraph() {
  if (State.graph) return State.graph;
  const response = await fetch(GRAPH_URL);
  if (!response.ok) throw new Error(`Failed to load graph.json: ${response.status}`);
  const graph = await response.json();
  applyGraph(graph);
  return graph;
}

async function afterGraphLoaded() {
  if (_appDataBooted) return;
  _appDataBooted = true;
  await initSearch(State.graph);
  initCommandPalette();
  patchSearchForDetailView();
  initSummaryView();
  renderAboutView();
}

function revealMapChrome() {
  document.getElementById('map-load-stage')?.classList.add('hidden');
  document.getElementById('app-workspace')?.classList.remove('hidden');
  document.getElementById('timeline-container')?.classList.remove('hidden');
  document.getElementById('map-status-bar')?.classList.remove('hidden');
  document.getElementById('quality-legend')?.classList.remove('hidden');
  document.getElementById('govt-level-legend')?.classList.remove('hidden');
  document.getElementById('mobile-workspace-tabs')?.classList.remove('hidden');
  document.getElementById('mode-switcher')?.classList.remove('hidden');
  const overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.style.display = 'none';
}

function initMapGate() {
  document.getElementById('btn-load-map')?.addEventListener('click', () => {
    approveMapLoad();
    setMapLoadPane(false, true);
  });

  document.getElementById('btn-map-gate-back')?.addEventListener('click', async () => {
    history.replaceState(null, '', `${location.pathname}${location.search}`);
    try {
      if (!State.graph) {
        await loadGraph();
        await afterGraphLoaded();
      }
      switchView('summary');
    } catch (err) {
      console.error('JEM overview load error:', err);
      showBootError(err);
    }
  });
}

// ── View Router ───────────────────────────────────────────────────────────────
// Views: 'summary' | 'detail' | 'map' | 'about'

let _mapBooted = false;       // full map initialised lazily on first switch
let _mapBootPromise = null;   // in-flight D3 + map shell init
let _mapReturnTarget = null;  // reserved for map navigation context

// ── URL hash routing ──────────────────────────────────────────────────────────
// Shareable deep-links via fragment: '#/entity/<id>' opens the detail view,
// '#/map' opens the map. Empty/absent hash = summary.
// Hash-only (not pathname) so static hosts need no rewrites.

function _entityIdFromHash() {
  const m = (location.hash || '').match(/^#\/entity\/(.+)$/);
  return m ? decodeURIComponent(m[1]) : null;
}

function _hashViewFromHash() {
  if (/^#\/entity\/.+/.test(location.hash)) return 'detail';
  if (location.hash === '#/map') return 'map';
  if (location.hash === '#/about') return 'about';
  return 'summary';
}

let _suppressHashSync = false;

function _syncHashForView(view, entityId) {
  if (_suppressHashSync) return;
  let target = '';
  if (view === 'detail' && entityId) target = `#/entity/${encodeURIComponent(entityId)}`;
  else if (view === 'map') target = '#/map';
  else if (view === 'about') target = '#/about';
  // Empty hash for summary.
  if (location.hash === target) return;
  const url = target ? `${location.pathname}${location.search}${target}` : `${location.pathname}${location.search}`;
  history.pushState(null, '', url);
}

function _showMissingEntityToast(id) {
  const el = document.createElement('div');
  el.className = 'jem-toast jem-toast-warn';
  el.textContent = `Entity “${id}” not found — showing overview.`;
  document.body.appendChild(el);
  requestAnimationFrame(() => el.classList.add('jem-toast-in'));
  setTimeout(() => {
    el.classList.remove('jem-toast-in');
    setTimeout(() => el.remove(), 300);
  }, 3200);
}

function _applyHashRoute() {
  const view = _hashViewFromHash();
  _suppressHashSync = true;
  void (async () => {
    try {
      if (view !== 'map' && !State.graph) {
        await loadGraph();
        await afterGraphLoaded();
        if (!document.body.classList.contains('jem-ready')) finishBoot();
      }

      if (view === 'detail') {
        const id = _entityIdFromHash();
        const e = id ? State.getEntityById(id) : null;
        if (e) {
          switchView('detail', id);
        } else {
          if (id) _showMissingEntityToast(id);
          history.replaceState(null, '', `${location.pathname}${location.search}`);
          switchView('summary');
        }
      } else if (view === 'map') {
        switchView('map');
      } else if (view === 'about') {
        switchView('about');
      } else {
        switchView('summary');
      }
    } finally {
      _suppressHashSync = false;
    }
  })();
}

function switchView(view, entityId = null) {
  const prevView = document.body.dataset.appView;

  // Capture return info BEFORE state is cleared below
  const fromDetailEntityId = document.body.dataset.prevDetailEntity || null;

  // Determine where map's back button should return to
  if (view === 'map') {
    if (prevView === 'detail' && fromDetailEntityId) {
      _mapReturnTarget = { view: 'detail', entityId: fromDetailEntityId };
    } else if (prevView !== 'map') {
      // Arrived from summary, initial load, or toolbar direct
      _mapReturnTarget = { view: 'summary' };
    }
    // Already in map — preserve existing return target so the user doesn't lose their path
  } else if (view === 'summary') {
    _mapReturnTarget = null;
  }

  document.body.dataset.appView = view;

  // Clear detail view state when navigating away from it
  if (prevView === 'detail' && view !== 'detail') {
    clearDetailView();
    delete document.body.dataset.prevDetailEntity;
  }

  const summaryEl   = document.getElementById('summary-view');
  const detailEl    = document.getElementById('detail-view');
  const aboutEl     = document.getElementById('about-view');
  const workspaceEl = document.getElementById('app-workspace');
  const timelineEl  = document.getElementById('timeline-container');
  const statusEl    = document.getElementById('map-status-bar');
  const qualEl      = document.getElementById('quality-legend');
  const govtEl      = document.getElementById('govt-level-legend');
  const mobileNav   = document.getElementById('mobile-workspace-tabs');
  const mapStage    = document.getElementById('map-load-stage');
  const aboutBtn    = document.getElementById('btn-about');
  const mapChromeReady = view === 'map' && _mapBooted;

  if (summaryEl)   summaryEl.classList.toggle('hidden', view !== 'summary');
  if (detailEl)    detailEl.classList.toggle('hidden', view !== 'detail');
  if (aboutEl)     aboutEl.classList.toggle('hidden', view !== 'about');
  if (workspaceEl) workspaceEl.classList.toggle('hidden', view !== 'map' || !_mapBooted);
  if (mapStage)    mapStage.classList.toggle('hidden', view !== 'map' || _mapBooted);
  if (timelineEl)  timelineEl.classList.toggle('hidden', !mapChromeReady);
  if (statusEl)    statusEl.classList.toggle('hidden', !mapChromeReady);
  if (qualEl)      qualEl.classList.toggle('hidden', !mapChromeReady);
  if (govtEl)      govtEl.classList.toggle('hidden', !mapChromeReady);
  if (mobileNav)   mobileNav.classList.toggle('hidden', !mapChromeReady);
  if (aboutBtn)    aboutBtn.classList.toggle('active', view === 'about');

  document.getElementById('mode-switcher')?.classList.toggle('hidden', view !== 'map' || !_mapBooted);

  if (view === 'summary') {
    // Nothing to re-init; summaryView is rendered once after graph load
  } else if (view === 'about') {
    window.__jemSmartSearch?.collapseSearchUI?.({ clearInput: true });
    renderAboutView();
    syncChromeTop();
  } else if (view === 'detail' && entityId) {
    window.__jemSmartSearch?.collapseSearchUI?.();
    const fromId = document.body.dataset.prevDetailEntity || null;
    renderDetailView(entityId, fromId !== entityId ? fromId : null);
    document.body.dataset.prevDetailEntity = entityId;
    syncChromeTop();
  } else if (view === 'map') {
    if (!State.graph) {
      setMapLoadPane(true, false);
    } else {
      approveMapLoad();
      setMapLoadPane(false, true);
    }
    void ensureMapBooted().then(() => {
      if (entityId) {
        const e = State.getEntityById(entityId);
        if (e) {
          selectAndOpenEntity(e);
          expandPathToEntity(entityId);
        }
      }
      requestAnimationFrame(() => {
        render();
        requestAnimationFrame(() => fitFocusToView({ animate: false }));
      });
    }).catch((err) => {
      console.error('JEM map boot error:', err);
      showMapBootError(err);
    });
  }

  _syncHashForView(view, entityId);
}

function wireNavigationEvents() {
  State.subscribe('navigateToDetail', (id) => {
    window.__jemSmartSearch?.collapseSearchUI?.();
    switchView('detail', id);
  });

  State.subscribe('navigateToSummary', () => {
    switchView('summary');
  });

  State.subscribe('navigateToMap', (id) => {
    approveMapLoad();
    switchView('map', id);
  });

  document.getElementById('btn-home')?.addEventListener('click', () => {
    window.__jemSmartSearch?.collapseSearchUI?.({ clearInput: true });
    switchView('summary');
  });
}

// ── Command Palette ───────────────────────────────────────────────────────────

let _commandPaletteActive = false;

function initCommandPalette() {
  // "/" key opens the search input and populates with ranked entities
  document.addEventListener('keydown', (e) => {
    if (e.defaultPrevented) return;
    const el = e.target;
    if (el && (el.closest?.('input, textarea, select') || el.isContentEditable)) return;
    if (e.key === '/') {
      e.preventDefault();
      const input = document.getElementById('search-input');
      if (input) {
        input.focus();
        input.value = '';
        input.dispatchEvent(new Event('input'));
        showCommandPaletteDefault();
      }
    }
  });
}

function showCommandPaletteDefault() {
  const graph = State.graph;
  if (!graph) return;
  const results = document.getElementById('search-results');
  if (!results) return;

  const top20 = [...graph.entities]
    .filter(e => e.derived?.independence_risk_score != null)
    .sort((a, b) => (b.derived.independence_risk_score || 0) - (a.derived.independence_risk_score || 0))
    .slice(0, 20);

  const RISK_COLORS = { low: '#16a34a', moderate: '#d97706', high: '#dc2626', severe: '#7c3aed' };
  results.innerHTML = `<div class="palette-hint">Top entities by independence risk · press <kbd>/</kbd> then type to search</div>`
    + top20.map(e => {
      const level = e.derived?.independence_risk_level;
      const score = e.derived?.independence_risk_score;
      const color = level ? RISK_COLORS[level] : '#888';
      const nc = e.operational_status === 'Not_Constituted' ? '<span class="sr-badge nc">NC</span>' : '';
      return `<div class="search-result" data-id="${e.id}">
        <span class="sr-name ${e.data_quality}">${entityDisplayName(e)}</span>
        ${nc}
        ${level ? `<span class="sr-risk" style="color:${color}">${level} · ${score}</span>` : ''}
      </div>`;
    }).join('');
  results.classList.remove('hidden');

  results.querySelectorAll('.search-result').forEach(el => {
    el.addEventListener('click', () => {
      const id = el.dataset.id;
      const input = document.getElementById('search-input');
      if (input) { input.value = ''; }
      results.classList.add('hidden');
      switchView('detail', id);
    });
  });
}

// ── KPI Strip (declared before boot so the symbol always exists at runtime) ───
// Four large action cards below the toolbar; each wires one view/filter action.

const FILTER_TO_CARD = {
  high_independence_risk: 'kpi-card-ir',
  has_structural_gaps: 'kpi-card-gaps',
  blocked_or_absent: 'kpi-card-blocked',
};

const INSPECTOR_WIDTH_KEY = 'jem-inspector-width';

let kpiCardsWired = false;

function syncKpiCardActive() {
  document.querySelectorAll('.kpi-card').forEach(c => c.classList.remove('active'));

  const cardIdForFilter = FILTER_TO_CARD[State.activeImpactFilter];
  if (cardIdForFilter) {
    document.getElementById(cardIdForFilter)?.classList.add('active');
  }

  if (State.viewMode === 'gaps' || State.activeImpactFilter === 'has_structural_gaps') {
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
  const gapMetrics = metrics.structural_gaps_entity_count;
  const gapFallback = getGapStats().gapEntityCount;
  setNum('kpi-num-gaps', gapMetrics != null ? gapMetrics : (gapFallback > 0 ? gapFallback : 0));
  setNum('kpi-num-blocked', (metrics.appellate_vacuum_count || 0) + (metrics.not_constituted_count || 0));
  setNum('kpi-num-clog',    metrics.critical_high_clog_count);

  const gapsCard = document.getElementById('kpi-card-gaps');
  if (gapsCard && gapMetrics == null && !getGapStats().hasGapAnnotations) {
    gapsCard.title = 'Structural gap counts are not in this graph build yet — switches to Gaps mode to preview markers when data is added';
  }

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
        requestAnimationFrame(() => fitFocusToView({ animate: false }));
      });
    };

    onCard('kpi-card-ir', () => {
      if (State.viewMode !== 'risk') State.setViewMode('risk');
      State.setImpactFilter('high_independence_risk');
    });

    onCard('kpi-card-gaps', () => {
      if (State.viewMode !== 'gaps') State.setViewMode('gaps');
      State.setImpactFilter(
        State.activeImpactFilter === 'has_structural_gaps' ? null : 'has_structural_gaps',
      );
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
        requestAnimationFrame(() => fitFocusToView({ animate: false }));
      });
    }

    State.subscribe('filterChanged', () => {
      syncKpiCardActive();
      render();
      requestAnimationFrame(() => fitFocusToView({ animate: false }));
    });
    State.subscribe('viewModeChanged', syncKpiCardActive);
    State.subscribe('derivedToggle', syncKpiCardActive);
  }

  syncKpiCardActive();
}

function ensureMapBooted() {
  if (_mapBooted) return _mapBootPromise || Promise.resolve();
  if (!_mapBootPromise) {
    _mapBootPromise = (async () => {
      await _mapLoadPromise;

      if (!State.graph) {
        setMapLoadPane(false, true);
        await loadGraph();
        await afterGraphLoaded();
      } else if (!_appDataBooted) {
        await afterGraphLoaded();
      }

      await bootMapWorkspace();
      revealMapChrome();
    })().catch((err) => {
      _mapBootPromise = null;
      throw err;
    });
  }
  return _mapBootPromise;
}

async function bootMapWorkspace() {
  if (_mapBooted) return;

  mountMapShell();
  await loadD3();

  initViewStatus();
  initFocusCanvas();
  initNavigatorTree();
  initGroupReport();
  initTimeline();
  initPanel();
  initNeighborhoodPanel();
  initToolbar();
  initMobileWorkspaceTabs();
  initInspectorResize();
  syncNavFacetVisibility();

  const graph = State.graph;
  if (graph) {
    populateKpiCards(graph.impact_metrics || {});
    expandPathToEntity(State.focusEntityId);
    ['supreme_court_india', 'president_india'].forEach((id) => {
      if (State.getEntityById(id)) expandPathToEntity(id);
    });
    State.setZoomLevel(2);
    render();
  }

  _mapBooted = true;
}

function finishBoot() {
  document.body.classList.add('jem-ready');
  const boot = document.getElementById('jem-boot-screen');
  if (boot) boot.setAttribute('aria-busy', 'false');
}

function showBootError(err) {
  const boot = document.getElementById('jem-boot-screen');
  if (!boot) return;
  boot.setAttribute('aria-busy', 'false');
  boot.innerHTML = `
    <img src="public/assets/jem-logo.png" class="jem-boot-wordmark" alt="JEM — Judiciary Entity Map (India)" width="460" height="212" decoding="async">
    <div class="loading-error">
      <strong>Failed to load graph data</strong><br>
      ${err.message}<br><br>
      Run <code>python scripts/build.py</code> to generate <code>web/public/graph.json</code>
    </div>`;
}

// ── Boot Sequence ─────────────────────────────────────────────────────────────

async function boot() {
  initChromeTopSync();
  initToolbarAuth(document.getElementById('toolbar-auth'));
  initAboutPage();
  initMapGate();
  initDistrictLatticeHotkeys();
  wireNavigationEvents();

  const coldMap = _hashViewFromHash() === 'map';

  try {
    if (!coldMap) {
      await loadGraph();
      await afterGraphLoaded();
    }

    finishBoot();

    if (location.hash) {
      _applyHashRoute();
    } else {
      switchView('summary');
    }

    window.addEventListener('popstate', _applyHashRoute);
    window.addEventListener('hashchange', _applyHashRoute);
  } catch (err) {
    console.error('JEM boot error:', err);
    showBootError(err);
  }
}

// When in summary/detail view, search results navigate to detail instead of map
function patchSearchForDetailView() {
  if (_searchPatchWired) return;
  _searchPatchWired = true;
  const results = document.getElementById('search-results');
  if (!results) return;

  // Observe result clicks; if not in map view, go to detail
  results.addEventListener('click', (e) => {
    const row = e.target.closest('.search-result');
    if (!row) return;
    if (row.classList.contains('search-insight-hit')) return;
    const view = document.body.dataset.appView;
    if (view === 'summary' || view === 'detail') {
      // Prevent the default search handler from running (it fires on the element itself)
      // by switching view here first; the existing handler will then noop on empty state
      e.stopImmediatePropagation();
      const id = row.dataset.id;
      const input = document.getElementById('search-input');
      if (input) { input.value = ''; }
      results.classList.add('hidden');
      if (id) switchView('detail', id);
    }
    // In map view: let the existing search handler do its thing
  }, true /* capture — runs before the existing delegated handler */);
}

function syncNavFacetVisibility() {
  const facet = document.getElementById('nav-facet-switch');
  if (!facet) return;
  facet.classList.toggle('hidden', State.navMode !== 'browse');
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
  const advSlot = document.getElementById('nav-advanced-slot');

  State.setViewMode('structure');

  syncExplorerTreeActions();
  syncLensToolbarButtons();
  syncDerivedToolbarButtons();
  syncModeToolbarButtons();
  const noteEl = document.getElementById('unvalidated-note');
  if (noteEl) noteEl.style.visibility = 'visible';

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
    advToggle.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const nowOpen = !advDrawer.classList.contains('hidden');
      advDrawer.classList.toggle('hidden', nowOpen);
      advToggle.setAttribute('aria-expanded', nowOpen ? 'false' : 'true');
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
    syncNavFacetVisibility();
  });
  State.subscribe('navModeChanged', () => syncNavFacetVisibility());
  State.subscribe('collapseChanged', () => {
    syncExplorerTreeActions();
  });
  State.subscribe('aggregateChanged', () => {
    syncExplorerTreeActions();
  });

  // IR/DP toolbar toggles removed — structural health is the default ring;
  // constituents are exposed via hover micro-card and entity detail panel.

  State.subscribe('derivedToggle', () => {
    const note = document.getElementById('unvalidated-note');
    if (note) note.style.visibility = 'visible';
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
    if (note) note.style.visibility = 'visible';
  });

  document.addEventListener('click', (e) => {
    if (!advDrawer || !advToggle || advDrawer.classList.contains('hidden')) return;
    if (advSlot && advSlot.contains(e.target)) return;
    advDrawer.classList.add('hidden');
    advToggle.setAttribute('aria-expanded', 'false');
  });
}

function initInspectorResize() {
  const resizer = document.getElementById('inspector-resizer');
  if (!resizer) return;

  const root = document.documentElement;
  const readMin = () => parseInt(getComputedStyle(root).getPropertyValue('--jem-inspector-min'), 10) || 300;
  const readMax = () => {
    const cssMax = parseInt(getComputedStyle(root).getPropertyValue('--jem-inspector-max'), 10) || 920;
    return Math.min(cssMax, window.innerWidth - 320);
  };

  try {
    const saved = localStorage.getItem(INSPECTOR_WIDTH_KEY);
    if (saved) {
      const w = parseInt(saved, 10);
      if (w >= readMin() && w <= readMax()) {
        root.style.setProperty('--jem-inspector-width', `${w}px`);
      }
    }
  } catch {
    /* ignore storage errors */
  }

  let dragging = false;

  const applyWidth = (clientX) => {
    const w = Math.min(readMax(), Math.max(readMin(), window.innerWidth - clientX));
    root.style.setProperty('--jem-inspector-width', `${w}px`);
    return w;
  };

  const stopDrag = () => {
    if (!dragging) return;
    dragging = false;
    document.body.classList.remove('jem-resizing-inspector');
    try {
      const w = parseInt(getComputedStyle(root).getPropertyValue('--jem-inspector-width'), 10);
      if (w) localStorage.setItem(INSPECTOR_WIDTH_KEY, String(w));
    } catch {
      /* ignore */
    }
  };

  resizer.addEventListener('mousedown', (e) => {
    if (e.button !== 0) return;
    dragging = true;
    document.body.classList.add('jem-resizing-inspector');
    e.preventDefault();
  });

  window.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    applyWidth(e.clientX);
  });

  window.addEventListener('mouseup', stopDrag);

  resizer.addEventListener('keydown', (e) => {
    const step = e.shiftKey ? 40 : 16;
    const cur = parseInt(getComputedStyle(root).getPropertyValue('--jem-inspector-width'), 10) || 440;
    if (e.key === 'ArrowLeft') {
      root.style.setProperty('--jem-inspector-width', `${Math.min(readMax(), cur + step)}px`);
      e.preventDefault();
    } else if (e.key === 'ArrowRight') {
      root.style.setProperty('--jem-inspector-width', `${Math.max(readMin(), cur - step)}px`);
      e.preventDefault();
    }
  });
}

function initMobileWorkspaceTabs() {
  const tabs = document.getElementById('mobile-workspace-tabs');
  if (!tabs) return;

  const setPanel = (panel) => {
    document.body.dataset.mobilePanel = panel;
    tabs.querySelectorAll('.mobile-tab').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.mobilePanel === panel);
    });
  };

  tabs.querySelectorAll('.mobile-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      setPanel(btn.dataset.mobilePanel);
      if (btn.dataset.mobilePanel === 'focus') {
        requestAnimationFrame(() => fitFocusToView({ animate: false }));
      }
    });
  });

  setPanel('focus');

  State.subscribe('entitySelected', (id) => {
    if (id && window.matchMedia('(max-width: 900px)').matches) {
      setPanel('inspector');
    }
  });
}

// ── Search ────────────────────────────────────────────────────────────────────

async function initSearch(graph) {
  const input = document.getElementById('search-input');
  const results = document.getElementById('search-results');
  const panel = document.getElementById('insight-panel');
  const chips = document.getElementById('search-insight-chips');

  const pickEntity = (id) => {
    window.__jemSmartSearch?.collapseSearchUI?.();
    if (!State.getEntityById(id)) return;
    switchView('detail', id);
  };

  const Fuse = await loadFuse();

  const wireSearch = (g) => {
    const fuse = new Fuse(g.entities, {
      keys: [
        { name: 'name', weight: 0.55 },
        { name: 'abbreviation', weight: 0.25 },
        { name: 'aliases', weight: 0.15 },
        { name: 'constitutional_basis', weight: 0.03 },
        { name: 'statutory_basis', weight: 0.02 },
      ],
      threshold: 0.28,
      minMatchCharLength: 3,
      ignoreLocation: false,
      includeScore: true,
    });
    window.__jemFuse = fuse;

    const api = initSmartSearch({
      graph: g,
      inputEl: input,
      resultsEl: results,
      panelEl: panel,
      chipsEl: chips,
      fuseFactory: (items, opts) => new Fuse(items, opts),
      onEntityPick: pickEntity,
      onLayoutChange: syncChromeTop,
    });
    api.setEntityFuse(fuse);
    window.__jemSmartSearch = api;
    return api;
  };

  const api = graph ? wireSearch(graph) : null;

  if (!graph) {
    State.subscribe('graphLoaded', wireSearch);
  }

  document.addEventListener('click', (e) => {
    const toolbar = document.getElementById('toolbar');
    if (toolbar && !toolbar.contains(e.target)) {
      results.classList.add('hidden');
      window.__jemSmartSearch?.refreshSearchChrome?.();
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

function renderAboutView() {
  renderAboutPage();
}

function initAboutPage() {
  document.getElementById('btn-about')?.addEventListener('click', (e) => {
    e.preventDefault();
    if (document.body.dataset.appView === 'about') {
      switchView('summary');
      return;
    }
    window.__jemSmartSearch?.collapseSearchUI?.({ clearInput: true });
    switchView('about');
  });
}

// ── Start ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', boot);
