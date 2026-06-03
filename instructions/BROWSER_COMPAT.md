# WellFair — Browser Compatibility Notes

## Audit results (as of 2026-05-30)

### Gun write audit
All Gun writes go to the `wf-v1-signal/` namespace (signalling only). No writes to `core/` or any
other namespace. No health data ever reaches Gun relay nodes. Specifically:

| Site | Write | Purpose |
|------|-------|---------|
| `connector/index.html` | `node.put({ offer, created })` | SDP offer broadcast |
| `connector/index.html` | `node.put({ offer: null, created: null })` | Offer cleanup post-answer |
| `connector/index.html` | `node.get('answer').put({ sdp: null })` | Answer cleanup post-handshake |
| `pair.html` | `node.get('answer').put({ sdp, t })` | SDP answer |
| `pair.html` | `node.get('answer').put({ sdp: null, t: null })` | Answer cleanup post-handshake |
| `pair.html` | `gunSessionNode.put(null)` | Full session teardown (TTL / disconnect) |

**Verdict: CLEAN.** SEA encryption is not required for these signalling blobs because they contain
only WebRTC SDP and session IDs — no health data.

### Connector storage audit
Zero calls to `localStorage`, `sessionStorage`, or `IndexedDB` in `docs/connector/index.html`.
Session keys and vault data are held only in JS heap variables and are nulled in `teardown()`.

**Verdict: CLEAN.**

---

## Test matrix (to be completed on real devices)

| Browser / OS | WebRTC DataChannel | Camera QR scan | PWA install | Backgrounding | Status |
|---|---|---|---|---|---|
| Chrome Desktop (latest) | expected ✓ | N/A | N/A | N/A | not yet tested |
| Firefox Desktop (latest) | Ed25519 WebCrypto — check | N/A | N/A | N/A | not yet tested |
| Android Chrome | expected ✓ | expected ✓ | expected ✓ | check | not yet tested |
| iOS 17 Safari | check DataChannel | check camera | check PWA add | check BFCache | not yet tested |
| iOS 16.4 Safari | check DataChannel | check camera | check PWA add | check BFCache | not yet tested |

### Known risks / things to verify

- **Firefox**: `Ed25519` key generation (`SubtleCrypto.generateKey`) landed in Firefox 111. Check
  `X25519` support too (landed Firefox 130). If older Firefox must be supported, add detection.
- **iOS Safari backgrounding**: When the vault PWA is backgrounded mid-session, `visibilitychange`
  fires and a 2-minute grace timer starts (via connector). Verify the timer fires correctly and
  `pagehide` teardown works on force-close.
- **iOS PWA**: Home-screen installed PWAs on iOS run in a separate process; camera access requires
  explicit permission re-grant. Test `Html5Qrcode` camera initialisation.
- **iOS Wake Lock**: `navigator.wakeLock` is supported from iOS 16.4. Verify screen stays active
  during a serving session on both 16.4 and 17.
- **Android Chrome PWA**: `manifest.webmanifest` is wired; verify "Add to Home Screen" prompt
  appears and `start_url: /pair.html` loads correctly when launched from launcher.
- **SURB stress test**: Simulate poor connectivity (airplane mode then reconnect) while Nym is
  active to verify SURB pool replenishment and fragment reassembly buffer expiry.

---

## iOS backgrounding / Sanctuary check-in interaction

If the vault PWA is force-closed on iOS while a DMS check-in is pending:
- The `pagehide` handler fires → `endSession(false)` → `teardown()` — session keys zeroed.
- `dmsTimer` is cleared in `pagehide` listener (`clearTimeout(dmsTimer)`).
- **Question**: should a force-close count as a missed DMS check-in? Current behaviour: no —
  the timer is cancelled. If desired, the timer would need to persist via a Service Worker
  background sync or a server-side tombstone — deferred to a future milestone.

---

*Update this file as real-device testing is completed.*
