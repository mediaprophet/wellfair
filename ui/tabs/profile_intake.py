from __future__ import annotations
import streamlit as st
from datetime import datetime, date
from src.phr_models.profile import (
    EpistemicStatus, PatientProfile, DisabilitySupport, AllergyConditionNode,
    DwellingType, SleepSecurityLevel, SocialFoundationsRecord, WalkaboutProfile
)

def render_profile_intake(dark_mode: bool, normalized: dict):
    st.markdown("## 📋 Sovereign Profile & Medical Intake")
    
    st.markdown(
        """<div class="premium-card" style="border-left: 5px solid #3b82f6; margin-bottom: 20px;">
<h4 style="margin: 0; color: #3b82f6;">📋 Sovereign Intake Credentials & Epistemic Audit</h4>
<p style="font-size: 0.9rem; color: #64748b; margin-top: 5px; margin-bottom: 0;">
Manage your personal demographics, pronouns, ancestry, and primary language. Track disability accessibility support needs, and audit pre-existing conditions and allergies with linked evidence.
</p>
</div>""",
        unsafe_allow_html=True
    )
    
    # Initialize mock data in session state
    if "patient_profile" not in st.session_state:
        st.session_state.patient_profile = {
            "full_name": "John Doe",
            "date_of_birth": date(1980, 5, 20),
            "biological_sex": "Male",
            "pronouns": "He/Him",
            "gender_identity": "Male",
            "ancestry_lineage": "Anglo-Celtic / Western European",
            "primary_language": "English",
            "medicare_number": "1234 56789 1",
            "insurance_provider": "Medibank Private",
            "insurance_policy_number": "MP987654321",
            "emergency_contact_name": "Jane Doe",
            "emergency_contact_phone": "+61 400 123 456"
        }
        
    if "disability_supports" not in st.session_state:
        st.session_state.disability_supports = [
            {
                "id": "dis-1",
                "support_name": "Sensory & Cognitive Accommodations",
                "description": "Requires visual formatting overrides (such as high-contrast and dark mode presets) and simplified textual summaries during clinical stress events.",
                "accessibility_requirements": ["Visual Layout Filters", "Plain Text Summaries"],
                "has_ndis_funding": True,
                "registered_provider": "NDIS NSW Support Services"
            }
        ]
        
    if "allergies_conditions" not in st.session_state:
        st.session_state.allergies_conditions = [
            {
                "id": "cond-1",
                "name": "Penicillin Allergy",
                "category": "Drug Allergy",
                "epistemic_status": EpistemicStatus.DISPUTED_MISDIAGNOSIS,
                "dispute_rationale": "Childhood skin rash occurred; modern clinical skin testing at Sydney Allergy Centre was negative (12-Mar-2025). Asserted drug allergy is likely a misdiagnosis.",
                "date_onset": date(1986, 6, 12),
                "linked_evidence_uris": ["DiagnosticReport_Lipids"]
            },
            {
                "id": "cond-2",
                "name": "Hypercholesterolemia",
                "category": "Cardiovascular / Lipid",
                "epistemic_status": EpistemicStatus.CLINICALLY_VERIFIED,
                "dispute_rationale": None,
                "date_onset": date(2023, 11, 15),
                "linked_evidence_uris": ["DiagnosticReport_Lipids"]
            }
        ]

    if "social_foundations" not in st.session_state:
        st.session_state.social_foundations = {
            "dwelling_type": "couch-surfing",
            "homelessness_or_insecure_sleep": True,
            "sleep_insecurity_reason": "Family separation & financial strain",
            "threat_of_violence": True,
            "actual_violence_experienced": False,
            "environmental_hazards": ["Black Mould", "Insecure Lock"],
            "is_home_distinct_from_dwelling": True,
            "is_trapped_at_location": True,
            "trapped_reason": "Lack of affordable housing / financial barriers to move out",
            "deeply_unhappy_or_threatened": True,
            "subjective_safety_score": 4,
            "feels_unsafe_due_to_own_behaviors": False,
            "own_behaviors_detail": ""
        }

    if "walkabout_profile" not in st.session_state:
        st.session_state.walkabout_profile = {
            "shelter_type": "Van (Home on Wheels)",
            "sleep_security_level": "public-parking-medium-risk",
            "has_water": True,
            "has_food_storage": True,
            "has_hygiene_facilities": False,
            "has_power": False,
            "transit_frequency": "Nomadic / Weekly",
            "transit_details": "Traveling between coastal campsites and public parking areas depending on ranger activities",
            "notes": "Looking for a safe designated campsite space with electrical hookup."
        }
        
    t_profile, t_disability, t_allergies, t_social = st.tabs([
        "📋 Medical Intake & Demographics",
        "♿ Disability Supports & Needs",
        "⚠️ Allergies & Conditions (Epistemic Vault)",
        "🏡 Social Foundations & Walkabout"
    ])
    
    # ------------------ TAB 1: MEDICAL INTAKE ------------------
    with t_profile:
        st.markdown("### 📋 Sovereign Patient Intake Sheet")
        st.write("This data represents your self-sovereign identity profile, commonly required when registering at a new medical practice.")
        
        prof = st.session_state.patient_profile
        
        col_view, col_edit = st.columns([2, 1])
        
        with col_view:
            st.markdown("#### Active Intake Credentials")
            
            # Draw intake sheet card
            st.markdown(
                f"""<div class="premium-card" style="border-left: 4px solid #3b82f6; padding: 24px;">
<h3 style="margin: 0 0 16px 0; color:#3b82f6; border-bottom: 1px solid rgba(0,0,0,0.08); padding-bottom: 8px;"> John Doe</h3>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; font-size: 0.92rem;">
<div><b>Date of Birth:</b> {prof["date_of_birth"].strftime('%B %d, %Y')}</div>
<div><b>Biological Sex:</b> {prof["biological_sex"]}</div>
<div><b>Pronouns:</b> {prof["pronouns"]}</div>
<div><b>Gender Identity:</b> {prof["gender_identity"] or "Not Specified"}</div>
<div><b>Genetic Ancestry:</b> {prof["ancestry_lineage"]}</div>
<div><b>Primary Language:</b> {prof["primary_language"]}</div>
<div><b>Medicare Number:</b> {prof["medicare_number"] or "N/A"}</div>
<div><b>Private Insurance:</b> {prof["insurance_provider"]} ({prof["insurance_policy_number"]})</div>
<div><b>Emergency Contact:</b> {prof["emergency_contact_name"]} ({prof["emergency_contact_phone"]})</div>
</div>
</div>""",
                unsafe_allow_html=True
            )
            
        with col_edit:
            st.markdown("#### Update Profile")
            with st.form("edit_profile_form"):
                name = st.text_input("Full Name", value=prof["full_name"])
                dob = st.date_input("Date of Birth", value=prof["date_of_birth"])
                sex = st.selectbox("Biological Sex", ["Male", "Female", "Intersex"], index=["Male", "Female", "Intersex"].index(prof["biological_sex"]))
                pronouns = st.text_input("Pronouns", value=prof["pronouns"])
                gender = st.text_input("Gender Identity", value=prof["gender_identity"] or "")
                ancestry = st.text_input("Genetic Ancestry / Lineage", value=prof["ancestry_lineage"])
                lang = st.text_input("Primary Language", value=prof["primary_language"])
                medicare = st.text_input("Medicare Number", value=prof["medicare_number"] or "")
                ins_prov = st.text_input("Insurance Provider", value=prof["insurance_provider"])
                ins_pol = st.text_input("Insurance Policy Number", value=prof["insurance_policy_number"])
                em_name = st.text_input("Emergency Contact Name", value=prof["emergency_contact_name"])
                em_phone = st.text_input("Emergency Contact Phone", value=prof["emergency_contact_phone"])
                
                submitted = st.form_submit_button("💾 Save Profile Changes")
                if submitted:
                    st.session_state.patient_profile = {
                        "full_name": name,
                        "date_of_birth": dob,
                        "biological_sex": sex,
                        "pronouns": pronouns,
                        "gender_identity": gender if gender else None,
                        "ancestry_lineage": ancestry,
                        "primary_language": lang,
                        "medicare_number": medicare if medicare else None,
                        "insurance_provider": ins_prov,
                        "insurance_policy_number": ins_pol,
                        "emergency_contact_name": em_name,
                        "emergency_contact_phone": em_phone
                    }
                    st.success("Sovereign profile updated.")
                    st.rerun()

    # ------------------ TAB 2: DISABILITY SUPPORTS ------------------
    with t_disability:
        st.markdown("### ♿ Accessibility & Disability Supports")
        st.write("Track adjustments, sensory needs, assistive aids, or program requirements to ensure clinics accommodate your specific disability supports.")
        
        col_dis_list, col_dis_add = st.columns([2, 1])
        
        with col_dis_list:
            st.markdown("#### Registered Disability Accommodations")
            for item in st.session_state.disability_supports:
                reqs_badge = "".join([f"<span style='font-size:0.75rem; background:rgba(0,0,0,0.04); padding:2px 6px; border-radius:4px; margin-right:6px;'>{r}</span>" for r in item["accessibility_requirements"]])
                ndis_badge = "<span style='font-size:0.72rem; background:#10b98122; color:#10b981; padding:2px 6px; border-radius:4px; font-weight:bold; float:right;'>✓ NDIS FUNDED</span>" if item["has_ndis_funding"] else ""
                
                st.markdown(
                    f"""<div class="premium-card" style="border-left: 4px solid #8b5cf6; padding: 16px; margin-bottom: 12px;">
{ndis_badge}
<h4 style="margin: 0 0 6px 0; color:#475569;">{item["support_name"]}</h4>
<p style="font-size:0.88rem; color:#475569; margin: 4px 0;">{item["description"]}</p>
<div style="margin-top:8px; margin-bottom:8px;">
{reqs_badge}
</div>
<div style="font-size:0.8rem; color:#64748b;">
<b>Registered Provider:</b> {item["registered_provider"] or "Self-managed"}
</div>
</div>""",
                    unsafe_allow_html=True
                )
                
        with col_dis_add:
            st.markdown("#### Log Support Requirement")
            with st.form("add_dis_form", clear_on_submit=True):
                sup_name = st.text_input("Accommodation Name", placeholder="e.g., Mobility support / Visual reader")
                sup_desc = st.text_area("Adjustment Description", placeholder="Specify what adjustments are required from medical providers...")
                reqs = st.text_input("Accessibility Tags (comma separated)", placeholder="e.g. Ramp Access, Sign Language")
                has_ndis = st.checkbox("NDIS / Government Funded", value=False)
                provider = st.text_input("Support Coordinator / Provider", placeholder="e.g. NDIS NSW")
                
                submitted_dis = st.form_submit_button("💾 Save Support Need")
                if submitted_dis and sup_name:
                    tags = [r.strip() for r in reqs.split(",")] if reqs else []
                    st.session_state.disability_supports.append({
                        "id": f"dis-{int(datetime.now().timestamp())}",
                        "support_name": sup_name,
                        "description": sup_desc,
                        "accessibility_requirements": tags,
                        "has_ndis_funding": has_ndis,
                        "registered_provider": provider if provider else None
                    })
                    st.success("Accommodation need logged.")
                    st.rerun()

    # ------------------ TAB 3: ALLERGIES & CONDITIONS ------------------
    with t_allergies:
        st.markdown("### ⚠️ Allergies & Pre-existing Conditions")
        st.write("Track clinical diagnoses or self-reported sensitivities. Link cryptographic evidence and audits to flag suspected misdiagnoses or source conflicts.")
        
        col_all_list, col_all_add = st.columns([2, 1])
        
        with col_all_list:
            st.markdown("#### Verified & Audited Conditions")
            for item in st.session_state.allergies_conditions:
                status_color = {
                    EpistemicStatus.CLINICALLY_VERIFIED: "#10b981",
                    EpistemicStatus.SELF_REPORTED_UNVERIFIED: "#f59e0b",
                    EpistemicStatus.SUSPECTED_ONSET: "#3b82f6",
                    EpistemicStatus.DISPUTED_MISDIAGNOSIS: "#ef4444"
                }.get(item["epistemic_status"], "#64748b")
                
                status_text = {
                    EpistemicStatus.CLINICALLY_VERIFIED: "Verified Diagnostic",
                    EpistemicStatus.SELF_REPORTED_UNVERIFIED: "Self-Reported (Unverified)",
                    EpistemicStatus.SUSPECTED_ONSET: "Suspected / Unconfirmed",
                    EpistemicStatus.DISPUTED_MISDIAGNOSIS: "Disputed / Potential Misdiagnosis"
                }.get(item["epistemic_status"], "Unknown")
                
                evidence_section = ""
                if item.get("linked_evidence_uris"):
                    links = []
                    for uri in item["linked_evidence_uris"]:
                        links.append(f"<a href='#' style='font-size:0.75rem; color:#3b82f6; text-decoration:underline;'>📄 Evidence: {uri}</a>")
                    evidence_section = "<div style='margin-top:8px;'>" + " | ".join(links) + "</div>"
                    
                dispute_section = ""
                if item.get("epistemic_status") == EpistemicStatus.DISPUTED_MISDIAGNOSIS and item.get("dispute_rationale"):
                    dispute_section = f"""<div style="margin-top: 10px; padding: 10px; border-left: 3px solid #ef4444; background: rgba(239, 68, 68, 0.04); font-size: 0.8rem; color: #ef4444;">
<b>Conflict / Dispute Rationale:</b> {item["dispute_rationale"]}
</div>"""
                
                st.markdown(
                    f"""<div class="premium-card" style="border-left: 4px solid {status_color}; padding: 16px; margin-bottom: 12px;">
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-size:0.75rem; background:rgba(0,0,0,0.04); padding:2px 6px; border-radius:4px; color:#475569; font-weight:bold;">
{item["category"].upper()}
</span>
<span style="font-size:0.75rem; background:{status_color}1a; color:{status_color}; padding:2px 8px; border-radius:4px; font-weight:bold;">
{status_text}
</span>
</div>
<h4 style="margin: 8px 0 4px 0; color:#475569; font-size:1.1rem;">{item["name"]}</h4>
<div style="font-size:0.8rem; color:#64748b;">
<b>Onset Date:</b> {item["date_onset"].strftime('%Y') if item.get("date_onset") else "Unknown"}
</div>
{dispute_section}
{evidence_section}
</div>""",
                    unsafe_allow_html=True
                )
                
        with col_all_add:
            st.markdown("#### Log Sensitivity or Diagnosis")
            with st.form("add_allergy_form", clear_on_submit=True):
                cond_name = st.text_input("Condition / Allergy Name", placeholder="e.g. Penicillin Allergy / Asthma")
                category = st.selectbox("Category", ["Drug Allergy", "Food Allergy", "Environmental Allergy", "Chronic Illness", "Cardiovascular", "Other"])
                ep_status = st.selectbox("Epistemic / Verification Status", [e.value for e in EpistemicStatus], format_func=lambda x: {
                    "clinically-verified": "Clinically Verified",
                    "self-reported-unverified": "Self-Reported (Unverified)",
                    "suspected-onset": "Suspected / Unconfirmed",
                    "disputed-misdiagnosis": "Disputed / Potential Misdiagnosis"
                }[x])
                dispute = st.text_area("Dispute / Conflict Rationale (If applicable)", placeholder="Explain why this diagnosis might be incorrect, unconfirmed, or disputed...")
                onset = st.date_input("Onset Date (Approximate)", value=date.today())
                
                # Mock Evidence Linking
                st.markdown("##### Link Supporting Evidence")
                link_report = st.checkbox("Link to Laverty Pathology Report (Lipids)", value=False)
                
                submitted_all = st.form_submit_button("💾 Save Condition Node")
                if submitted_all and cond_name:
                    evidence = ["DiagnosticReport_Lipids"] if link_report else []
                    st.session_state.allergies_conditions.append({
                        "id": f"cond-{int(datetime.now().timestamp())}",
                        "name": cond_name,
                        "category": category,
                        "epistemic_status": EpistemicStatus(ep_status),
                        "dispute_rationale": dispute if dispute else None,
                        "date_onset": onset,
                        "linked_evidence_uris": evidence
                    })
                    st.success(f"Condition '{cond_name}' saved to Epistemic Vault.")
                    st.rerun()

    # ------------------ TAB 4: SOCIAL FOUNDATIONS & WALKABOUT ------------------
    with t_social:
        st.markdown("### 🏡 Social Foundations & Walkabout Profile")
        st.write("Track aspects of dwelling safety, homelessness risk, subjective vs. objective safety indices, and resource readiness for nomadic living.")

        col_social_view, col_social_edit = st.columns([1, 1])

        sf = st.session_state.social_foundations
        wp = st.session_state.walkabout_profile

        with col_social_view:
            st.markdown("#### Current Social Foundations & Safety Audit")
            
            # Subjective safety alert badge based on score
            safety_score = sf["subjective_safety_score"]
            if safety_score <= 3:
                safety_badge = "<span style='background:#ef444422; color:#ef4444; padding:4px 8px; border-radius:4px; font-weight:bold; font-size:0.8rem;'>⚠️ CRITICAL INSECURITY</span>"
            elif safety_score <= 6:
                safety_badge = "<span style='background:#f59e0b22; color:#f59e0b; padding:4px 8px; border-radius:4px; font-weight:bold; font-size:0.8rem;'>⚠️ VULNERABLE / INSECURE</span>"
            else:
                safety_badge = "<span style='background:#10b98122; color:#10b981; padding:4px 8px; border-radius:4px; font-weight:bold; font-size:0.8rem;'>✓ STABLE / SECURE</span>"

            # Format list of environmental hazards
            hazards_html = ""
            if sf["environmental_hazards"]:
                hazards_html = " ".join([f"<span style='background:rgba(0,0,0,0.04); color:#1f2937; padding:2px 6px; border-radius:4px; font-size:0.75rem; margin-right:4px;'>☣️ {h}</span>" for h in sf["environmental_hazards"]])
            else:
                hazards_html = "<span style='color:#64748b; font-size:0.85rem;'>None reported</span>"

            # Trapped status
            trapped_html = ""
            if sf["is_trapped_at_location"]:
                trapped_html = f"""<div style="margin-top: 10px; padding: 10px; border-left: 3px solid #ef4444; background: rgba(239, 68, 68, 0.04); font-size: 0.85rem; color: #ef4444;">
<b>Trapped at Dwelling:</b> {sf['trapped_reason'] or 'Yes, unable to leave due to financial or other factors.'}
</div>"""

            # Violence threats
            violence_status = []
            if sf["threat_of_violence"]:
                violence_status.append("Threats of violence / Coercive control")
            if sf["actual_violence_experienced"]:
                violence_status.append("Actual violence experienced")
            
            violence_html = ""
            if violence_status:
                violence_html = f"""<div style="margin-top: 8px; padding: 10px; border-left: 3px solid #ef4444; background: rgba(239, 68, 68, 0.04); color: #ef4444; font-size: 0.85rem; font-weight: bold;">
⚠️ {', '.join(violence_status)}
</div>"""

            # Own behavior vs objective
            behavior_html = ""
            if sf["feels_unsafe_due_to_own_behaviors"]:
                behavior_html = f"""<div style="margin-top: 10px; padding: 10px; border-left: 3px solid #3b82f6; background: rgba(59, 130, 246, 0.04); font-size: 0.85rem; color: #1e3a8a;">
<b>Subjective Feeling Unsafe (Internal/Behavioral):</b> {sf['own_behaviors_detail'] or 'Indicated feeling unsafe relates to internal clinical status/behaviors.'}
</div>"""

            # Render Social Foundations Card
            st.markdown(
                f"""<div class="premium-card" style="border-left: 4px solid #f59e0b; padding: 20px; margin-bottom: 20px;">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px;">
<h4 style="margin: 0; color:#b45309;">🏡 Dwelling & Environmental Safety</h4>
{safety_badge}
</div>
<div style="font-size:0.92rem; color:#475569; display:grid; grid-template-columns: 1fr; gap: 8px;">
<div><b>Dwelling Status:</b> {str(sf['dwelling_type']).upper().replace('-', ' ')}</div>
<div><b>Insecure Place of Sleep / Homelessness:</b> {'Yes 🚨' if sf['homelessness_or_insecure_sleep'] else 'No'}</div>
{f"<div><b>Sleep Insecurity Reason:</b> {sf['sleep_insecurity_reason']}</div>" if sf['sleep_insecurity_reason'] else ""}
<div><b>Is 'Home' distinct from Dwelling / House:</b> {'Yes (deeply unhappy or unsafe in this structure)' if sf['is_home_distinct_from_dwelling'] else 'No'}</div>
<div><b>Subjective Safety Score:</b> {sf['subjective_safety_score']}/10</div>
</div>
{violence_html}
{trapped_html}
{behavior_html}
<div style="margin-top:12px;">
<div style="font-size:0.85rem; font-weight:bold; margin-bottom:4px; color:#475569;">Environmental Hazards / Health Risks:</div>
{hazards_html}
</div>
</div>""",
                unsafe_allow_html=True
            )

            # Render Walkabout Profile Card
            st.markdown("#### Nomadic Living & Walkabout Profile")
            
            # Calculate resource readiness score
            checked_resources = sum([wp["has_water"], wp["has_food_storage"], wp["has_hygiene_facilities"], wp["has_power"]])
            readiness_percent = int((checked_resources / 4) * 100)
            
            if readiness_percent == 100:
                readiness_color = "#10b981"
                readiness_text = "FULL RESOURCE READINESS"
            elif readiness_percent >= 50:
                readiness_color = "#f59e0b"
                readiness_text = "PARTIAL RESOURCE SECURED"
            else:
                readiness_color = "#ef4444"
                readiness_text = "CRITICAL RESOURCE DEFICIT"

            # Sleep Security level string formatting
            sleep_sec_str = str(wp["sleep_security_level"]).replace('-', ' ').upper()

            st.markdown(
                f"""<div class="premium-card" style="border-left: 4px solid #10b981; padding: 20px;">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px;">
<h4 style="margin: 0; color:#0f766e;">⛺ Walkabout / Nomadic Profile</h4>
<span style='background:{readiness_color}22; color:{readiness_color}; padding:4px 8px; border-radius:4px; font-weight:bold; font-size:0.8rem;'>{readiness_text} ({readiness_percent}%)</span>
</div>
<div style="font-size:0.92rem; color:#475569; display:grid; grid-template-columns: 1fr; gap: 8px; margin-bottom: 12px;">
<div><b>Mobile Shelter Type:</b> {wp['shelter_type']}</div>
<div><b>Sleep Place Security Level:</b> {sleep_sec_str}</div>
<div><b>Transit Frequency:</b> {wp['transit_frequency']}</div>
<div><b>Transit Routing/Details:</b> {wp['transit_details'] or 'N/A'}</div>
<div><b>Profile Notes:</b> {wp['notes'] or 'None'}</div>
</div>

<div style="font-size:0.85rem; font-weight:bold; margin-bottom:6px; color:#475569;">Daily Resource Checklist:</div>
<div style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px;">
<div>{'🟢' if wp['has_water'] else '🔴'} Potable Water Access</div>
<div>{'🟢' if wp['has_food_storage'] else '🔴'} Cold Food Storage</div>
<div>{'🟢' if wp['has_hygiene_facilities'] else '🔴'} Shower/Hygiene Facilities</div>
<div>{'🟢' if wp['has_power'] else '🔴'} Electric/Off-Grid Power</div>
</div>
</div>""",
                unsafe_allow_html=True
            )

        with col_social_edit:
            st.markdown("#### Log / Update Social & Walkabout Status")
            
            # Edit Sub-Tabs for edit forms to keep the column clean
            e_sf, e_wp = st.tabs(["🏡 Edit Dwelling Safety", "⛺ Edit Walkabout Status"])
            
            with e_sf:
                with st.form("edit_social_foundations_form"):
                    dwell_opt = ["fixed-house", "couch-surfing", "rough-sleeping", "mobile-home-van", "camping-tent", "other"]
                    
                    # Convert to string to avoid comparison errors with Enum if stored as Enum
                    curr_dwell = sf["dwelling_type"]
                    if hasattr(curr_dwell, "value"):
                        curr_dwell = curr_dwell.value
                    
                    dwell_type_val = st.selectbox(
                        "Dwelling Type", 
                        dwell_opt, 
                        index=dwell_opt.index(curr_dwell) if curr_dwell in dwell_opt else 0,
                        format_func=lambda x: x.replace('-', ' ').title()
                    )
                    
                    homeless_val = st.checkbox("Homelessness or Insecure Place of Sleep", value=sf["homelessness_or_insecure_sleep"])
                    sleep_reason_val = st.text_input("Sleep Insecurity Reason", value=sf["sleep_insecurity_reason"] or "", placeholder="e.g. family separation, poverty")
                    
                    st.markdown("---")
                    st.markdown("##### Threats & Violence Safety")
                    threat_val = st.checkbox("Threat of Violence / Coercive Control", value=sf["threat_of_violence"])
                    violence_val = st.checkbox("Actual Violence Experienced", value=sf["actual_violence_experienced"])
                    
                    hazards_list = ["Black Mould", "Dampness", "Insecure Lock", "Lack of Heating/Cooling", "Structural Defect"]
                    hazards_val = st.multiselect("Environmental Hazards / Health Hazards", hazards_list, default=sf["environmental_hazards"])
                    
                    st.markdown("---")
                    st.markdown("##### Subjective Safety & Trapped Status")
                    distinct_home_val = st.checkbox("The concept of 'home' is not the same as dwelling (e.g. trapped/unhappy)", value=sf["is_home_distinct_from_dwelling"])
                    trapped_val = st.checkbox("Trapped at location / Unable to leave", value=sf["is_trapped_at_location"])
                    trapped_reason_val = st.text_input("Reason Trapped", value=sf["trapped_reason"] or "")
                    
                    safety_score_val = st.slider("Subjective Safety Score (1 = Extremely Unsafe, 10 = Completely Safe)", 1, 10, int(sf["subjective_safety_score"]))
                    
                    st.markdown("---")
                    st.markdown("##### Behavioral / Clinical Safety")
                    behaviors_val = st.checkbox("Feels unsafe due to own behaviours / clinical status", value=sf["feels_unsafe_due_to_own_behaviors"])
                    behaviors_desc_val = st.text_area("Detail of own behavior influence", value=sf["own_behaviors_detail"] or "", placeholder="Describe if mental health symptoms or internal episodes affect safety feelings...")
                    
                    submitted_sf = st.form_submit_button("💾 Save Dwelling & Safety Data")
                    if submitted_sf:
                        # Instantiate Pydantic model for validation
                        record = SocialFoundationsRecord(
                            id="sf-record",
                            dwelling_type=DwellingType(dwell_type_val),
                            homelessness_or_insecure_sleep=homeless_val,
                            sleep_insecurity_reason=sleep_reason_val if sleep_reason_val else None,
                            threat_of_violence=threat_val,
                            actual_violence_experienced=violence_val,
                            environmental_hazards=hazards_val,
                            is_home_distinct_from_dwelling=distinct_home_val,
                            is_trapped_at_location=trapped_val,
                            trapped_reason=trapped_reason_val if trapped_reason_val else None,
                            deeply_unhappy_or_threatened=threat_val or trapped_val,
                            subjective_safety_score=safety_score_val,
                            feels_unsafe_due_to_own_behaviors=behaviors_val,
                            own_behaviors_detail=behaviors_desc_val if behaviors_desc_val else None
                        )
                        st.session_state.social_foundations = record.model_dump()
                        st.success("Dwelling and safety audit updated.")
                        st.rerun()
                        
            with e_wp:
                with st.form("edit_walkabout_profile_form"):
                    shelter_val = st.text_input("Mobile Shelter Type", value=wp["shelter_type"], placeholder="e.g. Van, Tent, Caravan, Swag")
                    
                    sec_opts = ["secure-campground", "public-parking-medium-risk", "unprotected-rough-camping-high-risk"]
                    curr_sec = wp["sleep_security_level"]
                    if hasattr(curr_sec, "value"):
                        curr_sec = curr_sec.value
                    sec_level_val = st.selectbox(
                        "Sleep Place Security Level",
                        sec_opts,
                        index=sec_opts.index(curr_sec) if curr_sec in sec_opts else 0,
                        format_func=lambda x: x.replace('-', ' ').title()
                    )
                    
                    st.markdown("##### Daily Resource Readiness")
                    water_val = st.checkbox("Potable Water Access", value=wp["has_water"])
                    food_val = st.checkbox("Cold Food Storage", value=wp["has_food_storage"])
                    hygiene_val = st.checkbox("Hygiene & Shower Facilities", value=wp["has_hygiene_facilities"])
                    power_val = st.checkbox("Electric / Off-Grid Power Support", value=wp["has_power"])
                    
                    st.markdown("##### Nomadic Movement")
                    transit_freq_val = st.text_input("Transit Frequency", value=wp["transit_frequency"], placeholder="e.g. Nomadic, Weekly, Daily")
                    transit_details_val = st.text_area("Transit Routing / Details", value=wp["transit_details"] or "")
                    
                    notes_val = st.text_area("Walkabout Profile Notes", value=wp["notes"] or "")
                    
                    submitted_wp = st.form_submit_button("💾 Save Walkabout Profile")
                    if submitted_wp:
                        # Instantiate Pydantic model for validation
                        profile = WalkaboutProfile(
                            id="wp-profile",
                            shelter_type=shelter_val,
                            sleep_security_level=SleepSecurityLevel(sec_level_val),
                            has_water=water_val,
                            has_food_storage=food_val,
                            has_hygiene_facilities=hygiene_val,
                            has_power=power_val,
                            transit_frequency=transit_freq_val,
                            transit_details=transit_details_val if transit_details_val else None,
                            notes=notes_val if notes_val else None
                        )
                        st.session_state.walkabout_profile = profile.model_dump()
                        st.success("Walkabout profile updated.")
                        st.rerun()
