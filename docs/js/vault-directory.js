'use strict';

// ── Verified Directory — contact graph, FOAF-inspired, encrypted IDB ──────────
// Depends on: vault-idb.js (_ST_CONTACTS, _ST_RELS, _ST_AGREEMENTS, _dbPut,
//             _dbGet, _dbGetAll, _dbDelete), vault-crypto.js (_sEnc, _sDec)
//
// All contact, relationship, and agreement records are AES-256-GCM encrypted
// before being written to IDB. The raw IDB values are never plaintext.
//
// Module init: call initDirectory(aesKey) when the vault unlocks.
// vault.html wires this in VC-7b (Session 2).

// ── Module state ──────────────────────────────────────────────────────────────

let _dirKey = null; // AES-GCM CryptoKey set by initDirectory()

// ── Relationship type constants (mirrors wf:RelationshipShape sh:in list) ─────

const DIR_REL_TYPES = Object.freeze({
  PERSONAL:     'personal',
  PROFESSIONAL: 'professional',
  CLINICAL:     'clinical',
  LEGAL:        'legal',
});

// ── Init ──────────────────────────────────────────────────────────────────────

function initDirectory(aesKey) {
  _dirKey = aesKey;
}

function _requireKey() {
  if (!_dirKey) throw new Error('[Directory] Key not set — call initDirectory(key) after vault unlocks');
}

// ── Encryption helpers ────────────────────────────────────────────────────────

async function _encRecord(plain) {
  const { iv, ct } = await _sEnc(_dirKey, plain);
  return { id: plain.id, iv, ct };
}

async function _decRecord(stored) {
  return _sDec(_dirKey, { iv: stored.iv, ct: stored.ct });
}

// ── Public API — contacts ─────────────────────────────────────────────────────

// Create a new contact and persist it encrypted.
// Returns the plaintext record (including the generated id).
async function addContact(name, did, webId = null, notes = '') {
  _requireKey();
  const record = {
    id:         crypto.randomUUID(),
    name,
    did,
    webId:      webId  || null,
    notes:      notes  || '',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
  await _dbPut(_ST_CONTACTS, await _encRecord(record));
  return record;
}

// Retrieve and decrypt a single contact by id. Returns null if not found.
async function getContact(id) {
  _requireKey();
  const stored = await _dbGet(_ST_CONTACTS, id);
  return stored ? _decRecord(stored) : null;
}

// Retrieve and decrypt all contacts. Returns an array (may be empty).
async function getAllContacts() {
  _requireKey();
  const all = await _dbGetAll(_ST_CONTACTS);
  return Promise.all(all.map(r => _decRecord(r)));
}

// Merge `fields` into an existing contact record and re-encrypt.
// Returns the updated plaintext record.
async function updateContact(id, fields) {
  _requireKey();
  const existing = await getContact(id);
  if (!existing) throw new Error(`[Directory] Contact not found: ${id}`);
  const updated = { ...existing, ...fields, id, updated_at: new Date().toISOString() };
  await _dbPut(_ST_CONTACTS, await _encRecord(updated));
  return updated;
}

// Delete a contact and its associated relationship + agreement records.
async function deleteContact(id) {
  _requireKey();
  await _dbDelete(_ST_CONTACTS, id);
  await _dbDelete(_ST_RELS,      id).catch(() => {});
  await _dbDelete(_ST_AGREEMENTS, id).catch(() => {});
}

// Look up a contact by their identity credential (did:key or did:peer).
// Returns the first matching plaintext contact record, or null.
// Used by the caller gating module (VC-9) to identify inbound callers.
async function lookupByDid(did) {
  _requireKey();
  const all = await getAllContacts();
  return all.find(c => c.did === did) ?? null;
}

// ── Public API — relationships & agreements ───────────────────────────────────

// Return the decrypted relationship record for a contact, including the
// nested agreement (if one has been saved). Returns null if none exists.
async function getRelationship(contactId) {
  _requireKey();
  const relStored = await _dbGet(_ST_RELS, contactId);
  if (!relStored) return null;
  const rel = await _decRecord(relStored);

  const agStored  = await _dbGet(_ST_AGREEMENTS, contactId);
  const agreement = agStored ? await _decRecord(agStored) : null;

  return { ...rel, agreement };
}

// Persist a relationship and its signed ODRL agreement after a Semantic
// Handshake (VC-8). Both sides call this once the handshake is finalised.
//
// contactId      — id of the wf:Contact this relationship belongs to
// peerDid        — did:peer generated during the handshake
// agreementJsonLd — full ODRL Agreement as a JSON-LD string
// ourSig         — base64 Ed25519 sig over canonical agreement JSON (our key)
// theirSig       — counterparty's base64 Ed25519 sig (may be null on initiator
//                  side until finaliseHandshake() is called)
async function saveRelationship(contactId, peerDid, agreementJsonLd, ourSig, theirSig) {
  _requireKey();
  const now = new Date().toISOString();

  const relRecord = {
    id:         contactId,
    contactId,
    peerDid,
    type:       DIR_REL_TYPES.PERSONAL, // overrideable via updateContact after handshake
    created_at: now,
    updated_at: now,
  };
  await _dbPut(_ST_RELS, await _encRecord(relRecord));

  const agRecord = {
    id:             contactId,
    contactId,
    agreementJsonLd,
    ourSig,
    theirSig:       theirSig ?? null,
    created_at:     now,
    updated_at:     now,
  };
  await _dbPut(_ST_AGREEMENTS, await _encRecord(agRecord));

  return { relationship: relRecord, agreement: agRecord };
}
