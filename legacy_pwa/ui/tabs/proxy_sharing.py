import streamlit as st
import textwrap

from src.phr_models.proxy_consent import RelatedPerson, ProxyConsent, PrivacyMode, LegalBasis, ProxyRelationship

def render_proxy_sharing(dark_mode: bool):
    st.markdown("## 🛡️ Proxy Disclosures & Sharing Control")
    
    st.markdown(
        textwrap.dedent("""
        <div class="premium-card" style="border-left: 5px solid #10b981; margin-bottom: 20px;">
            <h4 style="margin: 0; color: #10b981;">👥 Proxy Consent & Authority Engine</h4>
            <p style="font-size: 0.9rem; color: #64748b; margin-top: 5px; margin-bottom: 0;">
                Manage carer, guardian, and nominated person authorizations aligned with My Health Record rules and the NSW Mental Health Act. Use the <b>Carer View Simulator</b> below to test data redaction in real time.
            </p>
        </div>
        """),
        unsafe_allow_html=True
    )
    
    st.markdown("### 🎭 Carer View Simulator")
    st.write("Simulate what a third-party (e.g. your doctor or carer) actually sees when they log in to view your health record. Data is dynamically redacted based on Privacy Mode A/B/C security labels.")
    
    sim_role = st.selectbox(
        "Select Simulated View Role:",
        options=["Owner", "Doctor", "Carer"],
        format_func=lambda x: {
            "Owner": "👑 Full Patient Owner (Full View: Mode A, B, C)",
            "Doctor": "🩺 Doctor / GP (View: Mode A and B - Confidential & Clinical)",
            "Carer": "👥 Carer / Father (View: Mode C - Normal/Shared)"
        }[x],
        key="sim_role_select"
    )
    st.session_state.simulated_role = sim_role
    
    obs_all = st.session_state.get("psychiatric_observations", [])
    loc_all = st.session_state.get("location_events", [])
    med_all = st.session_state.get("medication_administrations", [])
    
    def count_visible(dataset, role):
        visible = 0
        for item in dataset:
            mode = item["privacy_mode"]
            if role == "Owner":
                visible += 1
            elif role == "Doctor":
                if mode in [PrivacyMode.MODE_A_STRICT, PrivacyMode.MODE_B_PRIVILEGED]:
                    visible += 1
            elif role == "Carer":
                if mode == PrivacyMode.MODE_C_SHARED:
                    visible += 1
        return visible
    
    v_obs = count_visible(obs_all, sim_role)
    v_loc = count_visible(loc_all, sim_role)
    v_med = count_visible(med_all, sim_role)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Visible Psychiatry Records", f"{v_obs} / {len(obs_all)}")
    c2.metric("Visible Location Logs", f"{v_loc} / {len(loc_all)}")
    c3.metric("Visible Medication Records", f"{v_med} / {len(med_all)}")
    
    st.divider()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 👥 Registered Related Persons (Proxies)")
        for rp in st.session_state.related_persons:
            st.markdown(
                textwrap.dedent(f"""
                <div class="premium-card" style="border-left: 3px solid #3b82f6; padding: 12px; margin-bottom: 10px;">
                    <strong>{rp.description}</strong>
                    <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">
                        Relationship: {rp.relationship.name} | ID: <code>{rp.id}</code> | Anonymous for Safety: {'Yes 🔒' if rp.is_anonymous else 'No'}
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )
            
        with st.expander("➕ Register New Related Person"):
            with st.form("new_rp_form", clear_on_submit=True):
                desc = st.text_input("Name & Title / Description", placeholder="e.g. John Doe (Father)")
                rel = st.selectbox("Relationship Type", options=[ProxyRelationship.PARENT, ProxyRelationship.CARER, ProxyRelationship.GUARDIAN, ProxyRelationship.PARTNER])
                anon = st.checkbox("Keep Anonymous (for safety planning)", value=False)
                
                submitted = st.form_submit_button("Register Proxy")
                if submitted and desc:
                    new_rp = RelatedPerson(
                        id=f"rp-{len(st.session_state.related_persons)+1}",
                        patient_id="patient-self",
                        relationship=rel,
                        is_anonymous=anon,
                        description=desc
                    )
                    st.session_state.related_persons.append(new_rp)
                    st.success("Related Person registered.")
                    st.rerun()
                    
    with col2:
        st.markdown("### 📜 Active Proxy Consents & Legal Basis")
        for pc in st.session_state.proxy_consents:
            proxy_desc = "Unknown Proxy"
            for rp in st.session_state.related_persons:
                if rp.id == pc.proxy_id:
                    proxy_desc = rp.description
                    break
            st.markdown(
                textwrap.dedent(f"""
                <div class="premium-card" style="border-left: 3px solid #10b981; padding: 12px; margin-bottom: 10px;">
                    <strong>Access: {proxy_desc}</strong>
                    <div style="font-size: 0.75rem; color: #94a3b8; margin: 4px 0;">
                        Legal Basis: {pc.legal_basis.value} | Sharing Mode: {pc.privacy_mode.name}
                    </div>
                    <div style="font-size: 0.7rem; color: #ef4444;">
                        {'⚠️ Strict Audit Trails Silenced (Safety Planning Active)' if pc.audit_silenced else '✓ Standard Security Audit Logging Active'}
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )
            
        with st.expander("➕ Add Consent Authorization"):
            with st.form("new_consent_form", clear_on_submit=True):
                proxies = {p.description: p.id for p in st.session_state.related_persons}
                sel_p = st.selectbox("Authorize Proxy", options=list(proxies.keys()))
                basis = st.selectbox("Legal Authorization Basis", options=[LegalBasis.EXPLICIT_CONSENT, LegalBasis.GUARDIAN_AUTHORITY, LegalBasis.MHA_NOMINATED, LegalBasis.SAFETY_OVERRIDE])
                mode = st.selectbox("Maximum Permitted Privacy Level", options=[PrivacyMode.MODE_A_STRICT, PrivacyMode.MODE_B_PRIVILEGED, PrivacyMode.MODE_C_SHARED])
                silence_audit = st.checkbox("Silence Audits for Safety", value=False)
                
                submitted = st.form_submit_button("Grant Authorization")
                if submitted:
                    new_pc = ProxyConsent(
                        id=f"consent-{len(st.session_state.proxy_consents)+1}",
                        patient_id="patient-self",
                        proxy_id=proxies[sel_p],
                        legal_basis=basis,
                        privacy_mode=mode,
                        audit_silenced=silence_audit
                    )
                    st.session_state.proxy_consents.append(new_pc)
                    st.success("Proxy consent authorization granted.")
                    st.rerun()
