// Correction proposals + upvotes. Uses API when JEM_API_BASE is set or auto-detected.

import {
  apiFetch,
  linkedinButtonHtml,
  linkedinLoginHref,
  loadAuthState,
} from './auth.js';

const STORES = new Map(); // scope -> in-memory fallback

export function commentsHTML(scope = 'global', { title = 'Corrections' } = {}) {
  return `
    <section class="dv-comments" data-comments-scope="${scope}" aria-label="Community corrections">
      <header class="dv-comments-head">
        <h2 class="dv-comments-title">${title}</h2>
        <span class="dv-comments-count" data-comments-count>0</span>
        <span class="dv-comments-stub" data-comments-stub hidden></span>
        <span class="dv-comments-auth" data-comments-auth></span>
      </header>

      <form class="dv-comment-form" data-comments-form onsubmit="return false">
        <textarea class="dv-comment-input" data-comments-input rows="3"
          placeholder="Describe the correction or missing data…" maxlength="2000" required></textarea>
        <input class="dv-comment-source" data-comments-source type="url"
          placeholder="Primary source URL (required)" maxlength="2048" required>
        <div class="dv-comment-form-row">
          <button class="dv-comment-submit" data-comments-submit type="submit">Propose correction</button>
        </div>
        <p class="dv-comment-hint" data-comments-hint></p>
      </form>

      <ul class="dv-comment-list" data-comments-list></ul>
      <p class="dv-comment-empty" data-comments-empty>No corrections yet.</p>
    </section>
  `;
}

export function wireComments(root) {
  if (!root) return;
  root.querySelectorAll('[data-comments-scope]').forEach(section => {
    wireSection(section);
  });
}

