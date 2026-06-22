// Comments + upvote UI. ponytail: in-memory only; swap the `comments` array
// for a fetch/insert when the backend lands.

const STORES = new Map(); // scope -> array of { id, author, body, ts, votes, voted }

export function commentsHTML(scope = 'global', { title = 'Comments' } = {}) {
  return `
    <section class="dv-comments" data-comments-scope="${scope}" aria-label="Community comments">
      <header class="dv-comments-head">
        <h2 class="dv-comments-title">${title}</h2>
        <span class="dv-comments-count" data-comments-count>0</span>
        <span class="dv-comments-stub">Read-only preview · backend not wired yet</span>
      </header>

      <form class="dv-comment-form" data-comments-form onsubmit="return false">
        <textarea class="dv-comment-input" data-comments-input rows="3"
          placeholder="Flag a source, propose a correction, or share context…" maxlength="2000"></textarea>
        <div class="dv-comment-form-row">
          <input class="dv-comment-name" data-comments-name type="text"
            placeholder="Your name (optional)" maxlength="60" autocomplete="name">
          <button class="dv-comment-submit" data-comments-submit type="submit">Post comment</button>
        </div>
      </form>

      <ul class="dv-comment-list" data-comments-list></ul>
      <p class="dv-comment-empty" data-comments-empty>No comments yet. Be the first.</p>
    </section>
  `;
}

export function wireComments(root) {
  if (!root) return;
  root.querySelectorAll('[data-comments-scope]').forEach(section => {
    const scope = section.getAttribute('data-comments-scope');
    if (!STORES.has(scope)) STORES.set(scope, []);
    const comments = STORES.get(scope);

    const form  = section.querySelector('[data-comments-form]');
    const input = section.querySelector('[data-comments-input]');
    const name  = section.querySelector('[data-comments-name]');
    const list  = section.querySelector('[data-comments-list]');
    const empty = section.querySelector('[data-comments-empty]');
    const count = section.querySelector('[data-comments-count]');

    const esc = s => s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const initials = n => (n || 'A').trim().split(/\s+/).slice(0,2).map(p => p[0]).join('').toUpperCase() || 'A';
    const fmtTime = ts => {
      const s = Math.round((Date.now() - ts) / 1000);
      if (s < 60) return 'just now';
      if (s < 3600) return `${Math.floor(s/60)}m ago`;
      if (s < 86400) return `${Math.floor(s/3600)}h ago`;
      return new Date(ts).toLocaleDateString();
    };

    const render = () => {
      count.textContent = comments.length;
      empty.style.display = comments.length ? 'none' : '';
      list.innerHTML = comments.map(c => `
        <li class="dv-comment" data-id="${c.id}">
          <div class="dv-comment-vote">
            <button type="button" class="dv-vote-btn${c.voted ? ' voted' : ''}" aria-label="Upvote" data-id="${c.id}">▲</button>
            <span class="dv-vote-count">${c.votes}</span>
          </div>
          <div class="dv-comment-body">
            <div class="dv-comment-meta">
              <span class="dv-comment-avatar">${initials(c.author)}</span>
              <span class="dv-comment-author">${esc(c.author || 'Anonymous')}</span>
              <span class="dv-comment-time">· ${fmtTime(c.ts)}</span>
            </div>
            <p class="dv-comment-text">${esc(c.body)}</p>
          </div>
        </li>
      `).join('');
    };

    form.addEventListener('submit', () => {
      const body = (input.value || '').trim();
      if (!body) return;
      comments.unshift({
        id: Date.now().toString(36) + Math.random().toString(36).slice(2,6),
        author: (name.value || '').trim(),
        body, ts: Date.now(), votes: 0, voted: false,
      });
      input.value = '';
      render();
    });

    list.addEventListener('click', e => {
      const btn = e.target.closest('.dv-vote-btn');
      if (!btn) return;
      const c = comments.find(x => x.id === btn.dataset.id);
      if (!c) return;
      c.voted = !c.voted;
      c.votes += c.voted ? 1 : -1;
      render();
    });

    render();
  });
}
