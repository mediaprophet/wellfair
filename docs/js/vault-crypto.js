'use strict';

// ── Fixed public salts — security lives in the PIN, not the salt ─────────────
const _MAIN_SALT = new Uint8Array([0x77,0x66,0x2d,0x6d,0x61,0x69,0x6e,0x73,
                                    0x61,0x6c,0x74,0x2d,0x76,0x31,0x00,0x00]);
const _SANC_SALT = new Uint8Array([0x77,0x66,0x2d,0x73,0x61,0x6e,0x63,0x2d,
                                    0x73,0x61,0x6c,0x74,0x2d,0x76,0x31,0x00]);
const _DURS_SALT = new Uint8Array([0x77,0x66,0x2d,0x64,0x75,0x72,0x73,0x2d,
                                    0x73,0x61,0x6c,0x74,0x2d,0x76,0x31,0x00]);

function toB64(u8) { return btoa(String.fromCharCode(...u8)); }
function fromB64(s) { return Uint8Array.from(atob(s), c => c.charCodeAt(0)); }

// PBKDF2-SHA256, 310 000 iterations (OWASP 2023 minimum for SHA-256).
async function deriveVaultKey(pin, salt) {
  const raw  = new TextEncoder().encode(pin);
  const base = await crypto.subtle.importKey('raw', raw, 'PBKDF2', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, hash: 'SHA-256', iterations: 310_000 }, base, 256
  );
  return crypto.subtle.importKey('raw', bits, { name: 'AES-GCM' }, false, ['encrypt', 'decrypt']);
}

// commitment = sha256( sha256(entry_bytes) ‖ nonce )
async function computeCommitment(entryBytes) {
  const nonce    = crypto.getRandomValues(new Uint8Array(16));
  const inner    = new Uint8Array(await crypto.subtle.digest('SHA-256', entryBytes));
  const combined = new Uint8Array(32 + 16);
  combined.set(inner); combined.set(nonce, 32);
  const outer = new Uint8Array(await crypto.subtle.digest('SHA-256', combined));
  return { nonce: toB64(nonce), commitment: toB64(outer) };
}

async function _sEnc(key, plain) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const pt = new TextEncoder().encode(JSON.stringify(plain));
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, pt));
  return { iv: toB64(iv), ct: toB64(ct) };
}

async function _sDec(key, { iv, ct }) {
  const pt = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: fromB64(iv) }, key, fromB64(ct)
  );
  return JSON.parse(new TextDecoder().decode(pt));
}
