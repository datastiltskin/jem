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
