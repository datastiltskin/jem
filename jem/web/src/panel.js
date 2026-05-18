// JEM — Entity Detail Panel (Level 3)
// Opens on entity click. Shows all attributes with sourced facts.
// Derived scores shown with "Pending review" notice if not validated.

import { State } from './state.js';
import { openNeighborhoodPanel, closeNeighborhoodPanel } from './neighborhoodPanel.js';
import { buildEntityConnectionSummary, formatCategoryLabel } from './entityConnections.js';

export function openDetailPanel(entity) {
  const panel = document.getElementById('detail-panel');
  const nameEl = document.getElementById('detail-entity-name');
  const typeEl = document.getElementById('detail-entity-type');
  const body = document.getElementById('detail-panel-body');

  if (entity._jemSyntheticAggregate) {
    closeNeighborhoodPanel();
    nameEl.textContent = entity.name;
    typeEl.textContent = 'Collapsed lattice (map convenience)';
    typeEl.className = 'detail-type';
    const n = entity.memberCount ?? '—';
    body.innerHTML = `
      <div class="detail-quality-banner quality-partial">
        This node stands in for <strong>${n}</strong> separate district benches on the map.
      </div>
      <p style="margin-top:12px;line-height:1.5">
        Use the <strong>teal + / −</strong> control on the node to expand or collapse just this state.
        Keyboard: <kbd>+</kbd> or <kbd>=</kbd> expands every state lattice; <kbd>−</kbd> collapses all to one row per state (or this summary where no generic row exists).
      </p>
    `;
    panel.classList.remove('hidden');
    panel.scrollTop = 0;
    return;
  }

  nameEl.textContent = entity.name;
  if (entity.name_hindi) {
    nameEl.innerHTML = `${entity.name}<span class="detail-name-hindi"> ${entity.name_hindi}</span>`;
  }

  typeEl.textContent = `${formatType(entity.type)} · ${entity.level_of_government} · ${entity.operational_status}`;
  typeEl.className = `detail-type status-${entity.operational_status.toLowerCase().replace('_','-')}`;

  body.innerHTML = buildPanelHTML(entity);

  panel.classList.remove('hidden');
  panel.scrollTop = 0;

  openNeighborhoodPanel(entity);
}

export function closeDetailPanel() {
  document.getElementById('detail-panel').classList.add('hidden');
  closeNeighborhoodPanel();
  State.clearEntity();
}

