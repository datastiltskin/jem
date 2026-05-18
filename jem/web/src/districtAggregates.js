/**
 * Collapsible district-court lattices: many per-state district nodes collapse to
 * the state's `*_district_courts_generic` row when present, else a synthetic aggregate.
 */

const MEMBER_RE = /^([a-z]{2})_district_court_(.+)$/;

/** State lattice prefix → principal High Court id (not a permanent bench). */
export const PRINCIPAL_HC_BY_STATE_CODE = {
  tn: 'hc_madras',
};

/**
 * Pick the principal HC for a district lattice (not whichever bench edge appears first).
 */
export function inferPrincipalHcForDistrictLattice(memberIds, relationships) {
  const counts = new Map();
  for (const r of relationships || []) {
    if (r.relationship_category !== 'appellate_chain') continue;
    if (!memberIds.has(r.source) || !r.target?.startsWith('hc_')) continue;
    counts.set(r.target, (counts.get(r.target) || 0) + 1);
  }
  let best = null;
  let bestScore = -1;
  for (const [target, count] of counts) {
    const isPrincipal = !target.includes('_bench_');
    const score = count + (isPrincipal ? 1_000_000 : 0);
    if (score > bestScore) {
      bestScore = score;
      best = target;
    }
  }
  return best;
}

/**
 * @param {object[]} entities
 * @param {object[]} relationships
 * @returns {{ groups: Array<{
 *   groupId: string,
 *   stateCode: string,
 *   memberIds: Set<string>,
 *   proxyId: string | null,
 *   synthetic: boolean,
 *   hcTargetId: string | null,
 *   centroid: { x: number, y: number },
 * }> }}
 */
export function buildDistrictAggregateIndex(entities, relationships) {
  const byState = new Map();
  for (const e of entities) {
    const m = MEMBER_RE.exec(e.id);
    if (!m) continue;
    const st = m[1];
    const tail = m[2];
    if (tail === 'generic') continue;
    if (!byState.has(st)) byState.set(st, []);
    byState.get(st).push(e);
  }

  const allIds = new Set(entities.map(e => e.id));
  const posById = new Map(entities.map(e => [e.id, e.position || { x: 0, y: 0 }]));

  const memberSet = (ids) => {
    const s = new Set();
    for (const id of ids) s.add(id);
    return s;
  };

  const groups = [];
  for (const [stateCode, members] of byState) {
    if (members.length < 2) continue;
    const memberIds = memberSet(members.map(e => e.id));
    const hcTargetId =
      PRINCIPAL_HC_BY_STATE_CODE[stateCode]
      || inferPrincipalHcForDistrictLattice(memberIds, relationships);
    const proxyId = `${stateCode}_district_courts_generic`;
    const hasProxy = allIds.has(proxyId);
    let sx = 0;
    let sy = 0;
    let n = 0;
    for (const e of members) {
      const p = posById.get(e.id) || { x: 0, y: 0 };
      sx += p.x || 0;
      sy += p.y || 0;
      n++;
    }
    groups.push({
      groupId: `district_lattice:${stateCode}`,
      stateCode,
      memberIds,
      proxyId: hasProxy ? proxyId : null,
      synthetic: !hasProxy,
      hcTargetId,
      centroid: { x: n ? sx / n : 0, y: n ? sy / n : 0 },
    });
  }
  return { groups };
}

export function syntheticAggregateEntity(group, entities) {
  const sample = entities.find(e => group.memberIds.has(e.id)) || {};
  const n = group.memberIds.size;
  const code = group.stateCode.toUpperCase();
  return {
    id: `__jem_agg_${group.stateCode}_district_courts`,
    name: `District Courts (${code} — ${n} districts)`,
    abbreviation: `${code} Dist.`,
    type: sample.type || 'SubordinateCivilCourt',
    cluster: sample.cluster || 'subordinate_courts',
    level_of_government: sample.level_of_government || 'State',
    created_year: sample.created_year || 1950,
    operational_status: 'Active',
    data_quality: sample.data_quality || 'partial',
    jurisdiction_scope: {
      states_covered: [group.stateCode.toUpperCase()],
    },
    derived: sample.derived || {},
    position: { ...group.centroid },
    memberCount: n,
    _jemSyntheticAggregate: true,
    _jemAggregateGroupId: group.groupId,
  };
}

/** Edges so the map stays connected when a lattice is collapsed to a synthetic node. */
export function syntheticAggregateRelationships(group) {
  if (!group.synthetic || !group.hcTargetId) return [];
  const sid = `__jem_agg_${group.stateCode}_district_courts`;
  const hc = group.hcTargetId;
  return [
    {
      id: `__jem_syn_${group.stateCode}_district_appellate`,
      source: sid,
      target: hc,
      relationship_type: 'AppealableTo',
      relationship_category: 'appellate_chain',
      is_binding: true,
      data_quality: 'partial',
      notes: 'Aggregate of district courts (collapsed view)',
    },
    {
      id: `__jem_syn_${group.stateCode}_district_supervise`,
      source: hc,
      target: sid,
      relationship_type: 'AdministrativeSupervision',
      relationship_category: 'supervisory',
      is_binding: true,
      data_quality: 'partial',
      notes: 'Aggregate of district courts (collapsed view)',
    },
  ];
}
