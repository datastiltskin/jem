// Plain-language checks on entity profiles.
// SAMPLE GATE: only SAT until the maintainer confirms JEM-wide rollout.
// Codes (verdicts, join outcomes) stay in the dashboard JSON. This module
// never prints them.

export const CONSENSUS_NOTES_JEM_WIDE = false;
export const CONSENSUS_NOTE_SAMPLE_IDS = ['sat'];

export const LETI_DISCORD = 'https://discord.gg/TVGhWNwN3';

const DASH_URL = './public/consensus_dashboard.json';

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const FIELD_LABEL = {
  pending_cases: 'Pending cases',
  filed_last_year: 'Filed (last year)',
  disposed_last_year: 'Disposed (last year)',
  disposal_rate: 'Disposal rate',
  avg_disposal_days: 'Avg disposal days',
  njdg_source_stamp: 'National Judicial Data Grid listing',
};

let _dashPromise = null;

export function consensusNotesEnabledFor(entityId) {
  if (!entityId) return false;
  if (CONSENSUS_NOTES_JEM_WIDE) return true;
  return CONSENSUS_NOTE_SAMPLE_IDS.includes(entityId);
}

export function loadConsensusDashboard() {
  if (!_dashPromise) {
    _dashPromise = fetch(DASH_URL)
      .then((r) => (r.ok ? r.json() : null))
      .catch(() => null);
  }
  return _dashPromise;
}

export function cellsForEntity(dash, entityId) {
  if (!dash || !entityId) return [];
  return (dash.cells || []).filter((c) => c.entity_id === entityId);
}

export function creditLabel(c) {
  if (c.anonymous || !c.display_name) return 'Anonymous';
  return c.display_name;
}

