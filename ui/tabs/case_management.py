from datetime import datetime
import streamlit as st

from ui.utils import find_df_by_datatype
from src.phr_models.proxy_consent import PrivacyMode
from src.phr_models.cases import CaseFile, CaseTask, CaseCategory, CaseStatus

def render_case_management(dark_mode: bool, normalized: dict):
    st.markdown("## 💼 Case Management & Claims Vault")
    
    st.markdown(
        """
        <div class="premium-card" style="border-left: 5px solid #0d9488; margin-bottom: 20px;">
            <h4 style="margin: 0; color: #0d9488;">📂 Case Files & Claims Engine</h4>
            <p style="font-size: 0.9rem; color: #64748b; margin-top: 5px; margin-bottom: 0;">
                Group symptoms, Samsung Health measurements, clinical documentation, and tasks under self-sovereign <b>Case Files</b>. 
                Use these to support a health hypothesis, belief, or diagnostic requirement (e.g., Sleep Apnea evaluation, routine checks, or interval lab tests). 
                All Case Files default to <b>Strict Privacy Mode (Mode A)</b>.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    cases = st.session_state.get("case_files", [])
    
    total_cases = len(cases)
    suspected_count = sum(1 for c in cases if c.status == CaseStatus.SUSPECTED)
    total_tasks = sum(len(c.tasks) for c in cases)
    open_tasks = sum(sum(1 for t in c.tasks if not t.is_completed) for c in cases)
    completed_tasks = total_tasks - open_tasks
    
    k1, k2, k3, k4 = st.columns(4)
    kpi_data = [
        (k1, "Total Case Files", str(total_cases), "📂", "#3b82f6"),
        (k2, "Suspected Conditions", str(suspected_count), "🔍", "#f59e0b"),
        (k3, "Pending Tasks", str(open_tasks), "📝", "#ef4444"),
        (k4, "Completed Tasks", str(completed_tasks), "✅", "#10b981"),
    ]
    for col, title, value, emoji, color in kpi_data:
        with col:
            st.markdown(
                f"""
                <div class="premium-card" style="border-left: 5px solid {color};">
                    <div class="flex-center">
                        <div class="icon-circle" style="background: {color}22; color: {color};">{emoji}</div>
                        <div>
                            <div class="metric-title">{title}</div>
                            <div class="metric-value">{value}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
    st.divider()
    
    col_left, col_right = st.columns([1.6, 1])
    
    with col_right:
        st.markdown("### ➕ Create New Case File")
        with st.form("new_case_form", clear_on_submit=True):
            title = st.text_input("Case Title", placeholder="e.g. Suspected Gluten Intolerance")
            category = st.selectbox("Category", options=list(CaseCategory))
            hypothesis = st.text_area("Hypothesis / Claim / Reason", placeholder="e.g. Experiencing frequent bloating and lethargy after eating wheat-based foods.")
            linked_data = st.multiselect("Link Wearable Datatypes", options=["com.samsung.shealth.sleep", "com.samsung.shealth.sleep_snoring", "com.samsung.health.weight", "com.samsung.health.heart_rate"])
            notes = st.text_area("Additional Notes", placeholder="Include any details or family history.")
            privacy = st.selectbox("Privacy Level", options=[PrivacyMode.MODE_A_STRICT, PrivacyMode.MODE_B_PRIVILEGED, PrivacyMode.MODE_C_SHARED])
            initial_tasks_raw = st.text_area("Initial Tasks (one per line)", value="Discuss symptoms with GP\nResearch diagnostic criteria")
            
            submitted = st.form_submit_button("Log Case File")
            if submitted and title and hypothesis:
                tasks = []
                for idx, t_title in enumerate(initial_tasks_raw.split("\n")):
                    t_title = t_title.strip()
                    if t_title:
                        tasks.append(CaseTask(id=f"task-new-{idx}-{datetime.now().timestamp()}", title=t_title, is_completed=False))
                        
                new_case = CaseFile(
                    id=f"case-{len(cases)+1}-{int(datetime.now().timestamp())}",
                    patient_id="patient-self",
                    title=title,
                    category=category,
                    status=CaseStatus.SUSPECTED,
                    hypothesis_or_claim=hypothesis,
                    date_created=datetime.now(),
                    date_updated=datetime.now(),
                    privacy_mode=privacy,
                    linked_datatypes=linked_data,
                    tasks=tasks,
                    notes=notes if notes else None
                )
                st.session_state.case_files.append(new_case)
                st.success("Case File created successfully!")
                st.rerun()
                
    with col_left:
        st.markdown("### 📋 Active Case Files")
        if not cases:
            st.info("No case files recorded.")
        else:
            for case in cases:
                category_label = case.category.value.replace("-", " ").title()
                status_label = case.status.value.upper()
                
                cat_colors = {
                    CaseCategory.SUSPECTED_CONDITION: "#f59e0b",
                    CaseCategory.ROUTINE_CHECK: "#3b82f6",
                    CaseCategory.INTERVAL_TEST: "#10b981",
                    CaseCategory.OTHER: "#64748b"
                }
                status_colors = {
                    CaseStatus.SUSPECTED: "#f59e0b",
                    CaseStatus.INVESTIGATING: "#3b82f6",
                    CaseStatus.ACTIVE: "#ef4444",
                    CaseStatus.MONITORING: "#10b981",
                    CaseStatus.RESOLVED: "#10b981",
                    CaseStatus.CLOSED: "#64748b"
                }
                c_color = cat_colors.get(case.category, "#64748b")
                s_color = status_colors.get(case.status, "#64748b")
                
                with st.expander(f"📁 {case.title} — {category_label} ({status_label})", expanded=(case.id == "case-1")):
                    st.markdown(
                        f"""
                        <div class="premium-card" style="border-left: 5px solid {c_color};">
                            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                                <strong style="font-size: 1.15rem;">{case.title}</strong>
                                <div style="display: flex; gap: 6px;">
                                    <span style="font-size: 0.7rem; background: {c_color}22; color: {c_color}; padding: 2px 8px; border-radius: 4px; font-weight: bold;">
                                        {category_label}
                                    </span>
                                    <span style="font-size: 0.7rem; background: {s_color}22; color: {s_color}; padding: 2px 8px; border-radius: 4px; font-weight: bold;">
                                        {status_label}
                                    </span>
                                </div>
                            </div>
                            <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 8px;">
                                Created: {case.date_created.strftime('%d %b %Y')} | Updated: {case.date_updated.strftime('%d %b %Y')} | Privacy: {case.privacy_mode.name}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    st.markdown("#### 🎯 Hypothesis / Claim")
                    st.write(case.hypothesis_or_claim)
                    
                    if case.notes:
                        st.markdown("#### 📝 Notes")
                        st.info(case.notes)
                        
                    if case.linked_datatypes:
                        st.markdown("#### 🔗 Linked Wearable Evidence")
                        
                        for dtype in case.linked_datatypes:
                            if dtype == "com.samsung.shealth.sleep":
                                sleep_df = find_df_by_datatype(normalized, "com.samsung.shealth.sleep")
                                if sleep_df is not None and not sleep_df.empty:
                                    avg_dur = sleep_df["sleep_duration"].mean() if "sleep_duration" in sleep_df.columns else 0
                                    avg_eff = sleep_df["efficiency"].mean() if "efficiency" in sleep_df.columns else 0
                                    st.markdown(
                                        f"""
                                        <div style="font-size: 0.85rem; padding: 10px; background: rgba(139, 92, 246, 0.1); border-left: 3px solid #8b5cf6; border-radius: 4px; margin-bottom: 8px;">
                                            📊 <b>Linked Sleep Summary</b> (From {len(sleep_df)} recorded nights):<br>
                                            • Average Duration: {int(avg_dur//60)}h {int(avg_dur%60)}m<br>
                                            • Average Efficiency: {avg_eff:.1f}%
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )
                                else:
                                    st.caption("⚠️ Sleep summary linked but no records found in active export.")
                                    
                            elif dtype == "com.samsung.shealth.sleep_snoring":
                                snoring_df = find_df_by_datatype(normalized, "com.samsung.shealth.sleep_snoring")
                                if snoring_df is not None and not snoring_df.empty:
                                    total_events = len(snoring_df)
                                    avg_duration = snoring_df["duration"].mean() if "duration" in snoring_df.columns else 0
                                    st.markdown(
                                        f"""
                                        <div style="font-size: 0.85rem; padding: 10px; background: rgba(245, 158, 11, 0.1); border-left: 3px solid #f59e0b; border-radius: 4px; margin-bottom: 8px;">
                                            🔊 <b>Linked Snoring Logs</b>:<br>
                                            • Total Snoring Events Recorded: {total_events}<br>
                                            • Average Event Duration: {avg_duration:.1f} seconds
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )
                                else:
                                    st.caption("⚠️ Snoring data linked but no records found in active export.")
                                    
                            elif dtype == "com.samsung.health.weight":
                                weight_df = find_df_by_datatype(normalized, "com.samsung.health.weight")
                                if weight_df is not None and not weight_df.empty:
                                    latest_w = weight_df.sort_values("start_datetime").iloc[-1]["weight"] if "start_datetime" in weight_df.columns else weight_df.iloc[-1]["weight"]
                                    st.markdown(
                                        f"""
                                        <div style="font-size: 0.85rem; padding: 10px; background: rgba(16, 185, 129, 0.1); border-left: 3px solid #10b981; border-radius: 4px; margin-bottom: 8px;">
                                            ⚖️ <b>Linked Weight Logs</b>:<br>
                                            • Latest Recorded Weight: {latest_w:.1f} kg
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )
                                else:
                                    st.caption("⚠️ Weight logs linked but no records found.")
                                    
                            elif dtype == "com.samsung.health.heart_rate":
                                hr_df = find_df_by_datatype(normalized, "com.samsung.shealth.tracker.heart_rate")
                                if hr_df is not None and not hr_df.empty:
                                    avg_hr = hr_df["heart_rate"].mean() if "heart_rate" in hr_df.columns else hr_df["pulse"].mean()
                                    st.markdown(
                                        f"""
                                        <div style="font-size: 0.85rem; padding: 10px; background: rgba(239, 68, 68, 0.1); border-left: 3px solid #ef4444; border-radius: 4px; margin-bottom: 8px;">
                                            💓 <b>Linked Heart Rate Logs</b>:<br>
                                            • Average Heart Rate: {int(avg_hr)} BPM
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )
                                else:
                                    st.caption("⚠️ Heart rate logs linked but no records found.")

                    st.markdown("#### 🛤️ Action Items & Tasks")
                    if not case.tasks:
                        st.caption("No tasks defined for this case file.")
                    else:
                        for task in case.tasks:
                            t_key = f"chk_{case.id}_{task.id}"
                            is_completed = st.checkbox(task.title, value=task.is_completed, key=t_key, help=task.description)
                            if is_completed != task.is_completed:
                                task.is_completed = is_completed
                                case.date_updated = datetime.now()
                                st.rerun()
                                
                    with st.expander("➕ Add Task to this Case", expanded=False):
                        with st.form(f"add_task_form_{case.id}", clear_on_submit=True):
                            new_t_title = st.text_input("Task Title", key=f"t_title_{case.id}")
                            new_t_desc = st.text_input("Task Description (optional)", key=f"t_desc_{case.id}")
                            t_submitted = st.form_submit_button("Add Task")
                            if t_submitted and new_t_title:
                                new_task = CaseTask(
                                    id=f"task-{len(case.tasks)+1}-{int(datetime.now().timestamp())}",
                                    title=new_t_title,
                                    description=new_t_desc if new_t_desc else None,
                                    is_completed=False
                                )
                                case.tasks.append(new_task)
                                case.date_updated = datetime.now()
                                st.success("Task added!")
                                st.rerun()
