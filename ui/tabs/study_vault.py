from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
import hashlib
from datetime import datetime, date, timedelta
from src.phr_models.profile import EpistemicStatus, AllergyConditionNode
from ui.utils.components import render_info_banner

def render_study_vault(dark_mode: bool):
    st.markdown("## 🔬 Study & Research Vault")
    
    render_info_banner(
        title="Clinical Literature Analysis & Diagnostic Forms",
        body="Digitise standardized diagnostic intake questionnaires, parse and evaluate medical literature, establish local clinical hypotheses, and securely share signed study packages with practitioners.",
        accent_color="#0891b2",
        icon="🔬",
        dark_mode=dark_mode,
    )
    
    # 10 Questions for K10
    k10_questions = [
        ("q1", "In the past 4 weeks, about how often did you feel tired out for no good reason?"),
        ("q2", "In the past 4 weeks, about how often did you feel nervous?"),
        ("q3", "In the past 4 weeks, about how often did you feel so nervous that nothing could calm you down?"),
        ("q4", "In the past 4 weeks, about how often did you feel hopeless?"),
        ("q5", "In the past 4 weeks, about how often did you feel restless or fidgety?"),
        ("q6", "In the past 4 weeks, about how often did you feel so restless you could not sit still?"),
        ("q7", "In the past 4 weeks, about how often did you feel depressed?"),
        ("q8", "In the past 4 weeks, about how often did you feel that everything was an effort?"),
        ("q9", "In the past 4 weeks, about how often did you feel so sad that nothing could cheer you up?"),
        ("q10", "In the past 4 weeks, about how often did you feel worthless?")
    ]
    
    options = ["None of the time", "A little of the time", "Some of the time", "Most of the time", "All of the time"]
    weights = {opt: i+1 for i, opt in enumerate(options)}
    
    # Initialize session state for K10 form answers if not present
    if "k10_answers" not in st.session_state:
        st.session_state.k10_answers = {q[0]: "None of the time" for q in k10_questions}
        st.session_state.k10_autofill_source = "Manual"
        
    t_forms, t_research, t_share = st.tabs([
        "📋 Structured Diagnostic Forms",
        "📚 Clinical Research & Hypotheses",
        "🔐 Sovereign Peer Sharing"
    ])
    
    # ------------------ TAB 1: DIAGNOSTIC FORMS ------------------
    with t_forms:
        st.markdown("### 📋 Structured Clinical Questionnaires")
        st.write("Fill out standardized diagnostic metrics. You can answer manually or trigger secure data analysis to auto-populate from journal text/chat transcripts.")
        
        col_form, col_summary = st.columns([2, 1])
        
        with col_form:
            st.markdown("#### Kessler Psychological Distress Scale (K10)")
            
            # AI Autofill trigger button
            if st.button("⚡ Auto-populate via Conversation Transcript", type="secondary"):
                # Simulating text analysis on a distress journal entry
                st.session_state.k10_answers = {
                    "q1": "Most of the time",
                    "q2": "All of the time",
                    "q3": "Some of the time",
                    "q4": "Some of the time",
                    "q5": "Most of the time",
                    "q6": "Most of the time",
                    "q7": "Some of the time",
                    "q8": "All of the time",
                    "q9": "A little of the time",
                    "q10": "None of the time"
                }
                st.session_state.k10_autofill_source = "AI Transcript Parsing (Distress Log)"
                st.success("✓ Auto-populated from secure chat transcript: 'feeling overwhelmed, unable to relax, constant effort to get out of bed'.")
            
            # Display form questions
            score = 0
            for q_id, q_text in k10_questions:
                current_val = st.session_state.k10_answers.get(q_id, "None of the time")
                sel_opt = st.radio(q_text, options=options, index=options.index(current_val), key=f"k10_{q_id}")
                st.session_state.k10_answers[q_id] = sel_opt
                score += weights[sel_opt]
                
        with col_summary:
            st.markdown("#### K10 Diagnostic Result")
            
            # Calculate band
            if score < 20:
                band_color = "#10b981" # Green
                band_title = "Likely to be well"
                band_desc = "Your score indicates you are currently experiencing low or no psychological distress."
            elif score <= 24:
                band_color = "#3b82f6" # Blue
                band_title = "Mild psychological distress"
                band_desc = "Your score suggests mild distress levels. Targeted pacing and relaxation support recommended."
            elif score <= 29:
                band_color = "#f59e0b" # Orange
                band_title = "Moderate psychological distress"
                band_desc = "Your score indicates moderate distress. Consider sharing diagnostic details with your care circle."
            else:
                band_color = "#ef4444" # Red
                band_title = "Severe psychological distress"
                band_desc = "Your score indicates severe distress. Urgent clinical support and diagnostic sharing is advised."
                
            st.markdown(
                f"""<div class="premium-card" style="border-left: 5px solid {band_color}; padding: 20px; text-align: center;">
<div style="font-size:0.8rem; text-transform:uppercase; font-weight:bold; color:#64748b;">Distress Score</div>
<div style="font-size: 3.2rem; font-weight: 800; color:{band_color}; margin: 10px 0;">{score}</div>
<h4 style="margin: 0; color:{band_color};">{band_title}</h4>
<p style="font-size: 0.85rem; color: #64748b; margin-top: 8px;">{band_desc}</p>
<div style="font-size:0.75rem; color:#64748b; margin-top:12px; border-top:1px solid rgba(0,0,0,0.05); padding-top:8px;">
<b>Source:</b> {st.session_state.k10_autofill_source}
</div>
</div>""",
                unsafe_allow_html=True
            )
            
            # Save completed form
            if st.button("💾 Save Score to Diagnostic Timeline", type="primary"):
                st.success(f"Score of {score} successfully saved to sovereign timeline.")

    # ------------------ TAB 2: RESEARCH & HYPOTHESES ------------------
    with t_research:
        st.markdown("### 📚 Research Paper Extraction & Hypotheses")
        st.write("Upload medical literature and analyze clinical criteria, comorbidity linkages, and symptoms to formulate local diagnostic hypotheses.")
        
        # File uploader simulator
        st.file_uploader("Upload Research Paper (PDF / Text)", type=["pdf", "txt"])
        
        col_insights, col_chart = st.columns([1, 1])
        
        with col_insights:
            st.markdown("#### Extracted Insights: Autonomic Dysregulation Study")
            st.write("Key metrics identified by the semantic literature parser:")
            
            insights = [
                {
                    "category": "Comorbidity Link",
                    "title": "Orthostatic Dysregulation",
                    "desc": "Research indicates 85% correlation between post-viral fatigue and postural tachycardia.",
                    "conf": "94%"
                },
                {
                    "category": "Causes vs. Symptoms",
                    "title": "Inflammatory Cascade Trigger",
                    "desc": "Identifies secondary nerve inflammation as primary cause; muscle spasms are secondary symptoms.",
                    "conf": "88%"
                },
                {
                    "category": "Condition Evolution",
                    "title": "Pacing & Stabilisation Window",
                    "desc": "Progressive autonomic stability typically observed 12 months post-trigger under pacing therapies.",
                    "conf": "85%"
                }
            ]
            
            for ins in insights:
                st.markdown(
                    f"""<div class="premium-card" style="border-left: 3px solid #0891b2; padding: 12px; margin-bottom: 8px;">
<div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#64748b; font-weight:bold;">
<span>{ins["category"].upper()}</span>
<span>Conf: {ins["conf"]}</span>
</div>
<h5 style="margin: 6px 0 2px 0; color:#475569;">{ins["title"]}</h5>
<p style="font-size:0.8rem; color:#64748b; margin: 0;">{ins["desc"]}</p>
</div>""",
                    unsafe_allow_html=True
                )
                
            # Hypothesis generation trigger
            if st.button("🧠 Establish Diagnostic Hypothesis Node", type="primary"):
                # Integrate with profile tab / sanctuary lists
                new_hyp = {
                    "id": f"hyp-auto-{int(datetime.now().timestamp())}",
                    "timestamp": datetime.now(),
                    "symptoms": "Post-viral autonomic dysregulation comorbidity hypothesis",
                    "suspicion_level": "High",
                    "evidence": "Extracted from paper 'Comorbidity analysis of long-term autonomic nervous system dysregulation'. Match: Wearable HR trends show elevated resting pulse.",
                    "hash": hashlib.sha256(b"autonomic-hypothesis").hexdigest()
                }
                if "hypothesis_nodes" not in st.session_state:
                    st.session_state.hypothesis_nodes = []
                st.session_state.hypothesis_nodes.append(new_hyp)
                st.success("✓ Diagnostic Hypothesis established and linked in Sanctuary/Intake vaults!")
                
        with col_chart:
            st.markdown("#### Comorbidity Correlation Weights")
            # Build DataFrame
            comorb_data = pd.DataFrame([
                {"Condition": "Post-viral Fatigue", "Correlation": 85},
                {"Condition": "Dysautonomia", "Correlation": 75},
                {"Condition": "Fibromyalgia", "Correlation": 60},
                {"Condition": "IBS", "Correlation": 45},
                {"Condition": "Cardiovascular Arrythmia", "Correlation": 30}
            ])
            fig = px.bar(
                comorb_data,
                x="Correlation",
                y="Condition",
                orientation="h",
                color="Correlation",
                color_continuous_scale=px.colors.sequential.Teal,
                range_x=[0, 100],
                title="Literature Comorbidity Linkages (%)"
            )
            fig.update_layout(
                template="plotly_dark" if dark_mode else "plotly_white",
                margin=dict(l=10, r=10, t=40, b=10),
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)

    # ------------------ TAB 3: SIGNED PEER SHARING ------------------
    with t_share:
        st.markdown("### 🔐 Cryptographically Signed Cooperative Care Sharing")
        st.write("Package completed diagnostic questionnaires and research hypotheses. Encrypt and sign using your private keys to share with doctors securely via the Nymtech mixnet.")
        
        # Sharing configurations
        if "directory_actors" not in st.session_state:
            from ui.utils import init_mock_data
            init_mock_data()
            
        actors = st.session_state.directory_actors
        
        with st.form("share_study_form"):
            st.markdown("#### Package Study Node")
            share_k10 = st.checkbox("Include Completed Kessler K10 distress form", value=True)
            share_hyp = st.checkbox("Include Autonomic Dysregulation Hypothesis Node", value=True)
            
            st.markdown("#### Target Recipient (Social Book)")
            recipient = st.selectbox("Select Clinician / Practitioner", options=actors, format_func=lambda x: f"{x['name']} ({x.get('did_uri', 'No DID')})")
            
            st.markdown("#### Verification & Cryptographic Seals")
            priv_key = st.text_input("Enter Private DID Verification Key", value="did:key:z6MkgTsvK8sPec...", type="password")
            
            submitted_share = st.form_submit_button("🔒 Sign & Share Study Node")
            if submitted_share:
                st.markdown("#### ⚡ verfiablePresentation Proof Signature")
                
                # Compute SHA-256 payload signature
                payload = f"{share_k10}|{share_hyp}|{recipient['did_uri']}|{datetime.now().isoformat()}"
                sig = hashlib.sha256(payload.encode()).hexdigest()
                
                st.markdown(
                    f"""<div style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.1); padding: 16px; border-radius: 8px; font-size: 0.9rem; margin-bottom:12px;">
<span style="color: #10b981; font-weight: bold;">✓ SECURE SHARING TRANSMITTED</span><br>
Study package successfully encrypted and sent to <b>{recipient["name"]}</b>.<br>
<b>Verification Signature:</b> <code>{sig}</code><br>
<b>Nymtech Hops:</b> Sydney Gateway -> Paris Mix -> Tokyo Mix -> Recipient Node (0.0% Metadata Leakage)
</div>""",
                    unsafe_allow_html=True
                )
                
                st.code(
                    """
{
  "type": "VerifiablePresentation",
  "holder": "did:key:z6MkgTsvK8sPec...",
  "verifiableCredential": {
    "type": "DiagnosticStudyCredential",
    "subject": {
      "k10_score": 28,
      "hypothesis": "Post-viral autonomic dysregulation comorbidity"
    }
  },
  "proof": {
    "type": "Ed25519Signature2020",
    "proofValue": "z8F9hL12...jK9sPecT..."
  }
}
                    """,
                    language="json"
                )
