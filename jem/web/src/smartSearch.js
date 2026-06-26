// JEM — Curated structural insights (client-side over graph.json)
// Answers common researcher questions from sourced fields only.

import { isScoredEntity, shouldShowStructuralScores } from './scoreDisplay.js';

function extractGapEntries(entity) {
  const out = [];
  for (const block of entity.gaps || []) {
    if (!block || typeof block !== 'object') continue;
    const list = Array.isArray(block.gaps) ? block.gaps : (block.gap_id ? [block] : []);
    for (const g of list) {
      if (g && typeof g === 'object') out.push(g);
    }
  }
  return out;
}

function judgeStrength(e) {
  const js = e._detail?.judge_strength;
  if (!js || typeof js !== 'object') return null;
  const hasProvenance = Boolean(js.source_url || js.data_as_of || js.source_type);
  const allotted = js.allotted;
  const appointed = js.appointed;
  const vacancy = js.vacancy_count;
  if (!hasProvenance) return null;
  if (vacancy == null && allotted == null && appointed == null) return null;
  const computedVacancy = vacancy ?? (
    allotted != null && appointed != null ? Math.max(0, allotted - appointed) : null
  );
  if (computedVacancy == null && allotted == null) return null;
  return { ...js, vacancy_count: computedVacancy };
}

function caseVolume(e) {
  const cv = e._detail?.case_volume;
  if (!cv || cv.pending_cases == null) return null;
  if (!cv.source_url && !cv.source_type) return null;
  return cv;
}

function formatType(type) {
  return (type || '').replace(/([A-Z])/g, ' $1').trim();
}

function isHighCourt(e) {
  return e.cluster === 'constitutional_courts'
    && (e.id?.startsWith('hc_') || e.type === 'ConstitutionalCourt');
}

function isDistrictCourt(e) {
  return e.type === 'DistrictCourt' || /district_court/.test(e.id || '');
}

function isTribunal(e) {
  return e.cluster === 'tribunals_adr' && !isDistrictCourt(e);
}

function isSubordinateCourt(e) {
  return e.cluster === 'subordinate_courts' || isDistrictCourt(e);
}

