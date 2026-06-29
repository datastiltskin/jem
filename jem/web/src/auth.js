// Shared API client + LinkedIn sign-in for corrections and toolbar chrome.

let apiBasePromise = null;

function isCrossOrigin(base) {
  if (!base || base.startsWith('/')) return false;
  try {
    return new URL(base).origin !== window.location.origin;
  } catch {
    return false;
  }
}

export function resolveApiBase() {
  if (window.JEM_API_BASE !== undefined) {
    return Promise.resolve(window.JEM_API_BASE || null);
  }
  if (apiBasePromise) return apiBasePromise;
  apiBasePromise = (async () => {
    for (const base of ['/api/jem/v1', '/api/v1']) {
      try {
        const r = await fetch(`${base}/health`, { credentials: 'same-origin' });
        if (r.ok) return base;
      } catch (_) { /* try next */ }
    }
    return null;
  })();
  return apiBasePromise;
}

export function apiFetch(base, path, options = {}) {
  const credentials = isCrossOrigin(base) ? 'include' : 'same-origin';
  return fetch(`${base}${path}`, {
    credentials,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
}

export function linkedinLoginHref(apiBase, returnTo = window.location.href) {
  if (!apiBase) return null;
  const url = new URL(`${apiBase.replace(/\/$/, '')}/auth/linkedin/login`);
  url.searchParams.set('next', returnTo);
  return url.href;
}

export function linkedinButtonHtml(href, { className = 'jem-linkedin-signin', compact = false } = {}) {
  const label = compact ? 'Sign in' : 'Sign in with LinkedIn';
  return `<a href="${href}" class="${className}" rel="noopener">${label}</a>`;
}

export async function loadAuthState() {
  const apiBase = await resolveApiBase();
  if (!apiBase) return { apiBase: null, me: null, providers: null };

  let providers = null;
  let me = null;
  try {
    const provResp = await apiFetch(apiBase, '/auth/providers');
    if (provResp.ok) providers = await provResp.json();
  } catch (_) { /* offline */ }
  try {
    const meResp = await apiFetch(apiBase, '/auth/me');
    if (meResp.ok) me = await meResp.json();
  } catch (_) { /* offline */ }
  return { apiBase, me, providers };
}

export async function logout(apiBase) {
  await apiFetch(apiBase, '/auth/logout', { method: 'POST' });
}

export async function initToolbarAuth(container) {
  if (!container) return;
  const { apiBase, me, providers } = await loadAuthState();
  if (!apiBase || !providers?.linkedin) {
    container.innerHTML = '';
    container.hidden = true;
    return;
  }
  container.hidden = false;

  if (me) {
    container.innerHTML = `
      <span class="jem-auth-user" title="${me.role}">${me.display_name}</span>
      <button type="button" class="jem-auth-logout btn-ghost">Sign out</button>
    `;
    container.querySelector('.jem-auth-logout')?.addEventListener('click', async () => {
      await logout(apiBase);
      window.location.reload();
    });
    return;
  }

  const href = linkedinLoginHref(apiBase);
  container.innerHTML = linkedinButtonHtml(href, { compact: true });
}
