// Lazy-load Fuse.js (~24KB) for entity search after first paint.

const FUSE_URL = 'https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.min.js';

let loadPromise = null;

export function loadFuse() {
  if (typeof window.Fuse === 'function') return Promise.resolve(window.Fuse);
  if (loadPromise) return loadPromise;
  loadPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = FUSE_URL;
    script.async = true;
    script.onload = () => {
      if (typeof window.Fuse === 'function') resolve(window.Fuse);
      else reject(new Error('Fuse script loaded but window.Fuse is missing'));
    };
    script.onerror = () => reject(new Error('Failed to load Fuse.js'));
    document.head.appendChild(script);
  });
  return loadPromise;
}
