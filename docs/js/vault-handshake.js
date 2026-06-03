'use strict';

// ── Semantic Handshake — ODRL agreement generation + Ed25519 signing ──────────
// Depends on: vault-idb.js, vault-crypto.js (toB64, fromB64),
//             vault-did.js (generateDidKey), vault-directory.js (getContact,
//             lookupByDid, addContact, saveRelationship)
//
// Four-step protocol:
//   Initiator: initiateHandshake(contactId) → { qrData, nymSent, uid }
//   Receiver:  receiveHandshake(payloadB64) → { contactName, did, agreement, sigValid }
//   Receiver:  acceptHandshake(payloadB64, approved) → { blob, agreement } | null
//   Initiator: finaliseHandshake(blobB64) → { contact, agreement }
//
// Agreement payload (ODRL JSON-LD), see wf:UsageAgreementShape in access-profiles.ttl.

// Pending initiator state — lives in memory; lost on page reload (acceptable for VC-8).
// Key: agreement uid.  Value: { contactId, privateKey, ourDid, peerDid, agreement }
const _pendingHandshakes = new Map();

// ── Public API ────────────────────────────────────────────────────────────────

// Build and sign a handshake proposal for contactId.
// Returns: { qrData (base64 JSON), nymSent (bool), uid, ourDid, peerDid }
async function initiateHandshake(contactId) {
  const contact = await getContact(contactId);
  if (!contact) throw new Error('[Handshake] Contact not found: ' + contactId);

  const ourKeys = await generateDidKey();
  const peerDid = 'did:peer:' + crypto.randomUUID();
  const uid     = 'urn:uuid:' + crypto.randomUUID();

  const agreement = {
    '@context': [
      'http://www.w3.org/ns/odrl.jsonld',
      'https://wellfare.social/ns/vault#',
    ],
    '@type':          'odrl:Agreement',
    uid,
    'wf:initiator':   ourKeys.did,
    'wf:counterparty': contact.did || '',
    'wf:peerDid':     peerDid,
    permission: [
      { action: 'odrl:read', target: 'wf:overview'    },
      { action: 'odrl:read', target: 'wf:medications' },
    ],
    'wf:initiatorSig':    '',
    'wf:counterpartySig': null,
  };

  agreement['wf:initiatorSig'] = await _sign(ourKeys.privateKey, _canonical(agreement));

  _pendingHandshakes.set(uid, {
    contactId,
    privateKey: ourKeys.privateKey,
    ourDid:     ourKeys.did,
    peerDid,
    agreement: { ...agreement },
  });

  const payload = { type: 'wf:handshake_proposal', v: 1, agreement };
  const qrData  = btoa(JSON.stringify(payload));

  let nymSent = false;
  if (contact.nymAddress && typeof nymAdapter !== 'undefined' && nymAdapter) {
    try { await nymAdapter.send(contact.nymAddress, payload); nymSent = true; } catch (_) {}
  }

  return { qrData, nymSent, uid, ourDid: ourKeys.did, peerDid };
}

// Parse an incoming proposal and verify the initiator's signature.
// Returns: { contactName, did, peerDid, agreement, sigValid }
async function receiveHandshake(payloadB64) {
  const payload = JSON.parse(atob(payloadB64));
  if (payload.type !== 'wf:handshake_proposal' || payload.v !== 1) {
    throw new Error('[Handshake] Invalid payload type');
  }
  const { agreement } = payload;

  const contact  = agreement['wf:initiator'] ? await lookupByDid(agreement['wf:initiator']) : null;
  const sigValid = await _verifyFromDid(
    agreement['wf:initiator'],
    agreement['wf:initiatorSig'],
    _canonical({ ...agreement, 'wf:initiatorSig': '', 'wf:counterpartySig': null }),
  );

  return {
    contactName: contact?.name ?? null,
    did:         agreement['wf:initiator'],
    peerDid:     agreement['wf:peerDid'],
    agreement,
    sigValid,
  };
}

// Sign and accept (or decline) a received proposal.
// If approved: saves relationship on receiver side, returns { blob, agreement }.
// If declined: returns null.
async function acceptHandshake(payloadB64, approved) {
  if (!approved) return null;

  const payload   = JSON.parse(atob(payloadB64));
  const { agreement } = payload;

  const ourKeys = await generateDidKey();

  const signed = {
    ...agreement,
    'wf:counterparty':    ourKeys.did,
    'wf:counterpartySig': '',
  };

  signed['wf:counterpartySig'] = await _sign(ourKeys.privateKey, _canonical(signed));

  // Find or create contact for the initiator
  let contact = await lookupByDid(agreement['wf:initiator']);
  if (!contact) {
    const placeholder = agreement['wf:initiator'].slice(0, 32) + '…';
    contact = await addContact(placeholder, agreement['wf:initiator']);
  }

  await saveRelationship(
    contact.id,
    signed['wf:peerDid'],
    JSON.stringify(signed),
    signed['wf:counterpartySig'],
    agreement['wf:initiatorSig'],
  );

  // PIA4 — git-signed N-Quads bundle for legal-grade audit trail
  const nqBundle = _agreementToNQuads(signed);
  _sign(ourKeys.privateKey, new TextEncoder().encode(nqBundle))
    .then(nqSig => _writeContractEvent(signed.uid, nqBundle, nqSig, ourKeys.did))
    .catch(() => {});

  const blob = btoa(JSON.stringify({ type: 'wf:handshake_response', v: 1, agreement: signed }));
  return { blob, ourDid: ourKeys.did, agreement: signed };
}

