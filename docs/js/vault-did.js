'use strict';

// ── Identity credentials — did:key generation ────────────────────────────────
// Ed25519 key pair; DID encoded as did:key:z<base58btc(0xed01 || pubkey)>

const B58_ALPHA = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';

function base58btcEncode(bytes) {
  let n = 0n;
  for (const b of bytes) n = (n << 8n) | BigInt(b);
  const digits = [];
  while (n > 0n) { digits.push(B58_ALPHA[Number(n % 58n)]); n /= 58n; }
  for (const b of bytes) { if (b !== 0) break; digits.push(B58_ALPHA[0]); }
  return digits.reverse().join('');
}

async function generateDidKey() {
  const kp     = await crypto.subtle.generateKey({ name: 'Ed25519' }, false, ['sign', 'verify']);
  const pubRaw = new Uint8Array(await crypto.subtle.exportKey('raw', kp.publicKey));
  const prefixed = new Uint8Array(2 + pubRaw.length);
  prefixed[0] = 0xed; prefixed[1] = 0x01;
  prefixed.set(pubRaw, 2);
  return { did: 'did:key:z' + base58btcEncode(prefixed), publicKey: kp.publicKey, privateKey: kp.privateKey };
}