/** Map collapse / generic rows — not individual institutions (see lattice README). */
function isAggregateOrGeneric(e) {
  if (!e) return true;
  if (e._jemSyntheticAggregate) return true;
  const id = e.id || '';
  if (id.endsWith('_generic') || /_generic$/.test(id)) return true;
  const name = e.name || '';
  if (/\(remaining districts\)|\(consolidated\)|\(Generic\)|\(generic\)|\(collapsed/i.test(name)) {
    return true;
  }
  return false;
}

function isConcreteEntity(e) {
  return !isAggregateOrGeneric(e);
}

function concreteEntities(entities) {
  return entities.filter(isConcreteEntity);
}

function rankByPendingCases(entities, limit = 5) {
  return concreteEntities(entities)
    .map((e) => ({ e, cv: caseVolume(e) }))
    .filter((x) => x.cv)
    .sort((a, b) => b.cv.pending_cases - a.cv.pending_cases)
    .slice(0, limit);
}

function pendingCasesInsight({ id, title, chip, aliases, keywords, filter, categoryLabel }) {
  return {
    id,
    title,
    chip,
    aliases,
    keywords,
    compute(graph) {
      const ranked = rankByPendingCases(graph.entities.filter(filter));
      if (!ranked.length) {
        return insufficient(
          id,
          title,
          `Insufficient sourced data in JEM for this query. No ${categoryLabel} with sourced case_volume.pending_cases in the current graph.`,
          graph,
        );
      }
      const top = ranked[0];
      const entities = ranked.map((x) => x.e);
      const asOf = top.cv.data_as_of ? ` (data as of ${top.cv.data_as_of})` : '';
      return ok(
        id,
        title,
        `${top.e.name} has the highest sourced pending_cases among ${categoryLabel} in JEM: `
          + `${top.cv.pending_cases.toLocaleString('en-IN')}${asOf}. `
          + 'Collapsed lattice rows (_generic, remaining districts, consolidated) are excluded.',
        entities,
        top.cv.source_url
          ? [{ label: top.cv.source_type || 'Case volume source', url: top.cv.source_url }]
          : topSourcesFromEntities(entities),
        graph,
      );
    },
  };
}

function primaryState(e) {
  const scope = e.jurisdiction_scope || e._detail?.jurisdiction_scope;
  const states = scope?.states_covered;
  return Array.isArray(states) && states.length ? states[0] : null;
}

function buildSnapshotNote(graph) {
  const when = graph?.meta?.generated_at;
  if (!when) return 'Data from the latest JEM snapshot — not a live feed.';
  try {
    const d = new Date(when);
    const label = Number.isNaN(d.getTime()) ? when : d.toISOString().slice(0, 10);
    return `Data as checked on: ${label}. Snapshot only — not a live feed.`;
  } catch {
    return `Data as checked on: ${when}. Snapshot only — not a live feed.`;
  }
}

/** Which metric to show on entity cards for each insight question. */
const INSIGHT_STAT_MODE = {
  largest_judge_vacancy: 'judge_strength',
  hc_highest_vacancies: 'judge_strength',
  avg_days_vacancy_unfilled: 'vacancy_days',
  highest_case_pendency: 'pending_cases',
  hc_highest_pendency: 'pending_cases',
  tribunal_highest_pendency: 'pending_cases',
  subordinate_highest_pendency: 'pending_cases',
  highest_independence_risk: 'independence_risk',
  lowest_structural_health: 'structural_health',
  newest_entity: 'created_year',
  oldest_active_entity: 'created_year',
  latest_abolished: 'abolished_year',
  year_most_entities_created: 'created_year',
  year_most_entities_abolished: 'abolished_year',
  decade_most_entities_created: 'created_year',
  longest_institutional_gap: 'gap',
  critical_structural_gaps: 'gap',
  tribunal_gap_hc_writ_load: 'gap',
  not_constituted: 'status',
  partial_operational_tribunals: 'status',
  de_facto_blocked: 'status',
  broken_appellate_paths: 'status',
  state_most_district_courts: 'jurisdiction',
  contested_data_quality: 'data_quality',
};

function insufficient(id, title, reason, graph) {
  return {
    id,
    title,
    insufficient: true,
    answer: reason,
    entities: [],
    sources: [],
    snapshotNote: buildSnapshotNote(graph),
  };
}

function ok(id, title, answer, entities, sources, graph, extra = {}) {
  return {
    id,
    title,
    insufficient: false,
    answer,
    entities: entities.filter(Boolean),
    sources: sources.filter(Boolean),
    snapshotNote: buildSnapshotNote(graph),
    ...extra,
  };
}

function topSourcesFromEntities(entities, max = 3) {
  const seen = new Set();
  const out = [];
  for (const e of entities) {
    for (const s of e.sources || []) {
      const key = s.url || s.label;
      if (!key || seen.has(key)) continue;
      seen.add(key);
      out.push(s);
      if (out.length >= max) return out;
    }
  }
  return out;
}

function entitySearchFields(entity) {
  return [entity.name, entity.abbreviation, ...(entity.aliases || [])]
    .filter(Boolean)
    .map((s) => String(s).toLowerCase());
}

function substringEntityRank(entity, lower) {
  let best = Infinity;
  for (const field of entitySearchFields(entity)) {
    const idx = field.indexOf(lower);
    if (idx < 0) continue;
    const rank = idx + (idx === 0 ? 0 : 12) + field.length * 0.0005;
    best = Math.min(best, rank);
  }
  return best;
}

/** Substring matches first; fuzzy only fills gaps (strict score cap). */
function searchEntityHits(query, entities, fuse, limit = 8) {
  const q = query.trim();
  if (!q) return [];
  const lower = q.toLowerCase();

  const substringMatches = entities
    .map((e) => ({ item: e, rank: substringEntityRank(e, lower) }))
    .filter((x) => x.rank < Infinity)
    .sort((a, b) => a.rank - b.rank || (a.item.name || '').localeCompare(b.item.name || ''));

  const seen = new Set(substringMatches.map((x) => x.item.id));
  const out = substringMatches.slice(0, limit).map((x) => ({ item: x.item, score: 0 }));

  if (out.length >= limit || !fuse) return out;

  const maxFuzzyScore = Math.min(0.22, 0.12 + lower.length * 0.02);
  for (const h of fuse.search(q)) {
    if (seen.has(h.item.id) || h.score > maxFuzzyScore) continue;
    out.push(h);
    seen.add(h.item.id);
    if (out.length >= limit) break;
  }
  return out;
}

function insightSearchBlob(d) {
  return [d.title, d.chip, ...(d.aliases || []), ...(d.keywords || [])].join(' ').toLowerCase();
}

function searchInsightDefs(query, fuse, availableIds) {
  const q = query.trim();
  if (!q || !availableIds?.size) return [];

  const eligible = INSIGHT_DEFS.filter((d) => availableIds.has(d.id));
  const explicit = eligible.filter((d) => insightMatchesQuery(q, d));
  if (explicit.length) {
    return explicit.slice(0, 6).map((d) => ({ item: { id: d.id, title: d.title }, score: 0 }));
  }

  const fuseHits = fuse.search(q).filter((h) => availableIds.has(h.item.id) && h.score <= 0.32);
  return fuseHits.slice(0, 6);
}

function insightMatchesQuery(q, def) {
  const lower = q.trim().toLowerCase();
  if (lower.length < 3) return false;
  const blob = insightSearchBlob(def);
  if (blob.includes(lower)) return true;
  const tokens = lower.split(/\s+/).filter((t) => t.length >= 2);
  if (tokens.length >= 2 && tokens.every((t) => blob.includes(t))) return true;
  if (tokens.length === 1) {
    const t = tokens[0];
    if (def.chip?.toLowerCase().includes(t)) return true;
    if ((def.keywords || []).some((k) => {
      const kl = k.toLowerCase();
      return kl.includes(t) || t.includes(kl);
    })) return true;
    if ((def.aliases || []).some((a) => a.toLowerCase().includes(t))) return true;
  }
  return false;
}

function findUnavailableInsightMatch(q, availableIds) {
  const lower = q.trim().toLowerCase();
  if (lower.length < 3) return null;
  return INSIGHT_DEFS.find((d) => !availableIds.has(d.id) && insightMatchesQuery(q, d)) || null;
}

function computeAvailableInsightIds(graph) {
  const ids = new Set();
  for (const d of INSIGHT_DEFS) {
    const result = d.compute.call(d, graph);
    if (result && !result.insufficient) ids.add(d.id);
  }
  return ids;
}

const MISSING_INSIGHT_LOG_KEY = 'jem_missing_insight_requests';
const MISSING_INSIGHT_LOG_LOCAL_CAP = 30;

let insightApiBasePromise = null;

function resolveInsightApiBase() {
  if (window.JEM_API_BASE !== undefined) {
    return Promise.resolve(window.JEM_API_BASE || null);
  }
  if (insightApiBasePromise) return insightApiBasePromise;
  insightApiBasePromise = (async () => {
    for (const base of ['/api/v1', '/api/jem/v1']) {
      try {
        const r = await fetch(`${base}/health`, { credentials: 'same-origin' });
        if (r.ok) return base;
      } catch {
        /* try next */
      }
    }
    return null;
  })();
  return insightApiBasePromise;
}

function getMissingInsightLog() {
  try {
    return JSON.parse(localStorage.getItem(MISSING_INSIGHT_LOG_KEY) || '[]');
  } catch {
    return [];
  }
}

function logMissingInsightRequestLocal(id, title) {
  try {
    const log = getMissingInsightLog();
    const now = new Date().toISOString();
    const row = log.find((x) => x.id === id);
    if (row) {
      row.count += 1;
      row.lastAt = now;
    } else {
      log.push({ id, title, count: 1, firstAt: now, lastAt: now });
    }
    localStorage.setItem(
      MISSING_INSIGHT_LOG_KEY,
      JSON.stringify(log.slice(-MISSING_INSIGHT_LOG_LOCAL_CAP)),
    );
  } catch {
    /* ignore storage errors */
  }
}

async function fetchInsightRequestLog(limit = 8) {
  const base = await resolveInsightApiBase();
  if (base) {
    try {
      const r = await fetch(`${base}/insights/requests?limit=${limit}`, { credentials: 'same-origin' });
      if (r.ok) {
        const data = await r.json();
        return (data.items || []).map((x) => ({
          id: x.insight_id,
          title: x.title,
          count: x.request_count,
          lastAt: x.last_requested_at,
        }));
      }
    } catch {
      /* fall back to local */
    }
  }
  return getMissingInsightLog();
}

async function logMissingInsightRequest(id, title, queryText = '') {
  logMissingInsightRequestLocal(id, title);
  const base = await resolveInsightApiBase();
  if (!base) return;
  try {
    await fetch(`${base}/insights/requests`, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        insight_id: id,
        title,
        query_text: queryText || null,
      }),
    });
  } catch {
    /* offline or API unavailable */
  }
}

async function refreshInsightRequestLog(panelEl) {
  if (!panelEl) return;
  const log = await fetchInsightRequestLog(8);
  const html = renderMissingInsightLogTable(log);
  const host = panelEl.querySelector('.insight-request-log');
  if (host) {
    if (html) host.outerHTML = html;
    else host.remove();
  } else if (html) {
    panelEl.insertAdjacentHTML('beforeend', html);
  }
}

