// JEM — Map workspace DOM (mounted on first visit to map view only)

const MAP_SHELL_HTML = `
<div id="app-workspace" class="hidden">
  <aside id="nav-panel" aria-label="Entity navigator">
    <div class="nav-panel-head">
      <div class="nav-mode-switch" role="group" aria-label="Navigation mode">
        <button type="button" class="nav-mode-btn active" data-nav-mode="appellate">Appellate</button>
        <button type="button" class="nav-mode-btn" data-nav-mode="browse">Browse</button>
      </div>
      <div class="nav-facet-switch browse-only hidden" id="nav-facet-switch">
        <button type="button" class="nav-facet-btn active" data-browse-facet="cluster">Cluster</button>
        <button type="button" class="nav-facet-btn" data-browse-facet="type">Type</button>
        <button type="button" class="nav-facet-btn" data-browse-facet="state">State</button>
      </div>
      <div class="nav-presets">
        <button type="button" class="nav-preset" data-preset="tamilnadu">Tamil Nadu</button>
        <button type="button" class="nav-preset" data-preset="nclt">NCLT</button>
        <button type="button" class="nav-preset" data-preset="tribunals">Tribunals</button>
        <button type="button" class="nav-preset" data-preset="quasi">Quasi-judicial</button>
      </div>
      <div id="nav-impact-filters" class="nav-impact-filters" aria-label="Impact filters">
        <div class="nav-impact-head">
          <span class="nav-impact-title">Impact filters</span>
          <button type="button" id="btn-clear-filter" class="nav-clear-filter hidden">Clear</button>
        </div>
        <div class="nav-impact-grid">
          <button type="button" class="kpi-card" id="kpi-card-ir" data-card="ir"
                  title="High or severe independence risk — Risk mode + map filter">
            <span class="kpi-number" id="kpi-num-ir">—</span>
            <span class="kpi-label">High risk</span>
          </button>
          <button type="button" class="kpi-card" id="kpi-card-gaps" data-card="gaps"
                  title="Entities with structural gaps — Gaps mode + map filter">
            <span class="kpi-number" id="kpi-num-gaps">—</span>
            <span class="kpi-label">Gaps</span>
          </button>
          <button type="button" class="kpi-card" id="kpi-card-blocked" data-card="blocked"
                  title="Blocked, absent, or appellate vacuum — map filter">
            <span class="kpi-number" id="kpi-num-blocked">—</span>
            <span class="kpi-label">Blocked</span>
          </button>
          <button type="button" class="kpi-card" id="kpi-card-clog" data-card="clog"
                  title="Case clog critical/high overlay on map labels">
            <span class="kpi-number" id="kpi-num-clog">—</span>
            <span class="kpi-label">Clog</span>
          </button>
        </div>
      </div>
      <div id="nav-advanced-slot" class="nav-advanced-slot">
        <button type="button" id="btn-advanced-toggle" class="btn-advanced-toggle" aria-expanded="false" title="Relationship lenses and map options">Filters &amp; lenses</button>
        <div id="advanced-drawer" class="advanced-drawer nav-advanced-drawer hidden">
          <div class="advanced-drawer-inner">
            <div class="lens-header-row">
              <span class="lens-label">Relationship lenses</span>
              <div class="lens-bulk-actions">
                <button type="button" class="lens-bulk" id="lens-select-all" title="Show all relationship types">All</button>
                <button type="button" class="lens-bulk" id="lens-clear-all" title="Hide all relationship types">None</button>
              </div>
            </div>
            <div id="lens-toggles">
              <button type="button" class="lens-btn active" data-lens="appellate_chain" title="Show appellate chain">⚖ Appellate</button>
              <button type="button" class="lens-btn" data-lens="appointment" title="Show appointment relationships">👤 Appointment</button>
              <button type="button" class="lens-btn" data-lens="funding" title="Show funding flows">₹ Funding</button>
              <button type="button" class="lens-btn" data-lens="supervisory" title="Show supervisory relationships">👁 Supervisory</button>
              <button type="button" class="lens-btn" data-lens="audit" title="Show audit relationships">🔍 Audit</button>
              <button type="button" class="lens-btn" data-lens="complaint" title="Show complaint mechanisms">📋 Complaints</button>
              <button type="button" class="lens-btn" data-lens="digital" title="Show digital infrastructure">🖥 Digital</button>
              <button type="button" class="lens-btn" data-lens="security" title="Show security relationships">🛡 Security</button>
              <button type="button" class="lens-btn" data-lens="training" title="Show training / professional links">📚 Training</button>
              <button type="button" class="lens-btn" data-lens="statutory_ref" title="Show statutory references">§ Statutory</button>
              <button type="button" class="lens-btn lens-investigative" data-lens="investigative" title="CBI/ED investigative overlay">⚠ CBI/ED</button>
            </div>
            <div id="explorer-tree-actions" class="explorer-tree-actions hidden">
              <span class="lens-label explorer-appellate-label">District lattices</span>
              <div class="explorer-tree-row" id="explorer-district-row">
                <button type="button" class="explorer-tree-btn" id="explorer-expand-districts" title="Expand all district rows">Expand districts</button>
                <button type="button" class="explorer-tree-btn" id="explorer-collapse-districts" title="Collapse district rows">Collapse districts</button>
              </div>
              <p class="explorer-tree-hint">Keys: <kbd>−</kbd> collapse all district lattices · <kbd>+</kbd> expand</p>
            </div>
            <div id="derived-toggles">
              <div class="unvalidated-note" id="unvalidated-note">⚐ Derived scores — pending community review</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div id="nav-tree-scroll" class="nav-tree-scroll">
      <div id="nav-tree-list" class="nav-tree-list"></div>
    </div>
  </aside>

  <main id="focus-panel" aria-label="Map — three generations">
    <div id="focus-header">
      <div id="focus-breadcrumbs" class="focus-breadcrumbs" aria-label="Map path"></div>
      <div class="focus-zoom-controls" aria-label="Map zoom and pan">
        <button type="button" id="btn-focus-zoom-in" title="Zoom in">+</button>
        <button type="button" id="btn-focus-zoom-reset" title="Fit map to view">⌂</button>
        <button type="button" id="btn-focus-zoom-out" title="Zoom out">−</button>
      </div>
    </div>
    <p class="focus-map-hint" id="focus-map-hint">Scroll to pan · drag map · pinch or Ctrl+wheel to zoom</p>
    <div id="focus-canvas-wrap" tabindex="0" aria-label="Map — scrollable">
      <svg id="focus-svg" class="focus-svg">
        <defs>
          <marker id="arrow-appellate_chain" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#2c3e50"/>
          </marker>
          <marker id="arrow-appointment" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#e67e22"/>
          </marker>
          <marker id="arrow-funding" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#27ae60"/>
          </marker>
          <marker id="arrow-supervisory" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#8e44ad"/>
          </marker>
          <marker id="arrow-audit" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#7f8c8d"/>
          </marker>
          <marker id="arrow-complaint" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#e74c3c"/>
          </marker>
          <marker id="arrow-investigative" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#c0392b"/>
          </marker>
          <marker id="arrow-digital" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#2980b9"/>
          </marker>
          <marker id="arrow-security" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#6d4c41"/>
          </marker>
          <marker id="arrow-training" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#16a085"/>
          </marker>
          <marker id="arrow-statutory_ref" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#bdc3c7"/>
          </marker>
          <pattern id="pat-exception-stripes" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="8" height="8" fill="rgba(255,255,255,0)"/>
            <path d="M0,8 L8,0 M-2,2 L2,-2 M6,10 L10,6" stroke="rgba(231,76,60,0.85)" stroke-width="2.5"/>
          </pattern>
        </defs>
        <g id="focus-root">
          <g id="focus-layer-edges"></g>
          <g id="focus-layer-nodes"></g>
        </g>
      </svg>
    </div>

    <div id="neighborhood-panel" class="hidden" role="dialog" aria-modal="false" aria-labelledby="neighborhood-title">
      <div class="neighborhood-backdrop" aria-hidden="true"></div>
      <div class="neighborhood-card">
        <div class="neighborhood-card-header">
          <div>
            <div id="neighborhood-title" class="neighborhood-title">Neighborhood</div>
            <div id="neighborhood-subtitle" class="neighborhood-subtitle"></div>
          </div>
          <button type="button" id="neighborhood-close" class="neighborhood-close" aria-label="Close neighborhood map">✕</button>
        </div>
        <div id="neighborhood-legend" class="neighborhood-legend" role="toolbar" aria-label="Filter neighborhood links"></div>
        <div class="neighborhood-body">
          <div class="neighborhood-graph-wrap">
            <div class="neighborhood-graph-zoom" aria-label="Neighborhood graph zoom">
              <button type="button" id="nb-zoom-in" class="nb-zoom-btn" title="Zoom in">+</button>
              <button type="button" id="nb-zoom-reset" class="nb-zoom-btn" title="Fit graph to view">⌂</button>
              <button type="button" id="nb-zoom-out" class="nb-zoom-btn" title="Zoom out">−</button>
            </div>
            <div id="neighborhood-graph-scroll" class="neighborhood-graph-scroll" tabindex="0" aria-label="Neighborhood graph — drag to pan, scroll or use +/− to zoom">
              <svg id="neighborhood-svg" class="neighborhood-svg"></svg>
            </div>
          </div>
          <div id="neighborhood-links" class="neighborhood-links" aria-label="Direct connections list"></div>
        </div>
      </div>
    </div>
  </main>

  <div id="inspector-resizer" class="inspector-resizer" role="separator" aria-orientation="vertical" aria-label="Resize detail panel" tabindex="0"></div>

  <aside id="inspector-panel" aria-label="Entity inspector">
    <div class="inspector-tabs" role="tablist">
      <button type="button" class="inspector-tab active" data-inspector-tab="detail">Entity detail</button>
      <button type="button" class="inspector-tab" data-inspector-tab="report">Group report</button>
      <button type="button" class="btn-ghost btn-print-mini" id="btn-print-detail" title="Print entity profile">Print</button>
    </div>
    <div id="inspector-tab-detail" class="inspector-tab-pane">
      <div id="detail-empty" class="detail-empty">
        <p>Select an entity in the map or tree to view its full structural profile — appointment, funding, gaps, risk scores, and sources.</p>
      </div>
      <div id="detail-panel" class="hidden">
        <header class="jem-print-brand" aria-hidden="true">
          <img src="public/assets/jem-mark.svg" class="jem-print-brand-mark" alt="JEM" width="32" height="32" decoding="async">
          <div class="jem-print-brand-text">
            <strong class="jem-print-brand-name">JEM</strong>
            <span class="jem-print-brand-tag">Judiciary Entity Map (India)</span>
          </div>
        </header>
        <div id="detail-panel-header">
          <div>
            <div id="detail-entity-name"></div>
            <div id="detail-entity-type"></div>
          </div>
          <button id="detail-close" type="button" aria-label="Clear selection">✕</button>
        </div>
        <div id="detail-panel-body"></div>
      </div>
    </div>
    <div id="inspector-tab-report" class="inspector-tab-pane scroll-pane hidden">
      <div class="group-report-toolbar">
        <button type="button" class="btn-ghost" id="btn-print-group">Print group report</button>
      </div>
      <div id="group-report-body" class="group-report-body"></div>
    </div>
  </aside>
</div>

<nav id="mobile-workspace-tabs" class="mobile-workspace-tabs hidden" aria-label="Switch panel">
  <button type="button" class="mobile-tab" data-mobile-panel="nav">Tree</button>
  <button type="button" class="mobile-tab active" data-mobile-panel="focus">Map</button>
  <button type="button" class="mobile-tab" data-mobile-panel="inspector">Detail</button>
</nav>

<div id="govt-level-legend" class="hidden">
  <div class="legend-item"><span class="legend-swatch central"></span>Central</div>
  <div class="legend-item"><span class="legend-swatch state"></span>State</div>
  <div class="legend-item"><span class="legend-swatch shared"></span>Shared</div>
</div>

<div id="quality-legend" class="hidden">
  <div class="ql-row"><span class="ql-sample verified">Text</span> Verified source</div>
  <div class="ql-row"><span class="ql-sample complete">Text</span> Complete</div>
  <div class="ql-row"><span class="ql-sample partial">Text?</span> Partial data</div>
  <div class="ql-row"><span class="ql-sample unverified">Text</span> Unverified</div>
  <div class="ql-row"><span class="ql-sample contested">Text⚑</span> Contested</div>
  <div class="ql-row"><span class="ql-node-sample not-constituted"></span> Not constituted</div>
  <div class="ql-row"><span class="ql-node-sample abolished"></span> Abolished</div>
</div>

<div id="map-status-bar" class="map-status-bar hidden" aria-live="polite">
  <span id="view-status-text" class="view-status-text"></span>
</div>

<div id="timeline-container" class="hidden">
  <div id="timeline-label-left">1950</div>
  <div id="timeline-track">
    <div id="timeline-events-layer"></div>
    <div id="timeline-progress"></div>
    <div id="timeline-thumb" draggable="false"></div>
  </div>
  <div id="timeline-label-right"></div>
  <div id="timeline-year-max" class="hidden"></div>
  <div id="timeline-year-display"></div>
</div>
`;

export function isMapShellMounted() {
  return !!document.getElementById('app-workspace');
}

/** Insert map workspace + timeline + legends (first map visit only). */
export function mountMapShell() {
  if (isMapShellMounted()) return;

  const anchor = document.querySelector('script[src*="main.js"]');
  const holder = document.createElement('div');
  holder.innerHTML = MAP_SHELL_HTML.trim();

  const fragment = document.createDocumentFragment();
  while (holder.firstChild) {
    fragment.appendChild(holder.firstChild);
  }

  if (anchor?.parentNode) {
    anchor.parentNode.insertBefore(fragment, anchor);
  } else {
    document.body.appendChild(fragment);
  }
}
