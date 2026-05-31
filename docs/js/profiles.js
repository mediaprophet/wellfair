'use strict';

// ── Profile loading, rendering, and emergency pre-auth ────────────────────────
// Used by webconnect.html only.

let profiles             = [];
let activeProfile        = null;
let allowedSections      = new Set();
let preAuthorizedProfiles = new Set();

async function loadProfiles() {
  try {
    const res = await fetch('/profiles/profiles.json');
    const data = await res.json();
    profiles = data.profiles;
  } catch (_) {
    profiles = [];
  }
}

function renderProfileList() {
  const list = document.getElementById('profile-list');
  list.innerHTML = '';

  const normals    = profiles.filter(p => !p.emergencyOnly);
  const emergencies = profiles.filter(p => p.emergencyOnly);

  normals.forEach(p => list.appendChild(makeProfileCard(p)));

  if (emergencies.length) {
    const divider = document.createElement('div');
    divider.style.cssText = 'font-size:.72rem;font-weight:600;text-transform:uppercase;' +
      'letter-spacing:.06em;color:var(--red);margin:.875rem 0 .4rem;';
    divider.textContent = 'Emergency access (pre-authorised)';
    list.appendChild(divider);
    emergencies.forEach(p => list.appendChild(makeProfileCard(p)));
  }
}

function makeProfileCard(profile) {
  const card = document.createElement('div');
  card.className = 'profile-card' + (profile.emergencyOnly ? ' emergency-card' : '');

  const credLabel = {
    'none':                          '',
    'personal_pin':                  'PIN required',
    'emergency_responder_vc':        'Emergency responder VC',
    'clinical_professional_vc':      'Clinical VC',
    'mental_health_practitioner_vc': 'MH practitioner VC',
    'social_worker_vc':              'Social worker VC'
  }[profile.credentialRequired] || profile.credentialRequired;

  const badgeClass = profile.emergencyOnly ? 'emergency'
    : profile.credentialRequired === 'personal_pin' ? 'pin' : '';

  card.innerHTML = `
    <div class="profile-icon">${profile.icon || '👤'}</div>
    <div class="profile-info">
      <div class="profile-name">${profile.label}</div>
      <div class="profile-desc">${profile.description || ''}</div>
      ${credLabel ? `<span class="profile-badge ${badgeClass}">${credLabel}</span>` : ''}
    </div>`;
  card.onclick = () => selectProfile(profile);
  return card;
}

function selectProfile(profile) {
  activeProfile = profile;

  if (profile.emergencyOnly) {
    if (preAuthorizedProfiles.has(profile.id)) {
      autoApproveEmergency(profile);
    } else {
      document.getElementById('emergency-warning').style.display = 'block';
      _buildConsentStep(profile);
      showStep('step-consent');
    }
    return;
  }

  if (profile.isOwner || profile.credentialRequired === 'personal_pin') {
    document.getElementById('emergency-warning').style.display = 'none';
    showStep('step-pin');
    return;
  }

  document.getElementById('emergency-warning').style.display = 'none';
  _buildConsentStep(profile);
  showStep('step-consent');
}

function _buildConsentStep(profile) {
  const pill = document.getElementById('consent-profile-pill');
  pill.innerHTML = `<div class="profile-pill" style="background:${profile.color || '#6c757d'}">
    ${profile.icon || '👤'} ${profile.label}
  </div>`;

  document.getElementById('consent-sid').textContent = currentSid ? currentSid.slice(0, 16) + '…' : '—';

  const checklist = document.getElementById('section-checklist');
  checklist.innerHTML = '';
  (profile.sections || []).forEach(sectionId => {
    const li = document.createElement('li');
    li.innerHTML = `
      <input type="checkbox" id="chk-${sectionId}" checked />
      <label for="chk-${sectionId}">${SECTION_LABELS[sectionId] || sectionId}</label>`;
    checklist.appendChild(li);
  });
}

function autoApproveEmergency(profile) {
  allowedSections = new Set(profile.sections || []);
  sessionActive   = true;
  serveStart      = Date.now();
  acquireWakeLock();

  document.getElementById('serve-sid').textContent = currentSid ? currentSid.slice(0, 16) + '…' : '—';
  const bar = document.getElementById('active-profile-bar');
  bar.style.background = profile.color || '#dc3545';
  bar.textContent = (profile.icon || '🚨') + '  ' + profile.label + ' (emergency)';

  showStep('step-serving');

  serveTimer = setInterval(() => {
    const s = Math.floor((Date.now() - serveStart) / 1000);
    document.getElementById('serve-timer').textContent =
      String(Math.floor(s/60)).padStart(2,'0') + ':' + String(s%60).padStart(2,'0');
  }, 1000);

  sessionTtlTimer = setTimeout(() => {
    if (gunSessionNode) { gunSessionNode.put(null); gunSessionNode = null; }
    endSession(true);
  }, SESSION_TTL_MS);

  if (dc && dc.readyState === 'open') {
    secureSend({
      type: 'session_info',
      vault_did: vaultDidKey ? vaultDidKey.did : 'did:key:pending',
      profile: { id: profile.id, label: profile.label,
        color: profile.color, icon: profile.icon, emergencyOnly: true },
      sections: [...allowedSections]
    });
  }
}

// ── Emergency pre-auth panel ──────────────────────────────────────────────────

function showPreauthPanel() {
  const panel = document.getElementById('emergency-preauth-panel');
  if (!panel) return;
  panel.style.display = 'block';
  const list = document.getElementById('preauth-checklist');
  list.innerHTML = '';
  profiles.filter(p => p.emergencyOnly).forEach(p => {
    const li = document.createElement('li');
    li.style.cssText = 'display:flex;align-items:center;gap:.5rem;padding:.2rem 0';
    li.innerHTML = `
      <input type="checkbox" id="preauth-${p.id}"
             ${preAuthorizedProfiles.has(p.id) ? 'checked' : ''}
             onchange="togglePreauth('${p.id}', this.checked)" />
      <label for="preauth-${p.id}" style="cursor:pointer;font-size:.82rem;margin:0">
        ${p.icon} ${p.label}
      </label>`;
    list.appendChild(li);
  });
}

function togglePreauthPanel() {
  const body = document.getElementById('emergency-preauth-body');
  if (body.style.display === 'none') {
    showPreauthPanel();
    body.style.display = 'block';
  } else {
    body.style.display = 'none';
  }
}

function togglePreauth(profileId, enabled) {
  if (enabled) preAuthorizedProfiles.add(profileId);
  else         preAuthorizedProfiles.delete(profileId);
}
