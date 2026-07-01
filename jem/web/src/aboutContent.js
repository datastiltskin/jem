// About page body — single source for the full About view.

import { JEM_HOME_INTRO, JEM_HOME_STATUS } from './siteCopy.js';
import { State } from './state.js';
import { logoWordmarkHTML } from './brand.js';

const GITHUB = 'https://github.com/datastiltskin/jem';
const ISSUES = `${GITHUB}/issues`;
const DEMO = 'https://friedso.com/apps/jem/';

const MAINTAINERS = [
  {
    name: 'Divya Sornaraja',
    linkedin: 'https://www.linkedin.com/in/divya-sornaraja-12a14a14',
    github: 'https://github.com/dso6060',
    handle: '@dso6060',
    role: 'lead maintainer (data, pipeline, deploy)',
  },
  {
    name: 'Prajna Prayas',
    linkedin: 'https://www.linkedin.com/in/prajna-prayas',
    github: 'https://github.com/Prajna1999',
    handle: '@Prajna1999',
    role: 'co-maintainer (UI, GitHub admin)',
  },
  {
    name: 'Agriya Khetarpal',
    linkedin: 'https://www.linkedin.com/in/agriyakhetarpal',
    github: 'https://github.com/agriyakhetarpal',
    handle: '@agriyakhetarpal',
    role: 'co-maintainer (public repo, GitHub admin)',
  },
];

function maintainerLine({ name, linkedin, github, handle, role }) {
  return `<li><a href="${linkedin}" target="_blank" rel="noopener noreferrer">${name}</a>(<a href="${github}" target="_blank" rel="noopener noreferrer">${handle}</a>) — ${role}</li>`;
}

function resolveMaintainerToolsContext() {
  const { hostname, origin } = window.location;
  const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';

  if (isLocal) {
    let serverOrigin = 'http://127.0.0.1:8001';
    const base = window.JEM_API_BASE;
    if (typeof base === 'string' && base) {
      try {
        const u = new URL(base);
        serverOrigin = `${u.protocol}//${u.host}`;
      } catch { /* keep default */ }
    }
    return { origin: serverOrigin, apiPrefix: '/api/v1' };
  }

  if (hostname === 'friedso.com' || hostname === 'www.friedso.com' || hostname === 'staging.friedso.com') {
    return { origin, apiPrefix: '/api/jem/v1' };
  }

  return null;
}

function apiLinks(ctx) {
  const row = (label, path, note = '') => {
    if (!ctx?.origin) {
      return `<li><strong>${label}</strong> — <code>${path}</code>${note ? ` <span class="about-muted">${note}</span>` : ''}</li>`;
    }
    const href = `${ctx.origin}${path}`;
    return `<li><a href="${href}" target="_blank" rel="noopener noreferrer">${label}</a>${note ? ` <span class="about-muted">${note}</span>` : ''}</li>`;
  };
  const apiPrefix = ctx?.apiPrefix || '/api/v1';
  return `
    <ul class="about-link-list">
      ${row('API health check', `${apiPrefix}/health`)}
      ${row('OpenAPI docs (Swagger)', '/docs', 'try entity search here')}
      ${row('Expert staging portal', '/portal/', 'maintainer review queue')}
      ${row('Admin — corrections queue', '/admin/', 'maintainer role required')}
      ${row('MCP tools', '/mcp/', 'HTTP tools for agents')}
    </ul>`;
}

function entityApiExamples(ctx) {
  const apiPrefix = ctx?.apiPrefix || '/api/v1';
  const searchPath = `${apiPrefix}/entities?q=NCLT`;
  const clusterPath = `${apiPrefix}/clusters/summary`;
  if (!ctx?.origin) {
    return `<p class="about-muted"><strong>Entity ids:</strong> search first — <code>GET ${searchPath}</code> returns an <code>id</code> slug (e.g. <code>nclt</code>). Use that for detail and relationships. Cluster overview: <code>GET ${clusterPath}</code>.</p>`;
  }
  const searchHref = `${ctx.origin}${searchPath}`;
  const clusterHref = `${ctx.origin}${clusterPath}`;
  return `<p class="about-muted"><strong>Entity ids:</strong> search first — <a href="${searchHref}" target="_blank" rel="noopener noreferrer"><code>GET ${searchPath}</code></a> returns an <code>id</code> slug (e.g. <code>nclt</code>). Use that for detail and relationships. Cluster overview: <a href="${clusterHref}" target="_blank" rel="noopener noreferrer"><code>GET ${clusterPath}</code></a>.</p>`;
}

