from datetime import datetime
import pandas as pd
import streamlit as st
import textwrap

from src.phr_models.proxy_consent import PrivacyMode
from src.phr_models.location import SemanticCategory

def render_location(dark_mode: bool):
    st.markdown("## 📍 Location & Environmental Triggers")
    
    st.markdown(
        """
        <div class="premium-card" style="border-left: 5px solid #06b6d4; margin-bottom: 20px;">
            <h4 style="margin: 0; color: #06b6d4;">🗺️ Privacy-Aware Geolocation Model</h4>
            <p style="font-size: 0.9rem; color: #64748b; margin-top: 5px; margin-bottom: 0;">
                Geospatial events default to <b>Normal (Mode C)</b> unless they are linked to a sensitive clinical observation (e.g. visiting a psychiatry clinic), in which case they inherit the strict privacy policy of the linked record.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown("### 📡 Record Location Event")
        with st.form("new_location_form", clear_on_submit=True):
            category = st.selectbox(
                "Semantic Category",
                options=[SemanticCategory.HOME, SemanticCategory.WORK, SemanticCategory.MEDICAL_FACILITY, SemanticCategory.TRAVEL, SemanticCategory.OTHER]
            )
            
            col_1, col_2 = st.columns(2)
            with col_1:
                lat = st.number_input("Latitude", value=-33.8688, format="%.4f")
            with col_2:
                lon = st.number_input("Longitude", value=151.2093, format="%.4f")
                
            symptom_options = {"None": None}
            for obs in st.session_state.psychiatric_observations:
                symptom_options[f"{obs['symptom_name']} ({obs['date_recorded'].strftime('%b %d')})"] = obs["id"]
                
            linked_symptom = st.selectbox(
                "Link to Symptom Observation (Inherit Strict Privacy)",
                options=list(symptom_options.keys())
            )
            
            submitted = st.form_submit_button("Log Location Event")
            if submitted:
                s_id = symptom_options[linked_symptom]
                inherited_privacy = PrivacyMode.MODE_C_SHARED
                
                if s_id:
                    for obs in st.session_state.psychiatric_observations:
                        if obs["id"] == s_id:
                            inherited_privacy = obs["privacy_mode"]
                            break
                            
                new_event = {
                    "id": f"geo-{len(st.session_state.location_events)+1}",
                    "patient_id": "patient-self",
                    "timestamp": datetime.now(),
                    "latitude": lat,
                    "longitude": lon,
                    "category": category,
                    "privacy_mode": inherited_privacy,
                    "linked_symptom_id": s_id
                }
                st.session_state.location_events.append(new_event)
                st.success(f"Location logged successfully! Inherited Privacy: {inherited_privacy.name}")
                st.rerun()
                
        st.markdown("### 🔍 Environmental Trigger Analysis")
        symptom_triggers = {}
        for event in st.session_state.location_events:
            if event["linked_symptom_id"]:
                cat = event["category"].value.upper()
                symptom_triggers[cat] = symptom_triggers.get(cat, 0) + 1
                
        if not symptom_triggers:
            st.info("No symptoms currently linked to location events. Link a location log to a symptom above to analyze triggers.")
        else:
            st.write("Symptom occurrences correlated with semantic locations:")
            for cat, count in symptom_triggers.items():
                st.markdown(
                    f"""
                    <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 8px; padding: 10px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <strong>📍 {cat}</strong>
                        <span style="color: #ef4444; font-weight: bold;">{count} Symptom Event(s) logged here</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
    with c2:
        st.markdown("### 🗺️ Visualizing Geospatial Data")
        
        sim_role = st.session_state.get("simulated_role", "Owner")
        
        filtered_events = []
        for ev in st.session_state.location_events:
            mode = ev["privacy_mode"]
            if sim_role == "Owner":
                filtered_events.append(ev)
            elif sim_role == "Doctor":
                if mode in [PrivacyMode.MODE_A_STRICT, PrivacyMode.MODE_B_PRIVILEGED]:
                    filtered_events.append(ev)
            elif sim_role == "Carer":
                if mode == PrivacyMode.MODE_C_SHARED:
                    filtered_events.append(ev)
                    
        if filtered_events:
            map_data = pd.DataFrame([
                {
                    "lat": ev["latitude"],
                    "lon": ev["longitude"],
                    "Category": ev["category"].value,
                    "Privacy Mode": ev["privacy_mode"].name
                } for ev in filtered_events
            ])
            st.map(map_data)
            
            st.markdown("#### Geolocation History")
            for ev in filtered_events:
                color_map = {
                    PrivacyMode.MODE_A_STRICT: "#ef4444",
                    PrivacyMode.MODE_B_PRIVILEGED: "#f59e0b",
                    PrivacyMode.MODE_C_SHARED: "#10b981"
                }
                color = color_map.get(ev["privacy_mode"], "#64748b")
                st.markdown(
                    textwrap.dedent(f"""
                    <div class="premium-card" style="border-left: 5px solid {color}; padding: 10px; margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong>Category: {ev['category'].value.capitalize()}</strong>
                            <span style="font-size: 0.75rem; background: {color}22; color: {color}; padding: 2px 6px; border-radius: 4px; font-weight: bold;">
                                {ev['privacy_mode'].name}
                            </span>
                        </div>
                        <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">
                            Lat: {ev['latitude']:.4f}, Lon: {ev['longitude']:.4f} | Logged: {ev['timestamp'].strftime('%b %d, %H:%M')}
                        </div>
                        {f'<div style="font-size: 0.7rem; color: #ef4444; margin-top: 4px;">⚠️ Associated with Symptom ID: {ev["linked_symptom_id"]}</div>' if ev["linked_symptom_id"] else ''}
                    </div>
                    """),
                    unsafe_allow_html=True
                )
        else:
            st.info("No location events visible under the current simulated role view.")
