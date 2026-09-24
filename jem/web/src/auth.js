// Shared API client. Sign-in is not shown in the map UI.

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