function buildPanelHTML(e) {
  const d = e._detail || {};
  const derived = e.derived || {};
  const irColors = State.graph ? State.getIndependenceRiskColors() : {};
  const irLevel = derived.independence_risk_level || 'unknown';
  const irScore = derived.independence_risk_score;
  const dpScore = derived.discretionary_power_score;

  let html = '';

  // ── Data Quality Banner ────────────────────────────────
  html += `<div class="detail-quality-banner quality-${e.data_quality}">
    ${qualityIcon(e.data_quality)} Data: <strong>${e.data_quality}</strong>
    ${e.data_quality_notes ? `— ${e.data_quality_notes}` : ''}
  </div>`;

  // ── Lifecycle ──────────────────────────────────────────
  html += section('Lifecycle', `
    <div class="detail-row"><span class="lbl">Established</span><span>${e.created_year}</span></div>
    ${e.abolished_year ? `<div class="detail-row abolished"><span class="lbl">Abolished</span><span>${e.abolished_year}</span></div>` : ''}
    <div class="detail-row"><span class="lbl">Status</span><span class="status-badge status-${(e.operational_status||'').toLowerCase().replace('_','-')}">${e.operational_status}</span></div>
    ${e.constitutional_basis ? `<div class="detail-row"><span class="lbl">Constitutional basis</span><span class="monospace">${e.constitutional_basis}</span></div>` : ''}
    ${e.statutory_basis ? `<div class="detail-row"><span class="lbl">Statutory basis</span><span>${e.statutory_basis}</span></div>` : ''}
  `);

  // ── Parent HC (permanent bench) ───────────────────────
  if (d.parent_hc) {
    html += section('High Court structure', `
      ${row('Parent High Court', d.parent_hc)}
    `);
  }

  // ── Direct structural links (graph) ───────────────────
  html += buildConnectionsSectionHTML(e.id);

  // ── Judge strength (v2.0) ─────────────────────────────
  html += buildJudgeStrengthSectionHTML(e, d);

  // ── Appointment Chain ──────────────────────────────────
  if (d.appointment) {
    const a = d.appointment;
    html += section('Appointment Chain', `
      ${row('Nominates', a.nominates)}
      ${row('Recommends', a.recommends)}
      ${a.consulted && a.consulted.length ? row('Consulted (binding: ' + (a.consultation_binding ? 'YES' : 'no') + ')', a.consulted.join(', ')) : ''}
      ${row('Formally appoints', a.formally_appoints)}
      ${a.criteria_public !== null && a.criteria_public !== undefined ?
        `<div class="detail-row ${!a.criteria_public ? 'risk-flag' : ''}">
          <span class="lbl">Appointment criteria public?</span>
          <span>${a.criteria_public ? '✓ Yes' : '✗ No — opacity risk'}</span>
        </div>` : ''}
      ${row('Tenure', a.tenure)}
      ${a.reappointment_possible !== undefined ?
        `<div class="detail-row ${a.reappointment_possible ? 'risk-flag' : ''}">
          <span class="lbl">Reappointment possible?</span>
          <span>${a.reappointment_possible ? '⚠ Yes — creates dependency' : '✓ No'}</span>
        </div>` : ''}
      ${row('Removal authority', a.removal_authority)}
      ${a.removal_requires_parliament !== undefined ?
        `<div class="detail-row">
          <span class="lbl">Removal requires Parliament?</span>
          <span>${a.removal_requires_parliament ? '✓ Yes' : '✗ No'}</span>
        </div>` : ''}
    `);
  }

  // ── Funding ────────────────────────────────────────────
  if (d.funding) {
    const f = d.funding;
    html += section('Funding', `
      ${row('Primary source', f.primary_source)}
      ${row('Responsible ministry', f.ministry_responsible)}
      ${f.state_contribution_percent ? row('State share', f.state_contribution_percent + '%') : ''}
      ${f.budget_figure_crore ? row('Budget (₹ crore)', `${f.budget_figure_crore} Cr (FY ${f.budget_year})`) : ''}
    `);
  }

  // ── Case volume & clog (NJDG / reports) ─────────────────
  if (d.case_volume && typeof d.case_volume === 'object') {
    const cv = d.case_volume;
    const rows = [];
    if (cv.data_as_of) rows.push(row('Data as of', cv.data_as_of));
    if (cv.pending_cases != null) rows.push(row('Pending cases (approx.)', String(cv.pending_cases).replace(/\B(?=(\d{3})+(?!\d))/g, ',')));
    if (cv.filed_last_year != null) rows.push(row('Filed (last year)', String(cv.filed_last_year)));
    if (cv.disposed_last_year != null) rows.push(row('Disposed (last year)', String(cv.disposed_last_year)));
    if (cv.disposal_rate != null) rows.push(row('Disposal rate', String(cv.disposal_rate)));
    if (cv.avg_disposal_days != null) rows.push(row('Avg disposal days', String(cv.avg_disposal_days)));
    if (cv.sanctioned_strength != null && d.judge_strength?.allotted == null) {
      rows.push(row('Sanctioned strength (legacy)', String(cv.sanctioned_strength)));
    }
    if (cv.working_strength != null && d.judge_strength?.appointed == null) {
      rows.push(row('Working strength (legacy)', String(cv.working_strength)));
    }
    if (cv.clog_severity) rows.push(row('Clog severity', cv.clog_severity));
    if (cv.source_type) rows.push(row('Volume source type', cv.source_type));
    if (cv.source_url) rows.push(`<div class="detail-row"><span class="lbl">Volume source</span><span><a href="${cv.source_url}" target="_blank" rel="noopener noreferrer">${cv.source_url}</a></span></div>`);
    if (rows.length) {
      html += section('Case volume & clogging', rows.join(''));
    }
  }

  // ── Audit ──────────────────────────────────────────────
  if (d.audit) {
    const a = d.audit;
    html += section('Audit & Oversight', `
      ${row('Audited by', a.audited_by)}
      ${row('Audit type', a.audit_type)}
      ${a.audit_report_public !== undefined ?
        `<div class="detail-row">
          <span class="lbl">Audit reports public?</span>
          <span>${a.audit_report_public ? '✓ Yes' : '✗ No'}</span>
        </div>` : ''}
      ${row('Conduct oversight body', a.conduct_oversight_body || 'None identified')}
    `);
  }

  // ── Complaint Mechanism ────────────────────────────────
  if (d.complaint_mechanism) {
    const c = d.complaint_mechanism;
    let complaintHtml = '';
    if (c.bias_complaint_to && c.bias_complaint_to.length > 0) {
      c.bias_complaint_to.forEach((b, i) => {
        complaintHtml += `<div class="complaint-body">
          <strong>${i+1}. ${b.body}</strong>
          <div class="complaint-detail">${b.mechanism}</div>
          <div class="complaint-flags">
            ${b.external_to_judiciary ? '<span class="flag green">External oversight</span>' : '<span class="flag orange">Internal only</span>'}
            ${b.is_public_process ? '<span class="flag green">Public process</span>' : '<span class="flag grey">Not public</span>'}
            ${b.complainant_has_locus ? '<span class="flag green">Complainant has locus</span>' : '<span class="flag red">No locus for complainant</span>'}
            ${b.timeframe_defined ? '<span class="flag green">Timeframe defined</span>' : '<span class="flag grey">No defined timeframe</span>'}
          </div>
        </div>`;
      });
    } else {
      complaintHtml = '<div class="risk-flag-block">⚠ No complaint mechanism found</div>';
    }
    if (c.criminal_prosecution) {
      const cp = c.criminal_prosecution;
      complaintHtml += `<div class="detail-row risk-flag">
        <span class="lbl">Criminal prosecution requires sanction from</span>
        <span>${cp.requires_sanction_from}</span>
      </div>`;
      if (cp.consultation_required_with) {
        complaintHtml += `<div class="detail-row ${cp.consultation_binding ? 'risk-flag' : ''}">
          <span class="lbl">Consultation with (binding: ${cp.consultation_binding ? 'YES' : 'no'})</span>
          <span>${cp.consultation_required_with}</span>
        </div>`;
      }
    }
    if (c.lokpal_jurisdiction) {
      const ljClass = c.lokpal_jurisdiction === 'No' ? 'risk-flag' : c.lokpal_jurisdiction === 'Contested' ? 'contested-flag' : '';
      complaintHtml += `<div class="detail-row ${ljClass}">
        <span class="lbl">Lokpal jurisdiction</span>
        <span>${c.lokpal_jurisdiction}${c.lokpal_jurisdiction_note ? ' — ' + c.lokpal_jurisdiction_note : ''}</span>
      </div>`;
    }
    html += section('Complaint Mechanism (Bias / Misconduct)', complaintHtml);
  }

  // ── Derived Scores ─────────────────────────────────────
  if (irScore !== undefined || dpScore !== undefined) {
    const validated = derived.scores_validated;
    html += `<div class="detail-section">
      <div class="detail-section-title">
        Structural Risk Indicators
        ${!validated ? '<span class="unvalidated-badge">⚐ Pending community review</span>' : ''}
      </div>
      ${irScore !== undefined ? `
        <div class="score-row">
          <div class="score-label">Independence Risk</div>
          <div class="score-bar-outer">
            <div class="score-bar-fill ir-${irLevel}" style="width:${Math.min(100, irScore*8)}%"></div>
          </div>
          <div class="score-number" style="color:${irColors[irLevel] || '#27ae60'}">${irScore} — ${irLevel.toUpperCase()}</div>
        </div>
        ${buildBreakdown(derived.independence_risk_breakdown)}
      ` : ''}
      ${dpScore !== undefined ? `
        <div class="score-row" style="margin-top:12px">
          <div class="score-label">Discretionary Power</div>
          <div class="score-bar-outer">
            <div class="score-bar-fill dp" style="width:${Math.min(100, dpScore*6)}%"></div>
          </div>
          <div class="score-number">${dpScore}</div>
        </div>
        ${buildBreakdown(derived.discretionary_power_breakdown)}
      ` : ''}
      <div class="score-note">
        These scores are algorithmically derived from the data fields above.
        They are structural indicators, not judgments on conduct.
        Each factor links back to a data field — see ARCHITECTURE.md.
      </div>
    </div>`;
  }

  // ── Sources ────────────────────────────────────────────
  if (e.sources && e.sources.length > 0) {
    let sourceHtml = e.sources.map(s =>
      `<div class="source-row">
        <span class="source-type source-type-${(s.type||'').toLowerCase()}">${s.type || '?'}</span>
        <a href="${s.url}" target="_blank" rel="noopener noreferrer">${s.label}</a>
        ${s.accessed_date ? `<span class="source-date">Accessed ${s.accessed_date}</span>` : ''}
      </div>`
    ).join('');
    html += section('Primary Sources', sourceHtml);
  }

  return html;
}

