// JEM brand assets — shared logo paths and markup

export const LOGO_MARK = 'public/assets/jem-mark.svg';
export const LOGO_MARK_WHITE = 'public/assets/jem-mark-white.svg';
export const LOGO_FAVICON = 'public/assets/jem-favicon.svg';
export const LOGO_APP_ICON = 'public/assets/jem-app-icon.svg';
export const LOGO_LOCKUP = 'public/assets/jem-lockup.png';
export const LOGO_WORDMARK = 'public/assets/jem-logo.png';

const LOCKUP_ASPECT = 310 / 730;
const WORDMARK_ASPECT = 350 / 758;

export function logoImg({ variant = 'mark', className = 'jem-mark', size = 24, alt = '' } = {}) {
  const src = variant === 'white' ? LOGO_MARK_WHITE : LOGO_MARK;
  return `<img src="${src}" class="${className}" alt="${alt}" width="${size}" height="${size}" decoding="async">`;
}

/** Compact lockup — icon + JEM (toolbar, exports). */
export function logoLockupHTML({ className = 'jem-logo-lockup', width = 320, alt = 'JEM' } = {}) {
  const height = Math.round(width * LOCKUP_ASPECT);
  return `<img src="${LOGO_LOCKUP}" class="${className}" alt="${alt}" width="${width}" height="${height}" decoding="async">`;
}

/** Full wordmark — icon + JEM + tagline (home masthead). */
export function logoWordmarkHTML({ className = 'jem-logo-wordmark', width = 460, alt = 'JEM — Judiciary Entity Map' } = {}) {
  const height = Math.round(width * WORDMARK_ASPECT);
  return `<img src="${LOGO_WORDMARK}" class="${className}" alt="${alt}" width="${width}" height="${height}" decoding="async">`;
}

/** Header block shown on print / PDF exports only. */
export function printBrandBlock() {
  return `<header class="jem-print-brand" aria-hidden="true">
    ${logoImg({ className: 'jem-print-brand-mark', size: 32, alt: 'JEM' })}
    <div class="jem-print-brand-text">
      <strong class="jem-print-brand-name">JEM</strong>
      <span class="jem-print-brand-tag">Judiciary Entity Map (India)</span>
    </div>
  </header>`;
}
