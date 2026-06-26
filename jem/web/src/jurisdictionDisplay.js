// JEM — Territorial jurisdiction + cross-region appellate routing (profile sections)

import { State } from './state.js';
import { buildEntityConnectionSummary } from './entityConnections.js';

/** ISO state / UT codes used in jurisdiction_scope YAML. */
export const STATE_CODE_LABELS = {
  AN: 'Andaman & Nicobar',
  AP: 'Andhra Pradesh',
  AR: 'Arunachal Pradesh',
  AS: 'Assam',
  BR: 'Bihar',
  CH: 'Chandigarh',
  CG: 'Chhattisgarh',
  DL: 'Delhi',
  DN: 'Dadra & Nagar Haveli and Daman & Diu',
  GA: 'Goa',
  GJ: 'Gujarat',
  HP: 'Himachal Pradesh',
  HR: 'Haryana',
  JH: 'Jharkhand',
  JK: 'Jammu & Kashmir',
  KA: 'Karnataka',
  KL: 'Kerala',
  LA: 'Ladakh',
  LD: 'Lakshadweep',
  MH: 'Maharashtra',
  ML: 'Meghalaya',
  MN: 'Manipur',
  MP: 'Madhya Pradesh',
  MZ: 'Mizoram',
  NL: 'Nagaland',
  OD: 'Odisha',
  PB: 'Punjab',
  PY: 'Puducherry',
  RJ: 'Rajasthan',
  SK: 'Sikkim',
  TN: 'Tamil Nadu',
  TR: 'Tripura',
  TS: 'Telangana',
  UK: 'Uttarakhand',
  UP: 'Uttar Pradesh',
  WB: 'West Bengal',
};

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function humanizeToken(str) {
  return String(str || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function getJurisdictionScope(entity) {
  if (!entity) return null;
  return entity._detail?.jurisdiction_scope || entity.jurisdiction_scope || null;
}

function scopeCodes(scope) {
  if (!scope) return [];
  return [
    ...(scope.states_covered || []),
    ...(scope.uts_covered || []),
  ].map((c) => String(c).toUpperCase());
}

function formatCodeList(codes, { compact = false } = {}) {
  const uniq = [...new Set(codes.filter(Boolean))];
  if (!uniq.length) return '';
  if (compact) return uniq.join(', ');
  return uniq
    .map((code) => {
      const name = STATE_CODE_LABELS[code];
      return name ? `${name} (${code})` : code;
    })
    .join(', ');
}

/** City token from drt_* / drat_* id → state where the bench sits physically. */
const BENCH_CITY_STATE = {
  agra: 'UP',
  ahmedabad: 'GJ',
  allahabad: 'UP',
  amritsar: 'PB',
  aurangabad: 'MH',
  bengaluru: 'KA',
  bangalore: 'KA',
  bhopal: 'MP',
  chandigarh: 'CH',
  chennai: 'TN',
  coimbatore: 'TN',
  cuttack: 'OD',
  dehradun: 'UK',
  delhi: 'DL',
  ernakulam: 'KL',
  guwahati: 'AS',
  hyderabad: 'TS',
  indore: 'MP',
  jabalpur: 'MP',
  jaipur: 'RJ',
  jodhpur: 'RJ',
  kolkata: 'WB',
  kochi: 'KL',
  lucknow: 'UP',
  madurai: 'TN',
  mumbai: 'MH',
  nagpur: 'MH',
  patna: 'BR',
  prayagraj: 'UP',
  pune: 'MH',
  ranchi: 'JH',
  siliguri: 'WB',
  visakhapatnam: 'AP',
};

function benchSittingState(entity) {
  if (!entity?.id) return null;
  const m = entity.id.match(/^(?:drt|drat)_(.+)$/);
  if (!m) return null;
  const token = m[1].split('_')[0];
  return BENCH_CITY_STATE[token] || null;
}

/**
 * True when the appellate bench sits in a different state/UT than the
 * first-instance tribunal's territorial scope (e.g. AP DRT → Kolkata DRAT).
 */
function isGeographicCrossRegion(lowerEntity, appellateEntity) {
  const lowerScope = getJurisdictionScope(lowerEntity);
  const sitting = benchSittingState(appellateEntity);
  if (!lowerScope || !sitting) return false;
  const codes = new Set(scopeCodes(lowerScope));
  if (!codes.size) return false;
  return !codes.has(sitting);
}

function relNoteFor(entityId, otherId) {
  if (!State.graph?.relationships) return '';
  const rel = State.graph.relationships.find(
    (r) =>
      r.relationship_category === 'appellate_chain'
      && r.source === entityId
      && r.target === otherId,
  );
  return rel?.notes ? String(rel.notes).trim() : '';
}

function benchOfChildren(aggregateId) {
  if (!State.graph?.relationships) return [];
  return State.graph.relationships
    .filter(
      (r) =>
        r.target === aggregateId
        && (r.relationship_type === 'BenchOf' || r.relationship_category === 'bench_of'),
    )
    .map((r) => State.getEntityById(r.source))
    .filter(Boolean)
    .sort((a, b) => (a.name || '').localeCompare(b.name || ''));
}

function row(label, value) {
  if (!value) return '';
  return `<div class="detail-row">
    <span class="lbl">${escapeHtml(label)}</span>
    <span>${value}</span>
  </div>`;
}

function entityLink(entityId, label) {
  if (!entityId) return escapeHtml(label);
  return `<button type="button" class="detail-connection-row jurisdiction-entity-link" data-entity-id="${escapeHtml(entityId)}">
    <span class="detail-connection-name">${escapeHtml(label)}</span>
  </button>`;
}

function crossRegionCallout({ fromLabel, toLabel, note }) {
  return `<div class="jurisdiction-cross-region">
    <div class="jurisdiction-cross-region-head">Cross-region appellate routing</div>
    <p>First-instance matters at <strong>${escapeHtml(fromLabel)}</strong> appeal to
    <strong>${escapeHtml(toLabel)}</strong> — outside the tribunal's home state/UT footprint.</p>
    <p class="jurisdiction-friction-note">Geographic mismatch adds travel, filing, and scheduling friction.
    JEM maps the structural assignment; it does not measure transit or disposal delay.</p>
    ${note ? `<p class="jurisdiction-routing-source">${escapeHtml(note)}</p>` : ''}
  </div>`;
}

function renderScopeBlock(scope) {
  if (!scope) return '';
  let html = '';

  if (scope.is_all_india) {
    html += row('Territorial scope', '<span class="jurisdiction-chip jurisdiction-chip-all">All India</span>');
  }

  const states = formatCodeList(scope.states_covered || []);
  const uts = formatCodeList(scope.uts_covered || []);
  if (states) html += row('States covered', states);
  if (uts) html += row('Union Territories covered', uts);

  if (scope.is_shared_multi) {
    html += row('Shared jurisdiction', 'Multi-state / multi-UT body (shared regulator pattern)');
  }
  if (scope.shared_appointer) {
    html += row('Shared appointer', humanizeToken(scope.shared_appointer));
  }

  const types = (scope.jurisdiction_types || []).filter(Boolean);
  if (types.length) {
    html += row(
      'Jurisdiction types',
      types.map((t) => `<span class="jurisdiction-chip">${escapeHtml(humanizeToken(t))}</span>`).join(' '),
    );
  }

  return html;
}

function renderDratAggregateBenchTable(entity) {
  const benches = benchOfChildren(entity.id);
  if (!benches.length) return '';

  let html = `<p class="jurisdiction-overview-lead">Only <strong>${benches.length} DRAT benches</strong> nationwide — each covers multiple states; appeals are often filed far from the first-instance DRT.</p>`;
  html += '<div class="jurisdiction-bench-table jurisdiction-bench-table-compact">';
  html += '<div class="jurisdiction-bench-head"><span>Bench</span><span>Scope</span></div>';

  for (const bench of benches) {
    const scope = getJurisdictionScope(bench);
    const territory = scope?.is_all_india
      ? 'All India'
      : formatCodeList(scopeCodes(scope), { compact: true }) || '—';
    html += `<div class="jurisdiction-bench-row">
      <span class="jurisdiction-bench-name">${entityLink(bench.id, bench.abbreviation || bench.name)}</span>
      <span class="jurisdiction-bench-states">${escapeHtml(territory)}</span>
    </div>`;
  }
  html += '</div>';
  return html;
}

function collectCrossRegionRoutes(entity) {
  const routes = [];
  const seen = new Set();

  function add(fromEntity, toEntity, note) {
    if (!fromEntity || !toEntity) return;
    if (!isGeographicCrossRegion(fromEntity, toEntity)) return;
    const key = `${fromEntity.id}→${toEntity.id}`;
    if (seen.has(key)) return;
    seen.add(key);
    routes.push({
      fromId: fromEntity.id,
      fromLabel: fromEntity.abbreviation || fromEntity.name,
      toId: toEntity.id,
      toLabel: toEntity.abbreviation || toEntity.name,
      note: note || '',
    });
  }

  if (entity.id === 'drat') {
    for (const bench of benchOfChildren(entity.id)) {
      const summary = buildEntityConnectionSummary(bench.id);
      for (const from of summary.appellateFrom) {
        add(State.getEntityById(from.entityId), bench, from.note || relNoteFor(from.entityId, bench.id));
      }
    }
    return routes;
  }

  const summary = buildEntityConnectionSummary(entity.id);
  for (const toward of summary.appellateToward) {
    const higher = State.getEntityById(toward.entityId);
    add(entity, higher, toward.note || relNoteFor(entity.id, higher?.id));
  }
  for (const from of summary.appellateFrom) {
    const lower = State.getEntityById(from.entityId);
    add(lower, entity, from.note || relNoteFor(lower?.id, entity.id));
  }
  return routes;
}

function renderCrossRegionRoutesBlock(routes, { collapsed = false } = {}) {
  if (!routes.length) return '';

  const chips = routes.map((r) => `
    <span class="jurisdiction-route-chip${r.note ? ' has-note' : ''}" title="${escapeHtml(r.note)}">
      ${entityLink(r.fromId, r.fromLabel)} → ${entityLink(r.toId, r.toLabel)}
    </span>`).join('');

  const openAttr = collapsed ? '' : ' open';
  return `<details class="jurisdiction-routes-fold"${openAttr}>
    <summary>
      <span class="jurisdiction-routing-title">Cross-region routes</span>
      <span class="jurisdiction-routes-count">${routes.length}</span>
    </summary>
    <div class="jurisdiction-route-grid">${chips}</div>
    <p class="jurisdiction-friction-note">Bench city often differs from the DRT’s state footprint — travel and filing friction; JEM does not measure delay.</p>
  </details>`;
}

function renderAppellateRouting(entity, { compact = false } = {}) {
  const summary = buildEntityConnectionSummary(entity.id);
  let html = '';

  if (summary.appellateToward.length) {
    html += '<div class="jurisdiction-routing-block jurisdiction-routing-compact">';
    html += '<div class="jurisdiction-routing-title">Appellate route (higher)</div>';
    for (const toward of summary.appellateToward) {
      const higher = State.getEntityById(toward.entityId);
      const cross = higher && isGeographicCrossRegion(entity, higher);
      const note = toward.note ? `<span class="jurisdiction-routing-source">${escapeHtml(compact ? toward.note.slice(0, 120) + (toward.note.length > 120 ? '…' : '') : toward.note)}</span>` : '';

      html += `<div class="jurisdiction-routing-item${cross ? ' is-cross-region' : ''}">
        ${entityLink(toward.entityId, toward.entityName)}
        ${cross ? '<span class="jurisdiction-cross-tag">Cross-region</span>' : ''}
        ${note}
      </div>`;

      if (!compact && cross && higher) {
        html += crossRegionCallout({
          fromLabel: entity.abbreviation || entity.name,
          toLabel: higher.abbreviation || higher.name,
          note: toward.note || relNoteFor(entity.id, higher.id),
        });
      }
    }
    html += '</div>';
  }

  if (summary.appellateFrom.length) {
    html += '<div class="jurisdiction-routing-block jurisdiction-routing-compact">';
    html += '<div class="jurisdiction-routing-title">Receives appeals from (lower)</div>';
    html += '<div class="jurisdiction-route-grid jurisdiction-route-grid-loose">';
    for (const from of summary.appellateFrom) {
      const lower = State.getEntityById(from.entityId);
      const cross = lower && isGeographicCrossRegion(lower, entity);
      html += `<span class="jurisdiction-route-chip${cross ? ' is-cross-region' : ''}">
        ${entityLink(from.entityId, from.entityName)}
        ${cross ? '<span class="jurisdiction-cross-tag">Cross-region</span>' : ''}
      </span>`;
    }
    html += '</div></div>';
  }

  return html;
}

/**
 * Profile sub-sections for column balancing (detail view). Side panel uses merged body.
 */
export function getJurisdictionProfileSections(entity) {
  const scope = getJurisdictionScope(entity);
  const hasScope = scope && (
    scope.is_all_india
    || scopeCodes(scope).length
    || (scope.jurisdiction_types || []).length
    || scope.is_shared_multi
    || scope.shared_appointer
  );

  const summary = buildEntityConnectionSummary(entity.id);
  const hasRouting = summary.appellateToward.length || summary.appellateFrom.length;
  const isDratAggregate = entity.id === 'drat';
  const crossRoutes = collectCrossRegionRoutes(entity);
  const sections = [];

  if (isDratAggregate) {
    const benchHtml = renderDratAggregateBenchTable(entity);
    if (benchHtml) {
      sections.push({ key: 'jurisdiction_circuit', title: 'Appellate benches', body: benchHtml, weight: 4 });
    }
    if (hasRouting) {
      sections.push({
        key: 'jurisdiction_routing',
        title: 'Appellate routing',
        body: renderAppellateRouting(entity, { compact: true }),
        weight: 2,
      });
    }
  } else if (hasScope) {
    sections.push({ key: 'jurisdiction_scope', title: 'Territorial scope', body: renderScopeBlock(scope), weight: 2 });
  }

  if (!isDratAggregate && hasRouting) {
    const routingHtml = renderAppellateRouting(entity, { compact: crossRoutes.length > 0 });
    if (routingHtml) {
      sections.push({
        key: 'jurisdiction_routing',
        title: 'Appellate routing',
        body: routingHtml,
        weight: 3 + summary.appellateFrom.length + summary.appellateToward.length,
      });
    }
  } else if (!isDratAggregate && !hasScope && hasRouting) {
    sections.push({
      key: 'jurisdiction_routing',
      title: 'Appellate routing',
      body: `<p class="detail-empty-hint">Territorial scope not yet recorded.</p>${renderAppellateRouting(entity)}`,
      weight: 3,
    });
  }

  if (crossRoutes.length) {
    const routesCollapsed = crossRoutes.length > 4;
    sections.push({
      key: 'jurisdiction_routes',
      title: 'Cross-region routes',
      body: renderCrossRegionRoutesBlock(crossRoutes, { collapsed: routesCollapsed }),
      weight: routesCollapsed ? 1.5 : 2 + Math.ceil(crossRoutes.length / 3),
    });
  }

  if (isDratAggregate && hasScope) {
    sections.unshift({
      key: 'jurisdiction_scope',
      title: 'Territorial scope',
      body: renderScopeBlock(scope),
      weight: 1,
    });
  }

  return sections.filter((s) => s.body && s.body.trim());
}

/**
 * Inner HTML for the Jurisdiction profile widget (side panel — single block).
 */
export function buildJurisdictionBody(entity) {
  const parts = getJurisdictionProfileSections(entity);
  if (!parts.length) return '';
  return parts.map((p) => p.body).join('');
}
