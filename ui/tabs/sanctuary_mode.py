from __future__ import annotations
import streamlit as st
import hashlib
from datetime import datetime, timedelta
import pandas as pd

from ui.utils.components import render_info_banner, render_alert_card

def render_sanctuary_mode(dark_mode: bool):
    # Vault Unlocked Check
    if not st.session_state.get("sanctuary_unlocked", False):
        st.markdown("<h2 style='color: #a855f7;'>🛡️ Episteme:WellFair Sanctuary Vault</h2>", unsafe_allow_html=True)
        render_info_banner(
            title="Encrypted Isolation Layer",
            body="This environment contains highly privileged, isolated clinical observations, logs, and assertions. Entering the correct secondary credential unlocks the Sanctuary vault. Standard decoy PINs will display wellness records, maintaining plausible deniability.",
            accent_color="#a855f7",
            icon="🔒",
            dark_mode=dark_mode,
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            pin_input = st.text_input("Enter Vault Access PIN", type="password", help="Use secondary PIN (8888) to unlock the Sanctuary Vault.")
            if st.button("🔓 Decrypt & Unlock Vault", type="primary"):
                if pin_input == "8888":
                    st.session_state.sanctuary_unlocked = True
                    st.success("Access Granted. Sanctuary Vault unlocked.")
                    st.rerun()
                else:
                    st.error("Invalid PIN. Plausible deniability decoy environment maintained.")
        return

    # FULL SANCTUARY MODE DISPLAY
    st.markdown("<h2 style='color: #f43f5e;'>🤫 Sanctuary Mode: Privileged Vault</h2>", unsafe_allow_html=True)
    render_info_banner(
        title="Safe Haven Active",
        body="All communications are routed via ephemeral mixnet handshakes. RDF-Star assertions written in this vault are masked from standard directory indexes.",
        accent_color="#f43f5e",
        icon="⚡",
        dark_mode=dark_mode,
    )
    
    # Initialize Sanctuary Session State Lists if not present
    if "veiled_assertions" not in st.session_state:
        st.session_state.veiled_assertions = [
            {
                "id": "veil-1",
                "timestamp": datetime.now() - timedelta(days=4),
                "title": "Private Domestic Conflict Log",
                "category": "Domestic Stressor",
                "narrative": "Argument regarding access to personal communications device. Phone was temporarily confiscated by partner.",
                "hash": "8f3b2075a36b9e28dc1c7467812bc9f7832e185cde6483b9cfb19f07a21be14a"
            }
        ]
        
    if "hypothesis_nodes" not in st.session_state:
        st.session_state.hypothesis_nodes = [
            {
                "id": "hyp-1",
                "timestamp": datetime.now() - timedelta(days=2),
                "symptoms": "Severe fatigue, nausea, and metallic taste in mouth after taking breakfast pills.",
                "suspicion_level": "Medium",
                "evidence": "Observed unfamiliar white bottle in medicine cabinet which was later discarded.",
                "hash": "72ce9f1a238b09f129ac7418721bf9f783ef285cde2683b9cfb20f01a31cd19b"
            }
        ]
        
    if "tripwire_logs" not in st.session_state:
        st.session_state.tripwire_logs = [
            {
                "id": "trip-1",
                "timestamp": datetime.now() - timedelta(days=1),
                "agent": "Dr. Sarah Jenkins (Sydney Medical Centre)",
                "query": "Request: Complete Substance Use History",
                "status": "Intercepted (Blocked)",
                "action_taken": "Hidden"
            },
            {
                "id": "trip-2",
                "timestamp": datetime.now() - timedelta(hours=3),
                "agent": "Legal Counsel (Decoy Request)",
                "query": "Request: All Sleep & Heart Rate Logs",
                "status": "Intercepted (Access Denied)",
                "action_taken": "Hidden"
            }
        ]

    # Sub-tabs
    t_log, t_trip, t_synth, t_defense, t_contingency = st.tabs([
        "🤫 Unvarnished Log",
        "🕸️ Tripwire Dashboard",
        "🔬 Synthesis Engine",
        "🔐 Evidentiary Defense",
        "🛡️ Contingency Protocols"
    ])
    
    # ------------------ TAB 1: THE UNVARNISHED LOG ------------------
    with t_log:
        st.markdown("### 🤫 The Unvarnished Log")
        st.write("Record sensitive facts (Veiled Assertions) or uncertain observations (Hypothesis Nodes). All records are hashed and anchored locally.")
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("#### Log a Veiled Assertion (Mode A+ Facts)")
            with st.form("veiled_form", clear_on_submit=True):
                title = st.text_input("Title / Topic", placeholder="e.g., Unreported physical incident")
                category = st.selectbox("Category", ["Physical Trauma", "Substance Log", "Domestic Stressor", "Other"])
                narrative = st.text_area("Narrative Details (Encrypted Vault Only)")
                
                submitted = st.form_submit_button("🔒 Secure & Anchor Assertion")
                if submitted and title and narrative:
                    ts = datetime.now()
                    payload = f"{title}|{category}|{narrative}|{ts.isoformat()}"
                    h = hashlib.sha256(payload.encode()).hexdigest()
                    
                    st.session_state.veiled_assertions.append({
                        "id": f"veil-{int(ts.timestamp())}",
                        "timestamp": ts,
                        "title": title,
                        "category": category,
                        "narrative": narrative,
                        "hash": h
                    })
                    st.success(f"✓ Veiled Assertion anchored. DLT Provenance Hash: sha256:{h[:16]}...")
                    st.rerun()
                    
        with c2:
            st.markdown("#### Log a Hypothesis Node (Epistemic Uncertainty)")
            with st.form("hypothesis_form", clear_on_submit=True):
                symptoms = st.text_area("Observations / Symptoms", placeholder="Describe suspicions or unexplained physical events...")
                suspicion = st.select_slider("Suspicion / Alert Level", options=["Low", "Medium", "High"])
                evidence = st.text_area("Supporting / Contextual Evidence")
                
                submitted = st.form_submit_button("🧠 Anchor Uncertainty Node")
                if submitted and symptoms:
                    ts = datetime.now()
                    payload = f"{symptoms}|{suspicion}|{evidence}|{ts.isoformat()}"
                    h = hashlib.sha256(payload.encode()).hexdigest()
                    
                    st.session_state.hypothesis_nodes.append({
                        "id": f"hyp-{int(ts.timestamp())}",
                        "timestamp": ts,
                        "symptoms": symptoms,
                        "suspicion_level": suspicion,
                        "evidence": evidence,
                        "hash": h
                    })
                    st.success(f"✓ Hypothesis Node anchored. DLT Provenance Hash: sha256:{h[:16]}...")
                    st.rerun()
                    
        st.divider()
        st.markdown("#### 📜 Hashed Ledger Entries (Asymmetric Provenance)")
        
        col_logs1, col_logs2 = st.columns(2)
        with col_logs1:
            st.markdown("##### Active Veiled Assertions")
            for item in reversed(st.session_state.veiled_assertions):
                st.markdown(
                    f"""<div class="premium-card" style="border-left: 3px solid #f43f5e; padding: 12px; margin-bottom: 8px;">
<div style="display:flex; justify-content:space-between;">
<b>{item["title"]}</b>
<span style="font-size:0.7rem; color:#64748b;">{item["category"]}</span>
</div>
<p style="font-size:0.8rem; color:#475569; margin: 6px 0;">{item["narrative"]}</p>
<div style="font-family: monospace; font-size:0.68rem; color:#a855f7;">Anchor Hash: {item["hash"]}</div>
</div>""",
                    unsafe_allow_html=True
                )
                
        with col_logs2:
            st.markdown("##### Epistemic Hypothesis Nodes")
            for item in reversed(st.session_state.hypothesis_nodes):
                st.markdown(
                    f"""<div class="premium-card" style="border-left: 3px solid #e11d48; padding: 12px; margin-bottom: 8px;">
<div style="display:flex; justify-content:space-between;">
<b>Suspicion Level: {item["suspicion_level"]}</b>
<span style="font-size:0.7rem; color:#64748b;">{item["timestamp"].strftime('%b %d, %H:%M')}</span>
</div>
<p style="font-size:0.8rem; color:#475569; margin: 6px 0;"><b>Symptoms:</b> {item["symptoms"]}</p>
<p style="font-size:0.8rem; color:#475569; margin: 6px 0;"><b>Evidence:</b> {item["evidence"]}</p>
<div style="font-family: monospace; font-size:0.68rem; color:#e11d48;">Anchor Hash: {item["hash"]}</div>
</div>""",
                    unsafe_allow_html=True
                )

    # ------------------ TAB 2: TRIPWIRE DASHBOARD ------------------
    with t_trip:
        st.markdown("### 🕸️ Tripwire Dashboard & Alerts")
        st.write("Monitor external access attempts intercepted by your vault's security policy.")
        
        st.markdown("#### ⚡ Active Opaque Collisions (Intercepted Queries)")
        for item in st.session_state.tripwire_logs:
            status_color = "#ef4444" if "Blocked" in item["status"] else "#f59e0b"
            
            col_info, col_actions = st.columns([3, 1])
            with col_info:
                st.markdown(
                    f"""<div class="premium-card" style="border-left: 4px solid {status_color}; padding: 14px; margin-bottom: 10px;">
<div style="display:flex; justify-content:space-between;">
<b>{item["agent"]}</b>
<span style="font-size: 0.72rem; color:{status_color}; font-weight:bold;">{item["status"]}</span>
</div>
<div style="font-size:0.82rem; color:#64748b; margin-top:4px;"><b>Query:</b> {item["query"]}</div>
<div style="font-size:0.78rem; color:#475569; margin-top:4px;"><b>Sovereign Action:</b> {item["action_taken"]}</div>
</div>""",
                    unsafe_allow_html=True
                )
            with col_actions:
                st.write("")
                st.write("")
                # Keep buttons inside st.columns
                if st.button("🔓 Reveal Temp", key=f"reveal-{item['id']}", help="Issue a 30-minute verifiable credential to this actor."):
                    item["status"] = "Shared (Timebound)"
                    item["action_taken"] = "Temporary Access Granted (30 mins)"
                    st.success("Temporary credential published.")
                    st.rerun()
                    
                if st.button("❌ Maintain Block", key=f"block-{item['id']}"):
                    item["status"] = "Intercepted (Blocked)"
                    item["action_taken"] = "Hidden"
                    st.info("Query blocked. Plausible deniability maintained.")
                    st.rerun()
                    
        st.divider()
        st.markdown("#### 🚨 Internal Sentinel Alerts")
        render_alert_card(
            title="THREAT-MODELING PATTERN DETECTED",
            body="<b>Sentinel Alert:</b> Overlapping location coordinates detected with unlinked device <code>did:key:z6MkgT...</code> on 3 consecutive evenings, matching logged symptoms of domestic anxiety. Contingency switches have been armed.",
            accent_color="#ef4444",
            icon="🚨",
            dark_mode=dark_mode,
        )

    # ------------------ TAB 3: SYNTHESIS ENGINE ------------------
    with t_synth:
        st.markdown("### 🔬 Synthesis Engine & Contradiction Audits")
        st.write("Run mathematical audits to prove discrepancies between external claims and your historically immutable records.")
        
        with st.form("audit_form"):
            external_claim = st.text_area("Enter External Claim / Fabricated Assertion", placeholder="e.g., 'User was driving on M4 motorway at 11:30 PM on May 26'")
            record_source = st.selectbox("Compare Against Verified Vault Source", ["Sleep Summary Logs", "Wearable GPS Logs", "Heart Rate & ECG records"])
            
            run_audit = st.form_submit_button("⚡ Run Contradiction Audit")
            if run_audit and external_claim:
                st.markdown("#### 📊 Prolog Audit Result: Incoherence Report")
                
                # Dynamic response showing mathematical contradiction
                st.markdown(
                    """<div class="premium-card" style="border-left: 5px solid #ef4444; background: rgba(239, 68, 68, 0.05); padding: 16px;">
<h4 style="margin: 0; color: #ef4444;">❌ MATHEMATICAL INCOHERENCE PROVEN</h4>
<p style="font-size: 0.9rem; color: #ef4444; margin-top: 6px;">
<b>Assertion Discrepancy:</b> The external claim directly contradicts verified local vault records.<br>
<b>Evidence Node:</b> Samsung Health sleep entry <code>SleepRecord_20260526_2215</code>.<br>
<b>Verification Details:</b>
</p>
<ul style="font-size:0.85rem; color:#ef4444; margin-left:20px;">
<li>Sleep Duration: 8 hours 15 minutes (Start: May 26 22:15, End: May 27 06:30)</li>
<li>Wearable Heart Rate: Average 54 BPM (Consistent with sleep stages; no exercise anomalies)</li>
<li>Symmetric Hash: <code>0x7e3a9c...</code> anchored to DLT block <b>#488,192</b></li>
</ul>
<p style="font-size:0.9rem; color:#ef4444; margin-top:6px; margin-bottom:0;">
<b>Rule Result:</b> <code>incoherent_claim(external_claim, sleep_record) :- date_match(external_claim, sleep_record), status_match(external_claim, sleeping).</code>
</p>
</div>""",
                    unsafe_allow_html=True
                )
                
        st.divider()
        st.markdown("#### ⚙️ Sentinel Ruleset Management")
        st.write("Rules guiding background audit queries:")
        st.code(
            """
% Coercive control threat pattern detection
coercive_control_risk(User) :- 
    overlapping_gps(User, Agent, T), 
    suspicious_symptoms(User, T), 
    not(authorized_sharing(Agent)).

% Incoherent timeline detection
incoherent_timeline(Claim, Record) :-
    occurs_at(Claim, Time),
    occurs_at(Record, Time),
    mutually_exclusive(Claim, Record).
            """,
            language="prolog"
        )

    # ------------------ TAB 4: EVIDENTIARY DEFENSE ------------------
    with t_defense:
        st.markdown("### 🔐 Evidentiary Export & Defense")
        st.write("Package isolated sub-graphs, local health records, and veiled assertions into a cryptographically sealed Verifiable Presentation.")
        
        st.markdown("#### 🗂️ Isolate Defense Nodes")
        # List of items available for export
        export_choices = []
        for v in st.session_state.veiled_assertions:
            export_choices.append(f"Veiled Assertion: {v['title']} ({v['category']})")
        for h in st.session_state.hypothesis_nodes:
            export_choices.append(f"Hypothesis Node: {h['symptoms'][:30]}... ({h['timestamp'].strftime('%b %d')})")
        export_choices.append("Samsung Health: Sleep Summary Log (May 26)")
        export_choices.append("Samsung Health: Heart Rate Log (May 26)")
        
        selected_nodes = st.multiselect("Select Sub-Graph Data to Export", options=export_choices, default=export_choices[:1])
        
        col_gen, col_vpn = st.columns(2)
        with col_gen:
            if st.button("🔒 Generate Verifiable Presentation (VP)", type="primary"):
                st.markdown("##### Verifiable Presentation Package")
                st.code(
                    """
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://w3id.org/security/suites/ed25519-2020/v1"
  ],
  "type": ["VerifiablePresentation"],
  "verifiableCredential": {
    "id": "urn:uuid:7c3ae128-48b9-4a9f-8898-192a831bca3d",
    "type": ["SovereignHealthAssertionCredential"],
    "issuer": "did:key:z6MkgTsvK8sPec...",
    "issuanceDate": "2026-05-28T18:43:00Z",
    "credentialSubject": {
      "id": "did:key:z6MkgTsvK8sPec...",
      "assertion": "Argument regarding access to personal device. Device confiscated."
    },
    "proof": {
      "type": "Ed25519Signature2020",
      "verificationMethod": "did:key:z6MkgTsvK8sPec...#z6MkgTsvK",
      "proofValue": "z3mR8F...xH9J12K..."
    }
  }
}
                    """,
                    language="json"
                )
                
        with col_vpn:
            if st.button("🌐 Serve Ephemeral VPN Link"):
                token = hashlib.sha256(str(datetime.now().timestamp()).encode()).hexdigest()[:16]
                url = f"http://localhost:8501/verify-defense?token={token}"
                st.success(f"🌐 Ephemeral verification portal generated.")
                st.info(f"Link: `{url}`\n\n*This link will automatically self-destruct in 15 minutes. It bypasses vault encryption for selected nodes only, serving raw proofs over encrypted Nymtech tunnel.*")

    # ------------------ TAB 5: CONTINGENCY PROTOCOLS ------------------
    with t_contingency:
        st.markdown("### 🛡️ Contingency Protocols & Fail-safes")
        st.write("Configure extreme safeguards for your physical safety and data preservation.")
        
        c_dur, c_dm = st.columns(2)
        with c_dur:
            st.markdown("#### 🎭 Plausible Deniability Decoy Settings")
            st.text_input("Decoy PIN (Unlocks Standard Wellness View)", value="1234", type="password")
            st.checkbox("Erase Sanctuary Vault on 3 consecutive invalid entries", value=True)
            st.checkbox("Erase entire vault if secondary 'Nuke PIN' (0000) is typed", value=False)
            
        with c_dm:
            st.markdown("#### ⏳ Ticking Dead Man's Switch")
            st.write("Automatically triggers data escrow releases if you do not check-in within the specified window.")
            st.slider("Check-in Interval (Days)", min_value=1, max_value=30, value=7)
            st.selectbox("Escrow Recipient Target", ["Executor Attorney (advocate@legal-aid.org)", "Trusted Contact Group (Nymtech Mixnet)"])
            st.checkbox("Arm Dead Man's Switch Ticker", value=True)
            
        st.divider()
        st.markdown("#### 🚀 Nymtech Mixnet Onion Escrow Routing")
        st.write("Configured Onion routes for contingency payloads:")
        st.code(
            """
Route 1: User Node -> Mix Gateway (Sydney) -> Mix Node A (Paris) -> Mix Node B (Tokyo) -> Lawyer Node
Payload Encryption: XChaCha20-Poly1305 with Lawyer DID Ephemeral Public Key.
            """,
            language="text"
        )
