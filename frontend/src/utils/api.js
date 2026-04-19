const isDevFrontend =
  typeof window !== 'undefined' &&
  ['localhost', '127.0.0.1'].includes(window.location.hostname) &&
  window.location.port === '5173';

const envApiBase = (import.meta.env.VITE_API_BASE || '').trim();
export const API_BASE = (envApiBase || (isDevFrontend ? 'http://localhost:8000' : '')).replace(/\/$/, '');

const envWsBase = (import.meta.env.VITE_WS_BASE || '').trim();
const inferredWsBase = API_BASE
  ? API_BASE.replace(/^http:/, 'ws:').replace(/^https:/, 'wss:')
  : (typeof window !== 'undefined' ? window.location.origin.replace(/^http:/, 'ws:').replace(/^https:/, 'wss:') : '');

export const WS_BASE = (envWsBase || inferredWsBase).replace(/\/$/, '');

export function apiUrl(path) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE}${normalizedPath}`;
}

export function wsUrl(path) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${WS_BASE}${normalizedPath}`;
}