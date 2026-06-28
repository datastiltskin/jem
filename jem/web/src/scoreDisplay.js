// When to show structural health / IR / DP in the UI (mirrors derive.py exclusions).

export const GOVERNANCE_EXCLUDED_MSG =
  'Scores excluded: governance officeholder or administrative body';

const OFFICEHOLDER_IDS = new Set([
  'president_india',
  'chief_justice_india',
  'governor_state',
  'prime_minister',
  'speaker_lok_sabha',
  'deputy_chairman_rajya_sabha',
  'leader_opposition_lok_sabha',
  'leader_opposition_rajya_sabha',
]);

const OFFICEHOLDER_SUFFIXES = ['_lieutenant_governor', '_advocate_general'];

/** Governance graph anchors — not scored adjudicatory bodies (see derive.py). */
export function isGovernanceScoresExcluded(entity) {
  if (!entity) return true;
  const entityType = entity.type || '';
  if (entityType === 'AppointmentBody') return false;

  const entityId = entity.id || '';
  const cluster = entity.cluster || '';

  if (entityId.startsWith('ministry_') || entityId.startsWith('minister_')) return true;
  if (OFFICEHOLDER_IDS.has(entityId)) return true;
  if (OFFICEHOLDER_SUFFIXES.some((s) => entityId.endsWith(s))) return true;
  if (
    entityType === 'ExecutiveBody' &&
    ['legislative_executive', 'executive_interface'].includes(cluster)
  ) {
    return true;
  }
  return false;
}

export function hasGovernanceExclusionBreakdown(derived = {}) {
  for (const key of [
    'structural_health_breakdown',
    'independence_risk_breakdown',
    'discretionary_power_breakdown',
  ]) {
    const bd = derived[key];
    if (bd && GOVERNANCE_EXCLUDED_MSG in bd) return true;
  }
  return false;
}

/** @returns {'abolished' | 'governance' | null} */
export function structuralScoresHiddenReason(entity) {
  if (!entity) return 'governance';
  if (entity.operational_status === 'Abolished') return 'abolished';
  if (isGovernanceScoresExcluded(entity)) return 'governance';
  if (hasGovernanceExclusionBreakdown(entity.derived)) return 'governance';
  return null;
}

/**
 * Show structural health / IR / DP blocks.
 * Entity-adjacent roles (e.g. LegalOfficer — AG, SG) remain scored and visible.
 */
export function shouldShowStructuralScores(entity) {
  return structuralScoresHiddenReason(entity) == null;
}

export function structuralScoresHiddenMessage(entity) {
  const reason = structuralScoresHiddenReason(entity);
  if (reason === 'abolished') {
    return 'Structural scores are not shown for abolished institutions.';
  }
  if (reason === 'governance') {
    return 'Structural scores are not computed for governance anchors and officeholder nodes.';
  }
  return 'Structural scores are not available for this record.';
}

/** Insight search / rankings — scored adjudicatory and entity-adjacent bodies only. */
export function isScoredEntity(entity) {
  if (!shouldShowStructuralScores(entity)) return false;
  return typeof entity?.derived?.independence_risk_score === 'number';
}
