from ui.tabs.psychology import render_psychology
from ui.tabs.sleep_analytics import render_sleep_analytics
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import textwrap

from src.phr_models.proxy_consent import PrivacyMode
from src.phr_models.psychiatry import ObservationContext

def render_mental_health(dark_mode: bool, normalized: dict):
    st.markdown("## 🧠 Mental Health & Wellbeing")
    
    st.markdown(
        """
        <div class="premium-card" style="border-left: 5px solid #a855f7; margin-bottom: 20px;">
            <h4 style="margin: 0; color: #a855f7;">🛡️ Trauma-Informed Design Policy</h4>
            <p style="font-size: 0.9rem; color: #64748b; margin-top: 5px; margin-bottom: 0;">
                Mental health observations default to <b>Strict Privacy Mode (Mode A)</b>. No fields are mandatory, allowing you to log as much or as little as feels safe and supportive of your personal recovery.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Show recently captured structured assessments / pathology (from PDF + interactive forms)
    recent = st.session_state.get("recent_assessments", [])
    structured_path = st.session_state.get("structured_pathology_reports", [])
    if recent or structured_path:
        with st.expander("📊 Recently Captured Structured Data (from Assessments & PDFs)", expanded=False):
            if recent:
                st.markdown("**Recent Questionnaire Submissions**")
                for r in recent[-3:]:
                    st.markdown(f"- **{r.get('date')}** — {r.get('type')} — Score: **{r.get('score')}**")
            if structured_path:
                st.markdown("**Recent Structured Pathology (from PDFs)**")
                for rep in structured_path[-2:]:
                    st.markdown(f"- Report {str(rep.id)[:8]}… — {len(rep.observations)} observations on {rep.date_issued.date()}")
    
    tab_mood, tab_psychology, tab_sleep = st.tabs(["🧠 Mood & Observations", "🧪 Psychology", "💤 Sleep Analytics"])
    with tab_mood:
        c1, c2 = st.columns([1, 1])
    
        with c1:
            st.markdown("### 📝 Log New Observation / Mood")
            with st.form("new_psych_obs_form", clear_on_submit=True):
                symptom_name = st.selectbox(
                    "Observed Mood / Symptom",
                    options=["Anxiety / Panic Attack", "Depressed mood", "Agitation / Irritability", "Insomnia / Sleep issue", "Other / Custom"]
                )
                custom_symptom = ""
                if symptom_name == "Other / Custom":
                    custom_symptom = st.text_input("Enter custom symptom name:")
                    
                symptom_code_map = {
                    "Anxiety / Panic Attack": "48694002",
                    "Depressed mood": "366979004",
                    "Agitation / Irritability": "58596002",
                    "Insomnia / Sleep issue": "193462001",
                    "Other / Custom": "custom"
                }
                
                context = st.selectbox(
                    "Observation Context",
                    options=["Self-Reported", "Carer-Observed"]
                )
                
                proxy_selection = None
                if context == "Carer-Observed" and st.session_state.related_persons:
                    proxies = {p.description: p.id for p in st.session_state.related_persons}
                    selected_proxy_desc = st.selectbox("Recorded by Carer/Proxy", options=list(proxies.keys()))
                    proxy_selection = proxies[selected_proxy_desc]
                    
                notes = st.text_area("Observation Details / Notes", placeholder="e.g. experienced heart palpitations or feeling low energy.")
                
                privacy = st.selectbox(
                    "Privacy Level",
                    options=["Mode A - Strict (Self + Doctor only)", "Mode B - Privileged (Doctor-facing)", "Mode C - Normal (Carer/Family shared)"],
                    index=0
                )
                privacy_mode_map = {
                    "Mode A - Strict (Self + Doctor only)": PrivacyMode.MODE_A_STRICT,
                    "Mode B - Privileged (Doctor-facing)": PrivacyMode.MODE_B_PRIVILEGED,
                    "Mode C - Normal (Carer/Family shared)": PrivacyMode.MODE_C_SHARED
                }
                
                submitted = st.form_submit_button("Log Observation")
                if submitted:
                    s_name = custom_symptom if symptom_name == "Other / Custom" else symptom_name
                    s_code = "custom" if symptom_name == "Other / Custom" else symptom_code_map[symptom_name]
                    obs_ctx = ObservationContext.SELF_REPORTED if context == "Self-Reported" else ObservationContext.CARER_OBSERVED
                    
                    new_obs = {
                        "id": f"psych-obs-{len(st.session_state.psychiatric_observations)+1}",
                        "patient_id": "patient-self",
                        "date_recorded": datetime.now(),
                        "context": obs_ctx,
                        "recorded_by_proxy_id": proxy_selection,
                        "privacy_mode": privacy_mode_map[privacy],
                        "symptom_code": s_code,
                        "symptom_name": s_name,
                        "notes": notes,
                        "linked_medication_id": None
                    }
                    st.session_state.psychiatric_observations.append(new_obs)
                    st.success("Symptom logged successfully!")
                    st.rerun()
                    
            st.markdown("### 📊 Subjective Wellbeing Tracker (ONS-4)")
            st.write("The ONS-4 measures personal wellbeing across four core items from 0 (not at all) to 10 (completely).")
            with st.expander("Survey Form"):
                with st.form("ons4_form", clear_on_submit=True):
                    satisfaction = st.slider("1. Overall, how satisfied are you with your life nowadays?", 0, 10, 5)
                    worthwhile = st.slider("2. Overall, to what extent do you feel that the things you do in your life are worthwhile?", 0, 10, 5)
                    happiness = st.slider("3. Overall, how happy did you feel yesterday?", 0, 10, 5)
                    anxiety = st.slider("4. Overall, how anxious did you feel yesterday?", 0, 10, 5)
                    
                    submitted_ons = st.form_submit_button("Submit Survey")
                    if submitted_ons:
                        new_ons = {
                            "date": datetime.now(),
                            "life_satisfaction": satisfaction,
                            "worthwhile": worthwhile,
                            "happiness": happiness,
                            "anxiety": anxiety
                        }
                        st.session_state.ons4_responses.append(new_ons)
                        st.success("Thank you! Your survey responses have been added to your vault.")
                        st.rerun()
                        
        with c2:
            st.markdown("### 📈 Wellbeing Timeline & Trends")
            if st.session_state.ons4_responses:
                ons_df = pd.DataFrame(st.session_state.ons4_responses)
                ons_df["date_str"] = ons_df["date"].apply(lambda x: x.strftime("%b %d"))
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=ons_df["date_str"], y=ons_df["life_satisfaction"], name="Life Satisfaction", mode="lines+markers", line=dict(color="#10b981")))
                fig.add_trace(go.Scatter(x=ons_df["date_str"], y=ons_df["worthwhile"], name="Worthwhile", mode="lines+markers", line=dict(color="#3b82f6")))
                fig.add_trace(go.Scatter(x=ons_df["date_str"], y=ons_df["happiness"], name="Happiness", mode="lines+markers", line=dict(color="#f59e0b")))
                fig.add_trace(go.Scatter(x=ons_df["date_str"], y=ons_df["anxiety"], name="Anxiety Level", mode="lines+markers", line=dict(color="#ef4444")))
                
                fig.update_layout(
                    title="Weekly Subjective Wellbeing (ONS-4)",
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                    template="plotly_dark" if dark_mode else "plotly_white",
                    yaxis=dict(range=[0, 10])
                )
                st.plotly_chart(fig, use_container_width=True)
                
            st.markdown("### 📋 Psychiatry Observation History")
            
            sim_role = st.session_state.get("simulated_role", "Owner")
            
            filtered_obs = []
            for obs in st.session_state.psychiatric_observations:
                mode = obs["privacy_mode"]
                if sim_role == "Owner":
                    filtered_obs.append(obs)
                elif sim_role == "Doctor":
                    if mode in [PrivacyMode.MODE_A_STRICT, PrivacyMode.MODE_B_PRIVILEGED]:
                        filtered_obs.append(obs)
                elif sim_role == "Carer":
                    if mode == PrivacyMode.MODE_C_SHARED:
                        filtered_obs.append(obs)
                        
            if sim_role != "Owner":
                st.caption(f"🔒 Filtering observations for simulated role: **{sim_role}**")
                
            if not filtered_obs:
                st.info("No visible observations for this role view.")
            else:
                for obs in filtered_obs:
                    color_map = {
                        PrivacyMode.MODE_A_STRICT: "#ef4444",
                        PrivacyMode.MODE_B_PRIVILEGED: "#f59e0b",
                        PrivacyMode.MODE_C_SHARED: "#10b981"
                    }
                    color = color_map.get(obs["privacy_mode"], "#64748b")
                    
                    st.markdown(
                        textwrap.dedent(f"""
                        <div class="premium-card" style="border-left: 5px solid {color}; padding: 12px; margin-bottom: 10px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <strong style="color: {color};">{obs['symptom_name']}</strong>
                                <span style="font-size: 0.75rem; background: {color}22; color: {color}; padding: 2px 6px; border-radius: 4px; font-weight: bold;">
                                    {obs['privacy_mode'].name.replace('MODE_', '').replace('_', ' ')}
                                </span>
                            </div>
                            <div style="font-size: 0.75rem; color: #94a3b8; margin: 4px 0;">
                                Logged: {obs['date_recorded'].strftime('%Y-%m-%d %H:%M')} | Context: {obs['context'].value}
                            </div>
                            <p style="font-size: 0.85rem; margin-top: 4px; margin-bottom: 0;">{obs['notes']}</p>
                            {f'<div style="font-size: 0.7rem; color: #a855f7; margin-top: 4px;">🔗 Linked to Carer Proxy ID: <i>{obs["recorded_by_proxy_id"]}</i></div>' if obs.get("recorded_by_proxy_id") else ''}
                        </div>
                        """),
                        unsafe_allow_html=True
                    )

    with tab_psychology:
        render_psychology(dark_mode)

    with tab_sleep:
        render_sleep_analytics(dark_mode, normalized)
