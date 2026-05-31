'use strict';

// ── Noise_XX_25519_AESGCM_SHA256 — used by webconnect.html only ───────────────
// Depends on: vault-did.js (for toB64/fromB64 — loaded via vault-crypto.js)

async function hmacSHA256(key, data) {
  const k = await crypto.subtle.importKey('raw', key, { name:'HMAC', hash:'SHA-256' }, false, ['sign']);
  return new Uint8Array(await crypto.subtle.sign('HMAC', k, data));
}
async function noiseHKDF2(ck, ikm) {
  const tmp  = await hmacSHA256(ck, ikm);
  const out1 = await hmacSHA256(tmp, new Uint8Array([1]));
  const out2 = await hmacSHA256(tmp, new Uint8Array([...out1, 2]));
  return [out1, out2];
}
async function noiseDigest(a, b) {
  const buf = new Uint8Array(a.length + b.length);
  buf.set(a); buf.set(b, a.length);
  return new Uint8Array(await crypto.subtle.digest('SHA-256', buf));
}
async function noiseGenX25519() {
  const kp  = await crypto.subtle.generateKey({ name:'X25519' }, true, ['deriveBits']);
  const pub  = new Uint8Array(await crypto.subtle.exportKey('raw', kp.publicKey));
  return { priv: kp.privateKey, pub, pubKey: kp.publicKey };
}
async function noiseImportPub(raw) {
  return crypto.subtle.importKey('raw', raw, { name:'X25519' }, true, []);
}
async function noiseDH(priv, pubKey) {
  return new Uint8Array(await crypto.subtle.deriveBits({ name:'X25519', public: pubKey }, priv, 256));
}
function noiseIV(n) {
  const iv = new Uint8Array(12);
  new DataView(iv.buffer).setUint32(8, n >>> 0, true);
  return iv;
}
async function aesGCMEncrypt(k32, n, ad, pt) {
  const key = await crypto.subtle.importKey('raw', k32, { name:'AES-GCM' }, false, ['encrypt']);
  return new Uint8Array(await crypto.subtle.encrypt({ name:'AES-GCM', iv: noiseIV(n), additionalData: ad }, key, pt));
}
async function aesGCMDecrypt(k32, n, ad, ct) {
  const key = await crypto.subtle.importKey('raw', k32, { name:'AES-GCM' }, false, ['decrypt']);
  return new Uint8Array(await crypto.subtle.decrypt({ name:'AES-GCM', iv: noiseIV(n), additionalData: ad }, key, ct));
}
async function noiseStateInit() {
  const proto = new TextEncoder().encode('Noise_XX_25519_AESGCM_SHA256');
  const h = new Uint8Array(32);
  if (proto.length <= 32) h.set(proto);
  else h.set(new Uint8Array(await crypto.subtle.digest('SHA-256', proto)));
  return { h: h.slice(), ck: h.slice(), k: null, n: 0 };
}
async function noiseMH(st, data) { st.h = await noiseDigest(st.h, data); }
async function noiseMK(st, dh) {
  const [ck, k] = await noiseHKDF2(st.ck, dh);
  st.ck = ck; st.k = k; st.n = 0;
}
async function noiseEH(st, pt) {
  if (!st.k) { await noiseMH(st, pt); return pt; }
  const ct = await aesGCMEncrypt(st.k, st.n++, st.h, pt);
  await noiseMH(st, ct); return ct;
}
async function noiseDH2(st, ct) {
  if (!st.k) { await noiseMH(st, ct); return ct; }
  const pt = await aesGCMDecrypt(st.k, st.n++, st.h, ct);
  await noiseMH(st, ct); return pt;
}
async function noiseSplit(st) {
  const [k1r, k2r] = await noiseHKDF2(st.ck, new Uint8Array(0));
  const k1 = await crypto.subtle.importKey('raw', k1r, { name:'AES-GCM' }, false, ['encrypt','decrypt']);
  const k2 = await crypto.subtle.importKey('raw', k2r, { name:'AES-GCM' }, false, ['encrypt','decrypt']);
  return { k1, k2 };
}

let _noiseQ = [], _noiseR = [];
function noiseEnqueue(m) { if (_noiseR.length) _noiseR.shift()(m); else _noiseQ.push(m); }
function noiseAwait()    { if (_noiseQ.length) return Promise.resolve(_noiseQ.shift()); return new Promise(r => _noiseR.push(r)); }

let _sessionSend = null, _sessionRecv = null, _sendN = 0, _recvN = 0, _handshakeDone = false;
let _sendQueue   = Promise.resolve();

function noiseReset() {
  _sessionSend = null; _sessionRecv = null;
  _sendN = 0; _recvN = 0; _handshakeDone = false;
  _noiseQ = []; _noiseR = [];
  _sendQueue = Promise.resolve();
}

function dcRawSend(m) { dc.send(JSON.stringify(m)); }

function secureSend(m) {
  _sendQueue = _sendQueue.then(async () => {
    if (!_handshakeDone) { dcRawSend(m); return; }
    const n  = _sendN++;
    const pt = new TextEncoder().encode(JSON.stringify(m));
    const ct = new Uint8Array(await crypto.subtle.encrypt(
      { name:'AES-GCM', iv: noiseIV(n), additionalData: new Uint8Array(0) }, _sessionSend, pt));
    const buf = new ArrayBuffer(4 + ct.length);
    new DataView(buf).setUint32(0, n, true);
    new Uint8Array(buf, 4).set(ct);
    dc.send(buf);
  });
}

async function secureRecv(raw) {
  if (raw instanceof ArrayBuffer) {
    const n  = new DataView(raw).getUint32(0, true);
    if (n !== _recvN++) throw new Error('nonce mismatch');
    const ct = new Uint8Array(raw, 4);
    const pt = new Uint8Array(await crypto.subtle.decrypt(
      { name:'AES-GCM', iv: noiseIV(n), additionalData: new Uint8Array(0) }, _sessionRecv, ct));
    return JSON.parse(new TextDecoder().decode(pt));
  }
  return JSON.parse(raw);
}

// Noise_XX responder (vault / phone side)
async function runNoiseResponder(staticKp, msg1) {
  const st    = await noiseStateInit();
  const eiRaw = fromB64(msg1.e);
  await noiseMH(st, eiRaw);
  const eiPub = await noiseImportPub(eiRaw);

  const er = await noiseGenX25519();
  await noiseMH(st, er.pub);
  await noiseMK(st, await noiseDH(er.priv, eiPub));          // ee

  const srRaw = new Uint8Array(await crypto.subtle.exportKey('raw', staticKp.pubKey));
  const srEnc = await noiseEH(st, srRaw);
  await noiseMK(st, await noiseDH(staticKp.priv, eiPub));    // se

  const payload2 = await noiseEH(st, new Uint8Array(0));
  dcRawSend({ type: 'noise', msg: 2, e: toB64(er.pub), s: toB64(srEnc), p: toB64(payload2) });

  const msg3  = await noiseAwait();
  const eiEnc = fromB64(msg3.s);
  const eiPt  = await noiseDH2(st, eiEnc);
  const eiPub3 = await noiseImportPub(eiPt);
  await noiseMK(st, await noiseDH(er.priv, eiPub3));         // ee (msg3)
  await noiseMK(st, await noiseDH(staticKp.priv, eiPub3));   // se (msg3)
  await noiseDH2(st, fromB64(msg3.p));

  const { k1, k2 } = await noiseSplit(st);
  return { sendKey: k2, recvKey: k1 };
}
