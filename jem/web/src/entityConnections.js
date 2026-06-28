// JEM — Direct relationship summary for an entity (detail panel + neighborhood list)

import { State } from './state.js';

function entityLabel(e) {
  if (!e) return '—';
  return e.name || e.abbreviation || e.id;
}

function relRow(rel, otherEntity, directionLabel) {
  const cat = rel.relationship_category || 'link';
  const type = rel.relationship_type || '';
  const note = rel.notes ? String(rel.notes).trim().slice(0, 160) : '';
  return {
    relId: rel.id,
    category: cat,
    type,
    directionLabel,
    entityId: otherEntity?.id,
    entityName: entityLabel(otherEntity),
    entityAbbr: otherEntity?.abbreviation || '',
    note,
    dataQuality: rel.data_quality,
  };
}

/**
 * All graph relationships incident on entityId, grouped for display.
 * Appellate: source appeals → target (lower → higher).
 */
export function buildEntityConnectionSummary(entityId) {
  const empty = {
    appellateToward: [],
    appellateFrom: [],
    supervises: [],
    supervisedBy: [],
    byCategory: new Map(),
    all: [],
  };
  if (!entityId || !State.graph?.relationships) return empty;

  const appellateToward = [];
  const appellateFrom = [];
  const supervises = [];
  const supervisedBy = [];
  const byCategory = new Map();
  const all = [];

  for (const rel of State.graph.relationships) {
    if (rel.source !== entityId && rel.target !== entityId) continue;

    const otherId = rel.source === entityId ? rel.target : rel.source;
    const other = State.getEntityById(otherId);
    const cat = rel.relationship_category || 'other';

    let bucket = null;
    let directionLabel = '';

    if (cat === 'appellate_chain') {
      if (rel.source === entityId) {
        bucket = appellateToward;
        directionLabel = 'Appeals to (higher)';
      } else {
        bucket = appellateFrom;
        directionLabel = 'Appeals from (lower)';
      }
    } else if (cat === 'supervisory') {
      if (rel.source === entityId) {
        bucket = supervises;
        directionLabel = 'Supervises';
      } else {
        bucket = supervisedBy;
        directionLabel = 'Supervised by';
      }
    } else {
      directionLabel = rel.source === entityId ? 'Outgoing' : 'Incoming';
    }

    const row = relRow(rel, other, directionLabel);
    all.push(row);
    if (bucket) bucket.push(row);
    else {
      if (!byCategory.has(cat)) byCategory.set(cat, []);
      byCategory.get(cat).push(row);
    }
  }

  const sortFn = (a, b) => a.entityName.localeCompare(b.entityName);
  appellateToward.sort(sortFn);
  appellateFrom.sort(sortFn);
  supervises.sort(sortFn);
  supervisedBy.sort(sortFn);
  all.sort((a, b) => {
    if (a.category !== b.category) return a.category.localeCompare(b.category);
    return a.entityName.localeCompare(b.entityName);
  });

  return {
    appellateToward,
    appellateFrom,
    supervises,
    supervisedBy,
    byCategory,
    all,
  };
}

export function formatCategoryLabel(cat) {
  return (cat || 'other').replace(/_/g, ' ');
}

// ── Appellate chain walkers ──────────────────────────────────────────────────
// Edge direction: source appeals → target  (lower court → higher court).
// "Upstream"   = follow edges in the direction of target  (lower → higher)
// "Downstream" = follow edges in reverse (higher ← lower)

function _appellateAdjacency() {
  const out = new Map(); // node → [target]   (where node appeals to)
  const incoming = new Map(); // node → [source] (who appeals to node)
  for (const rel of State.graph?.relationships || []) {
    if (rel.relationship_category !== 'appellate_chain') continue;
    if (!out.has(rel.source)) out.set(rel.source, []);
    out.get(rel.source).push(rel.target);
    if (!incoming.has(rel.target)) incoming.set(rel.target, []);
    incoming.get(rel.target).push(rel.source);
  }
  return { out, incoming };
}

/**
 * Walk up the appellate chain from `entityId` (toward higher courts) up to `maxHops`.
 * Returns an array of tiers, each tier being the unique node ids at that hop distance.
 * Tier 0 is the immediate parent(s). Stops when a tier has no nodes.
 */
export function getAppellateUpstream(entityId, maxHops = 3) {
  const { out } = _appellateAdjacency();
  const tiers = [];
  let frontier = new Set([entityId]);
  const seen = new Set([entityId]);
  for (let h = 0; h < maxHops; h++) {
    const next = new Set();
    for (const id of frontier) {
      for (const t of out.get(id) || []) {
        if (!seen.has(t)) { next.add(t); seen.add(t); }
      }
    }
    if (!next.size) break;
    tiers.push([...next]);
    frontier = next;
  }
  return tiers;
}