/** @param {{ meta?: object, entities?: object[], maintainerTools?: { origin: string, apiPrefix: string } | null }} ctx */
export function aboutPageHTML(ctx = {}) {
  const meta = ctx.meta || {};
  const entities = ctx.entities || [];
  const entityCount = meta.entity_count ?? entities.length ?? '—';

  return `
    <header class="about-hero">
      ${logoWordmarkHTML({ className: 'about-logo-wordmark', width: 460 })}
      <h1 class="visually-hidden">Judiciary Entity Map (India) — JEM</h1>
      <p class="about-lead">${JEM_HOME_INTRO}</p>
      <p class="about-lead about-lead-status">${JEM_HOME_STATUS}</p>
    </header>

    <section class="about-section">
      <h2>What JEM is</h2>
      <p>JEM is an open structural map for legal researchers, journalists, litigants, ministry officials, and engineers. It is <strong>not a case-outcome tracker</strong>. The focus is how courts, tribunals, regulators, and quasi-judicial bodies are <em>constituted</em>, <em>appointed</em>, <em>funded</em>, <em>supervised</em>, and <em>held accountable</em> — and how that design changes over time.</p>
      <p>Information about India's judicial ecosystem is scattered across constitutional text, central and state Acts, Department of Justice and tribunal annual reports, NJDG case statistics, CAG audit chains, and gazette notifications. JEM consolidates structural facts into one navigable dashboard so you can see, for each institution:</p>
      <ul>
        <li>Appointment chains and whether the appointer is also a litigant or funder</li>
        <li>Funding flows and budget control</li>
        <li>Independence-risk and discretionary-power indicators (algorithmic, not conduct findings)</li>
        <li>Appellate paths, supervisory links, and documented structural gaps</li>
        <li>Operational status — active, abolished, merged, suspended, or <strong>legislated but not constituted (NC)</strong></li>
        <li>Case-volume and clog signals where NJDG or annual-report data is merged</li>
      </ul>
      <p>The long-term target is roughly <strong>1,500</strong> distinct judicial and quasi-judicial institutions. Coverage is strongest for constitutional courts, central tribunals, and regulators; state subordinate-court lattices vary by state (Tamil Nadu is deepest; others use core packs plus high-volume districts).</p>
    </section>

    <section class="about-section">
      <h2>How data is collected and maintained</h2>
      <p>JEM is maintained as <strong>version-controlled YAML</strong>, not hand-edited JSON. The pipeline:</p>
      <ol class="about-pipeline">
        <li><strong>Entity files</strong> — one YAML per institution under <code>jem/data/entities/</code>, validated against a Pydantic schema</li>
        <li><strong>Relationships</strong> — typed edge files (appointment, funding, appellate, …) under <code>jem/data/relationships/</code></li>
        <li><strong>Derive</strong> — <code>scripts/derive.py</code> computes independence risk, discretionary power, and structural health from structural fields</li>
        <li><strong>Build</strong> — <code>scripts/build.py</code> merges entities, scores, and relationships into <code>graph.json</code> for the web map</li>
        <li><strong>Database</strong> — <code>scripts/build_db.py</code> loads <code>graph.json</code> into SQLite (<code>data/jem.db</code>) for the REST API, MCP tools, and search</li>
      </ol>
      <p>Every field that affects a score requires a <strong>primary source</strong> (Constitution, statute, judgment, GoI report). Auto-fetched records stay in staging until a maintainer approves them via the expert portal. Community corrections go through signed-in proposals and maintainer review — nothing moves to published status without an audit log entry.</p>
      <p>Maintainer documentation: <a href="${GITHUB}/blob/main/jem/docs/KNOWLEDGE_TRANSFER.md" target="_blank" rel="noopener noreferrer">Knowledge transfer guide</a> · <a href="${GITHUB}/blob/main/jem/docs/ENTITY_BUILD_ROADMAP.md" target="_blank" rel="noopener noreferrer">Entity build roadmap</a> · <a href="${GITHUB}/blob/main/jem/docs/MCP_SETUP.md" target="_blank" rel="noopener noreferrer">API &amp; MCP setup</a></p>
    </section>

    <section class="about-section">
      <h2>Navigate this site</h2>
      <div class="about-nav-grid">
        <div class="about-nav-card">
          <h3>Map UI</h3>
          <ul>
            <li><a href="#/">Overview dashboard</a> — stats, spotlight, hierarchy</li>
            <li><a href="#/about">About</a> — this page</li>
            <li>Toolbar <strong>search</strong> — entity lookup and curated structural insights</li>
            <li>Entity <strong>profile</strong> — scores, neighborhood graph, sources, corrections</li>
            <li><a href="#/map">Interactive map</a> — full graph workspace (Structure / Risk / Gaps modes)</li>
          </ul>
        </div>
        <div class="about-nav-card">
          <h3>Hosted &amp; source</h3>
          <ul>
            <li><a href="${DEMO}" target="_blank" rel="noopener noreferrer">friedso.com/apps/jem/</a> — public demo (attribution appreciated)</li>
            <li><a href="${GITHUB}" target="_blank" rel="noopener noreferrer">GitHub repository</a> — data (CC0) + code (MIT)</li>
            <li><a href="${GITHUB}/blob/main/README.md" target="_blank" rel="noopener noreferrer">README</a> — coverage tables and release notes</li>
          </ul>
        </div>
        <div class="about-nav-card">
          <h3>API &amp; maintainer tools</h3>
          <p class="about-muted">Requires the FastAPI server (<code>uvicorn api.main:app</code>) locally, or the maintainer-deployed API on <a href="${DEMO}" target="_blank" rel="noopener noreferrer">friedso.com</a> (links below when deployed).</p>
          <p class="about-muted">Setup: <a href="${GITHUB}/blob/main/jem/docs/MCP_SETUP.md" target="_blank" rel="noopener noreferrer">API &amp; MCP setup guide</a></p>
          ${entityApiExamples(ctx.maintainerTools)}
          ${apiLinks(ctx.maintainerTools)}
        </div>
        <div class="about-nav-card">
          <h3>Feedback &amp; community</h3>
          <ul>
            <li><a href="${ISSUES}/new?template=data_correction.yml" target="_blank" rel="noopener noreferrer">Data correction</a> — cite a primary source</li>
            <li><a href="${ISSUES}/new?template=source_request.yml" target="_blank" rel="noopener noreferrer">Source request</a> — missing official link</li>
            <li><a href="${ISSUES}/new?template=bug_report.yml" target="_blank" rel="noopener noreferrer">Bug report</a> — UI or pipeline defect</li>
            <li><a href="${ISSUES}/new?template=contested_fact.yml" target="_blank" rel="noopener noreferrer">Contested fact</a> — two cited positions</li>
            <li><a href="${ISSUES}/new?template=expert_review.yml" target="_blank" rel="noopener noreferrer">Expert review</a> — domain reviewer workflow</li>
            <li><a href="${ISSUES}/new" target="_blank" rel="noopener noreferrer">Feature request / general issue</a></li>
            <li>In-app <strong>Propose correction</strong> on any entity profile (sign-in required when API auth is configured)</li>
          </ul>
        </div>
      </div>
    </section>

    <section class="about-section">
      <h2>What's in the map</h2>
      <ul class="about-layer-list">
        <li><strong>Appellate chain</strong> — who reviews whom</li>
        <li><strong>Appointment</strong> — nomination, recommendation, formal appointment</li>
        <li><strong>Funding</strong> — budget ministry or department</li>
        <li><strong>Supervisory</strong> — HC control over subordinate courts (Art. 235)</li>
        <li><strong>Audit &amp; complaints</strong> — CAG / PAC chains and bias-complaint pathways</li>
        <li><strong>Digital infrastructure</strong> — e-Committee, NIC, eCourts governance</li>
        <li><strong>Case volume</strong> — pending cases, disposal rate, clog severity (where sourced)</li>
        <li><strong>Structural gaps &amp; circularity</strong> — documented shortfalls and conflicting roles</li>
      </ul>
    </section>

    <section class="about-section">
      <h2>MCP for researchers &amp; AI agents</h2>
      <p>JEM exposes four <strong>MCP HTTP tools</strong> on the same server as the REST API: <code>search_entities</code>, <code>get_entity</code>, <code>get_relationships</code>, and <code>get_structural_gaps</code>. They read the same SQLite database as the map and return structured JSON with <code>data_quality</code> flags and source URLs.</p>
      <p><strong>When is MCP useful?</strong> If you use Cursor, Claude, or another agent to research Indian judicial structure, MCP (or REST) lets the agent query live data instead of uploading a stale <code>graph.json</code> snapshot. It is <em>not</em> needed for browsing the map — use toolbar search for that. Tools refuse legal advice, case outcomes, and judge-name requests.</p>
      <p><strong>How to use it:</strong> run <code>uvicorn api.main:app</code> locally (see <a href="${GITHUB}/blob/main/jem/docs/MCP_SETUP.md" target="_blank" rel="noopener noreferrer">MCP setup guide</a>), then point your agent at <code>/mcp/tools</code> or REST <code>/api/v1/</code>. Always <strong>search first</strong> (<code>search_entities</code> or <code>GET /entities?q=…</code>) to discover entity ids before calling <code>get_entity</code>. Native stdio MCP for Cursor <code>mcp.json</code> is discussed in <a href="${GITHUB}/blob/main/jem/docs/MCP_STDIO.md" target="_blank" rel="noopener noreferrer">MCP_STDIO.md</a> — not yet shipped; HTTP works today.</p>
    </section>

    <section class="about-section">
      <h2>Project status &amp; what's pending</h2>
      <ul>
        <li><strong>Coverage gap</strong> — ${entityCount} of ~1,500 entities mapped; state district lattices and some quasi-judicial bodies remain incomplete per the <a href="${GITHUB}/blob/main/jem/docs/ENTITY_BUILD_ROADMAP.md" target="_blank" rel="noopener noreferrer">roadmap</a></li>
        <li><strong>Score validation</strong> — independence risk and discretionary power weights are algorithmic; marked ⚐ pending community review until expert sign-off</li>
        <li><strong>NJDG merge</strong> — district-level case volume is partial; many entities await annual-report or NJDG snapshots</li>
        <li><strong>QA sprint</strong> — full operational audit of all 1,500 targets is ongoing</li>
        <li><strong>Auth</strong> — LinkedIn sign-in for corrections in production; dev mock login locally (see <a href="${GITHUB}/blob/main/jem/docs/AUTH_SETUP.md" target="_blank" rel="noopener noreferrer">AUTH_SETUP</a>)</li>
      </ul>
      <p>Maintainers of the <a href="${GITHUB}" target="_blank" rel="noopener noreferrer">public repository</a>:</p>
      <ul class="about-maintainers">
        ${MAINTAINERS.map(maintainerLine).join('\n        ')}
      </ul>
      <p>Contributors welcome — researchers for sourcing and validation, engineers for schema and tooling. Full team listing: <a href="${GITHUB}/blob/main/jem/docs/TEAM.md" target="_blank" rel="noopener noreferrer">TEAM.md</a>.</p>
    </section>

    <section class="about-section">
      <h2>Scores</h2>
      <p>Structural indicators only — not findings of bias, misconduct, or case outcomes. Use the <strong>?</strong> tooltips on entity profiles for quick definitions.</p>

      <h3>Structural Health (0.0–1.0) — master composite</h3>
      <p>Headline indicator shown as the ring colour around each entity node.
      Composite of two constituents below, on a 1.0 = healthy ↔ 0.0 = critical scale.</p>
      <p>Bands: <strong style="color:#e74c3c">Critical</strong> (&lt;0.3) ·
      <strong style="color:#f39c12">At Risk</strong> (0.3–0.6) ·
      <strong style="color:#f1c40f">Watch</strong> (0.6–0.8) ·
      <strong style="color:#27ae60">Healthy</strong> (≥0.8)</p>
      <p>Formula: <code>health = 1 − (0.6 · normalised IR + 0.4 · normalised DP)</code>.
      Constituents (IR, DP) use their own palettes inside the entity detail panel.</p>
      <p><em>Weight rationale:</em> Independence Risk (0.6) is weighted higher than Discretionary Power (0.4) because executive capture of appointment and funding chains is treated as the primary structural threat to institutional independence. These weights are an <strong>editorial choice pending community review</strong> — not derived from a published methodological study. See <code>jem/scripts/derive.py</code> and <code>docs/DATA_MODEL.md</code>.</p>

      <h3>Independence Risk (0–15+) — constituent</h3>
      <p>Structural vulnerability to executive influence.</p>
      <table class="about-table">
        <tr><td>Appointed by executive body</td><td>+3</td></tr>
        <tr><td>Reappointment by same executive</td><td>+2</td></tr>
        <tr><td>Funder = Appointing authority</td><td>+2</td></tr>
        <tr><td>No external complaint mechanism</td><td>+2</td></tr>
        <tr><td>No public appointment criteria</td><td>+1</td></tr>
        <tr><td>Removal by appointer, no committee</td><td>+1</td></tr>
        <tr><td>Constitutional basis</td><td>−2</td></tr>
        <tr><td>Collegium-appointed</td><td>−2</td></tr>
        <tr><td>Removal via Parliamentary address (President issues order under Arts 124(4), 218)</td><td>−1</td></tr>
      </table>
      <p><em>Note:</em> For SC and HC judges, Constitutional basis (−2) and Parliamentary-address removal (−1) <strong>both apply and are additive</strong>.</p>
      <p>Levels: Low (0–2) · Moderate (3–5) · High (6–8) · Severe (9+)</p>

      <h3>Discretionary Power (0–10+) — constituent</h3>
      <p>Opacity of criteria, removal authority over others, absence of mandatory timelines.</p>

      <h3>Clog Severity</h3>
      <p>From disposal rate (disposed ÷ filed) and avg disposal days.</p>
      <ul>
        <li>Critical: rate &lt;0.85 <strong>AND</strong> days &gt;730</li>
        <li>High: rate &lt;0.95 <strong>OR</strong> days &gt;365</li>
        <li>Moderate: rate &lt;1.0</li>
        <li>Low: rate ≥1.0 AND days ≤365</li>
      </ul>
    </section>

    <section class="about-section">
      <h2>Markers</h2>
      <ul>
        <li><strong>*</strong> — documented structural gap</li>
        <li><strong>⟳</strong> — structural circularity (appointer is also litigant, etc.)</li>
        <li><strong>⊘</strong> — appellate path blocked in practice</li>
        <li><strong>NC</strong> — legislated but not yet constituted</li>
        <li><strong>EX</strong> — structural exception (deviates from statutory template)</li>
        <li><strong>UT</strong> — Union Territory jurisdiction</li>
        <li>Double ring — shared jurisdiction across multiple states</li>
      </ul>
    </section>

    <section class="about-section about-disclaimer">
      <h2>Licence &amp; disclaimer</h2>
      <p><strong>Data:</strong> CC0 (public domain) · <strong>Code:</strong> MIT</p>
      <p>JEM presents structural information about institutions and their formal relationships, derived from public sources. It does not provide legal advice, predict case outcomes, or assess individual conduct. Data may be incomplete or outdated — verify critical facts against primary sources before relying on them in litigation, policy, or journalism.</p>
      <p class="about-footer-links">
        <a href="${DEMO}" target="_blank" rel="noopener noreferrer">Live map</a> ·
        <a href="${GITHUB}" target="_blank" rel="noopener noreferrer">GitHub</a> ·
        <a href="${ISSUES}" target="_blank" rel="noopener noreferrer">Issues</a> ·
        <a href="${GITHUB}/blob/main/jem/docs/CONTRIBUTING.md" target="_blank" rel="noopener noreferrer">Contributing</a>
      </p>
    </section>
  `;
}

export function renderAboutPage() {
  const el = document.getElementById('about-view');
  if (!el) return;
  const graph = State.graph;
  const meta = graph?.meta || {};
  const entities = graph?.entities || [];
  el.innerHTML = `<div class="about-inner">${aboutPageHTML({
    meta,
    entities,
    maintainerTools: resolveMaintainerToolsContext(),
  })}</div>`;
}
