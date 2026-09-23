// Engineering — crowdsourcing explainer, then the 1 Sep swimlane as a worked example.

import { LETI_DISCORD, loadConsensusDashboard } from './consensusNotes.js';

function esc(s) {
  return String(s ?? '—').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

const EXPLAINER = `
  <p class="eng-kicker">
    <a href="#/about">← About JEM</a>
    · <a href="#/prompts">Prompt registry</a>
    · <a href="#/consensus">Cell index</a>
    · <a href="${LETI_DISCORD}" target="_blank" rel="noopener noreferrer">LETI Discord</a>
  </p>
  <h1>Engineering</h1>
  <p class="about-lead">JEM is built in the open: people run written prompts, return structured files, independent checks are joined, and only then does a figure move into the map. This page is the outline of that project — not a place to submit data. Discussion lives on <a href="${LETI_DISCORD}" target="_blank" rel="noopener noreferrer">LETI (Discord)</a> and GitHub.</p>

  <section class="about-section">
    <h2>What the crowdsourcing project does</h2>
    <p>The map is YAML in git, not a live scrape. A <strong>prompt</strong> is a versioned instruction (generate a court, or verify a stored number). Someone — a maintainer, a researcher, or anyone given the prompt — returns a file. Those files are joined. Agreement can update canon; disagreement stays visible; experts can overwrite later.</p>
    <ol class="about-pipeline">
      <li><strong>Prompt</strong> — registered text. Generation (new structure) and verification (check a stored field) are different tracks.</li>
      <li><strong>Upload</strong> — email, Discord-to-PR, or a form-and-drive path. Several files may exist for one field.</li>
      <li><strong>Join</strong> — letters A|B|C are the current checks. Same person, newer file, replaces their letter; older files stay in the timestamped list.</li>
      <li><strong>Gate</strong> — auto-apply only when the join is unambiguous. Splits and gaps stay on the entity page.</li>
      <li><strong>Experts</strong> — one public queue; each reply records who the expert was. Canon can move when they answer.</li>
    </ol>
  </section>

  <section class="about-section">
    <h2>How to read a data-point</h2>
    <p>Trust is decided on the <strong>entity page</strong>, on that field. Expand the row: A|B|C, verdicts, values, join result, and the files that led there. SAT is the sample. A researcher index of every cell is <a href="#/consensus">#/consensus</a>.</p>
    <ul>
      <li><strong>Example — SAT pending cases.</strong> Stored 420 looked unsourced. Two independent verifications re-read SEBI’s FY25-26 table and both got 1,066. That figure is what the map shows; the old 420 stays in history.</li>
      <li><strong>Example — NJDG stamp.</strong> Both checks said the National Judicial Data Grid does not cover that body. The Grid listing was stripped. The disagreement (if any) remains on the row.</li>
    </ul>
  </section>

  <section class="about-section">
    <h2>A worked example — 1 September 2026 run</h2>
    <p class="about-muted">Intra-run packet: schema, Tamil Nadu generation tracks, classification counts, report-publication. Swimlane below is that run, not the live map.</p>
  </section>
`;

export function renderEngineeringView() {
  const el = document.getElementById('engineering-view');
  if (!el) return;
  el.innerHTML = `
    <div class="about-inner eng-inner">
      ${EXPLAINER}
      <iframe class="eng-swim" title="1 September 2026 orchestration swimlane"
        src="./public/orchestration/index.html"></iframe>
    </div>
  `;
}

function drawConsensus(el, d) {
  const f = d.funnel || {};
  const b = f.buckets || {};
  const tiles = [
    ['Total', f.total],
    ['Gaps', b.gap],
    ['NJDG strip', b.strip],
    ['Period', b.period],
    ['Verdict split', b.verdict_split],
    ['Value split', b.value_split],
    ['Auto-applied', f.auto_applied_to_canon],
    ['Expert-pending', f.expert_pending],
    ['Contamination dropped', f.dropped_as_contamination],
  ];
  const cells = (d.cells || []).map((c) => {
    const cls = {
      'reached canon': 'ok',
      'contamination-dropped': 'deny',
      'pending-expert': 'warn',
      gap: '',
    }[c.canon_result] || '';
    return `<details class="eng-cell">
      <summary><span class="mono">${esc(c.entity_id)}.${esc(c.field)}</span>
        — A ${esc(c.prajna && c.prajna.verdict)} | B ${esc(c.agriya && c.agriya.verdict)}
        → <span class="${cls}">${esc(c.canon_result)}</span></summary>
      <p>Reconcile: ${esc(c.reconcile_outcome)}. Open
        <a href="#/entity/${encodeURIComponent(c.entity_id)}">${esc(c.entity_id)}</a>
        and expand the field.</p>
    </details>`;
  }).join('');

  el.innerHTML = `
    <div class="about-inner eng-inner">
      <p class="eng-kicker">
        <a href="#/engineering">← Engineering</a>
        · <a href="#/prompts">Prompt registry</a>
      </p>
      <p class="badge">${esc(d.round_badge || 'PIPELINE EXERCISE')}</p>
      <h1>Cell index</h1>
      <p class="about-lead">Researcher scan of every (entity, field). The trust UI is the expandable row on the entity page.</p>
      <div class="eng-funnel">
        ${tiles.map(([k, v]) => `<div class="eng-tile"><strong>${esc(v)}</strong><span>${esc(k)}</span></div>`).join('')}
      </div>
      <div class="eng-cells">${cells}</div>
    </div>
  `;
}

export function renderConsensusView() {
  const el = document.getElementById('engineering-view');
  if (!el) return;
  el.innerHTML = `<div class="about-inner"><p class="about-lead">Loading cell index…</p></div>`;
  loadConsensusDashboard().then((d) => {
    if (!d) {
      el.innerHTML = `<div class="about-inner"><p>Could not load consensus JSON.</p>
        <p><a href="#/engineering">Engineering</a></p></div>`;
      return;
    }
    drawConsensus(el, d);
  });
}
