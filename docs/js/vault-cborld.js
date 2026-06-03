'use strict';

// ── CBOR-LD Encoder/Decoder (qualiaDB native format) ─────────────────────────
//
// qualiaDB's cbor_compiler.rs is the Strict Binary Gatekeeper — it rejects:
//   0x7B '{'  JSON / JSON-LD
//   0x3C '<'  RDF/XML
//   0x40 '@'  Turtle / N3
//
// The accepted format is a CBOR array of Lexicon-compressed u64 IDs:
//   [Subject_u64, Predicate_u64, Object_u64, Context_u64, Metadata_u64?]
//
// All IRI strings are mapped to u64 IDs through the Lexicon (wf-lexicon IDB,
// v10).  IDs are per-vault and auto-assigned; they are stored alongside the
// string so reverse lookup is always possible.
//
// Depends on: vault-idb.js (_ST_LEXICON, _dbGetAll, _dbPut)
//
// Init:  await vaultCborLd.initCborLd()  — call once after vault unlocks
// Then:  vaultCborLd.encodeIrisToCbor() / recordToCborLdQuins() as needed

// ── Lexicon cache ─────────────────────────────────────────────────────────────
// In-memory Map: string → BigInt (u64).  Backed by wf-lexicon IDB for persistence.

const _lex    = new Map(); // string → BigInt
let _lexMax   = 0n;        // highest assigned uid
let _lexReady = false;

async function initCborLd() {
  if (_lexReady) return;
  const all = await _dbGetAll(_ST_LEXICON);
  for (const entry of all) {
    const uid = BigInt(entry.uid);
    _lex.set(entry.id, uid);
    if (uid > _lexMax) _lexMax = uid;
  }
  _lexReady = true;
}

// Return or create the Lexicon u64 for a string (IRI or literal value).
// Auto-assigns a new ID if not found and persists it to wf-lexicon.
async function iriToId(str) {
  if (!_lexReady) await initCborLd();
  let uid = _lex.get(str);
  if (uid === undefined) {
    uid = ++_lexMax;
    _lex.set(str, uid);
    _dbPut(_ST_LEXICON, { id: str, uid: uid.toString() }).catch(() => {});
  }
  return uid; // BigInt
}

// Reverse: BigInt u64 → string. Returns null if unknown (no IDB fallback —
// if it's in the Lexicon it will be in the cache after initCborLd).
function idToIri(uid) {
  for (const [str, id] of _lex) {
    if (id === uid) return str;
  }
  return null;
}

// Sync lookup (no async) — use when you know the cache is warm.
function iriToIdSync(str) {
  return _lex.get(str) ?? null;
}

// ── CBOR unsigned integer encoding (RFC 8949) ─────────────────────────────────
// n is a BigInt; pushes bytes into the out array.

function _encUint(n, out) {
  if (n < 24n)          { out.push(Number(n)); }
  else if (n < 256n)    { out.push(0x18, Number(n)); }
  else if (n < 65536n)  { out.push(0x19, Number(n >> 8n) & 0xFF, Number(n) & 0xFF); }
  else if (n < 4294967296n) {
    out.push(0x1A,
      Number((n >> 24n) & 0xFFn), Number((n >> 16n) & 0xFFn),
      Number((n >>  8n) & 0xFFn), Number(n & 0xFFn));
  } else {
    out.push(0x1B,
      Number((n >> 56n) & 0xFFn), Number((n >> 48n) & 0xFFn),
      Number((n >> 40n) & 0xFFn), Number((n >> 32n) & 0xFFn),
      Number((n >> 24n) & 0xFFn), Number((n >> 16n) & 0xFFn),
      Number((n >>  8n) & 0xFFn), Number(n & 0xFFn));
  }
}

// ── CBOR unsigned integer decoding ────────────────────────────────────────────

function _decUint(bytes, offset) {
  const b   = bytes[offset];
  const add = b & 0x1F;
  if (add <= 23) return { v: BigInt(add), next: offset + 1 };
  if (add === 24) return { v: BigInt(bytes[offset + 1]), next: offset + 2 };
  if (add === 25) {
    const v = ((bytes[offset + 1] << 8) | bytes[offset + 2]) >>> 0;
    return { v: BigInt(v), next: offset + 3 };
  }
  if (add === 26) {
    const v = ((bytes[offset+1] << 24) | (bytes[offset+2] << 16) |
               (bytes[offset+3] <<  8) |  bytes[offset+4]) >>> 0;
    return { v: BigInt(v), next: offset + 5 };
  }
  if (add === 27) {
    const dv = new DataView(bytes.buffer, bytes.byteOffset + offset + 1, 8);
    const v  = (BigInt(dv.getUint32(0, false)) << 32n) | BigInt(dv.getUint32(4, false));
    return { v, next: offset + 9 };
  }
  throw new Error(`[CBOR-LD] Unsupported additional info: ${add}`);
}