// ── HTML Helpers ──────────────────────────────────────────────────────────────

function buildConnectionsSectionHTML(entityId) {
  const summary = buildEntityConnectionSummary(entityId);
  if (!summary.all.length) {
    return section('Structural links (graph)', `
      <p class="detail-connections-note">No direct relationships recorded in the graph for this entity yet
      (e.g. HC → Supreme Court appellate links may still be missing from the dataset).</p>
    `);
  }

  const blocks = [
    { title: 'Appellate toward (higher)', rows: summary.appellateToward },
    { title: 'Appellate from (lower)', rows: summary.appellateFrom },
    { title: 'Supervises', rows: summary.supervises },
    { title: 'Supervised by', rows: summary.supervisedBy },
  ];

  let inner = '';
  for (const block of blocks) {
    if (!block.rows.length) {
      inner += `<div class="detail-row detail-row-muted"><span class="lbl">${block.title}</span><span>—</span></div>`;
      continue;
    }
    inner += `<div class="detail-connection-block">
      <div class="detail-connection-block-title">${block.title}</div>`;
    for (const row of block.rows) {
      inner += `<button type="button" class="detail-connection-row" data-entity-id="${row.entityId}">
        <span class="detail-connection-name">${row.entityName}</span>
        <span class="detail-connection-meta">${row.type}${row.note ? ' — ' + row.note.slice(0, 80) : ''}</span>
      </button>`;
    }
    inner += '</div>';
  }

  const otherEntries = [...summary.byCategory.entries()];
  if (otherEntries.length) {
    inner += `<div class="detail-connection-block"><div class="detail-connection-block-title">Other</div>`;
    for (const [cat, rows] of otherEntries) {
      for (const row of rows) {
        inner += `<button type="button" class="detail-connection-row" data-entity-id="${row.entityId}">
          <span class="detail-connection-name">${row.entityName}</span>
          <span class="detail-connection-meta">${formatCategoryLabel(cat)} · ${row.directionLabel}</span>
        </button>`;
      }
    }
    inner += '</div>';
  }

  return section('Structural links (graph)', inner);
}

