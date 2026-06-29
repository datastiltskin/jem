// Local dev: point the static map at the researcher API (corrections, etc.)
// On hosted sites (friedso.com) leave unset so callers auto-detect /api/v1 or /api/jem/v1.
(function () {
  if (window.JEM_API_BASE !== undefined) return;
  const h = window.location.hostname;
  if (h === 'localhost' || h === '127.0.0.1') {
    window.JEM_API_BASE = 'http://127.0.0.1:8001/api/v1';
  }
})();
