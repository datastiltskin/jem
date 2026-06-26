// JEM — structural gap extraction and profile rendering

const GAP_SEVERITY_COLOR = {
  Critical: '#dc2626',
  High: '#d97706',
  Moderate: '#ca8a04',
  Low: '#16a34a',
};

const GAP_STATUS_COLOR = {
  Open: '#dc2626',
  Partial_Addressed: '#d97706',
  Addressed: '#16a34a',
  Contested: '#7c3aed',
};

/** Flatten gap records from graph entity (handles legacy nested build shape). */
export function extractGapEntries(entity) {
  const out = [];
  for (const block of entity?.gaps || []) {
    if (!block || typeof block !== 'object') continue;
    if (block.gap_id || block.gap_type || block.gap_description) {
      out.push(block);
      continue;
    }
    const list = Array.isArray(block.gaps) ? block.gaps : [];
    for (const g of list) {
      if (g && typeof g === 'object') out.push(g);
    }
  }
  return out;
}

export function entityHasGapContent(entity) {
  if (!entity) return false;
  return Boolean(
    entity.gap_flag
    || Number(entity.gap_count) > 0
    || extractGapEntries(entity).length > 0
    || entity.structural_exception
    || entity.operational_status === 'Partial_Operational'
    || entity.operational_status === 'Not_Constituted'
    || entity.operational_status === 'De_Facto_Blocked'
    || (entity.circularity_score ?? entity.derived?.circularity_score ?? 0) > 0,
  );
}

export function renderGapListHTML(entity, { includeOperationalNote = true } = {}) {
  const entries = extractGapEntries(entity);
  let html = '';

  if (includeOperationalNote && entity.operational_status === 'Partial_Operational') {
    html += '<p class="gap-operational-note">Marked <strong class="gap-partial-label">Partial Operational</strong> — statutory constitution is incomplete or only some benches/functions are active.</p>';
  }
  if (includeOperationalNote && entity.operational_status === 'Not_Constituted') {
    html += '<p class="gap-operational-note">Marked <strong class="gap-nc-label">Not Constituted</strong> — legislated or notified but not operational as a functioning body.</p>';
  }

  if (!entries.length) {
    if (entity.operational_status === 'Partial_Operational' || entity.operational_status === 'Not_Constituted') {
      return `${html}<p class="detail-empty-hint">Status flagged in JEM; maintainer gap narrative pending primary-source citation.</p>`;
    }
    return html;
  }

  html += '<ul class="detail-gap-list">';
  for (const g of entries) {
    const sev = g.gap_severity || '';
    const sevColor = GAP_SEVERITY_COLOR[sev] || 'var(--text-secondary)';
    const type = String(g.gap_type || 'gap').replace(/_/g, ' ');
    const desc = g.gap_description || g.description || g.note || '';
    const statusKey = g.gap_status || '';
    const status = statusKey ? String(statusKey).replace(/_/g, ' ') : '';
    const statusColor = GAP_STATUS_COLOR[statusKey] || 'var(--text-secondary)';
    const since = g.gap_since_year ? `Since ${g.gap_since_year}` : '';
    const timeline = g.gap_resolution_note || g.gap_timeline_note || '';
    const source = g.gap_source
      ? `<div class="gap-source">${String(g.gap_source).replace(/</g, '&lt;')}</div>`
      : '';

    html += `<li class="gap-item">
      <div class="gap-item-head">
        <span class="gap-severity" style="color:${sevColor}">${sev || 'Gap'}</span>
        <span class="gap-type">${type}</span>
        ${status ? `<span class="gap-status" style="color:${statusColor}">${status}</span>` : ''}
        ${since ? `<span class="gap-since">${since}</span>` : ''}
      </div>
      ${desc ? `<div class="gap-desc">${desc}</div>` : ''}
      ${timeline ? `<div class="gap-timeline">${timeline}</div>` : ''}
      ${source}
    </li>`;
  }
  html += '</ul>';
  return html;
}
