// JEM — Central State Store
// All UI state lives here. Modules subscribe to changes.

import {
  buildDistrictAggregateIndex,
  PRINCIPAL_HC_BY_STATE_CODE,
  syntheticAggregateEntity,
  syntheticAggregateRelationships,
} from './districtAggregates.js';

// Relationship categories shown in Structure (and as baseline for other modes).
// Keeps the map navigable — appointment / funding / etc. edges, not appellate-only.
const DEFAULT_STRUCTURE_LENSES = [
  'appellate_chain',
  'appointment',
  'funding',
  'supervisory',
  'audit',
  'complaint',
  'digital',
  'security',
  'training',
  'statutory_ref',
];

export const State = {
  // ── Data ──────────────────────────────────────────────
  graph: null,           // Loaded graph.json

  // ── View ──────────────────────────────────────────────
  zoomLevel: 0,          // 0=Constellation 1=Backbone 2=SubEntity 3=DetailPanel
  zoomTransform: null,   // d3.zoomTransform — current pan/zoom
  zoomScale: 1,          // transform.k — updated on every zoom event (see setTransform)
  selectedEntityId: null,

  // ── Time ──────────────────────────────────────────────
  currentYear: new Date().getFullYear(),

  // ── View mode (Structure | Risk | Gaps) ───────────────
  viewMode: 'structure', // 'structure' | 'risk' | 'gaps'

  // ── Filters / Lenses ──────────────────────────────────
  // Default Structure mode: appellate hierarchy only.
  activeLenses: new Set(DEFAULT_STRUCTURE_LENSES),
  showInvestigativeOverlay: false,
  activeImpactFilter: null,   // 'high_independence_risk' | 'not_constituted' | etc.

  // ── Derived Score Toggles ──────────────────────────────
  showIndependenceRisk: false,
  showDiscretionaryPower: false,

  // ── Gaps mode overlays (driven by setViewMode) ─────────
  showGaps: false,
  showExceptions: false,
  showCircularity: false,

  // ── Case-volume overlay (toggled from KPI strip "Critical clog" card) ──
  showCaseVolume: false,

  // ── Expand/Collapse ────────────────────────────────────
  // When true, only roots + expanded appellate children are shown; nodes with children get +/−.
  // If the graph has no appellate_chain from SC/President, we stay flat (all entities visible).
  useProgressiveExplorer: false,
  expandedEntityIds: new Set(),
  hiddenEntityIds: new Set(),
  _childrenByParent: null,

  /** Per-state district lattice: collapsed = generic or synthetic; expanded = every bench row. */
  _districtAggregateIndex: null,
  expandedDistrictAggregateIds: new Set(),

  // ── Subscribers ────────────────────────────────────────
  _listeners: {},

  get(key) {
    return this[key];
  },

  subscribe(event, fn) {
    if (!this._listeners[event]) this._listeners[event] = [];
    this._listeners[event].push(fn);
  },

  emit(event, data) {
    (this._listeners[event] || []).forEach(fn => fn(data));
  },

  // ── Setters ───────────────────────────────────────────
  setYear(year) {
    this.currentYear = year;
    this._buildBrowseIndex();
    this.emit('yearChanged', year);
  },

  setZoomLevel(level) {
    this.zoomLevel = level;
    this.emit('zoomLevelChanged', level);
    document.getElementById('zoom-level-label').textContent = `L${level}`;
  },

  setTransform(t) {
    this.zoomTransform = t;
    this.zoomScale = t.k;
    // Auto-infer zoom level from scale
    const k = t.k;
    // Keep the UX simple: avoid dropping into L0 (cluster dashboard),
    // which becomes unreadable at larger entity counts.
    let level = 1;
    if (k < 0.4) level = 1;
    else if (k >= 0.4 && k < 1.0) level = 1;
    else if (k >= 1.0 && k < 2.5) level = 2;
    else if (k >= 2.5) level = 2;  // Still Level 2 — Level 3 is click-triggered
    if (this.zoomLevel !== level) this.setZoomLevel(level);
  },

  selectEntity(id) {
    this.selectedEntityId = id;
    if (id) this.revealEntityOnMapForSelection(id);
    this.emit('entitySelected', id);
    if (id) this.setZoomLevel(3);
    else this.setZoomLevel(2);
  },

  /** District lattice group owned by this principal High Court (e.g. Madras → TN). */
  districtGroupForPrincipalHc(hcId) {
    if (!hcId || !this._districtAggregateIndex?.groups) return null;
    const direct = this._districtAggregateIndex.groups.find(g => g.hcTargetId === hcId);
    if (direct) return direct;
    return this._districtAggregateIndex.groups.find(
      g => PRINCIPAL_HC_BY_STATE_CODE[g.stateCode] === hcId
    ) || null;
  },

  /**
   * Selecting a principal HC should show its district lattice on the map
   * (expand explorer branch + individual district benches, not only the summary node).
   */
  revealEntityOnMapForSelection(id) {
    if (!id || !this.graph) return;
    let changed = false;

    const aggToggle = this.getDistrictAggregateToggleForEntityId(id);
    if (aggToggle && !this.expandedDistrictAggregateIds.has(aggToggle.groupId)) {
      this.expandedDistrictAggregateIds.add(aggToggle.groupId);
      this.emit('aggregateChanged', aggToggle.groupId);
      changed = true;
    }

    if (this.isPrincipalHighCourt(id) && this.useProgressiveExplorer) {
      const kids = this._childrenByParent?.[id] || [];
      if (kids.length && !this.expandedEntityIds.has(id)) {
        this.expandedEntityIds.add(id);
        changed = true;
      }
      if (this.expandDistrictLatticeForHc(id)) changed = true;
    }

    if (changed) {
      this._recomputeHiddenFromExpanded();
      this.emit('collapseChanged', id);
    }
  },

  clearEntity() {
    if (this.selectedEntityId === null) return;
    this.selectedEntityId = null;
    this.emit('entitySelected', null);
    // Return to Level 1 or 2 based on current transform
    const k = this.zoomTransform ? this.zoomTransform.k : 0.3;
    this.setZoomLevel(k >= 1.0 ? 2 : k >= 0.4 ? 1 : 0);
  },

  setViewMode(mode) {
    if (mode !== 'structure' && mode !== 'risk' && mode !== 'gaps') return;
    this.viewMode = mode;
    this.activeLenses = new Set(DEFAULT_STRUCTURE_LENSES);
    this.showInvestigativeOverlay = false;

    if (mode === 'structure') {
      this.showIndependenceRisk = false;
      this.showDiscretionaryPower = false;
      this.showGaps = false;
      this.showExceptions = false;
      this.showCircularity = false;
    } else if (mode === 'risk') {
      this.showIndependenceRisk = true;
      this.showDiscretionaryPower = true;
      this.showGaps = false;
      this.showExceptions = false;
      this.showCircularity = false;
    } else {
      this.showIndependenceRisk = false;
      this.showDiscretionaryPower = false;
      this.showGaps = true;
      this.showExceptions = true;
      this.showCircularity = true;
    }

    this.emit('viewModeChanged', mode);
    this.emit('lensChanged', 'viewMode');
    this.emit('derivedToggle', 'viewMode');
  },

  toggleLens(lens) {
    if (lens === 'investigative') {
      this.showInvestigativeOverlay = !this.showInvestigativeOverlay;
      this.emit('lensChanged', lens);
      return;
    }
    if (this.activeLenses.has(lens)) {
      this.activeLenses.delete(lens);
    } else {
      this.activeLenses.add(lens);
    }
    this.emit('lensChanged', lens);
  },

  /** All standard relationship categories (not the CBI/ED overlay). */
  selectAllRelationshipLenses() {
    this.activeLenses = new Set(DEFAULT_STRUCTURE_LENSES);
    this.emit('lensChanged', 'bulk');
  },

  /** No relationship edges; turns off investigative overlay too. */
  clearAllRelationshipLenses() {
    this.activeLenses = new Set();
    this.showInvestigativeOverlay = false;
    this.emit('lensChanged', 'bulk');
  },

  setImpactFilter(filterKey) {
    if (this.activeImpactFilter === filterKey) {
      this.activeImpactFilter = null;
    } else {
      this.activeImpactFilter = filterKey;
    }
    this.emit('filterChanged', this.activeImpactFilter);
  },

  toggleIR() {
    this.showIndependenceRisk = !this.showIndependenceRisk;
    this.emit('derivedToggle', 'ir');
  },

  toggleDP() {
    this.showDiscretionaryPower = !this.showDiscretionaryPower;
    this.emit('derivedToggle', 'dp');
  },

  toggleCaseVolume() {
    this.showCaseVolume = !this.showCaseVolume;
    this.emit('derivedToggle', 'caseVolume');
  },

  initDistrictAggregates() {
    if (!this.graph) return;
    this._districtAggregateIndex = buildDistrictAggregateIndex(
      this.graph.entities,
      this.graph.relationships || []
    );
    this.expandedDistrictAggregateIds = new Set();
  },

  initExplorerDefaults() {
    if (!this.graph) return;
    this.initDistrictAggregates();
    this._childrenByParent = this._buildChildrenByParent();
    const roots = ['supreme_court_india', 'president_india'];
    const anyAppellateChild = roots.some(
      r => (this._childrenByParent[r] || []).length > 0
    );
    if (!anyAppellateChild) {
      this.useProgressiveExplorer = false;
      this.expandedEntityIds = new Set();
      this.hiddenEntityIds = new Set();
      this.emit('collapseChanged', null);
      return;
    }
    // Focus Trinity replaces the old full-map progressive reveal; do not hide appellate children globally.
    this.useProgressiveExplorer = false;
    this.expandedEntityIds = new Set();
    this.hiddenEntityIds = new Set();
    this.emit('collapseChanged', null);
  },

  isPrincipalHighCourt(id) {
    return Boolean(id?.startsWith('hc_') && !id.includes('_bench_'));
  },

  expandDistrictLatticeForHc(hcId) {
    const g = this.districtGroupForPrincipalHc(hcId);
    if (!g || this.expandedDistrictAggregateIds.has(g.groupId)) return false;
    this.expandedDistrictAggregateIds.add(g.groupId);
    this.emit('aggregateChanged', g.groupId);
    return true;
  },

  collapseDistrictLatticeForHc(hcId) {
    const g = this.districtGroupForPrincipalHc(hcId);
    if (!g || !this.expandedDistrictAggregateIds.has(g.groupId)) return false;
    this.expandedDistrictAggregateIds.delete(g.groupId);
    this.emit('aggregateChanged', g.groupId);
    return true;
  },

  hasAppellateChildren(entityId) {
    return ((this._childrenByParent?.[entityId]) || []).length > 0;
  },

  /** Per-node +/− specs for map controls (appellate tree + district lattice). */
  getExplorerToggleSpecs(entity) {
    const id = entity?.id;
    if (!id) return [];
    const specs = [];

    if (this.useProgressiveExplorer && this.hasAppellateChildren(id)) {
      const n = (this._childrenByParent[id] || []).length;
      const expanded = this.expandedEntityIds.has(id);
      specs.push({
        role: 'appellate',
        expanded,
        title: expanded
          ? `Collapse ${n} direct appellate child${n === 1 ? '' : 'ren'}`
          : `Expand ${n} direct appellate child${n === 1 ? '' : 'ren'}`,
        activate: () => this.toggleExpand(id),
      });
    }

    const dist = this.getDistrictAggregateToggleForEntityId(id);
    if (dist) {
      const group = this._districtAggregateIndex?.groups?.find(g => g.groupId === dist.groupId);
      const hcId = group?.hcTargetId;
      const onPrincipalHc = Boolean(hcId && id === hcId);
      if (this.useProgressiveExplorer && onPrincipalHc && !this.expandedEntityIds.has(id)) {
        return specs;
      }
      const stateLabel = (dist.stateCode || group?.stateCode || '').toUpperCase();
      specs.push({
        role: 'district',
        expanded: dist.expanded,
        title: dist.expanded
          ? `Collapse ${stateLabel} district courts to one row`
          : `Expand ${stateLabel} district court benches`,
        activate: () => this.toggleDistrictAggregate(dist.groupId),
      });
    }
    return specs;
  },

  toggleExpand(entityId) {
    if (!entityId) return;
    if (!this.useProgressiveExplorer) return;
    if (this.expandedEntityIds.has(entityId)) {
      this.expandedEntityIds.delete(entityId);
      if (this.isPrincipalHighCourt(entityId)) this.collapseDistrictLatticeForHc(entityId);
    } else {
      this.expandedEntityIds.add(entityId);
      // Blue + reveals appellate children; also open the state's district lattice.
      if (this.isPrincipalHighCourt(entityId)) this.expandDistrictLatticeForHc(entityId);
    }
    this._recomputeHiddenFromExpanded();
    this.emit('collapseChanged', entityId);
  },

  /** Expand every branch under SC/President so the full appellate subtree is visible. */
  expandAllAppellateInExplorer() {
    if (!this.useProgressiveExplorer || !this.graph) return;
    if (!this._childrenByParent) this._childrenByParent = this._buildChildrenByParent();
    const roots = ['supreme_court_india', 'president_india'];
    const expanded = new Set();
    const q = roots.filter(r => this.graph.entities.some(e => e.id === r));
    const seen = new Set();
    while (q.length) {
      const id = q.shift();
      if (seen.has(id)) continue;
      seen.add(id);
      const ch = this._childrenByParent[id] || [];
      if (ch.length) {
        expanded.add(id);
        for (const c of ch) q.push(c);
      }
    }
    this.expandedEntityIds = expanded;
    this._recomputeHiddenFromExpanded();
    this.emit('collapseChanged', 'expandAll');
  },

  /** Collapse back to roots only (still in progressive mode). */
  collapseExplorerToRoots() {
    if (!this.useProgressiveExplorer || !this.graph) return;
    this.expandedEntityIds = new Set();
    this._recomputeHiddenFromExpanded();
    this.emit('collapseChanged', 'collapseRoots');
  },

  _buildChildrenByParent() {
    const children = {};
    for (const r of (this.graph?.relationships || [])) {
      if (r.relationship_category !== 'appellate_chain') continue;
      const parent = r.target;
      const child = r.source;
      if (!parent || !child) continue;
      (children[parent] ||= []).push(child);
    }
    return children;
  },

  _recomputeHiddenFromExpanded() {
    if (!this.graph) return;
    if (!this._childrenByParent) this._childrenByParent = this._buildChildrenByParent();

    const allIds = new Set((this.graph.entities || []).map(e => e.id));
    const visible = new Set();

    // Roots always visible (top-level band)
    const roots = ['supreme_court_india', 'president_india'];
    for (const r of roots) if (allIds.has(r)) visible.add(r);

    // Reveal tree one level at a time based on expanded nodes.
    const stack = [...visible];
    while (stack.length) {
      const cur = stack.pop();
      if (!this.expandedEntityIds.has(cur)) continue;
      const kids = this._childrenByParent[cur] || [];
      for (const k of kids) {
        if (!allIds.has(k) || visible.has(k)) continue;
        visible.add(k);
        stack.push(k);
      }
    }

    this.hiddenEntityIds = new Set([...allIds].filter(id => !visible.has(id)));
  },

  toggleDistrictAggregate(groupId) {
    if (!groupId || !this._districtAggregateIndex?.groups) return;
    if (this.expandedDistrictAggregateIds.has(groupId)) {
      this.expandedDistrictAggregateIds.delete(groupId);
    } else {
      this.expandedDistrictAggregateIds.add(groupId);
    }
    this.emit('aggregateChanged', groupId);
  },

  expandAllDistrictAggregates() {
    if (!this._districtAggregateIndex?.groups) return;
    for (const g of this._districtAggregateIndex.groups) {
      this.expandedDistrictAggregateIds.add(g.groupId);
    }
    this.emit('aggregateChanged', 'expandDistricts');
  },

  collapseAllDistrictAggregates() {
    this.expandedDistrictAggregateIds = new Set();
    this.emit('aggregateChanged', 'collapseDistricts');
  },

  getDistrictAggregateToggleForEntityId(id) {
    if (!this._districtAggregateIndex?.groups) return null;
    const fromPrincipal = this.districtGroupForPrincipalHc(id);
    if (fromPrincipal) {
      return {
        groupId: fromPrincipal.groupId,
        stateCode: fromPrincipal.stateCode,
        expanded: this.expandedDistrictAggregateIds.has(fromPrincipal.groupId),
      };
    }
    for (const g of this._districtAggregateIndex.groups) {
      const synthId = g.synthetic ? `__jem_agg_${g.stateCode}_district_courts` : null;
      if (g.proxyId === id || (synthId && synthId === id)) {
        return {
          groupId: g.groupId,
          stateCode: g.stateCode,
          expanded: this.expandedDistrictAggregateIds.has(g.groupId),
        };
      }
    }
    return null;
  },

  _applyDistrictAggregateToList(list) {
    if (!this._districtAggregateIndex?.groups?.length) return list;
    const drop = new Set();
    for (const g of this._districtAggregateIndex.groups) {
      const expanded = this.expandedDistrictAggregateIds.has(g.groupId);
      if (!expanded) {
        for (const mid of g.memberIds) drop.add(mid);
      } else if (g.proxyId) {
        drop.add(g.proxyId);
      }
    }
    const out = list.filter(e => !drop.has(e.id));
    for (const g of this._districtAggregateIndex.groups) {
      if (!g.synthetic) continue;
      if (this.expandedDistrictAggregateIds.has(g.groupId)) continue;
      // Collapsed lattice only when its appellate parent is on screen and drilled into.
      if (!g.hcTargetId) continue;
      if (this.hiddenEntityIds.has(g.hcTargetId)) continue;
      if (this.useProgressiveExplorer && !this.expandedEntityIds.has(g.hcTargetId)) continue;
      out.push(syntheticAggregateEntity(g, this.graph.entities));
    }
    return out;
  },

  _extraDistrictAggregateRelationships(visibleIds) {
    const extra = [];
    if (!this._districtAggregateIndex?.groups) return extra;
    for (const g of this._districtAggregateIndex.groups) {
      if (!g.synthetic || this.expandedDistrictAggregateIds.has(g.groupId)) continue;
      for (const r of syntheticAggregateRelationships(g)) {
        if (visibleIds.has(r.source) && visibleIds.has(r.target)) extra.push(r);
      }
    }
    return extra;
  },

  // ── Queries ───────────────────────────────────────────
  getVisibleEntities() {
    if (!this.graph) return [];
    const list = this.graph.entities.filter(e => {
      // Time filter
      const created = e.created_year || 1950;
      if (created > this.currentYear) return false;

      // Impact filter — show matches even when progressive explorer collapsed them
      if (this.activeImpactFilter) {
        return this._matchesImpactFilter(e, this.activeImpactFilter);
      }

      if (this.hiddenEntityIds.has(e.id)) return false;
      return true;
    });
    const out = this._applyDistrictAggregateToList(list);
    return this._includeExpandedDistrictLatticeMembers(out);
  },

  /** District benches stay visible when their lattice is expanded, even if explorer path skips them. */
  _includeExpandedDistrictLatticeMembers(list) {
    if (!this._districtAggregateIndex?.groups?.length) return list;
    const have = new Set(list.map(e => e.id));
    const extra = [];
    for (const g of this._districtAggregateIndex.groups) {
      if (!this.expandedDistrictAggregateIds.has(g.groupId)) continue;
      if (g.hcTargetId && this.hiddenEntityIds.has(g.hcTargetId)) continue;
      if (this.useProgressiveExplorer && g.hcTargetId && !this.expandedEntityIds.has(g.hcTargetId)) {
        continue;
      }
      for (const mid of g.memberIds) {
        if (have.has(mid)) continue;
        const e = this.graph.entities.find(x => x.id === mid);
        if (!e) continue;
        const created = e.created_year || 1950;
        if (created > this.currentYear) continue;
        if (this.activeImpactFilter && !this._matchesImpactFilter(e, this.activeImpactFilter)) continue;
        extra.push(e);
        have.add(mid);
      }
    }
    return extra.length ? list.concat(extra) : list;
  },

  _matchesImpactFilter(entity, filter) {
    const derived = entity.derived || {};
    switch(filter) {
      case 'high_independence_risk':
        return ['high', 'severe'].includes(derived.independence_risk_level);
      case 'appointer_funder_same':
        // Approximation — full check in build.py
        return derived.independence_risk_score >= 7;
      case 'no_public_criteria':
        return entity.appointment_criteria_public === false;
      case 'not_constituted':
        return entity.operational_status === 'Not_Constituted';
      case 'no_external_complaint':
        return entity.complaint_external_exists === false;
      case 'blocked_or_absent': {
        // KPI card 3 — appellate vacuums + bodies legislated but never set up.
        const gapTypes = (entity.gaps || [])
          .map(g => (g && typeof g === 'object' ? String(g.gap_type || '').toLowerCase() : null))
          .filter(Boolean);
        return entity.operational_status === 'De_Facto_Blocked'
            || entity.operational_status === 'Not_Constituted'
            || gapTypes.includes('appellate_vacuum');
      }
      case 'has_structural_gaps':
        return Boolean(entity.gap_flag) || (Array.isArray(entity.gaps) && entity.gaps.length > 0);
      default:
        return true;
    }
  },

  getVisibleRelationships() {
    if (!this.graph) return [];
    const visibleIds = new Set(this.getVisibleEntities().map(e => e.id));

    const base = this.graph.relationships.filter(r => {
      // Both endpoints must be visible
      if (!visibleIds.has(r.source) || !visibleIds.has(r.target)) return false;

      // Historical relationships: show as faded if year_abolished < currentYear
      // (handled by renderer opacity, not filtered out)

      // Lens filter
      if (r.relationship_category === 'investigative') {
        return this.showInvestigativeOverlay;
      }
      return this.activeLenses.has(r.relationship_category);
    });
    return base.concat(this._extraDistrictAggregateRelationships(visibleIds));
  },

  // Graph bundles may nest palettes under `legends` (repo-root graph.json) or
  // expose the same keys at the top level (jem/scripts/build.py output).
  getRelationshipColors() {
    if (!this.graph) return {};
    return this.graph.legends?.relationship_colors
      || this.graph.relationship_colors
      || {};
  },

  getDataQualityLegend() {
    if (!this.graph) return {};
    return this.graph.legends?.data_quality
      || this.graph.data_quality_legend
      || {};
  },

  getOperationalStatusLegend() {
    if (!this.graph) return {};
    return this.graph.legends?.operational_status
      || this.graph.operational_status_legend
      || {};
  },

  getIndependenceRiskColors() {
    if (!this.graph) return {};
    return this.graph.legends?.independence_risk_colors
      || this.graph.independence_risk_colors
      || {};
  },

  getStructuralHealthColors() {
    return this.graph?.legends?.structural_health_colors || {
      healthy: '#27ae60',
      watch: '#f1c40f',
      at_risk: '#f39c12',
      critical: '#e74c3c',
    };
  },

  structuralHealthBand(score) {
    if (score == null || Number.isNaN(score)) return null;
    if (score < 0.3) return 'critical';
    if (score < 0.6) return 'at_risk';
    if (score < 0.8) return 'watch';
    return 'healthy';
  },

  getDiscretionaryPowerColor() {
    return '#6366f1';
  },

  getEntityById(id) {
    if (!this.graph) return null;
    if (id?.startsWith('__browse_')) return this.getBrowseGroupEntity(id);
    const found = this.graph.entities.find(e => e.id === id);
    if (found) return found;
    if (id.startsWith('__jem_agg_') && this._districtAggregateIndex?.groups) {
      for (const g of this._districtAggregateIndex.groups) {
        if (!g.synthetic) continue;
        if (id === `__jem_agg_${g.stateCode}_district_courts`) {
          return syntheticAggregateEntity(g, this.graph.entities);
        }
      }
    }
    return null;
  },

  isEntityVisible(entity) {
    const created = entity.created_year || 1950;
    return created <= this.currentYear;
  },

  isEntityHistorical(entity) {
    const abolished = entity.abolished_year;
    return abolished && abolished < this.currentYear;
  },

  isRelationshipHistorical(rel) {
    const abolished = rel.year_abolished;
    return abolished && abolished < this.currentYear;
  },

  // ── Focus Trinity UI ───────────────────────────────────
  navMode: 'appellate',
  browseFacet: 'cluster',
  focusEntityId: null,
  treeSelectedIds: new Set(),
  _parentsByChild: null,
  _browseIndex: null,
  _browseKeyMap: null,

  browseGroupId(facet, key) {
    const slug = String(key).replace(/[^a-zA-Z0-9]+/g, '_');
    return `__browse_${facet}_${slug}`;
  },

  initFocusDefaults() {
    const roots = ['supreme_court_india', 'president_india'];
    const found = roots.find(r => this.graph?.entities?.some(e => e.id === r));
    this.focusEntityId = found || this.graph?.entities?.[0]?.id || null;
    this._parentsByChild = this._buildParentsByChild();
    this._buildBrowseIndex();
    this.emit('focusChanged', this.focusEntityId);
  },

  _buildParentsByChild() {
    const parents = {};
    for (const r of (this.graph?.relationships || [])) {
      if (r.relationship_category !== 'appellate_chain') continue;
      if (r.target && r.source) parents[r.source] = r.target;
    }
    return parents;
  },

  _buildBrowseIndex() {
    if (!this.graph) return;
    const clusters = {};
    const types = {};
    const states = {};
    for (const e of this.graph.entities) {
      if (!this._entityPassesTimeFilter(e)) continue;
      const c = e.cluster || 'other';
      (clusters[c] ||= []).push(e.id);
      const t = e.type || 'Other';
      (types[t] ||= []).push(e.id);
      const scope = e._detail?.jurisdiction_scope || e.jurisdiction_scope;
      if (scope) {
        const key = String(scope);
        (states[key] ||= []).push(e.id);
      }
    }
    const sortIds = (ids) => ids.sort((a, b) => {
      const ea = this.getEntityById(a);
      const eb = this.getEntityById(b);
      return (ea?.name || a).localeCompare(eb?.name || b);
    });
    Object.values(clusters).forEach(sortIds);
    Object.values(types).forEach(sortIds);
    Object.values(states).forEach(sortIds);
    this._browseIndex = { cluster: clusters, type: types, state: states };
    if (this.graph.browse_index) {
      Object.assign(this._browseIndex.cluster, this.graph.browse_index.clusters || {});
      Object.assign(this._browseIndex.type, this.graph.browse_index.types || {});
      Object.assign(this._browseIndex.state, this.graph.browse_index.states || {});
    }
    this._browseKeyMap = {};
    for (const facet of ['cluster', 'type', 'state']) {
      for (const key of Object.keys(this._browseIndex[facet] || {})) {
        this._browseKeyMap[this.browseGroupId(facet, key)] = { facet, key };
      }
    }
  },

  _entityPassesTimeFilter(e) {
    const created = e.created_year || 1950;
    return created <= this.currentYear;
  },

  setNavMode(mode) {
    if (mode !== 'appellate' && mode !== 'browse') return;
    this.navMode = mode;
    if (mode === 'appellate' && !this.getEntityById(this.focusEntityId)) {
      this.initFocusDefaults();
    } else if (mode === 'browse') {
      const keys = Object.keys(this._browseIndex?.[this.browseFacet] || {});
      if (keys.length && !String(this.focusEntityId || '').startsWith('__browse_')) {
        this.focusEntityId = this.browseGroupId(this.browseFacet, keys[0]);
      }
    }
    this.emit('navModeChanged', mode);
    this.emit('focusChanged', this.focusEntityId);
  },

  setBrowseFacet(facet) {
    if (!['cluster', 'type', 'state'].includes(facet)) return;
    this.browseFacet = facet;
    const keys = Object.keys(this._browseIndex?.[facet] || {});
    if (keys.length) this.focusEntityId = this.browseGroupId(facet, keys[0]);
    this.emit('browseFacetChanged', facet);
    this.emit('focusChanged', this.focusEntityId);
  },

  setFocusEntity(id, options = {}) {
    if (!id) return;
    this.focusEntityId = id;
    if (options.select === true) this.selectEntity(id);
    this.emit('focusChanged', id);
  },

  getBrowseGroupEntity(id) {
    if (!id?.startsWith('__browse_')) return null;
    const mapped = this._browseKeyMap?.[id];
    const facet = mapped?.facet;
    const key = mapped?.key;
    if (!facet || !key) return null;
    const memberIds = this._browseIndex?.[facet]?.[key] || [];
    const members = memberIds.map(mid => this.getEntityById(mid)).filter(Boolean);
    let gapCount = 0;
    let highIr = 0;
    for (const m of members) {
      if (m.gap_flag || (m.gaps?.length > 0)) gapCount++;
      const lvl = (m.derived || {}).independence_risk_level;
      if (lvl === 'high' || lvl === 'severe') highIr++;
    }
    return {
      id,
      name: key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      abbreviation: `${members.length} entities`,
      type: 'BrowseGroup',
      cluster: facet === 'cluster' ? key : 'browse',
      level_of_government: 'Central',
      operational_status: 'Active',
      data_quality: 'complete',
      _jemBrowseGroup: true,
      memberIds,
      rollup: { count: members.length, gapCount, highIr },
    };
  },

  getAppellateChildren(parentId, { forFocusView = false } = {}) {
    if (!parentId) return [];
    if (parentId.startsWith('__browse_')) {
      const g = this.getBrowseGroupEntity(parentId);
      return (g?.memberIds || [])
        .map(id => this.getEntityById(id))
        .filter(e => e && this._entityPassesTimeFilter(e));
    }
    if (!this._childrenByParent) this._childrenByParent = this._buildChildrenByParent();
    const ids = this._childrenByParent[parentId] || [];
    return ids
      .map(id => this.getEntityById(id))
      .filter(e => {
        if (!e || !this._entityPassesTimeFilter(e)) return false;
        if (forFocusView) return true;
        return !this.hiddenEntityIds.has(e.id);
      });
  },

  getFocusTrinitySlice() {
    const parentRaw = this.focusEntityId
      ? (this.getEntityById(this.focusEntityId) || this.getBrowseGroupEntity(this.focusEntityId))
      : null;
    if (!parentRaw) {
      return { parent: null, children: [], grandchildren: [], entityIds: new Set() };
    }

    let children = this.getAppellateChildren(parentRaw.id, { forFocusView: true });
    if (this.activeImpactFilter) {
      children = children.filter(e => this._matchesImpactFilter(e, this.activeImpactFilter));
    }

    const grandchildren = [];
    const childIds = new Set();
    for (const ch of children) {
      childIds.add(ch.id);
      let gcs = this.getAppellateChildren(ch.id, { forFocusView: true }).filter(e => !e._jemBrowseGroup);
      if (this.activeImpactFilter) {
        gcs = gcs.filter(e => this._matchesImpactFilter(e, this.activeImpactFilter));
      }
      for (const gc of gcs) grandchildren.push(gc);
    }

    const entityIds = new Set([parentRaw.id, ...children.map(c => c.id), ...grandchildren.map(g => g.id)]);

    return { parent: parentRaw, children, grandchildren, entityIds };
  },

  getTrinityRelationships(entityIds) {
    if (!this.graph || !entityIds?.size) return [];
    const visible = entityIds;
    return (this.graph.relationships || []).filter(r => {
      if (!visible.has(r.source) || !visible.has(r.target)) return false;
      if (r.relationship_category === 'investigative') {
        return this.showInvestigativeOverlay;
      }
      return this.activeLenses.has(r.relationship_category);
    });
  },

  ensureEntityInTrinityView(entityId) {
    if (!entityId || !this.graph) return;
    if (this.navMode === 'browse') {
      const e = this.getEntityById(entityId);
      if (!e) return;
      for (const [facet, groups] of Object.entries(this._browseIndex || {})) {
        for (const [key, ids] of Object.entries(groups)) {
          if (ids.includes(entityId)) {
            this.browseFacet = facet;
            this.focusEntityId = entityId;
            this.emit('browseFacetChanged', facet);
            this.emit('focusChanged', entityId);
            return;
          }
        }
      }
      this.focusEntityId = entityId;
      this.emit('focusChanged', entityId);
      return;
    }

    if (entityId.startsWith('__jem_agg_') || entityId.startsWith('__browse_')) {
      this.focusEntityId = entityId;
      this.emit('focusChanged', entityId);
      return;
    }

    const parents = this._parentsByChild || this._buildParentsByChild();
    this._parentsByChild = parents;

    const asParent = () => {
      this.focusEntityId = entityId;
      this.emit('focusChanged', entityId);
    };

    const children = this._childrenByParent?.[entityId] || [];
    if (children.length) {
      asParent();
      return;
    }

    const p1 = parents[entityId];
    if (p1 && (this._childrenByParent?.[p1] || []).includes(entityId)) {
      this.focusEntityId = p1;
      this.emit('focusChanged', p1);
      return;
    }

    const p2 = p1 ? parents[p1] : null;
    if (p2) {
      this.focusEntityId = p2;
      this.emit('focusChanged', p2);
      return;
    }

    asParent();
  },

  toggleTreeSelection(id, on) {
    if (!id) return;
    if (on === undefined) {
      if (this.treeSelectedIds.has(id)) this.treeSelectedIds.delete(id);
      else this.treeSelectedIds.add(id);
    } else if (on) this.treeSelectedIds.add(id);
    else this.treeSelectedIds.delete(id);
    this.emit('treeSelectionChanged', this.treeSelectedIds);
  },

  clearTreeSelection() {
    this.treeSelectedIds = new Set();
    this.emit('treeSelectionChanged', this.treeSelectedIds);
  },

  getTreeSelectedEntities() {
    const out = [];
    for (const id of this.treeSelectedIds) {
      const e = this.getEntityById(id) || this.getBrowseGroupEntity(id);
      if (e && !e._jemBrowseGroup) out.push(e);
      else if (e?._jemBrowseGroup) {
        for (const mid of e.memberIds || []) {
          const m = this.getEntityById(mid);
          if (m) out.push(m);
        }
      }
    }
    return out;
  },
};