/**
 * Walk down the appellate chain from `entityId` (toward lower courts) up to `maxHops`.
 * Returns tiers in the same shape as getAppellateUpstream.
 */
export function getAppellateDownstream(entityId, maxHops = 3) {
  const { incoming } = _appellateAdjacency();
  const tiers = [];
  let frontier = new Set([entityId]);
  const seen = new Set([entityId]);
  for (let h = 0; h < maxHops; h++) {
    const next = new Set();
    for (const id of frontier) {
      for (const s of incoming.get(id) || []) {
        if (!seen.has(s)) { next.add(s); seen.add(s); }
      }
    }
    if (!next.size) break;
    tiers.push([...next]);
    frontier = next;
  }
  return tiers;
}

const APPELLATE_CHAIN_MAX_HOPS = 64;

/** Map collapse / generic rows — not individual institutions (see lattice README). */
export function isAggregateOrGenericEntity(e) {
  if (!e) return true;
  if (e._jemSyntheticAggregate) return true;
  const id = e.id || '';
  if (id.endsWith('_generic') || /_generic$/.test(id)) return true;
  const name = e.name || '';
  if (/\(remaining districts\)|\(consolidated\)|\(Generic\)|\(generic\)|\(aggregate\)|\(collapsed/i.test(name)) {
    return true;
  }
  if (/—\s*Generic\b/i.test(name)) return true;
  return false;
}

function filterConcreteEntityIds(ids) {
  return ids.filter((id) => {
    const e = State.getEntityById(id);
    return e && !isAggregateOrGenericEntity(e);
  });
}

export function filterAppellateTiers(tiers) {
  return tiers
    .map((tier) => filterConcreteEntityIds(tier))
    .filter((tier) => tier.length > 0);
}

function entityHasAppellateEdges(entityId) {
  const { out, incoming } = _appellateAdjacency();
  return Boolean((out.get(entityId)?.length) || (incoming.get(entityId)?.length));
}

/**
 * Full appellate chain for profile strip / export: concrete entities only,
 * generic / aggregate / placeholder rows excluded.
 */
export function getAppellateChainForEntity(entityId, maxHops = APPELLATE_CHAIN_MAX_HOPS) {
  const upstream = filterAppellateTiers(getAppellateUpstream(entityId, maxHops));
  const downstream = filterAppellateTiers(getAppellateDownstream(entityId, maxHops));
  const upIds = [...new Set(upstream.flat())];
  const downIds = [...new Set(downstream.flat())];
  return {
    upstream,
    downstream,
    upCount: upIds.length,
    downCount: downIds.length,
    hasEdges: entityHasAppellateEdges(entityId),
  };
}

/**
 * Build the full appellate hierarchy as ordered tiers, where tier 0 are roots
 * (no outgoing appellate edges = top of chain, e.g. Supreme Court).
 * Uses longest-path layering so leaves sit at the bottom regardless of DAG shape.
 * Returns { tiers, edges, orphans }.
 */
export function buildAppellateHierarchy() {
  const { out, incoming } = _appellateAdjacency();
  const allNodes = new Set();
  const edges = [];
  for (const rel of State.graph?.relationships || []) {
    if (rel.relationship_category !== 'appellate_chain') continue;
    allNodes.add(rel.source);
    allNodes.add(rel.target);
    edges.push({ src: rel.source, tgt: rel.target });
  }
  // Roots = nodes with no outgoing appellate edges (nothing higher to appeal to).
  const roots = [...allNodes].filter(id => !(out.get(id)?.length));

  // Longest-path layer assignment: layer(n) = max(layer(parent)) + 1, roots = 0.
  // We follow incoming-edge ancestors via memoization (DAG assumed).
  const layer = new Map();
  const computeLayer = (id, stack = new Set()) => {
    if (layer.has(id)) return layer.get(id);
    if (stack.has(id)) { layer.set(id, 0); return 0; } // cycle guard
    stack.add(id);
    const parents = out.get(id) || []; // "higher than me" → my layer = parent+1
    if (!parents.length) { layer.set(id, 0); stack.delete(id); return 0; }
    let lv = 0;
    for (const p of parents) lv = Math.max(lv, computeLayer(p, stack) + 1);
    layer.set(id, lv);
    stack.delete(id);
    return lv;
  };
  for (const id of allNodes) computeLayer(id);

  const tierMap = new Map();
  for (const [id, lv] of layer) {
    if (!tierMap.has(lv)) tierMap.set(lv, []);
    tierMap.get(lv).push(id);
  }
  const maxLayer = Math.max(0, ...tierMap.keys());
  const tiers = [];
  for (let i = 0; i <= maxLayer; i++) tiers.push((tierMap.get(i) || []).slice().sort());

  // Orphan entities are court-like entities with no appellate edges at all.
  // We don't enumerate them here (would need entity-type filtering); caller
  // can compute separately if it wants to surface them.
  return { tiers, edges, roots };
}
