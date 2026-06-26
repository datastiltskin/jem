// JEM — Group report tab + print
import { State } from './state.js';
import { selectAndOpenEntity } from './entitySelection.js';
import { printBrandBlock } from './brand.js';

let bodyEl;

export function initGroupReport() {
  bodyEl = document.getElementById('group-report-body');
  document.querySelectorAll('[data-inspector-tab]').forEach(btn => {
    btn.addEventListener('click', () => setInspectorTab(btn.dataset.inspectorTab));
  });
  document.getElementById('btn-print-detail')?.addEventListener('click', () => {
    printWithBodyClass('print-detail-only');
  });
  document.getElementById('btn-print-group')?.addEventListener('click', () => {
    printWithBodyClass('print-group-only');
  });

  State.subscribe('treeSelectionChanged', renderGroupReport);
  State.subscribe('graphLoaded', renderGroupReport);
}

function setInspectorTab(tab) {
  document.querySelectorAll('[data-inspector-tab]').forEach(b => {
    b.classList.toggle('active', b.dataset.inspectorTab === tab);
  });
  document.getElementById('inspector-tab-detail')?.classList.toggle('hidden', tab !== 'detail');
  document.getElementById('inspector-tab-report')?.classList.toggle('hidden', tab !== 'report');
  if (tab === 'report') renderGroupReport();
}

export function renderGroupReport() {
  if (!bodyEl) return;
  const entities = State.getTreeSelectedEntities();
  if (!entities.length) {
    bodyEl.innerHTML = `<p class="detail-empty-hint">Select entities in the left tree (checkboxes) or use a preset chip to generate a group summary. Click any row to open the full entity profile.</p>`;
    return;
  }

  let gapCount = 0;
  let highIr = 0;
  let notConst = 0;
  let clogHigh = 0;
  const irBuckets = { low: 0, moderate: 0, high: 0, severe: 0 };

  for (const e of entities) {
    if (e.gap_flag || (e.gaps?.length > 0)) gapCount++;
    const lvl = (e.derived || {}).independence_risk_level || 'low';
    if (irBuckets[lvl] !== undefined) irBuckets[lvl]++;
    if (lvl === 'high' || lvl === 'severe') highIr++;
    if (e.operational_status === 'Not_Constituted') notConst++;
    const clog = e._detail?.case_volume?.clog_severity;
    if (clog === 'Critical' || clog === 'High') clogHigh++;
  }

  let html = `
    ${printBrandBlock()}
    <div class="group-report-summary">
      <div class="gr-stat"><span class="gr-num">${entities.length}</span><span class="gr-lbl">Entities</span></div>
      <div class="gr-stat"><span class="gr-num">${gapCount}</span><span class="gr-lbl">With gaps</span></div>
      <div class="gr-stat"><span class="gr-num">${highIr}</span><span class="gr-lbl">High IR</span></div>
      <div class="gr-stat"><span class="gr-num">${notConst}</span><span class="gr-lbl">Not constituted</span></div>
      <div class="gr-stat"><span class="gr-num">${clogHigh}</span><span class="gr-lbl">Clog high/critical</span></div>
    </div>
    <p class="detail-empty-hint">IR distribution: low ${irBuckets.low} · moderate ${irBuckets.moderate} · high ${irBuckets.high} · severe ${irBuckets.severe}</p>
    <div class="group-report-table-wrap">
    <table class="group-report-table">
      <thead><tr>
        <th>Name</th><th>Type</th><th>Cluster</th><th>IR</th><th>Gaps</th><th>Status</th>
      </tr></thead>
      <tbody>
  `;

  const sorted = [...entities].sort((a, b) => (a.name || '').localeCompare(b.name || ''));
  for (const e of sorted) {
    const ir = (e.derived || {}).independence_risk_level || '—';
    const gaps = e.gap_flag || (e.gaps?.length > 0) ? 'Yes' : '—';
    html += `<tr data-entity-id="${e.id}" class="group-report-row">
      <td>${e.name}</td>
      <td>${formatType(e.type)}</td>
      <td>${(e.cluster || '').replace(/_/g, ' ')}</td>
      <td>${ir}</td>
      <td>${gaps}</td>
      <td>${e.operational_status || '—'}</td>
    </tr>`;
  }
  html += '</tbody></table></div>';

  bodyEl.innerHTML = html;
  bodyEl.querySelectorAll('.group-report-row').forEach(row => {
    row.addEventListener('click', () => {
      const id = row.dataset.entityId;
      setInspectorTab('detail');
      selectAndOpenEntity(id);
    });
  });
}

function formatType(type) {
  return (type || '').replace(/([A-Z])/g, ' $1').trim();
}

/** Keep print-only body class until the browser finishes layout for print. */
function printWithBodyClass(className) {
  let cleaned = false;
  const cleanup = () => {
    if (cleaned) return;
    cleaned = true;
    document.body.classList.remove(className);
    window.removeEventListener('afterprint', cleanup);
    window.removeEventListener('beforeprint', ensureClass);
  };
  const ensureClass = () => {
    if (!document.body.classList.contains(className)) {
      document.body.classList.add(className);
    }
  };
  document.body.classList.add(className);
  window.addEventListener('beforeprint', ensureClass);
  window.addEventListener('afterprint', cleanup);
  setTimeout(cleanup, 120_000);
  window.print();
}