/** People who checked this field. Letters are not shown. */
export function contributionsForCell(cell) {
  if (Array.isArray(cell.contributions) && cell.contributions.length) {
    return cell.contributions;
  }
  const out = [];
  if (cell.prajna) {
    out.push({
      display_name: 'Prajna Prayas',
      anonymous: false,
      file: 'deepseek__verify-trib-01__prajna__20260831_131656.csv',
      recorded_at: '2026-08-31T13:16:56',
      verdict: cell.prajna.verdict,
      value: cell.prajna.value,
    });
  }
  if (cell.agriya) {
    out.push({
      display_name: 'Agriya Khetarpal',
      anonymous: false,
      file: 'codex__verify-trib-01__agriya__20260906_042259.csv',
      recorded_at: '2026-09-06T04:22:59',
      verdict: cell.agriya.verdict,
      value: cell.agriya.value,
    });
  }
  return out;
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

/** 2026-01-01 or 2026-01-01T13:16:56 → "1 Jan, 2026". */
export function formatPlainDate(iso) {
  const m = String(iso ?? '').match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return '';
  const month = MONTHS[Number(m[2]) - 1];
  if (!month) return '';
  return `${Number(m[3])} ${month}, ${m[1]}`;
}

function formatFigure(value) {
  if (value == null || value === '') return '';
  const raw = String(value).trim();
  if (raw.toLowerCase() === 'absent') return 'not listed';
  const n = Number(raw);
  if (!Number.isFinite(n)) return raw;
  if (Math.abs(n) < 10 && !Number.isInteger(n)) return raw;
  return new Intl.NumberFormat('en-IN').format(n);
}

function history(cell) {
  return Array.isArray(cell.value_history) ? cell.value_history : [];
}

/** What the map shows now, from the newest promoted trail entry. */
function currentEntry(cell) {
  const hist = history(cell);
  const promoted = hist.find((h) => (
    h.change_reason === 'corrected_false'
    || h.change_reason === 'source_corrected'
    || h.change_reason === 'superseded_newer_period'
    || h.change_reason === 'expert_confirmed'
    || h.change_reason === 'expert_overridden'
  ));
  if (promoted && promoted.value != null && promoted.value !== '') return promoted;
  const first = hist[0];
  if (first && first.value != null && first.value !== '') return first;
  return null;
}

/** JEM’s first published figure — the initial stored value, dated by data_as_of when we have it. */
function jemOriginal(cell) {
  const hist = history(cell);
  const initial = [...hist].reverse().find((h) => h.change_reason === 'initial' && h.value != null && h.value !== '');
  if (!initial) return null;
  const dated = hist.find((h) => (
    h.data_as_of && String(h.value) === String(initial.value)
  ));
  return {
    value: initial.value,
    asOf: (dated && dated.data_as_of) || initial.data_as_of || null,
  };
}

function checkerSentence(person) {
  const name = creditLabel(person);
  const when = formatPlainDate(person.recorded_at);
  const whenBit = when ? ` (${when})` : '';
  const shown = formatFigure(person.value);
  if (person.verdict === 'UNSOURCED' || !shown) {
    return `${name} checked it and did not find a matching source${whenBit}.`;
  }
  if (person.verdict === 'CONFIRM') {
    return `${name} checked it and agreed with ${shown}${whenBit}.`;
  }
  return `${name} checked it and read ${shown}${whenBit}.`;
}

function outcomeBits(cell) {
  const bits = [];
  if (cell.canon_result === 'reached canon') bits.push('The map was updated.');
  else if (cell.canon_result === 'contamination-dropped') bits.push('The stored figure was removed as unreliable.');
  else if (cell.canon_result === 'pending-expert') bits.push('Held for a reviewer.');
  else bits.push('No source found — JEM’s figure is unchanged.');
  if (cell.reconcile_outcome === 'disagree_period') {
    bits.push('The old figure was for a different period.');
  }
  return bits.join(' ');
}

function fieldLabel(cell) {
  return FIELD_LABEL[cell.field] || String(cell.field || '').replace(/_/g, ' ');
}

function listLine(cell) {
  const label = fieldLabel(cell);
  const cur = currentEntry(cell);
  const orig = jemOriginal(cell);
  const now = cur ? formatFigure(cur.value) : '';
  if (cell.canon_result === 'reached canon' && now) {
    const changed = orig && String(orig.value) !== String(cur.value);
    const origBit = changed ? ` JEM first published ${formatFigure(orig.value)}.` : '';
    return `${label} — the map now shows ${now}.${origBit}`;
  }
  if (cell.canon_result === 'contamination-dropped') {
    return `${label} — the stored figure was removed as unreliable.`;
  }
  if (cell.canon_result === 'pending-expert') {
    return `${label} — held for a reviewer.`;
  }
  return `${label} — no source found. JEM’s figure is unchanged.`;
}

function notesHTML(cells) {
  const items = cells.map((c) => `<li>${esc(listLine(c))}</li>`).join('');
  return `
    <details class="dv-check-notes">
      <summary>How these figures were checked</summary>
      <p class="dv-check-lede">JEM first published a figure. Later, people checked it against a source. This sample is SAT only. Discussion: <a href="${LETI_DISCORD}" target="_blank" rel="noopener noreferrer">LETI on Discord</a>.</p>
      <ul class="dv-check-list">${items}</ul>
    </details>`;
}

function expandHTML(cell) {
  const orig = jemOriginal(cell);
  const cur = currentEntry(cell);
  const people = contributionsForCell(cell);
  const origWhen = orig && orig.asOf ? ` (${formatPlainDate(orig.asOf)})` : '';
  const origLine = orig
    ? `<p>JEM first published <strong>${esc(formatFigure(orig.value))}</strong>${esc(origWhen)}.</p>`
    : '';
  const checks = people.map((p) => `<p>${esc(checkerSentence(p))}</p>`).join('');
  let nowLine = '';
  if (cur) {
    const asOf = cur.data_as_of ? ` (year ending ${formatPlainDate(cur.data_as_of)})` : '';
    nowLine = `<p>The map now shows <strong>${esc(formatFigure(cur.value))}</strong>${esc(asOf)}.</p>`;
  }
  const files = people.filter((p) => p.file).map((p) => {
    const when = formatPlainDate(p.recorded_at);
    return `<li>${esc(creditLabel(p))}${when ? ` — ${esc(when)}` : ''} <span class="cv-check-file">${esc(p.file)}</span></li>`;
  }).join('');
  const filesBlock = files
    ? `<details class="cv-check-files"><summary>Files</summary><ul>${files}</ul></details>`
    : '';
  return `
    <div class="cv-check-body">
      ${origLine}
      ${checks}
      ${nowLine}
      <p>${esc(outcomeBits(cell))}</p>
      ${filesBlock}
    </div>`;
}

function decorateFieldRow(el, cell) {
  if (el.closest('.cv-check-field')) return;
  const wrap = document.createElement('details');
  wrap.className = 'cv-check-field';
  const summary = document.createElement('summary');
  summary.className = 'cv-check-summary';
  el.parentNode.insertBefore(wrap, el);
  summary.appendChild(el);
  wrap.appendChild(summary);
  wrap.insertAdjacentHTML('beforeend', expandHTML(cell));
}

function annotateCaseVolume(container, cells) {
  const byField = Object.fromEntries(cells.map((c) => [c.field, c]));
  container.querySelectorAll('.cv-rows > [data-cv-field]').forEach((el) => {
    if (el.closest('.cv-check-field')) return;
    const cell = byField[el.getAttribute('data-cv-field')];
    if (!cell) return;
    decorateFieldRow(el, cell);
  });
}

export function mountConsensusNotes(container, entityId) {
  if (!container || !consensusNotesEnabledFor(entityId)) return;
  loadConsensusDashboard().then((dash) => {
    if (!dash) return;
    const cells = cellsForEntity(dash, entityId);
    if (!cells.length) return;
    annotateCaseVolume(container, cells);
    const host = container.querySelector('[data-consensus-host]');
    if (!host) return;
    host.querySelector('.dv-check-notes')?.remove();
    host.insertAdjacentHTML('beforeend', notesHTML(cells));
  });
}
