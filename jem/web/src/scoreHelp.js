// Score methodology help — shared between About page and profile tooltips.

const IR_TABLE = `
<table class="score-tip-table">
  <tr><td>Appointed by executive body</td><td>+3</td></tr>
  <tr><td>Reappointment by same executive</td><td>+2</td></tr>
  <tr><td>Funder = appointing authority</td><td>+2</td></tr>
  <tr><td>No external complaint mechanism</td><td>+2</td></tr>
  <tr><td>No public appointment criteria</td><td>+1</td></tr>
  <tr><td>Removal by appointer, no committee</td><td>+1</td></tr>
  <tr><td>Constitutional basis</td><td>−2</td></tr>
  <tr><td>Collegium-appointed</td><td>−2</td></tr>
  <tr><td>Removal via Parliamentary address</td><td>−1</td></tr>
</table>`;

export const SCORE_HELP = {
  structural_health: {
    title: 'Structural health',
    html: `<p>Headline composite (0.0–1.0) shown as the ring colour around entity nodes. Higher is healthier.</p>
<p><strong>Bands:</strong> Critical (&lt;0.3) · At Risk (0.3–0.6) · Watch (0.6–0.8) · Healthy (≥0.8)</p>
<p>Formula: <code>health = 1 − (0.6 · normalised IR + 0.4 · normalised DP)</code></p>
<p>Independence Risk is weighted 0.6 vs Discretionary Power 0.4 — an editorial choice pending community review, not a published methodological study.</p>`,
  },
  independence_risk: {
    title: 'Independence risk',
    html: `<p>Structural vulnerability to executive influence (0–15+). Not a finding on individual conduct.</p>
<p><strong>Levels:</strong> Low (0–2) · Moderate (3–5) · High (6–8) · Severe (9+)</p>
${IR_TABLE}
<p><em>SC/HC judges:</em> Constitutional basis (−2) and Parliamentary-address removal (−1) both apply.</p>`,
  },
  discretionary_power: {
    title: 'Discretionary power',
    html: `<p>Opacity of criteria, removal authority over others, and absence of mandatory timelines (0–10+).</p>
<p>Derived from structural fields in entity YAML — criteria publication, reappointment risk, removal difficulty, and scope of authority.</p>`,
  },
  clog_severity: {
    title: 'Clog severity',
    html: `<p>From disposal rate (disposed ÷ filed) and average disposal days in the NJDG snapshot.</p>
<ul>
  <li><strong>Critical:</strong> rate &lt;0.85 and days &gt;730</li>
  <li><strong>High:</strong> rate &lt;0.95 or days &gt;365</li>
  <li><strong>Moderate:</strong> rate &lt;1.0</li>
  <li><strong>Low:</strong> rate ≥1.0 and days ≤365</li>
</ul>`,
  },
};

/** Inline ? control with expandable methodology popover. */
export function scoreTip(topic) {
  const entry = SCORE_HELP[topic];
  if (!entry) return '';
  return `<details class="score-tip">
    <summary class="score-tip-btn" aria-label="About ${entry.title}">?</summary>
    <div class="score-tip-pop" role="note">
      <strong class="score-tip-pop-title">${entry.title}</strong>
      ${entry.html}
    </div>
  </details>`;
}