function wireSection(section) {
  const scope = section.getAttribute('data-comments-scope');
  if (!STORES.has(scope)) STORES.set(scope, []);

  const form   = section.querySelector('[data-comments-form]');
  const input  = section.querySelector('[data-comments-input]');
  const source = section.querySelector('[data-comments-source]');
  const list   = section.querySelector('[data-comments-list]');
  const empty  = section.querySelector('[data-comments-empty]');
  const count  = section.querySelector('[data-comments-count]');
  const stub   = section.querySelector('[data-comments-stub]');
  const authEl = section.querySelector('[data-comments-auth]');
  const hint   = section.querySelector('[data-comments-hint]');

  let apiBase = null;
  let me = null;
  let authProviders = null;
  let items = [];

  const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const initials = n => (n || 'A').trim().split(/\s+/).slice(0,2).map(p => p[0]).join('').toUpperCase() || 'A';
  const fmtTime = ts => {
    const d = typeof ts === 'number' ? ts : Date.parse(ts.replace(' ', 'T') + 'Z');
    const s = Math.round((Date.now() - d) / 1000);
    if (Number.isNaN(s) || s < 0) return '';
    if (s < 60) return 'just now';
    if (s < 3600) return `${Math.floor(s/60)}m ago`;
    if (s < 86400) return `${Math.floor(s/3600)}h ago`;
    return new Date(d).toLocaleDateString();
  };

  const setAuthUI = () => {
    if (!apiBase) {
      if (stub) {
        stub.hidden = false;
        stub.textContent = 'Offline preview · proposals stay in this browser only';
      }
      if (authEl) authEl.innerHTML = '';
      if (hint) hint.textContent = '';
      return;
    }
    if (stub) stub.hidden = true;
    if (!me) {
      if (authEl) {
        if (authProviders?.linkedin) {
          const href = linkedinLoginHref(apiBase, window.location.href);
          authEl.innerHTML = linkedinButtonHtml(href, { className: 'dv-comment-signin jem-linkedin-signin' });
        } else {
          authEl.textContent = 'Sign-in not configured on API';
        }
      }
      if (hint) hint.textContent = 'Sign in to propose corrections. Reading does not require login.';
      form.querySelector('[data-comments-submit]').disabled = true;
      return;
    }
    form.querySelector('[data-comments-submit]').disabled = false;
    if (authEl) authEl.textContent = `Signed in as ${me.display_name}`;
    if (hint) {
      hint.textContent = me.role === 'new'
        ? 'Your proposals are held for review until you are trusted (auto at 3 approvals).'
        : '';
    }
  };

  const render = () => {
    count.textContent = items.length;
    empty.style.display = items.length ? 'none' : '';
    list.innerHTML = items.map(c => `
      <li class="dv-comment${c.pending_for_viewer ? ' pending' : ''}" data-id="${c.id}">
        <div class="dv-comment-vote">
          <button type="button" class="dv-vote-btn${c.user_voted ? ' voted' : ''}"
            aria-label="Upvote" data-id="${c.id}" ${!me?.can_vote ? 'disabled' : ''}>▲</button>
          <span class="dv-vote-count">${c.vote_count ?? c.votes ?? 0}</span>
        </div>
        <div class="dv-comment-body">
          <div class="dv-comment-meta">
            <span class="dv-comment-avatar">${initials(c.author_name || c.author)}</span>
            <span class="dv-comment-author">${esc(c.author_name || c.author || 'Researcher')}</span>
            <span class="dv-comment-time">· ${fmtTime(c.created_at || c.ts)}</span>
            ${c.pending_for_viewer ? '<span class="dv-comment-pending">· awaiting review</span>' : ''}
          </div>
          <p class="dv-comment-text">${esc(c.body)}</p>
          ${c.source_url ? `<p class="dv-comment-source-link"><a href="${esc(c.source_url)}" target="_blank" rel="noopener">Source</a></p>` : ''}
        </div>
      </li>
    `).join('');
    setAuthUI();
  };

  const loadRemote = async () => {
    const resp = await apiFetch(apiBase, `/corrections?scope=${encodeURIComponent(scope)}`);
    if (!resp.ok) throw new Error('load failed');
    const data = await resp.json();
    items = data.items || [];
    render();
  };

  const loadLocal = () => {
    items = STORES.get(scope) || [];
    render();
  };

  const init = async () => {
    const state = await loadAuthState();
    apiBase = state.apiBase;
    authProviders = state.providers;
    me = state.me;
    if (apiBase) {
      try {
        await loadRemote();
      } catch (_) {
        items = [];
        render();
      }
    } else {
      loadLocal();
    }
  };

  form.addEventListener('submit', async () => {
    const body = (input.value || '').trim();
    const sourceUrl = (source.value || '').trim();
    if (!body || !sourceUrl) return;

    if (!apiBase) {
      const local = STORES.get(scope);
      local.unshift({
        id: Date.now().toString(36),
        author: 'You',
        body,
        source_url: sourceUrl,
        ts: Date.now(),
        vote_count: 0,
        user_voted: false,
      });
      input.value = '';
      source.value = '';
      loadLocal();
      return;
    }

    if (!me) return;
    const resp = await apiFetch(apiBase, '/corrections', {
      method: 'POST',
      body: JSON.stringify({ scope, body, source_url: sourceUrl }),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      if (hint) hint.textContent = err.detail || 'Could not submit proposal';
      return;
    }
    input.value = '';
    source.value = '';
    await loadRemote();
  });

  list.addEventListener('click', async e => {
    const btn = e.target.closest('.dv-vote-btn');
    if (!btn || btn.disabled) return;
    const id = btn.dataset.id;

    if (!apiBase) {
      const c = (STORES.get(scope) || []).find(x => x.id === id);
      if (!c) return;
      c.user_voted = !c.user_voted;
      c.vote_count = (c.vote_count || 0) + (c.user_voted ? 1 : -1);
      loadLocal();
      return;
    }

    if (!me?.can_vote) return;
    await apiFetch(apiBase, `/corrections/${id}/vote`, { method: 'POST' });
    await loadRemote();
  });

  init();
}