// Verify counterparty signature and save relationship on the initiator side.
// Returns: { contact, agreement }
async function finaliseHandshake(blobB64) {
  const parsed    = JSON.parse(atob(blobB64));
  if (parsed.type !== 'wf:handshake_response' || parsed.v !== 1) {
    throw new Error('[Handshake] Invalid response type');
  }
  const { agreement: signed } = parsed;
  const uid = signed.uid;

  const pending = _pendingHandshakes.get(uid);
  if (!pending) throw new Error('[Handshake] No pending handshake for uid: ' + uid);

  const sigValid = await _verifyFromDid(
    signed['wf:counterparty'],
    signed['wf:counterpartySig'],
    _canonical({ ...signed, 'wf:counterpartySig': '' }),
  );
  if (!sigValid) throw new Error('[Handshake] Counterparty signature verification failed');

  const contact = await getContact(pending.contactId);
  if (!contact) throw new Error('[Handshake] Original contact not found: ' + pending.contactId);

  await saveRelationship(
    contact.id,
    signed['wf:peerDid'],
    JSON.stringify(signed),
    pending.agreement['wf:initiatorSig'],
    signed['wf:counterpartySig'],
  );

  _pendingHandshakes.delete(uid);

  // PIA4 — git-signed N-Quads bundle for legal-grade audit trail
  const nqBundle = _agreementToNQuads(signed);
  _sign(pending.privateKey, new TextEncoder().encode(nqBundle))
    .then(nqSig => _writeContractEvent(uid, nqBundle, nqSig, pending.ourDid))
    .catch(() => {});

  return { contact, agreement: signed };
}

// ── PIA4: Git-signed contract provenance ──────────────────────────────────────
// On every fully countersigned agreement, generates an N-Quads bundle of the
// contract quads, signs it with the local Ed25519 key, and writes a
// git_commit_ref protocol event to wf-events IDB.

function _agreementToNQuads(agr) {
  const WF  = 'https://wellfare.social/ns/vault#';
  const QP  = 'https://qualia.id/ns/';
  const DCT = 'http://purl.org/dc/terms/';
  const XSD = 'http://www.w3.org/2001/XMLSchema#';
  const RDF = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#';
  const subj = `<${agr.uid}>`;
  const lines = [
    `${subj} <${RDF}type> <${QP}Contract> .`,
    `${subj} <${RDF}type> <${WF}UsageAgreement> .`,
  ];
  if (agr['wf:initiator'])      lines.push(`${subj} <${WF}initiator> "${agr['wf:initiator']}" .`);
  if (agr['wf:counterparty'])   lines.push(`${subj} <${WF}counterparty> "${agr['wf:counterparty']}" .`);
  if (agr['wf:peerDid'])        lines.push(`${subj} <${WF}peerDid> "${agr['wf:peerDid']}" .`);
  if (agr['wf:initiatorSig'])   lines.push(`${subj} <${WF}agreementSig> "${agr['wf:initiatorSig']}" .`);
  if (agr['wf:counterpartySig']) lines.push(`${subj} <${WF}counterpartySig> "${agr['wf:counterpartySig']}" .`);
  lines.push(`${subj} <${DCT}created> "${new Date().toISOString()}"^^<${XSD}dateTime> .`);
  return lines.join('\n');
}

async function _writeContractEvent(uid, nqBundle, nqSig, authorDid) {
  try {
    await _dbPut(_ST_EVENTS, {
      id:                crypto.randomUUID(),
      type:              'wf:ProtocolEvent',
      protocolEventType: 'git_commit_ref',
      agreementUid:      uid,
      nqBundle,
      nqSig,
      authorDid:         authorDid || null,
      timestamp:         new Date().toISOString(),
      piaEvent:          true,
    });
  } catch (e) {
    console.warn('[PIA4] _writeContractEvent failed:', e.message);
  }
}

// ── Crypto helpers ────────────────────────────────────────────────────────────

// Deterministic JSON bytes — sort keys recursively so both sides sign the same bytes.
function _canonical(obj) {
  return new TextEncoder().encode(JSON.stringify(_sortKeys(obj)));
}

function _sortKeys(v) {
  if (Array.isArray(v)) return v.map(_sortKeys);
  if (v && typeof v === 'object') {
    return Object.fromEntries(Object.keys(v).sort().map(k => [k, _sortKeys(v[k])]));
  }
  return v;
}

async function _sign(privateKey, data) {
  const sig = new Uint8Array(await crypto.subtle.sign('Ed25519', privateKey, data));
  return toB64(sig);
}

async function _verifyFromDid(did, sigB64, data) {
  if (!did || !sigB64) return false;
  try {
    const pubKey = await _importPubKeyFromDid(did);
    return crypto.subtle.verify('Ed25519', pubKey, fromB64(sigB64), data);
  } catch (_) { return false; }
}

// Decode a did:key:z<base58btc(0xed01||pubkey)> and import the Ed25519 public key.
async function _importPubKeyFromDid(did) {
  if (!did?.startsWith('did:key:z')) throw new Error('Not a did:key: ' + did);
  const decoded  = _b58Decode(did.slice('did:key:z'.length));
  // First two bytes are the multicodec prefix 0xed 0x01
  const pubBytes = decoded.slice(2);
  return crypto.subtle.importKey('raw', pubBytes, 'Ed25519', false, ['verify']);
}

// Base58btc decode — inverse of base58btcEncode in vault-did.js.
const _B58_ALPHA = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
function _b58Decode(s) {
  let n = 0n;
  for (const ch of s) {
    const idx = _B58_ALPHA.indexOf(ch);
    if (idx < 0) throw new Error('Invalid base58 char: ' + ch);
    n = n * 58n + BigInt(idx);
  }
  const bytes = [];
  while (n > 0n) { bytes.unshift(Number(n & 0xffn)); n >>= 8n; }
  for (const ch of s) { if (ch !== _B58_ALPHA[0]) break; bytes.unshift(0); }
  return new Uint8Array(bytes);
}
