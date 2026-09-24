// Prompt registry — first-class JEM route (#/prompts).

import { LETI_DISCORD } from './consensusNotes.js';

export function renderPromptsView() {
  const el = document.getElementById('prompts-view');
  if (!el) return;
  el.innerHTML = `
    <div class="about-inner eng-inner">
      <p class="eng-kicker">
        <a href="#/about">← About JEM</a>
        · <a href="#/engineering">Engineering</a>
        · <a href="${LETI_DISCORD}" target="_blank" rel="noopener noreferrer">LETI Discord</a>
      </p>
      <h1>Prompt registry</h1>
      <p class="about-lead">A prompt is versioned config: generate structure or verify a stored field. Public prompt packs will be listed here as they are handed out. Discussion is on Discord, not on this page.</p>
      <iframe class="eng-swim" title="JEM prompt registry"
        src="./public/orchestration/prompts.html"></iframe>
    </div>
  `;
}
