// Consensus notes on entity profiles.
// SAMPLE GATE: only SAT until the maintainer confirms JEM-wide rollout.
//
// Multi-upload display (locked for this UI):
//   • Current set is letters A | B | C | … — one letter per distinct contributor
//     still in the join (generate or verify).
//   • Same person, later file → that letter is replaced; older file stays in
//     upload history with its timestamp (not a new letter).
//   • Expand lists each current letter (verdict/value) and the upload history
//     (file + time + credit or Anonymous).

export const CONSENSUS_NOTES_JEM_WIDE = false;
export const CONSENSUS_NOTE_SAMPLE_IDS = ['sat'];

export const LETI_DISCORD = 'https://discord.gg/TVGhWNwN3';

const DASH_URL = './public/consensus_dashboard.json';

const FIELD_LABEL = {
  pending_cases: 'Pending cases',
  filed_last_year: 'Filed (last year)',
  disposed_last_year: 'Disposed (last year)',
  disposal_rate: 'Disposal rate',
  avg_disposal_days: 'Avg disposal days',
  njdg_source_stamp: 'NJDG source stamp',
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

/** Current join set. Prefer cell.contributions when the ledger emits it. */
export function contributionsForCell(cell) {
  if (Array.isArray(cell.contributions) && cell.contributions.length) {
    return cell.contributions;
  }
  const out = [];
  if (cell.prajna) {
    out.push({
      letter: 'A',
      role: 'verify',
      display_name: 'Prajna Prayas',
      anonymous: false,
      maintainer: true,
      file: 'deepseek__verify-trib-01__prajna__20260831_131656.csv',
      recorded_at: '2026-08-31T13:16:56',
      verdict: cell.prajna.verdict,
      value: cell.prajna.value,
    });
  }
  if (cell.agriya) {
    out.push({
      letter: 'B',
      role: 'verify',
      display_name: 'Agriya Khetarpal',
      anonymous: false,
      maintainer: true,
      file: 'codex__verify-trib-01__agriya__20260906_042259.csv',
      recorded_at: '2026-09-06T04:22:59',
      verdict: cell.agriya.verdict,
      value: cell.agriya.value,
    });
  }
  return out;
}

export function uploadHistoryForCell(cell) {
  if (Array.isArray(cell.upload_history) && cell.upload_history.length) {
    return cell.upload_history;
  }
  return contributionsForCell(cell);
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

export function rowClass(cell) {
  if (cell.canon_result === 'reached canon') return 'consensus-arrived';
  if (cell.canon_result === 'contamination-dropped') return 'consensus-dropped';
  if (cell.canon_result === 'pending-expert') return 'consensus-pending';
  return 'consensus-gap';
}

function letterChips(contribs) {
  return contribs.map((c) => {
    const title = `${c.letter} · independent check · ${creditLabel(c)}${c.maintainer ? ' (maintainer)' : ''}`;
    return `<span class="cv-letter" title="${esc(title)}">${esc(c.letter)}</span>`;
  }).join('<span class="cv-letter-sep" aria-hidden="true">|</span>');
}

function stripHTML(cell) {
  const contribs = contributionsForCell(cell);
  const hist = uploadHistoryForCell(cell);
  const cols = contribs.map((c) => `
    <div class="cv-ab-col">
      <div class="cv-ab-letter">${esc(c.letter)}</div>
      <div class="cv-ab-role">${esc(c.role || 'verify')}</div>
      <div class="cv-ab-verdict">${esc(c.verdict || '—')}</div>
      <div class="cv-ab-value">${esc(c.value == null || c.value === '' ? '—' : c.value)}</div>
      <div class="cv-ab-credit">${esc(creditLabel(c))}${c.maintainer ? ' · maintainer' : ''}</div>
    </div>`).join('');
  const histRows = hist.map((h) => `
    <tr>
      <td>${esc(h.letter || '')}</td>
      <td>${esc(h.role || '')}</td>
      <td>${esc(creditLabel(h))}</td>
      <td class="mono">${esc(h.file || '')}</td>
      <td class="mono">${esc(h.recorded_at || '')}</td>
    </tr>`).join('');
  return `
    <div class="cv-ab-strip" data-consensus-strip>
      <div class="cv-ab-grid">${cols}</div>
      <p class="cv-ab-outcome">Join: ${esc(cell.reconcile_outcome || '—')}
        · ${esc(cell.canon_result || '')}
        ${cell.classification ? ` · ${esc(cell.classification)}` : ''}</p>
      <details class="cv-ab-history">
        <summary>Uploads that led here (${hist.length})</summary>
        <table>
          <thead><tr><th></th><th>Role</th><th>Credit</th><th>File</th><th>Time</th></tr></thead>
          <tbody>${histRows}</tbody>
        </table>
      </details>
    </div>`;
}

function commentText(cell) {
  const label = FIELD_LABEL[cell.field] || cell.field;
  const letters = contributionsForCell(cell).map((c) => c.letter).join('|') || '—';
  const latest = (cell.value_history && cell.value_history[0]) || {};
  if (cell.canon_result === 'reached canon') {
    const shown = latest.value != null && latest.value !== '' ? latest.value : 'updated';
    return `${label}: consensus arrived (${letters}). JEM now shows ${shown}.`;
  }
  if (cell.canon_result === 'contamination-dropped') {
    return `${label}: stored figure dropped as contamination (${letters}). Held for expert review.`;
  }
  if (cell.canon_result === 'pending-expert') {
    return `${label}: checks disagree or period mismatch (${letters}). Held for expert review.`;
  }
  return `${label}: unsourced gap (${letters}). JEM value unchanged.`;
}

function tocHTML(cells, dash) {
  const arrived = cells.filter((c) => c.canon_result === 'reached canon').length;
  const badge = esc(dash?.round_badge || 'PIPELINE EXERCISE');
  const items = cells.map((c) => {
    const cls = rowClass(c);
    const letters = contributionsForCell(c).map((x) => x.letter).join('|');
    return `
      <li class="dv-comment ${cls}">
        <div class="dv-comment-vote" aria-hidden="true">
          <span class="dv-consensus-mark">${cls === 'consensus-arrived' ? '✓' : '·'}</span>
        </div>
        <div class="dv-comment-body">
          <div class="dv-comment-meta">
            <span class="dv-comment-author">${esc(FIELD_LABEL[c.field] || c.field)}</span>
            <span class="dv-comment-time">· ${esc(letters)} · ${esc(c.canon_result)}</span>
          </div>
          <p class="dv-comment-text">${esc(commentText(c))}</p>
        </div>
      </li>`;
  }).join('');
  return `
    <section class="dv-consensus-notes" aria-label="Consensus notes">
      <header class="dv-comments-head">
        <h2 class="dv-comments-title">Consensus</h2>
        <span class="dv-comments-count">${arrived} arrived</span>
        <span class="dv-consensus-badge">${badge}</span>
      </header>
      <p class="dv-consensus-lede">Read-only. Independent checks A|B (Prajna, Agriya — maintainers). SAT sample only. Discussion: <a href="${LETI_DISCORD}" target="_blank" rel="noopener noreferrer">LETI on Discord</a>.</p>
      <ul class="dv-comment-list">${items}</ul>
    </section>`;
}

function decorateFieldRow(el, cell) {
  if (el.closest('.cv-consensus-field')) return;
  const wrap = document.createElement('details');
  wrap.className = `cv-consensus-field ${rowClass(cell)}`;
  wrap.setAttribute('data-cv-field', el.getAttribute('data-cv-field') || '');
  const summary = document.createElement('summary');
  summary.className = 'cv-consensus-summary';
  const chips = document.createElement('span');
  chips.className = 'cv-letters';
  chips.innerHTML = letterChips(contributionsForCell(cell));
  el.parentNode.insertBefore(wrap, el);
  summary.appendChild(el);
  summary.appendChild(chips);
  wrap.appendChild(summary);
  wrap.insertAdjacentHTML('beforeend', stripHTML(cell));
}

function annotateCaseVolume(container, cells) {
  const byField = Object.fromEntries(cells.map((c) => [c.field, c]));
  container.querySelectorAll('.cv-rows > [data-cv-field]').forEach((el) => {
    if (el.closest('.cv-consensus-field')) return;
    const field = el.getAttribute('data-cv-field');
    const cell = byField[field];
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
    const host = container.querySelector('.dv-tab-activity .dv-comments')
      || container.querySelector('.dv-comments');
    if (!host) return;
    if (host.previousElementSibling?.classList.contains('dv-consensus-notes')) {
      host.previousElementSibling.remove();
    }
    host.insertAdjacentHTML('beforebegin', tocHTML(cells, dash));
  });
}