function section(title, content) {
  if (!content || content.trim() === '') return '';
  return `<div class="detail-section">
    <div class="detail-section-title">${title}</div>
    ${content}
  </div>`;
}

function row(label, value) {
  if (!value) return '';
  return `<div class="detail-row">
    <span class="lbl">${label}</span>
    <span>${value}</span>
  </div>`;
}

function buildBreakdown(breakdown) {
  if (!breakdown || Object.keys(breakdown).length === 0) return '';
  let html = '<div class="breakdown">';
  Object.entries(breakdown)
    .sort((a, b) => b[1] - a[1])
    .forEach(([reason, pts]) => {
      const sign = pts >= 0 ? '+' : '';
      const cls = pts > 0 ? 'breakdown-positive' : 'breakdown-negative';
      html += `<div class="breakdown-row ${cls}">
        <span class="breakdown-pts">${sign}${pts}</span>
        <span class="breakdown-reason">${reason}</span>
      </div>`;
    });
  html += '</div>';
  return html;
}

function isCourtLikeType(type) {
  return [
    'ConstitutionalCourt',
    'HighCourtBench',
    'SubordinateCivilCourt',
    'SubordinateCriminalCourt',
    'CityCivilCourt',
    'SpecialCourt',
    'CentralTribunal',
    'StateTribunal',
    'ConsumerCommission',
  ].includes(type);
}

function buildJudgeStrengthSectionHTML(entity, d) {
  if (!isCourtLikeType(entity.type)) return '';

  const js = d.judge_strength || {};
  const cv = d.case_volume || {};
  const allotted = js.allotted ?? cv.sanctioned_strength ?? null;
  const appointed = js.appointed ?? cv.working_strength ?? null;
  const vacancy =
    js.vacancy_count != null
      ? js.vacancy_count
      : allotted != null && appointed != null
        ? Math.max(0, allotted - appointed)
        : null;

  const fmt = (n) => (n == null ? '<em class="muted">Not yet recorded</em>' : String(n));
  const rows = [
    row('Judges allotted (sanctioned posts)', fmt(allotted)),
    row('Judges appointed (in post)', fmt(appointed)),
    row('Vacancies', fmt(vacancy)),
    js.data_as_of ? row('Strength data as of', js.data_as_of) : '',
    js.source_type ? row('Source type', js.source_type) : '',
    js.source_url
      ? `<div class="detail-row"><span class="lbl">Source</span><span><a href="${js.source_url}" target="_blank" rel="noopener noreferrer">${js.source_url}</a></span></div>`
      : '',
    js.notes ? `<div class="detail-row"><span class="lbl">Notes</span><span>${js.notes}</span></div>` : '',
  ].filter(Boolean);

  return section('Judge strength', rows.join(''));
}

function qualityIcon(dq) {
  switch(dq) {
    case 'verified': return '✓';
    case 'complete': return '✓';
    case 'partial': return '?';
    case 'unverified': return '~';
    case 'contested': return '⚑';
    default: return '';
  }
}

function formatType(type) {
  return (type || '').replace(/([A-Z])/g, ' $1').trim();
}

// ── Event Binding (called after DOM ready) ────────────────────────────────────

export function initPanel() {
  document.getElementById('detail-close').addEventListener('click', closeDetailPanel);
  State.subscribe('entitySelected', id => {
    if (!id) closeDetailPanel();
  });

  document.getElementById('detail-panel-body')?.addEventListener('click', async (e) => {
    const btn = e.target.closest('.detail-connection-row');
    if (!btn) return;
    e.preventDefault();
    const id = btn.getAttribute('data-entity-id');
    const ent = State.getEntityById(id);
    if (!ent) return;
    State.selectEntity(id);
    openDetailPanel(ent);
  });
}