function buildInsightFuse(fuseFactory, availableIds) {
  const defs = INSIGHT_DEFS.filter((d) => availableIds.has(d.id));
  return fuseFactory(
    defs.map((d) => ({
      id: d.id,
      title: d.title,
      aliases: d.aliases,
      chip: d.chip,
      keywords: d.keywords,
      searchBlob: insightSearchBlob(d),
    })),
    {
      keys: ['title', 'searchBlob', 'aliases', 'keywords'],
      threshold: 0.45,
      includeScore: true,
      ignoreLocation: true,
    },
  );
}

const FEATURED_CHIP_IDS = [
  'largest_judge_vacancy',
  'hc_highest_vacancies',
  'highest_case_pendency',
  'hc_highest_pendency',
  'tribunal_highest_pendency',
  'subordinate_highest_pendency',
  'not_constituted',
  'tribunal_gap_hc_writ_load',
  'newest_entity',
  'critical_structural_gaps',
];

const INSIGHT_DEFS = [
  {
    id: 'largest_judge_vacancy',
    title: 'Largest judge vacancy count (sourced strength data)',
    aliases: ['largest vacancy', 'biggest vacancy', 'highest vacancy count', 'most vacant bench', 'most vacancies', 'judge vacancies'],
    keywords: ['vacancy', 'vacancies', 'vacant', 'judge', 'largest', 'most'],
    chip: 'Largest vacancy',
    compute(graph) {
      const ranked = concreteEntities(graph.entities)
        .map((e) => ({ e, js: judgeStrength(e) }))
        .filter((x) => x.js?.vacancy_count != null)
        .sort((a, b) => b.js.vacancy_count - a.js.vacancy_count);
      if (!ranked.length) {
        return insufficient(
          this.id,
          this.title,
          'Insufficient sourced data in JEM for this query. No entity has judge_strength with vacancy_count and a source reference in the current graph.',
          graph,
        );
      }
      const top = ranked[0];
      const ties = ranked.filter((x) => x.js.vacancy_count === top.js.vacancy_count).map((x) => x.e);
      const asOf = top.js.data_as_of ? ` (strength data as of ${top.js.data_as_of})` : '';
      return ok(
        this.id,
        this.title,
        `${top.e.name} has the largest recorded judge vacancy count in JEM: ${top.js.vacancy_count} vacant post(s)${asOf}. `
          + `Sanctioned: ${top.js.allotted ?? '—'}, working: ${top.js.appointed ?? '—'}.`,
        ties,
        top.js.source_url
          ? [{ label: top.js.source_type || 'Judge strength source', url: top.js.source_url }]
          : topSourcesFromEntities(ties),
        graph,
      );
    },
  },
  {
    id: 'hc_highest_vacancies',
    title: 'High Court with highest judge vacancies',
    aliases: ['HC vacancies', 'high court vacancies', 'most vacant high court', 'high court vacancy'],
    keywords: ['vacancy', 'vacancies', 'high court', 'hc'],
    chip: 'HC vacancies',
    compute(graph) {
      const ranked = concreteEntities(graph.entities)
        .filter(isHighCourt)
        .map((e) => ({ e, js: judgeStrength(e) }))
        .filter((x) => x.js?.vacancy_count != null)
        .sort((a, b) => b.js.vacancy_count - a.js.vacancy_count);
      if (!ranked.length) {
        return insufficient(
          this.id,
          this.title,
          'Insufficient sourced data in JEM for this query. High Courts in the graph lack judge_strength vacancy figures with source references.',
          graph,
        );
      }
      const top = ranked[0];
      const topFive = ranked.slice(0, 5).map((x) => x.e);
      const asOf = top.js.data_as_of ? ` Data as of ${top.js.data_as_of}.` : '';
      return ok(
        this.id,
        this.title,
        `${top.e.name} has the highest recorded HC vacancy count in JEM: ${top.js.vacancy_count} post(s) vacant `
          + `(${top.js.appointed ?? '—'} working of ${top.js.allotted ?? '—'} sanctioned).${asOf}`,
        topFive,
        top.js.source_url
          ? [{ label: 'DoJ / HC strength source', url: top.js.source_url }]
          : topSourcesFromEntities(topFive),
        graph,
      );
    },
  },
  {
    id: 'avg_days_vacancy_unfilled',
    title: 'Longest average days a vacancy stayed unfilled',
    aliases: ['longest vacancy', 'longest unfilled vacancy', 'average vacancy days', 'avg days vacancy', 'appointment delay vacancy'],
    keywords: ['vacancy', 'delay', 'days', 'longest', 'unfilled'],
    chip: 'Longest vacancy (days)',
    compute(graph) {
      const ranked = graph.entities
        .map((e) => {
          const days = e._detail?.appointment?.avg_days_vacancy_unfilled;
          return days != null ? { e, days } : null;
        })
        .filter(Boolean)
        .sort((a, b) => b.days - a.days);
      if (!ranked.length) {
        return insufficient(
          this.id,
          this.title,
          'Insufficient sourced data in JEM for this query. The appointment.avg_days_vacancy_unfilled field is not populated in the current graph.',
          graph,
        );
      }
      const top = ranked[0];
      return ok(
        this.id,
        this.title,
        `${top.e.name} records the longest average unfilled vacancy period in JEM: ${top.days} days.`,
        [top.e],
        topSourcesFromEntities([top.e]),
        graph,
      );
    },
  },
  {
    id: 'newest_entity',
    title: 'Most recently created entity (by created_year)',
    aliases: ['last created entity', 'newest entity', 'most recent institution', 'latest created'],
    chip: 'Newest entity',
    compute(graph) {
      const years = graph.entities.map((e) => e.created_year).filter((y) => typeof y === 'number');
      if (!years.length) {
        return insufficient(this.id, this.title, 'No created_year values in the graph.', graph);
      }
      const maxYear = Math.max(...years);
      const matches = graph.entities.filter((e) => e.created_year === maxYear);
      return ok(
        this.id,
        this.title,
        `${matches.length} entit${matches.length === 1 ? 'y' : 'ies'} share the latest created_year in JEM: ${maxYear}.`,
        matches.slice(0, 8),
        topSourcesFromEntities(matches),
        graph,
        { year: maxYear },
      );
    },
  },
  {
    id: 'oldest_active_entity',
    title: 'Oldest active entity (by created_year)',
    aliases: ['oldest court', 'oldest active institution', 'earliest created active'],
    chip: 'Oldest active',
    compute(graph) {
      const active = graph.entities.filter((e) => e.operational_status === 'Active' && typeof e.created_year === 'number');
      if (!active.length) {
        return insufficient(this.id, this.title, 'No active entities with created_year in the graph.', graph);
      }
      const minYear = Math.min(...active.map((e) => e.created_year));
      const matches = active.filter((e) => e.created_year === minYear);
      return ok(
        this.id,
        this.title,
        `Among active entities, the earliest created_year in JEM is ${minYear} `
          + `(${matches.length} entit${matches.length === 1 ? 'y' : 'ies'}).`,
        matches.slice(0, 8),
        topSourcesFromEntities(matches),
        graph,
      );
    },
  },
  {
    id: 'latest_abolished',
    title: 'Most recently abolished entity',
    aliases: ['last abolished', 'recently abolished', 'latest abolished entity'],
    chip: 'Last abolished',
    compute(graph) {
      const abolished = graph.entities.filter((e) => typeof e.abolished_year === 'number');
      if (!abolished.length) {
        return insufficient(
          this.id,
          this.title,
          'Insufficient sourced data in JEM for this query. No entity has abolished_year set in the current graph.',
          graph,
        );
      }
      const maxYear = Math.max(...abolished.map((e) => e.abolished_year));
      const matches = abolished.filter((e) => e.abolished_year === maxYear);
      return ok(
        this.id,
        this.title,
        `${matches.length} entit${matches.length === 1 ? 'y was' : 'ies were'} last recorded as abolished in ${maxYear}.`,
        matches.slice(0, 8),
        topSourcesFromEntities(matches),
        graph,
      );
    },
  },
  pendingCasesInsight({
    id: 'hc_highest_pendency',
    title: 'High Court with highest pending cases',
    chip: 'HC pendency',
    aliases: ['high court pendency', 'HC pending cases', 'highest HC backlog', 'high court backlog'],
    keywords: ['pendency', 'pending', 'high court', 'hc', 'backlog', 'cases'],
    filter: isHighCourt,
    categoryLabel: 'High Courts',
  }),
  pendingCasesInsight({
    id: 'tribunal_highest_pendency',
    title: 'Tribunal with highest pending cases',
    chip: 'Tribunal pendency',
    aliases: ['tribunal pendency', 'tribunal pending cases', 'highest tribunal backlog'],
    keywords: ['pendency', 'pending', 'tribunal', 'backlog', 'cases'],
    filter: isTribunal,
    categoryLabel: 'tribunals',
  }),
  pendingCasesInsight({
    id: 'subordinate_highest_pendency',
    title: 'Subordinate court with highest pending cases',
    chip: 'District pendency',
    aliases: ['district court pendency', 'subordinate court backlog', 'district pending cases'],
    keywords: ['pendency', 'pending', 'district', 'subordinate', 'backlog', 'cases'],
    filter: isSubordinateCourt,
    categoryLabel: 'subordinate / district courts',
  }),
  {
    id: 'not_constituted',
    title: 'Bodies not yet constituted',
    aliases: ['not constituted', 'unconstituted bodies', 'NC entities', 'never constituted'],
    chip: 'Not constituted',
    compute(graph) {
      const matches = graph.entities.filter((e) => e.operational_status === 'Not_Constituted');
      if (!matches.length) {
        return insufficient(this.id, this.title, 'No Not_Constituted entities in the current graph.', graph);
      }
      return ok(
        this.id,
        this.title,
        `JEM records ${matches.length} entit${matches.length === 1 ? 'y' : 'ies'} with operational_status Not_Constituted.`,
        matches,
        topSourcesFromEntities(matches),
        graph,
      );
    },
  },
  {
    id: 'partial_operational_tribunals',
    title: 'Partially operational tribunals',
    aliases: ['partial operational', 'partially operational tribunal', 'GSTAT status', 'not fully operational tribunal'],
    chip: 'Partial tribunals',
    compute(graph) {
      const matches = graph.entities.filter(
        (e) => e.operational_status === 'Partial_Operational' && e.cluster === 'tribunals_adr',
      );
      if (!matches.length) {
        return insufficient(this.id, this.title, 'No Partial_Operational tribunals in the current graph.', graph);
      }
      return ok(
        this.id,
        this.title,
        `${matches.length} tribunal entit${matches.length === 1 ? 'y is' : 'ies are'} marked Partial_Operational in JEM.`,
        matches,
        topSourcesFromEntities(matches),
        graph,
      );
    },
  },
  {
    id: 'tribunal_gap_hc_writ_load',
    title: 'Tribunal gaps shifting load to High Courts (writ / HC appeals)',
    aliases: [
      'GST appeals high court',
      'GSTAT writ petitions',
      'tribunal not operational high court',
      'absent tribunal HC load',
      'GST appellate tribunal high court',
    ],
    chip: 'Tribunal → HC load',
    compute(graph) {
      const HC_RE = /\b(high court|writ petition|writ jurisdiction|hc\b|art\.?\s*226)/i;
      const matches = [];
      for (const e of graph.entities) {
        const gaps = extractGapEntries(e);
        const gapHits = gaps.filter((g) => HC_RE.test(g.gap_description || '') || HC_RE.test(g.gap_source || ''));
        const notesHit = HC_RE.test(e.data_quality_notes || '');
        if (gapHits.length || (notesHit && ['Not_Constituted', 'Partial_Operational', 'De_Facto_Blocked'].includes(e.operational_status))) {
          matches.push({ e, gapHits });
        }
      }
      if (!matches.length) {
        return insufficient(
          this.id,
          this.title,
          'Insufficient sourced data in JEM for this query. No recorded structural gap or maintainer note documents HC/writ load shift in the current graph.',
          graph,
        );
      }
      matches.sort((a, b) => {
        const sev = (x) => (x.gapHits[0]?.gap_severity === 'Critical' ? 2 : 1);
        return sev(b) - sev(a) || (b.gapHits[0]?.gap_since_year || 0) - (a.gapHits[0]?.gap_since_year || 0);
      });
      const entities = matches.map((m) => m.e);
      const lead = matches[0];
      const excerpt = lead.gapHits[0]?.gap_description || lead.e.data_quality_notes || '';
      const trimmed = excerpt.length > 280 ? `${excerpt.slice(0, 277)}…` : excerpt;
      return ok(
        this.id,
        this.title,
        `JEM records ${matches.length} entit${matches.length === 1 ? 'y' : 'ies'} where maintainer-documented gaps or notes reference High Court / writ jurisdiction while the tribunal layer is incomplete. `
          + `Example (${lead.e.name}): ${trimmed}`,
        entities.slice(0, 8),
        topSourcesFromEntities(entities),
        graph,
      );
    },
  },
  {
    id: 'highest_independence_risk',
    title: 'Highest structural independence risk (scored bodies)',
    aliases: ['independence risk', 'highest IR', 'most independence risk', 'severe independence risk'],
    chip: 'Independence risk',
    compute(graph) {
      const ranked = concreteEntities(graph.entities)
        .filter(isScoredEntity)
        .filter((e) => typeof e.derived?.independence_risk_score === 'number')
        .sort((a, b) => b.derived.independence_risk_score - a.derived.independence_risk_score);
      if (!ranked.length) {
        return insufficient(this.id, this.title, 'No scored independence_risk values in the graph.', graph);
      }
      const top = ranked[0];
      const topFive = ranked.slice(0, 5);
      const level = top.derived.independence_risk_level || '—';
      return ok(
        this.id,
        this.title,
        `${top.name} has the highest derived independence_risk_score in JEM: ${top.derived.independence_risk_score} (${level}). `
          + 'Scores are structural indicators — pending community review.',
        topFive,
        topSourcesFromEntities(topFive),
        graph,
      );
    },
  },
  {
    id: 'lowest_structural_health',
    title: 'Lowest structural health score',
    aliases: ['structural health', 'lowest health score', 'critical structural health', 'unhealthiest institution'],
    chip: 'Structural health',
    compute(graph) {
      const ranked = concreteEntities(graph.entities)
        .filter(isScoredEntity)
        .filter((e) => typeof e.derived?.structural_health_score === 'number')
        .sort((a, b) => a.derived.structural_health_score - b.derived.structural_health_score);
      if (!ranked.length) {
        return insufficient(this.id, this.title, 'No structural_health_score values in the graph.', graph);
      }
      const top = ranked[0];
      const topFive = ranked.slice(0, 5);
      return ok(
        this.id,
        this.title,
        `${top.name} has the lowest derived structural_health_score in JEM: ${top.derived.structural_health_score} `
          + `(${top.derived.structural_health_level || '—'}).`,
        topFive,
        topSourcesFromEntities(topFive),
        graph,
      );
    },
  },
  {
    id: 'critical_structural_gaps',
    title: 'Critical structural gaps',
    aliases: ['critical gaps', 'structural gaps critical', 'severe structural gap'],
    chip: 'Critical gaps',
    compute(graph) {
      const matches = [];
      for (const e of concreteEntities(graph.entities)) {
        const critical = extractGapEntries(e).filter((g) => g.gap_severity === 'Critical');
        if (critical.length) matches.push(e);
      }
      if (!matches.length) {
        return insufficient(this.id, this.title, 'No Critical gap_severity annotations in the current graph.', graph);
      }
      return ok(
        this.id,
        this.title,
        `${matches.length} entit${matches.length === 1 ? 'y has' : 'ies have'} at least one gap marked Critical in JEM.`,
        matches,
        topSourcesFromEntities(matches),
        graph,
      );
    },
  },
  {
    id: 'broken_appellate_paths',
    title: 'Broken or non-functional appellate paths',
    aliases: ['broken appellate', 'appellate vacuum', 'appellate path broken', 'non functional appellate'],
    chip: 'Broken appellate',
    compute(graph) {
      const byId = new Map(graph.entities.map((e) => [e.id, e]));
      const broken = new Set();
      for (const e of graph.entities) {
        if (e.derived?.appellate_functional === false || e.appellate_functional === false) {
          broken.add(e.id);
        }
        for (const g of extractGapEntries(e)) {
          if (g.gap_type === 'Appellate_Gap') broken.add(e.id);
        }
      }
      for (const r of graph.relationships || []) {
        if (r.relationship_category !== 'appellate_chain') continue;
        const src = byId.get(r.source);
        const tgt = byId.get(r.target);
        if (src?.operational_status === 'Not_Constituted' || tgt?.operational_status === 'Not_Constituted') {
          broken.add(src?.id || r.source);
          if (tgt) broken.add(tgt.id);
        }
      }
      const entities = [...broken].map((id) => byId.get(id)).filter(Boolean);
      if (!entities.length) {
        return insufficient(
          this.id,
          this.title,
          'Insufficient sourced data in JEM for this query. No appellate_functional=false flags or Not_Constituted appellate endpoints are recorded in the current graph.',
          graph,
        );
      }
      return ok(
        this.id,
        this.title,
        `JEM flags ${entities.length} entit${entities.length === 1 ? 'y' : 'ies'} on broken or non-functional appellate paths `
          + '(appellate_functional=false, Appellate_Gap records, or appellate target/source Not_Constituted).',
        entities.slice(0, 8),
        topSourcesFromEntities(entities),
        graph,
      );
    },
  },
  {
    id: 'de_facto_blocked',
    title: 'De facto blocked bodies',
    aliases: ['de facto blocked', 'blocked institution', 'defacto blocked'],
    chip: 'De facto blocked',
    compute(graph) {
      const matches = graph.entities.filter((e) => e.operational_status === 'De_Facto_Blocked');
      if (!matches.length) {
        return insufficient(
          this.id,
          this.title,
          'Insufficient sourced data in JEM for this query. No De_Facto_Blocked entities in the current graph.',
          graph,
        );
      }
      return ok(
        this.id,
        this.title,
        `${matches.length} entit${matches.length === 1 ? 'y is' : 'ies are'} marked De_Facto_Blocked.`,
        matches,
        topSourcesFromEntities(matches),
        graph,
      );
    },
  },
  {
    id: 'highest_case_pendency',
    title: 'Highest sourced case pendency (all entities)',
    aliases: ['highest pendency', 'most pending cases', 'case volume pendency', 'largest backlog', 'overall pendency'],
    keywords: ['pendency', 'pending', 'backlog', 'cases'],
    chip: 'Highest pendency',
    compute(graph) {
      const ranked = rankByPendingCases(graph.entities);
      if (!ranked.length) {
        return insufficient(
          this.id,
          this.title,
          'Insufficient sourced data in JEM for this query. No case_volume.pending_cases with source references in the current graph.',
          graph,
        );
      }
      const top = ranked[0];
      const topFive = ranked.map((x) => x.e);
      const asOf = top.cv.data_as_of ? ` (data as of ${top.cv.data_as_of})` : '';
      return ok(
        this.id,
        this.title,
        `${top.e.name} records the highest sourced pending_cases in JEM: ${top.cv.pending_cases.toLocaleString('en-IN')}${asOf}. `
          + 'Collapsed lattice rows (_generic, remaining districts, consolidated) are excluded.',
        topFive,
        top.cv.source_url
          ? [{ label: top.cv.source_type || 'Case volume source', url: top.cv.source_url }]
          : topSourcesFromEntities(topFive),
        graph,
      );
    },
  },
  {
    id: 'contested_data_quality',
    title: 'Entities with contested data quality',
    aliases: ['contested data', 'contested entity', 'disputed facts'],
    chip: 'Contested data',
    compute(graph) {
      const matches = graph.entities.filter((e) => e.data_quality === 'contested');
      if (!matches.length) {
        return insufficient(
          this.id,
          this.title,
          'Insufficient sourced data in JEM for this query. No entity has data_quality contested in the current graph.',
          graph,
        );
      }
      return ok(
        this.id,
        this.title,
        `${matches.length} entit${matches.length === 1 ? 'y has' : 'ies have'} data_quality contested in JEM.`,
        matches,
        topSourcesFromEntities(matches),
        graph,
      );
    },
  },
  {
    id: 'state_most_district_courts',
    title: 'State with the most district courts in JEM',
    aliases: ['most district courts', 'district court count by state', 'state district courts'],
    chip: 'District courts by state',
    compute(graph) {
      const counts = new Map();
      for (const e of graph.entities) {
        if (!isDistrictCourt(e)) continue;
        const st = primaryState(e);
        if (!st) continue;
        counts.set(st, (counts.get(st) || 0) + 1);
      }
      if (!counts.size) {
        return insufficient(this.id, this.title, 'No district courts with state jurisdiction in the graph.', graph);
      }
      const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1]);
      const [topState, topCount] = sorted[0];
      const sample = graph.entities
        .filter((e) => isDistrictCourt(e) && primaryState(e) === topState)
        .slice(0, 6);
      return ok(
        this.id,
        this.title,
        `${topState} has the most district-court entities in the JEM corpus: ${topCount} recorded.`,
        sample,
        topSourcesFromEntities(sample),
        graph,
        { stateCode: topState },
      );
    },
  },
  {
    id: 'year_most_entities_created',
    title: 'Year that created the most entities in JEM',
    aliases: ['most entities created', 'year most created', 'peak creation year', 'busiest creation year'],
    chip: 'Peak creation year',
    compute(graph) {
      const counts = new Map();
      for (const e of graph.entities) {
        if (typeof e.created_year !== 'number') continue;
        counts.set(e.created_year, (counts.get(e.created_year) || 0) + 1);
      }
      if (!counts.size) {
        return insufficient(this.id, this.title, 'No created_year values in the graph.', graph);
      }
      const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1] || b[0] - a[0]);
      const [year, count] = sorted[0];
      const sample = graph.entities.filter((e) => e.created_year === year).slice(0, 6);
      return ok(
        this.id,
        this.title,
        `${year} is the peak creation year in the JEM corpus: ${count} entities carry created_year ${year}.`,
        sample,
        topSourcesFromEntities(sample),
        graph,
        { year, count },
      );
    },
  },
  {
    id: 'year_most_entities_abolished',
    title: 'Year that abolished the most entities in JEM',
    aliases: ['most abolished year', 'peak abolition year', 'year most abolished'],
    chip: 'Peak abolition year',
    compute(graph) {
      const counts = new Map();
      for (const e of graph.entities) {
        if (typeof e.abolished_year !== 'number') continue;
        counts.set(e.abolished_year, (counts.get(e.abolished_year) || 0) + 1);
      }
      if (!counts.size) {
        return insufficient(
          this.id,
          this.title,
          'Insufficient sourced data in JEM for this query. No abolished_year values in the current graph.',
          graph,
        );
      }
      const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1] || b[0] - a[0]);
      const [year, count] = sorted[0];
      const sample = graph.entities.filter((e) => e.abolished_year === year).slice(0, 6);
      return ok(
        this.id,
        this.title,
        `${year} is the peak abolition year in the JEM corpus: ${count} entities carry abolished_year ${year}.`,
        sample,
        topSourcesFromEntities(sample),
        graph,
        { year, count },
      );
    },
  },
  {
    id: 'decade_most_entities_created',
    title: 'Decade with the most new entities in JEM',
    aliases: ['decade most created', 'busiest decade', 'creation decade'],
    chip: 'Peak decade',
    compute(graph) {
      const counts = new Map();
      for (const e of graph.entities) {
        if (typeof e.created_year !== 'number') continue;
        const decade = Math.floor(e.created_year / 10) * 10;
        counts.set(decade, (counts.get(decade) || 0) + 1);
      }
      if (!counts.size) {
        return insufficient(this.id, this.title, 'No created_year values in the graph.', graph);
      }
      const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1]);
      const [decade, count] = sorted[0];
      const sample = graph.entities
        .filter((e) => typeof e.created_year === 'number' && Math.floor(e.created_year / 10) * 10 === decade)
        .slice(0, 6);
      return ok(
        this.id,
        this.title,
        `The ${decade}s decade has the most entities by created_year in JEM: ${count} entities.`,
        sample,
        topSourcesFromEntities(sample),
        graph,
        { decade, count },
      );
    },
  },
  {
    id: 'longest_institutional_gap',
    title: 'Longest-running institutional gap (gap_since_year)',
    aliases: ['longest gap', 'oldest structural gap', 'gap since year'],
    chip: 'Longest gap',
    compute(graph) {
      let best = null;
      for (const e of graph.entities) {
        for (const g of extractGapEntries(e)) {
          if (typeof g.gap_since_year !== 'number') continue;
          if (!best || g.gap_since_year < best.gap.gap_since_year) {
            best = { e, gap: g };
          }
        }
      }
      if (!best) {
        return insufficient(
          this.id,
          this.title,
          'Insufficient sourced data in JEM for this query. No gap_since_year values in structural gap records.',
          graph,
        );
      }
      const yearsOpen = (graph.meta?.year_range?.[1] || new Date().getFullYear()) - best.gap.gap_since_year;
      return ok(
        this.id,
        this.title,
        `${best.e.name} carries the earliest gap_since_year in JEM: ${best.gap.gap_since_year} `
          + `(${best.gap.gap_type || 'gap'}, ${best.gap.gap_severity || 'severity not set'}, ~${yearsOpen}+ years in corpus timeline). `
          + `${best.gap.gap_description || ''}`,
        [best.e],
        best.gap.gap_source
          ? [{ label: 'Gap source (maintainer record)', url: null, title: best.gap.gap_source }]
          : topSourcesFromEntities([best.e]),
        graph,
      );
    },
  },
];

