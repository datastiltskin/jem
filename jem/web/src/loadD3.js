// Lazy-load D3 (~280KB) only when map or neighborhood graphs need it.

const D3_URL = 'https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js';

let loadPromise = null;

export function loadD3() {
  if (window.d3) return Promise.resolve(window.d3);
  if (loadPromise) return loadPromise;
  loadPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = D3_URL;
    script.async = true;
    script.onload = () => {
      if (window.d3) resolve(window.d3);
      else reject(new Error('D3 script loaded but window.d3 is missing'));
    };
    script.onerror = () => reject(new Error('Failed to load D3'));
    document.head.appendChild(script);
  });
  return loadPromise;
}