// ── Encoding ──────────────────────────────────────────────────────────────────

// Encode a quint of BigInt Lexicon IDs → Uint8Array (CBOR array of 4 or 5 uints).
function encodeQuinToCbor(s, p, o, c, m) {
  const hasM = m !== undefined && m !== null;
  const out  = [hasM ? 0x85 : 0x84];
  for (const n of hasM ? [s, p, o, c, m] : [s, p, o, c]) _encUint(n, out);
  return new Uint8Array(out);
}

// Encode IRI strings → CBOR-LD Uint8Array via the Lexicon.
async function encodeIrisToCbor(sIri, pIri, oIri, cIri, mFlags) {
  const [s, p, o, c] = await Promise.all([sIri, pIri, oIri, cIri].map(iriToId));
  const m = mFlags !== undefined && mFlags !== null ? BigInt(mFlags) : undefined;
  return encodeQuinToCbor(s, p, o, c, m);
}

// ── Decoding ──────────────────────────────────────────────────────────────────

// Decode CBOR-LD Uint8Array → array of BigInt Lexicon IDs [s, p, o, c, m?].
function decodeCborToIds(bytes) {
  const u8 = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  if (!u8.length) throw new Error('[CBOR-LD] Empty payload');
  const header = u8[0];
  if ((header & 0xE0) !== 0x80) {
    throw new Error(`[CBOR-LD] Not a CBOR array — first byte 0x${header.toString(16)} would be rejected by cbor_compiler.rs gatekeeper`);
  }
  const count = header & 0x1F;
  let off = 1;
  const ids = [];
  for (let i = 0; i < count; i++) {
    const { v, next } = _decUint(u8, off);
    ids.push(v);
    off = next;
  }
  return ids;
}

// Decode CBOR-LD Uint8Array → IRI strings. Unknown IDs return "urn:lexicon:<id>".
function decodeCborToIris(bytes) {
  return decodeCborToIds(bytes).map(id => idToIri(id) ?? `urn:lexicon:${id}`);
}

// ── Record → quint batch ──────────────────────────────────────────────────────
// Converts a PLAINTEXT JS record (before AES-GCM encryption) into an array of
// CBOR-LD quints — one per non-trivial (key, value) pair.
//
// Subject IRI:   urn:wf:<storeName>:<record.id>
// Predicate IRI: https://wellfare.social/ns/vault#<key>
// Object IRI:    urn:wf:lit:<value_string>
// Context IRI:   https://wellfare.social/ns/vault#store/<storeName>
//
// Keys 'iv' and 'ct' are always skipped (crypto blobs).
// Pass the PLAINTEXT record, not the encrypted {id,iv,ct} stored in IDB.

async function recordToCborLdQuins(storeName, plainRecord) {
  const ctx  = `https://wellfare.social/ns/vault#store/${storeName}`;
  const subj = `urn:wf:${storeName}:${plainRecord.id}`;
  const WF   = 'https://wellfare.social/ns/vault#';
  const quins = [];
  for (const [key, raw] of Object.entries(plainRecord)) {
    if (key === 'id' || key === 'iv' || key === 'ct') continue;
    if (raw === undefined || raw === null) continue;
    const pred   = `${WF}${key}`;
    const objStr = typeof raw === 'string'  ? raw
                 : typeof raw === 'number'  ? String(raw)
                 : typeof raw === 'boolean' ? String(raw)
                 : JSON.stringify(raw);
    const obj = `urn:wf:lit:${objStr}`;
    quins.push(await encodeIrisToCbor(subj, pred, obj, ctx));
  }
  // Always emit an rdf:type triple
  const typeBytes = await encodeIrisToCbor(
    subj,
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
    `${WF}StoredRecord`,
    ctx,
  );
  quins.unshift(typeBytes);
  return quins; // Array<Uint8Array>
}

// ── QualiaStore insertion helper ──────────────────────────────────────────────
// Encodes plainRecord as CBOR-LD quints and inserts each into the QualiaStore.
// Returns the count of quints inserted, or 0 if QualiaStore is not ready.

async function insertRecordToQualiaStore(storeName, plainRecord) {
  const qStore = window.vaultWasm?.getQualiaStore();
  if (!qStore) return 0;
  const quins = await recordToCborLdQuins(storeName, plainRecord);
  let count = 0;
  for (const bytes of quins) {
    if (qStore.insert_from_cbor_ld(bytes)) count++;
  }
  return count;
}

// ── Public API ────────────────────────────────────────────────────────────────

window.vaultCborLd = {
  initCborLd,
  iriToId, idToIri, iriToIdSync,
  encodeQuinToCbor, encodeIrisToCbor,
  decodeCborToIds, decodeCborToIris,
  recordToCborLdQuins,
  insertRecordToQualiaStore,
};