export function getInsightDefinitions() {
  return INSIGHT_DEFS;
}

export function computeInsight(insightId, graph) {
  const def = INSIGHT_DEFS.find((d) => d.id === insightId);
  if (!def || !graph) return null;
  return def.compute.call(def, graph);
}

export function entityDisplayName(entity) {
  return entity?.name || entity?.abbreviation || entity?.id || 'Unnamed entity';
}

function renderMissingInsightLogTable(log = getMissingInsightLog()) {
  if (!log.length) return '';
  const rows = log.slice(-8).reverse().map((r) => {
    const last = (r.lastAt || '').slice(0, 10);
    return `<tr><td>${r.title}</td><td>${r.count}</td><td>${last}</td></tr>`;
  }).join('');
  return `
    <div class="insight-request-log">
      <p class="insight-request-head">Insight requests noted for a future JEM update</p>
      <table class="insight-request-table">
        <thead><tr><th>Question</th><th>Times</th><th>Last asked</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function renderMissingInsightPanel(def, graph) {
  void logMissingInsightRequest(def.id, def.title, def.title);
  return `
    <div class="insight-onebox insight-insufficient insight-missing" role="region" aria-label="Insight not available">
      <button type="button" class="insight-close" aria-label="Close insight">×</button>
      <h3 class="insight-title">${def.title}</h3>
      <p class="insight-answer">This insight is not ready in JEM yet — the data needed to answer it has not been collected or verified. We’ve noted your interest for a future update.</p>
      <p class="insight-snapshot">${buildSnapshotNote(graph)}</p>
      ${renderMissingInsightLogTable()}
    </div>
  `;
}

function entityStatLine(entity, mode) {
  switch (mode) {
    case 'pending_cases': {
      const cv = caseVolume(entity);
      if (cv?.pending_cases == null) return '';
      const asOf = cv.data_as_of ? ` · as of ${cv.data_as_of}` : '';
      return `${cv.pending_cases.toLocaleString('en-IN')} pending cases${asOf}`;
    }
    case 'judge_strength': {
      const js = judgeStrength(entity);
      if (!js) return '';
      if (js.appointed != null && js.allotted != null) {
        const vacant = js.vacancy_count;
        const base = `${js.appointed} of ${js.allotted} judges`;
        return vacant != null ? `${base} · ${vacant} vacant` : base;
      }
      if (js.vacancy_count != null && js.allotted != null) {
        return `${js.vacancy_count} vacant of ${js.allotted} sanctioned`;
      }
      return '';
    }
    case 'vacancy_days': {
      const days = entity._detail?.appointment?.avg_days_vacancy_unfilled;
      return days != null ? `${days} days average unfilled` : '';
    }
    case 'independence_risk': {
      if (!shouldShowStructuralScores(entity)) return '';
      const ir = entity.derived?.independence_risk_score;
      if (ir == null) return '';
      return `Independence risk ${ir} · ${entity.derived.independence_risk_level || '—'}`;
    }
    case 'structural_health': {
      if (!shouldShowStructuralScores(entity)) return '';
      const health = entity.derived?.structural_health_score;
      if (health == null) return '';
      return `Structural health ${health}`;
    }
    case 'created_year':
      return entity.created_year != null ? `Created ${entity.created_year}` : '';
    case 'abolished_year':
      return entity.abolished_year != null ? `Abolished ${entity.abolished_year}` : '';
    case 'gap': {
      const gaps = extractGapEntries(entity);
      const g = gaps[0];
      if (!g) return '';
      const parts = [g.gap_severity, g.gap_type].filter(Boolean);
      const since = g.gap_since_year != null ? `since ${g.gap_since_year}` : '';
      return [parts.join(' · '), since].filter(Boolean).join(' · ') || 'Structural gap recorded';
    }
    case 'jurisdiction': {
      const st = primaryState(entity);
      return st ? `State: ${st}` : '';
    }
    case 'data_quality':
      return entity.data_quality ? `Data quality: ${entity.data_quality}` : '';
    case 'status':
    default:
      return entity.operational_status?.replace(/_/g, ' ') || '';
  }
}

function profileCard(entity, { primary = false, statMode } = {}) {
  const slug = entity.id;
  const status = entity.operational_status?.replace(/_/g, ' ') || '—';
  const stat = statMode ? entityStatLine(entity, statMode) : '';
  return `
    <button type="button" class="insight-profile-card${primary ? ' insight-profile-primary' : ''}" data-entity-id="${slug}">
      <span class="ipc-name ${entity.data_quality || ''}">${entityDisplayName(entity)}</span>
      <span class="ipc-meta">${formatType(entity.type)} · ${status}</span>
      ${stat ? `<span class="ipc-stat">${stat}</span>` : ''}
    </button>
  `;
}

export function renderInsightPanel(result) {
  if (!result) return '';
  const sourceList = (result.sources || [])
    .filter((s) => s && (s.url || s.title || s.label))
    .map((s) => {
      const label = s.label || s.title || s.url;
      if (s.url) {
        return `<li><a href="${s.url}" target="_blank" rel="noopener noreferrer">${label}</a></li>`;
      }
      return `<li>${label}</li>`;
    })
    .join('');

  const entities = result.entities || [];
  const primary = entities[0];
  const rest = entities.slice(1);
  const statMode = result.statMode || INSIGHT_STAT_MODE[result.id];

  const profiles = primary
    ? `<div class="insight-profiles">
        ${profileCard(primary, { primary: true, statMode })}
        ${rest.length ? `<div class="insight-profile-list">${rest.map((e) => profileCard(e, { statMode })).join('')}</div>` : ''}
      </div>`
    : '';

  const missingNote = result.insufficient
    ? ' We’ve noted this question for a future JEM update.'
    : '';
  const requestLog = result.insufficient ? renderMissingInsightLogTable() : '';

  return `
    <div class="insight-onebox${result.insufficient ? ' insight-insufficient' : ''}" role="region" aria-label="Insight answer">
      <button type="button" class="insight-close" aria-label="Close insight">×</button>
      <h3 class="insight-title">${result.title}</h3>
      <p class="insight-answer">${result.answer}${missingNote}</p>
      <p class="insight-snapshot">${result.snapshotNote}</p>
      ${sourceList ? `<ul class="insight-sources">${sourceList}</ul>` : ''}
      ${requestLog}
    </div>
    ${profiles}
  `;
}

export function initSmartSearch({
  graph: initialGraph,
  inputEl,
  resultsEl,
  panelEl,
  chipsEl,
  fuseFactory,
  onEntityPick,
  onInsightShow,
  onLayoutChange,
}) {
  if (!inputEl || !resultsEl) {
    return { showInsight: () => {}, setEntityFuse: () => {}, setGraph: () => {}, refreshSearchChrome: () => {} };
  }

  const wrapEl = document.getElementById('search-wrap');
  const containerEl = document.getElementById('search-container');
  const toolbarEl = document.getElementById('toolbar');
  let blurTimer = null;

  let graph = initialGraph || null;
  let availableInsightIds = graph ? computeAvailableInsightIds(graph) : new Set();
  let insightFuse = graph && fuseFactory ? buildInsightFuse(fuseFactory, availableInsightIds) : null;
  let entityFuse = null;

  function refreshSearchChrome() {
    const focused = document.activeElement === inputEl;
    const dropdownOpen = !resultsEl.classList.contains('hidden');
    const insightOpen = Boolean(panelEl && !panelEl.classList.contains('hidden'));
    const expanded = focused || dropdownOpen || insightOpen;
    wrapEl?.classList.toggle('search-active', expanded);
    toolbarEl?.classList.toggle('search-active', expanded);
    inputEl.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    onLayoutChange?.();
  }

  function setGraph(g) {
    graph = g;
    availableInsightIds = graph ? computeAvailableInsightIds(graph) : new Set();
    if (fuseFactory) insightFuse = buildInsightFuse(fuseFactory, availableInsightIds);
    renderChips();
    refreshSearchChrome();
  }

  function renderChips() {
    if (!chipsEl) return;
    const byId = new Map(INSIGHT_DEFS.map((d) => [d.id, d]));
    const featured = FEATURED_CHIP_IDS
      .map((id) => byId.get(id))
      .filter((d) => d?.chip && availableInsightIds.has(d.id));
    chipsEl.innerHTML = featured.map((d) =>
      `<button type="button" class="insight-chip" data-insight-id="${d.id}">${d.chip}</button>`,
    ).join('');
    chipsEl.querySelectorAll('.insight-chip').forEach((btn) => {
      btn.addEventListener('click', () => showInsight(btn.dataset.insightId));
    });
  }

  function collapseSearchUI({ clearInput = false } = {}) {
    resultsEl.classList.add('hidden');
    if (panelEl) {
      panelEl.classList.add('hidden');
      panelEl.innerHTML = '';
    }
    if (clearInput) inputEl.value = '';
    inputEl.blur();
    refreshSearchChrome();
  }

  function showMissingInsight(def) {
    if (!graph || !panelEl || !def) return;
    inputEl.value = def.title;
    panelEl.innerHTML = renderMissingInsightPanel(def, graph);
    panelEl.classList.remove('hidden');
    wirePanel(panelEl);
    resultsEl.classList.add('hidden');
    refreshSearchChrome();
  }

  function showInsight(id) {
    if (!graph) return;
    const def = INSIGHT_DEFS.find((d) => d.id === id);
    if (!def) return;
    if (!availableInsightIds.has(id)) {
      showMissingInsight(def);
      return;
    }
    inputEl.value = def.title;
    const result = computeInsight(id, graph);
    if (!result || !panelEl) return;
    if (result.insufficient) {
      void logMissingInsightRequest(id, def.title, inputEl.value.trim());
    }
    panelEl.innerHTML = renderInsightPanel(result);
    panelEl.classList.remove('hidden');
    wirePanel(panelEl);
    onInsightShow?.(result);
    resultsEl.classList.add('hidden');
    refreshSearchChrome();
  }

  function wirePanel(root) {
    root.querySelector('.insight-close')?.addEventListener('click', () => {
      collapseSearchUI();
    });
    root.querySelectorAll('[data-entity-id]').forEach((link) => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const id = link.dataset.entityId;
        collapseSearchUI();
        onEntityPick?.(id);
      });
    });
    if (root.querySelector('.insight-request-log, .insight-missing, .insight-insufficient')) {
      void refreshInsightRequestLog(root);
    }
  }

  function renderDropdown(query) {
    const q = query.trim();
    if (!q) {
      resultsEl.classList.add('hidden');
      refreshSearchChrome();
      return;
    }

    if (!graph || !insightFuse) {
      resultsEl.innerHTML = '<div class="search-empty">Loading map data…</div>';
      resultsEl.classList.remove('hidden');
      refreshSearchChrome();
      return;
    }

    const insightHits = searchInsightDefs(q, insightFuse, availableInsightIds);
    const entityHits = entityFuse ? searchEntityHits(q, graph.entities, entityFuse, 8) : [];

    if (!insightHits.length && !entityHits.length) {
      const unavailable = findUnavailableInsightMatch(q, availableInsightIds);
      if (unavailable) {
        showMissingInsight(unavailable);
        return;
      }
      resultsEl.innerHTML = `<div class="search-empty">No matches for “${q}”. Try an entity name, or a question like “HC vacancies” or “GSTAT high court”.</div>`;
      resultsEl.classList.remove('hidden');
      refreshSearchChrome();
      return;
    }

    const insightHtml = insightHits.map((h) => `
      <div class="search-result search-insight-hit" data-insight-id="${h.item.id}">
        <span class="sr-insight-icon" aria-hidden="true">?</span>
        <span class="sr-name">${h.item.title}</span>
        <span class="sr-type">Insight</span>
      </div>
    `).join('');

    const entityHtml = entityHits.map((h) => {
      const e = h.item;
      return `<div class="search-result" data-id="${e.id}">
        <span class="sr-name ${e.data_quality}">${entityDisplayName(e)}</span>
        <span class="sr-type">${formatType(e.type)}</span>
        ${e.operational_status === 'Not_Constituted' ? '<span class="sr-badge nc">NC</span>' : ''}
      </div>`;
    }).join('');

    resultsEl.innerHTML = insightHtml + entityHtml;
    resultsEl.classList.remove('hidden');
    refreshSearchChrome();

    resultsEl.querySelectorAll('.search-insight-hit').forEach((el) => {
      el.addEventListener('click', () => {
        showInsight(el.dataset.insightId);
      });
    });
    resultsEl.querySelectorAll('.search-result[data-id]').forEach((el) => {
      el.addEventListener('click', () => {
        collapseSearchUI();
        onEntityPick?.(el.dataset.id);
      });
    });
  }

  function setEntityFuse(fuse) {
    entityFuse = fuse;
  }

  renderChips();

  const onInput = () => renderDropdown(inputEl.value);
  inputEl.addEventListener('input', onInput);
  inputEl.addEventListener('focus', () => {
    clearTimeout(blurTimer);
    if (inputEl.value.trim()) renderDropdown(inputEl.value);
    refreshSearchChrome();
  });
  inputEl.addEventListener('blur', () => {
    blurTimer = setTimeout(refreshSearchChrome, 160);
  });
  const preventBlurOnClick = (e) => {
    if (e.target.closest('.insight-chip, .search-result, .insight-close, .insight-profile-card')) {
      e.preventDefault();
    }
  };
  wrapEl?.addEventListener('mousedown', preventBlurOnClick);
  containerEl?.addEventListener('mousedown', preventBlurOnClick);

  refreshSearchChrome();

  return { showInsight, setEntityFuse, setGraph, refreshSearchChrome, collapseSearchUI };
}
