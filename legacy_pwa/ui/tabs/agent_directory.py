from __future__ import annotations
import streamlit as st
import textwrap
from datetime import datetime, timedelta
from src.phr_models.agents import ActorType, Actor, DelegationRule, VerificationStatus, evaluate_access
from src.phr_models.proxy_consent import PrivacyMode, LegalBasis
from src.phr_models.pathology import DiagnosticReport, PathologyObservation, DiagnosticReportStatus
from src.phr_models.psychiatry import PsychiatryObservation, ObservationContext

def render_agent_directory(dark_mode: bool, normalized: dict):
    st.markdown("## 👥 Agent Directory & Delegation Manager")
    
    st.markdown(
        """
        <div class="premium-card" style="border-left: 5px solid #7c3aed; margin-bottom: 20px;">
            <h4 style="margin: 0; color: #7c3aed;">👥 Identity & Delegation Control Panel</h4>
            <p style="font-size: 0.9rem; color: #64748b; margin-top: 5px; margin-bottom: 0;">
                Manage verified organizations, practitioners, personal delegates, and synthetic AI agents. Authorize and configure granular access delegations with legal consents, whitelists, and real-time policy simulations.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Initialize session states
    if "directory_actors" not in st.session_state or "delegation_rules" not in st.session_state:
        # Fallback if not initialized by init_mock_data
        from ui.utils import init_mock_data
        init_mock_data()
        
    actors = st.session_state.directory_actors
    rules = st.session_state.delegation_rules
    
    tab_catalog, tab_rules, tab_sharing, tab_comms, tab_emergency, tab_simulator = st.tabs([
        "👥 Actor Directory",
        "🛡️ Delegation Policies",
        "🛡️ Proxy & Sharing Control",
        "💬 Secure Communications",
        "🚨 Emergency & Failsafes",
        "🎛️ Access Policy Simulator"
    ])
    
    # ------------------ TAB 1: ACTOR DIRECTORY ------------------
    with tab_catalog:
        st.markdown("### 📋 Active Actor Catalog")
        
        # Display existing actors in a clean grid
        for idx, a in enumerate(actors):
            type_colors = {
                ActorType.ORGANIZATION: "#3b82f6",  # Blue
                ActorType.PRACTITIONER: "#0d9488",  # Teal
                ActorType.DELEGATE: "#f59e0b",      # Amber
                ActorType.SYNTHETIC_AGENT: "#7c3aed" # Purple
            }
            color = type_colors.get(a.actor_type, "#64748b")
            
            with st.container():
                st.markdown(
                    f"""<div class="premium-card" style="border-left: 4px solid {color}; padding: 16px; margin-bottom: 12px;">
<div style="display: flex; justify-content: space-between; align-items: center;">
<h4 style="margin: 0; color: {color}; font-size: 1.15rem;">
{a.name} 
<span style="font-size: 0.75rem; background: {color}22; color: {color}; padding: 2px 8px; border-radius: 20px; font-weight: bold; margin-left: 8px;">
{a.actor_type.value.upper()}
</span>
</h4>
<span style="font-size: 0.75rem; color: #10b981; font-weight: bold;">
{'✅ VERIFIED' if a.verification_status == VerificationStatus.VERIFIED else '⚠️ SELF CLAIMED'}
</span>
</div>
<div style="font-size: 0.85rem; color: #64748b; margin-top: 6px;">
{f"<b>Organization:</b> {a.organization} | " if a.organization else ""}<b>DID:</b> <code style="font-size: 0.75rem;">{a.did_uri or 'None'}</code>
</div>
<div style="margin-top: 8px;">
<span style="font-size: 0.8rem; font-weight: bold; color: #475569;">Roles: </span>
{" ".join([f"<span style='font-size: 0.75rem; background: rgba(0,0,0,0.04); padding: 2px 6px; border-radius: 4px; margin-right: 4px;'>{r}</span>" for r in a.roles])}
</div>
<div style="margin-top: 6px;">
<span style="font-size: 0.8rem; font-weight: bold; color: #475569;">Credentials / Qualifications: </span>
{" | ".join([f"<i style='font-size: 0.75rem;'>{q}</i>" for q in a.qualifications]) or "None Declared"}
</div>
</div>""",
                    unsafe_allow_html=True
                )
                
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    with st.expander("📜 Shared Values Agreement"):
                        signed_key = f"agreement_signed_{a.id}"
                        if signed_key not in st.session_state:
                            st.session_state[signed_key] = True if a.verification_status == VerificationStatus.VERIFIED else False
                        
                        is_signed = st.session_state[signed_key]
                        
                        if is_signed:
                            st.success("✓ Signed Shared Values Agreement Active")
                            st.markdown(
                                """
                                <div style="font-size: 0.8rem; color: #475569; background: rgba(0,0,0,0.02); padding: 8px; border-radius: 4px;">
                                    <b>Aligned Instruments:</b><br>
                                    • UN UDHR Art 12 (Privacy Rights)<br>
                                    • UN ICCPR Art 17 (Protection of Privacy)<br>
                                    • NSW Mental Health Act 2007 Principles
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            if st.button("🔴 Unilaterally Revoke Keys (Values Breach)", key=f"revoke_keys_{a.id}_{idx}"):
                                st.session_state[signed_key] = False
                                a.verification_status = VerificationStatus.SELF_CLAIMED
                                for r in rules:
                                    if r.actor_id == a.id:
                                        r.is_active = False
                                st.warning(f"Immediately revoked derivative keys for {a.name} due to suspected values breach!")
                                st.rerun()
                        else:
                            st.warning("⚠️ No Signed Shared Values Agreement found!")
                            if st.button("📜 Sign Shared Values Agreement", key=f"sign_keys_{a.id}_{idx}"):
                                st.session_state[signed_key] = True
                                a.verification_status = VerificationStatus.VERIFIED
                                st.success(f"Signed values agreement with {a.name}!")
                                st.rerun()
                with col_c2:
                    with st.expander("🔑 Credentials & Cryptographic Keys"):
                        st.markdown(
                            f"""
                            <div style="font-family: monospace; font-size: 0.78rem; background: rgba(0,0,0,0.02); padding: 8px; border-radius: 4px; line-height: 1.3;">
                                <b>Root DID:</b><br>{a.did_uri or 'None'}<br>
                                <b>Derivative Key (Insured Scope):</b><br>
                                SHA256: 8a4c3f7e9b01c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7<br>
                                <b>Linked Accreditations:</b><br>
                                • {" | ".join(a.qualifications) if a.qualifications else "Self-declared (Uninsured)"}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                
        st.divider()
        st.markdown("### ➕ Register New Actor")
        
        with st.expander("Register Organization / Practitioner / Delegate / AI Agent"):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Full Name / Organization Name", placeholder="e.g. Dr. Jane Foster")
                new_type = st.selectbox("Actor Type", options=[t for t in ActorType], format_func=lambda x: x.value.upper())
                new_org = st.text_input("Affiliated Organization (Optional)", placeholder="e.g. Royal Prince Alfred Hospital")
            with col2:
                new_did = st.text_input("DID URI (Optional)", placeholder="e.g. did:key:z6Mkp...")
                new_roles_str = st.text_area("Assigned Roles (comma separated)", placeholder="e.g. Primary Care, Health Advocate")
                new_quals_str = st.text_area("Accreditations / Qualifications (comma separated)", placeholder="e.g. M.B.B.S, AHPRA MED99210")
                
            if st.button("💾 Register Actor to Directory", type="primary"):
                if not new_name:
                    st.error("Please provide a valid name.")
                else:
                    roles_list = [r.strip() for r in new_roles_str.split(",") if r.strip()]
                    quals_list = [q.strip() for q in new_quals_str.split(",") if q.strip()]
                    
                    new_actor = Actor(
                        id=f"actor-manual-{int(datetime.now().timestamp())}",
                        actor_type=new_type,
                        name=new_name,
                        organization=new_org or None,
                        qualifications=quals_list,
                        roles=roles_list,
                        verification_status=VerificationStatus.VERIFIED if new_type != ActorType.DELEGATE else VerificationStatus.SELF_CLAIMED,
                        did_uri=new_did or None
                    )
                    st.session_state.directory_actors.append(new_actor)
                    st.success(f"Registered '{new_name}' to Agent Directory successfully!")
                    st.rerun()

    # ------------------ TAB 2: DELEGATION POLICIES ------------------
    with tab_rules:
        st.markdown("### 🛡️ Active Consent & Delegation Policies")
        st.write("Configure maximum sharing boundaries, Whitelist/Blacklist models, and case limits for directory actors.")
        
        for idx, r in enumerate(rules):
            actor_obj = next((a for a in actors if a.id == r.actor_id), None)
            actor_name = actor_obj.name if actor_obj else "Unknown Actor"
            actor_type = actor_obj.actor_type.value if actor_obj else "unknown"
            
            status_lbl = "✅ Active" if r.is_active else "❌ Suspended"
            status_color = "#10b981" if r.is_active else "#64748b"
            
            with st.container():
                st.markdown(
                    f"""<div class="premium-card" style="padding: 16px; margin-bottom: 12px; border-left: 4px solid {status_color};">
<div style="display: flex; justify-content: space-between; align-items: center;">
<h4 style="margin: 0; color: #4f46e5;">Rule {r.id} for {actor_name} ({actor_type.upper()})</h4>
<span style="font-size: 0.78rem; background: {status_color}22; color: {status_color}; padding: 2px 8px; border-radius: 4px; font-weight: bold;">
{status_lbl}
</span>
</div>
<div style="font-size: 0.85rem; color: #475569; margin-top: 6px;">
<b>Legal Basis:</b> <code>{r.legal_basis.value}</code> | 
<b>Max Privacy Clearance:</b> <code>{r.privacy_mode_limit.name} ({r.privacy_mode_limit.value})</code>
</div>
<div style="font-size: 0.82rem; color: #64748b; margin-top: 4px;">
<b>Whitelisted Record Types:</b> {", ".join(r.allowed_record_types) if r.allowed_record_types else "All"} <br>
<b>Restricted Record Types (Blacklist):</b> {", ".join(r.restricted_records) if r.restricted_records else "None"} <br>
<b>Case File Bounds:</b> {", ".join(r.linked_case_ids) if r.linked_case_ids else "Global (No Limit)"}
</div>
</div>""",
                    unsafe_allow_html=True
                )
                
                # Inline action triggers
                c_t1, c_t2 = st.columns(2)
                if r.is_active:
                    if c_t1.button("🔒 Suspend Policy", key=f"susp_{r.id}_{idx}"):
                        r.is_active = False
                        st.rerun()
                else:
                    if c_t1.button("🔓 Activate Policy", key=f"actv_{r.id}_{idx}"):
                        r.is_active = True
                        st.rerun()
                if c_t2.button("🗑️ Revoke Delegation", key=f"revk_{r.id}_{idx}"):
                    rules.pop(idx)
                    st.rerun()
                    
        st.divider()
        st.markdown("### 🛡️ Authorize New Delegation Policy")
        
        with st.expander("Configure Granular Delegation Rules for a Directory Actor"):
            actor_options = {a.id: f"{a.name} ({a.actor_type.value.upper()})" for a in actors}
            
            selected_actor_id = st.selectbox("Select Target Actor", options=list(actor_options.keys()), format_func=lambda x: actor_options[x])
            
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                leg_basis = st.selectbox("Legal Authorization Basis", options=[l for l in LegalBasis], format_func=lambda x: x.value.upper())
                max_priv = st.selectbox("Maximum Privacy Clearance Threshold", options=[p for p in PrivacyMode], format_func=lambda x: f"{x.name} ({x.value})", index=1)
                scope_cases = st.text_input("Limit to Case IDs (comma separated, optional)", placeholder="e.g. case-1, case-2")
            with col_r2:
                whitelist = st.text_input("Allowed Record Types (whitelist, optional)", placeholder="e.g. PathologyObservation, DiagnosticReport")
                blacklist = st.text_input("Restricted Record Types (blacklist, optional)", placeholder="e.g. PsychiatricObservation, MedicationAdministration")
                roles_del = st.text_input("Assigned Delegation Roles (comma separated)", placeholder="e.g. read_clinical_records")
                
            if st.button("💾 Authorize Delegation Rule", type="primary"):
                w_list = [w.strip() for w in whitelist.split(",") if w.strip()]
                b_list = [b.strip() for b in blacklist.split(",") if b.strip()]
                c_list = [c.strip() for c in scope_cases.split(",") if c.strip()]
                roles_list = [d.strip() for d in roles_del.split(",") if d.strip()]
                
                new_rule = DelegationRule(
                    id=f"rule-manual-{int(datetime.now().timestamp())}",
                    patient_id="patient-self",
                    actor_id=selected_actor_id,
                    granted_roles=roles_list,
                    legal_basis=leg_basis,
                    privacy_mode_limit=max_priv,
                    allowed_record_types=w_list,
                    restricted_records=b_list,
                    linked_case_ids=c_list,
                    is_active=True
                )
                st.session_state.delegation_rules.append(new_rule)
                st.success("Authorized new delegation policy successfully!")
                st.rerun()

    # ------------------ TAB 3: PROXY & SHARING CONTROL ------------------
    with tab_sharing:
        from ui.tabs.proxy_sharing import render_proxy_sharing
        render_proxy_sharing(dark_mode)



    # ------------------ TAB 5: SECURE COMMUNICATIONS ------------------
    with tab_comms:
        st.markdown("### 💬 Secure Ephemeral Communications Matrix")
        st.write("Route messages and attachments anonymously through the Nymtech mixnet with zero metadata leakage, bound by dynamic, point-in-time cryptographic constraints.")
        
        st.divider()
        
        # Connection Settings
        c_col1, c_col2 = st.columns([1, 1])
        
        with c_col1:
            st.markdown("#### 🛡️ Transport & Routing Layer")
            nym_enabled = st.toggle("Enable Ephemeral Mixnet Routing (Nymtech)", value=True, key="comms_nym_enabled")
            
            if nym_enabled:
                st.markdown(
                    """
                    <div style="background: rgba(13, 148, 136, 0.05); border: 1px solid rgba(13, 148, 136, 0.1); padding: 12px; border-radius: 8px; font-size: 0.85rem;">
                        <span style="color: #0d9488; font-weight: bold;">🟢 NYM MIXNET ROUTING ACTIVE</span><br>
                        <b>Active Gateway:</b> <code>198.51.100.4 (Sydney_Node)</code><br>
                        <b>Mix Hops:</b> <code>Hop 1 (Mix) -> Hop 2 (Mix) -> Hop 3 (Mix)</code><br>
                        <b>Packet Obfuscation:</b> Active (Cover Traffic Loop Enabled)<br>
                        <b>Metadata Leakage Risk:</b> <span style="color: #10b981; font-weight: bold;">0.00%</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    """
                    <div style="background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.1); padding: 12px; border-radius: 8px; font-size: 0.85rem;">
                        <span style="color: #ef4444; font-weight: bold;">🔴 DIRECT IP CONNECTION (INSECURE)</span><br>
                        <b>Route:</b> Direct HTTP/WS Transport<br>
                        <b>Metadata Leakage Risk:</b> <span style="color: #ef4444; font-weight: bold;">HIGH (IP & Timing correlation vulnerable)</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            st.markdown("#### 🤝 Ephemeral Session Handshake")
            st.markdown(
                """
                <div style="font-size: 0.85rem; line-height: 1.4;">
                    ✓ <b>DID Handshake:</b> Exchange authenticated DID signatures. (Completed)<br>
                    ✓ <b>Role Credentials Verification:</b> Insured qualifications checked. (Completed)<br>
                    ✓ <b>Shared Values Agreement:</b> Covenants verified. (Completed)<br>
                    🟢 <b>Session Active:</b> Decryption keys rotated.
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with c_col2:
            st.markdown("#### 🔒 Shared Asset & Dynamic Policy Generator")
            
            asset_to_share = st.selectbox(
                "Select Asset to Attach & Wrap:",
                options=["Pathology Report (Lipid Panel, 2026)", "Sleep & Snoring wearable data log (CSV)", "Psychiatric Mood Observation log"],
                key="share_asset_sel"
            )
            
            # Constraint options
            st.caption("Apply Dynamic Constraints:")
            timebound = st.slider("Temporal Bounds (Access Duration Limit)", min_value=1, max_value=48, value=4, format="%d hours", key="share_timebound")
            
            geofence_enabled = st.checkbox("Force Geofencing (Allowed Recipient Location)", value=True, key="share_geofence_enabled")
            if geofence_enabled:
                st.markdown(
                    """
                    <div style="font-size: 0.8rem; color: #4b5563; background: rgba(0,0,0,0.02); padding: 8px; border-radius: 4px; margin-bottom: 8px;">
                        <b>Coordinate Bounding Box:</b> Hospital/Clinic Area<br>
                        • Latitude: <code>[-33.8900, -33.8800]</code><br>
                        • Longitude: <code>[151.2000, 151.2100]</code>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            device_binding_enabled = st.checkbox("Lock to Recipient's Device Hardware DID", value=True, key="share_device_binding")
            
            if st.button("🔒 Generate Encrypted Sharing Container", type="primary", key="btn_gen_sharing_container"):
                st.session_state.sharing_container_generated = True
                
            if st.session_state.get("sharing_container_generated", False):
                st.success("Encrypted container generated and serialized successfully!")
                
                # Render the RDF-Star metadata assertion string
                st.markdown("##### RDF-Star Policy Assertions:")
                st.code(
                    textwrap.dedent(f"""
                    << :User :sharedAsset :Asset_{asset_to_share.split()[0]} >> 
                        :recipientAgent :Doctor_Sarah_Jenkins_DID ;
                        :validUntil "{(datetime.now() + timedelta(hours=timebound)).isoformat()}"^^xsd:dateTime ;
                        :allowedLocation :Hospital_Zone_Sydney_Central ;
                        :deviceBinding "did:web:sydneymedical.com.au:practitioners:sjenkins" ;
                        :allowPrint false ;
                        :exfiltrationDefense :DynamicVisualWatermarking .
                    """),
                    language="turtle"
                )

        st.divider()
        st.markdown("#### 🖥️ Exfiltration Defense Preview (Recipient View)")
        st.write("Simulates how the recipient views the shared record inside their sandboxed view portal. Note the visual watermarking and text-extraction protections.")
        
        # Preview Card with Watermark style
        st.markdown(
            f"""<div class="premium-card" style="position: relative; overflow: hidden; border: 1px solid rgba(220, 38, 38, 0.2); background: rgba(0,0,0,0.02); user-select: none;">
<!-- Watermark Layer -->
<div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; pointer-events: none; opacity: 0.08; font-size: 0.95rem; font-weight: bold; font-family: monospace; display: flex; flex-wrap: wrap; content: 'CONFIDENTIAL'; justify-content: space-around; align-content: space-around; transform: rotate(-15deg); z-index: 10;">
RECIPIENT: did:web:sydneymedical:sjenkins &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; RECIPIENT: did:web:sydneymedical:sjenkins<br>
SESSION: 4f8d-a2f9-9021 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; TIMESTAMP: 2026-05-28 18:30:29 UTC<br>
RECIPIENT: did:web:sydneymedical:sjenkins &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; RECIPIENT: did:web:sydneymedical:sjenkins<br>
</div>
<!-- Content -->
<div style="z-index: 1;">
<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(0,0,0,0.08); padding-bottom: 8px; margin-bottom: 12px;">
<h4 style="margin: 0; color: #475569;">🔬 Pathology Report: Lipid Panel</h4>
<span style="font-size: 0.72rem; color: #ef4444; background: rgba(239, 68, 68, 0.1); padding: 2px 8px; border-radius: 4px; font-weight: bold;">
⚠️ PRINT & COPY DISABLED
</span>
</div>
<table style="width: 100%; font-size: 0.9rem; border-collapse: collapse;">
<tr style="border-bottom: 1px solid rgba(0,0,0,0.04);">
<td style="padding: 6px 0; font-weight: bold; color: #475569;">Biomarker</td>
<td style="padding: 6px 0; font-weight: bold; color: #475569;">Value</td>
<td style="padding: 6px 0; font-weight: bold; color: #475569;">Reference Range</td>
</tr>
<tr style="border-bottom: 1px solid rgba(0,0,0,0.04);">
<td style="padding: 6px 0;">Total Cholesterol</td>
<td style="padding: 6px 0; font-weight: bold; color: #ef4444;">6.1 mmol/L (High)</td>
<td style="padding: 6px 0; color: #64748b;">3.0 - 5.5 mmol/L</td>
</tr>
<tr style="border-bottom: 1px solid rgba(0,0,0,0.04);">
<td style="padding: 6px 0;">HDL Cholesterol</td>
<td style="padding: 6px 0; font-weight: bold; color: #10b981;">1.4 mmol/L</td>
<td style="padding: 6px 0; color: #64748b;">> 1.0 mmol/L</td>
</tr>
<tr>
<td style="padding: 6px 0;">LDL Cholesterol</td>
<td style="padding: 6px 0; font-weight: bold; color: #ef4444;">4.2 mmol/L (High)</td>
<td style="padding: 6px 0; color: #64748b;">< 3.0 mmol/L</td>
</tr>
</table>
</div>
</div>""",
            unsafe_allow_html=True
        )

    # ------------------ TAB 6: EMERGENCY & FAILSAFES ------------------
    with tab_emergency:
        st.markdown("### 🚨 Contingency Protocols & Guardianship Failsafes")
        st.write("Configure autonomous fail-safes, next-of-kin AI proxies, and deadman switches to safeguard your health and assets in emergency or posthumous events.")
        
        st.divider()
        
        em_col1, em_col2 = st.columns(2)
        
        with em_col1:
            st.markdown("#### 🤖 Next of Kin AI Proxy (Digital Good Samaritan)")
            st.write("An autonomous agent trained on your explicit intentions. It acts as a fallback decision support system if you are unresponsive.")
            
            nok_scenario = st.text_area(
                "Simulated Emergency Scenario:",
                value="The user is found unconscious. Central Hospital paramedics request full location history and recent clinical logs to check for drug interactions or cardiac history.",
                height=100
            )
            
            if st.button("🧠 Query Next of Kin AI Proxy", type="primary"):
                st.session_state.nok_query_run = True
                
            if st.session_state.get("nok_query_run", False):
                st.markdown("##### 🤖 Next of Kin AI Evaluation & Action Report:")
                st.markdown(
                    """
                    <div style="background: rgba(124, 58, 237, 0.05); border: 1px solid rgba(124, 58, 237, 0.1); padding: 16px; border-radius: 8px; font-size: 0.9rem;">
                        <span style="color: #7c3aed; font-weight: bold;">📝 INTENTIONS EVALUATION DETECTED:</span><br>
                        <b>Status:</b> Consent evaluated and granted.<br>
                        <b>Predefined Intention Rule:</b> <i>"In life-threatening situations where I am unable to respond, paramedics and hospital staff are granted Mode B access level to clinical and location records."</i><br>
                        <b>Action Taken:</b> Issued temporary, timebound key container bound to <code>did:key:paramedics-sydney-central</code>.<br>
                        <b>Audit Trail:</b> Event logged under session ID <code>audit-nok-9a1c</code>.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
        with em_col2:
            st.markdown("#### ⏳ Deadman Switch & Digital Will")
            
            deadman_active = st.toggle("Enable Deadman Switch Failsafe", value=True)
            
            if deadman_active:
                st.slider("Inactivity Trigger Limit:", min_value=7, max_value=180, value=30, format="%d days")
                st.markdown(
                    """
                    <div style="background: rgba(245, 158, 11, 0.05); border: 1px solid rgba(245, 158, 11, 0.1); padding: 12px; border-radius: 8px; font-size: 0.85rem; margin-bottom: 12px;">
                        <span style="color: #d97706; font-weight: bold;">⏳ SWITCH ARMED & TICKING</span><br>
                        <b>Last Active Ping:</b> 12 hours ago (via mobile sync)<br>
                        <b>Next Trigger Check:</b> in 29 days, 12 hours<br>
                        <b>Verification Check:</b> App will send daily pushes 3 days prior to trigger.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            st.markdown("#### 📜 Digital Will Instructions")
            digital_will_executor = st.text_input("Nominated Digital Executor (DID)", value="did:key:executor-father-john")
            disposal_intentions = st.text_area("Bodily Disposal Intentions", value="Natural organic reduction or green burial, following eco-friendly practices.")
            
            st.caption("Upon switch trigger, execute the following actions:")
            c_act1 = st.checkbox("Delete browser history, private diaries, and chat logs (Wipe Mode A)", value=True)
            c_act2 = st.checkbox("Release pathology reports and clinical record timeline to digital executor", value=True)
            c_act3 = st.checkbox("Publish public journals (Mode C) to public Solid Pod archive", value=False)
            
            if st.button("💾 Save Failsafe Configuration"):
                st.success("Deadman switch and Digital Will settings updated successfully!")

    # ------------------ TAB 7: ACCESS SIMULATOR ------------------
    with tab_simulator:
        st.markdown("### 🎛️ Real-Time Access Control Simulator")
        st.write("Select an Actor, bind their delegation policy, and select a record to test policy evaluations and generate execution logs.")
        
        st.divider()
        
        # Simulator Settings
        sim_col1, sim_col2 = st.columns(2)
        
        with sim_col1:
            st.markdown("#### 1. Actor & Policy Binding")
            actor_map = {a.id: a for a in actors}
            sim_actor_id = st.selectbox(
                "Select Actor to Test",
                options=list(actor_map.keys()),
                format_func=lambda x: f"{actor_map[x].name} ({actor_map[x].actor_type.value.upper()})",
                key="sim_sel_actor"
            )
            
            # Find rules matching actor
            actor_rules = [r for r in rules if r.actor_id == sim_actor_id]
            if not actor_rules:
                st.warning("This Actor has no authorized delegation rules! Simulation will fail automatically.")
                sim_rule = None
            else:
                rule_map = {r.id: r for r in actor_rules}
                sim_rule_id = st.selectbox(
                    "Select Binding Delegation Policy",
                    options=list(rule_map.keys()),
                    format_func=lambda x: f"Rule {x} (Max: {rule_map[x].privacy_mode_limit.name})",
                    key="sim_sel_rule"
                )
                sim_rule = rule_map[sim_rule_id]
                
        with sim_col2:
            st.markdown("#### 2. Target Record Payload")
            
            # Record templates
            record_templates = {
                "lipid_report": "DiagnosticReport — Lipid Panel (Laverty Pathology, Mode B)",
                "cholesterol_obs": "PathologyObservation — Total Cholesterol (Laverty Pathology, Mode B)",
                "depression_obs": "PsychiatryObservation — Depression notes (Sarah Jenkins GP, Mode A)",
                "hiv_obs": "PathologyObservation — HIV Ag/Ab Screen (SSHC, Mode A)"
            }
            
            selected_template = st.selectbox(
                "Select Record Payload to Test",
                options=list(record_templates.keys()),
                format_func=lambda x: record_templates[x],
                key="sim_sel_template"
            )
            
            # Create instance based on selection
            if selected_template == "lipid_report":
                target_record = DiagnosticReport(
                    id="rep-sim-lipid",
                    patient_id="patient-self",
                    date_issued=datetime.now(),
                    status=DiagnosticReportStatus.FINAL,
                    pdf_attachment_uri="vault://docs/lipid-panel.pdf.enc",
                    privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                )
            elif selected_template == "cholesterol_obs":
                target_record = PathologyObservation(
                    id="obs-sim-chol",
                    test_name="Total Cholesterol",
                    value=6.1,
                    unit="mmol/L",
                    reference_range_high=5.5,
                    privacy_mode=PrivacyMode.MODE_B_PRIVILEGED
                )
            elif selected_template == "depression_obs":
                target_record = PsychiatryObservation(
                    id="obs-sim-dep",
                    patient_id="patient-self",
                    date_recorded=datetime.now(),
                    context=ObservationContext.CLINICIAN_OBSERVED,
                    symptom_code="366979004",
                    notes="Patient reports flat affect and low energy.",
                    privacy_mode=PrivacyMode.MODE_A_STRICT
                )
            else:  # hiv_obs
                target_record = PathologyObservation(
                    id="obs-sim-hiv",
                    test_name="HIV Ag/Ab Screen",
                    value=0.08,
                    unit="Index",
                    reference_range_high=0.90,
                    privacy_mode=PrivacyMode.MODE_A_STRICT
                )
                
            st.caption("Inspected target record attributes:")
            st.json({
                "ModelClass": target_record.__class__.__name__,
                "ID": target_record.id,
                "PrivacyMode": target_record.privacy_mode.name if hasattr(target_record, "privacy_mode") else "N/A"
            })
            
        st.divider()
        
        if st.button("🚀 Evaluate Access Policy & Run Simulation", type="primary"):
            if not sim_rule:
                st.error("Access Denied: No binding delegation policy exists for this actor.")
            else:
                actor_obj = actor_map[sim_actor_id]
                
                # Execute evaluation
                allowed, logs = evaluate_access(actor_obj, sim_rule, target_record)
                
                # Render results card
                if allowed:
                    st.markdown(
                        textwrap.dedent("""
                        <div class="premium-card" style="border-left: 5px solid #10b981; background: rgba(16, 185, 129, 0.05); padding: 20px;">
                            <h3 style="margin: 0; color: #10b981;">🔓 ACCESS GRANTED</h3>
                            <p style="font-size: 0.95rem; color: #10b981; margin-top: 5px; margin-bottom: 0; font-weight: bold;">
                                Policy evaluation succeeded. The Actor has authorized access to view this data package.
                            </p>
                        </div>
                        """),
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        textwrap.dedent("""
                        <div class="premium-card" style="border-left: 5px solid #ef4444; background: rgba(239, 68, 68, 0.05); padding: 20px;">
                            <h3 style="margin: 0; color: #ef4444;">🔒 ACCESS DENIED</h3>
                            <p style="font-size: 0.95rem; color: #ef4444; margin-top: 5px; margin-bottom: 0; font-weight: bold;">
                                Policy evaluation failed. The Actor is restricted from reading this data package.
                            </p>
                        </div>
                        """),
                        unsafe_allow_html=True
                    )
                    
                # Audit Trail Log
                st.markdown("#### 📜 Policy Audit Trail Log")
                
                log_html = ""
                for log_line in logs:
                    if "GRANTED" in log_line or "OK:" in log_line:
                        badge = "<span style='color: #10b981; font-weight: bold;'>[OK]</span>"
                    elif "DENIED" in log_line:
                        badge = "<span style='color: #ef4444; font-weight: bold;'>[FAIL]</span>"
                    else:
                        badge = "<span style='color: #3b82f6; font-weight: bold;'>[INFO]</span>"
                        
                    log_html += f"<div style='font-family: monospace; font-size: 0.85rem; margin-bottom: 6px;'>{badge} {log_line}</div>"
                    
                st.markdown(
                    textwrap.dedent(f"""
                    <div style="background: rgba(0,0,0,0.03); border: 1px solid rgba(0,0,0,0.06); padding: 16px; border-radius: 8px;">
                        {log_html}
                    </div>
                    """),
                    unsafe_allow_html=True
                )
