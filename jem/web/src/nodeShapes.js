// JEM — Shared node shape helpers (main map + neighborhood panel)
//
// Shape legend:
//   hexagon   — Supreme Court
//   pentagon  — High Courts (principal seat)
//   crescent  — HC permanent benches
//   circle    — subordinate / city / special courts
//   diamond   — tribunals & consumer commissions
//   triangle  — regulatory quasi-judicial bodies
//   square    — arbitration & ADR institutions
//   rect      — executive, appointment, other stakeholders

/** Permanent High Court bench (Madurai, Nagpur, etc.). */
export function isHighCourtBenchEntity(entity) {
  return entity?.type === 'HighCourtBench';
}

function isSupremeCourt(entity) {
  return entity?.id === 'supreme_court_india'
    || (entity?.type === 'ConstitutionalCourt' && entity?.id === 'supreme_court_india');
}

function isPrincipalHighCourt(entity) {
  return entity?.type === 'ConstitutionalCourt'
    && typeof entity?.id === 'string'
    && entity.id.startsWith('hc_');
}

function isTribunalEntity(entity) {
  if (isRegulatoryQJ(entity) || isArbitrationEntity(entity)) return false;
  const t = entity?.type;
  const c = entity?.cluster;
  if (t === 'CentralTribunal' || t === 'StateTribunal' || t === 'ConsumerCommission') return true;
  if (c === 'tribunals_adr' && t !== 'ADRBody') return true;
  return false;
}

function isRegulatoryQJ(entity) {
  return entity?.type === 'RegulatoryBodyQJ' || entity?.cluster === 'regulatory_bodies';
}

function isArbitrationEntity(entity) {
  const t = entity?.type;
  const c = entity?.cluster;
  return t === 'ArbitralInstitution' || t === 'MediationBody' || c === 'arbitration';
}

function isSubordinateCourt(entity) {
  const t = entity?.type;
  return t === 'SubordinateCivilCourt'
    || t === 'SubordinateCriminalCourt'
    || t === 'CityCivilCourt'
    || t === 'SpecialCourt';
}

/**
 * Resolved drawable shape id for an entity.
 * @returns {'hexagon'|'pentagon'|'crescent'|'circle'|'diamond'|'triangle'|'square'|'rect'}
 */
export function entityNodeShape(entity) {
  if (!entity) return 'rect';
  if (entity.role_layer) return 'rect';
  if (isHighCourtBenchEntity(entity)) return 'crescent';
  if (isSupremeCourt(entity)) return 'hexagon';
  if (isPrincipalHighCourt(entity)) return 'pentagon';
  if (isSubordinateCourt(entity)) return 'circle';
  if (isRegulatoryQJ(entity)) return 'triangle';
  if (isArbitrationEntity(entity)) return 'square';
  if (isTribunalEntity(entity)) return 'diamond';
  // ADR bodies (SLSA, lok adalat) — diamond (tribunal/ADR tier)
  if (entity.type === 'ADRBody') return 'diamond';
  // Remaining constitutional (e.g. aggregate stubs) — circle
  if (entity.type === 'ConstitutionalCourt') return 'circle';
  return 'rect';
}

/** SVG path d for shape, centred at (0,0). */
export function nodeShapePathD(shape, radius) {
  const r = radius;
  switch (shape) {
    case 'hexagon': return regularPolygonPath(6, r);
    case 'pentagon': return regularPolygonPath(5, r);
    case 'crescent': return crescentPathD(r);
    case 'diamond': return diamondPathD(r);
    case 'triangle': return trianglePathD(r);
    case 'square': return squarePathD(r);
    case 'circle': return circlePathD(r);
    default: return null;
  }
}

export function nodeShapePathForEntity(entity, radius) {
  const shape = entityNodeShape(entity);
  if (shape === 'rect') return null;
  return nodeShapePathD(shape, radius);
}

/** Layout collision radius — slightly larger for pointy shapes. */
export function shapeLayoutRadius(entity, baseRadius) {
  const shape = entityNodeShape(entity);
  if (shape === 'triangle') return baseRadius * 1.12;
  if (shape === 'hexagon' || shape === 'pentagon') return baseRadius * 1.06;
  if (shape === 'diamond' || shape === 'square') return baseRadius * 1.04;
  return baseRadius;
}

function regularPolygonPath(sides, radius, startAngle = -Math.PI / 2) {
  const pts = [];
  for (let i = 0; i < sides; i++) {
    const a = startAngle + (2 * Math.PI * i) / sides;
    pts.push([radius * Math.cos(a), radius * Math.sin(a)]);
  }
  return `M ${pts.map(([x, y]) => `${x.toFixed(2)},${y.toFixed(2)}`).join(' L ')} Z`;
}

export function crescentPathD(radius) {
  const r = radius;
  const rInner = r * 0.68;
  const offsetX = r * 0.42;
  return `${circleSubpath(0, 0, r)} ${circleSubpath(offsetX, 0, rInner)}`;
}

function circleSubpath(cx, cy, r) {
  return `M ${cx - r},${cy} a ${r},${r} 0 1,0 ${2 * r},0 a ${r},${r} 0 1,0 ${-2 * r},0 Z`;
}

function circlePathD(r) {
  return circleSubpath(0, 0, r);
}

function diamondPathD(r) {
  return `M 0,${-r} L ${r},0 L 0,${r} L ${-r},0 Z`;
}

function trianglePathD(r) {
  const top = -r * 1.05;
  const base = r * 0.72;
  return `M 0,${top} L ${r},${base} L ${-r},${base} Z`;
}

function squarePathD(r) {
  return `M ${-r},${-r} L ${r},${-r} L ${r},${r} L ${-r},${r} Z`;
}
