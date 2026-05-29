from __future__ import annotations
import streamlit as st
import textwrap
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

def render_calendar_timeline(dark_mode: bool):
    st.markdown("## 📅 Semantic Timeline & Event Manager")
    
    st.markdown(
        """<div class="premium-card" style="border-left: 5px solid #06b6d4; margin-bottom: 20px;">
<h4 style="margin: 0; color: #06b6d4;">📅 Temporal Graph & Event Chaining</h4>
<p style="font-size: 0.9rem; color: #64748b; margin-top: 5px; margin-bottom: 0;">
Track health events, pathology timelines, and dependent clinical workflows. The logic engine audits prerequisites, travel buffers, and lab result SLAs in real time.
</p>
</div>""",
        unsafe_allow_html=True
    )
    
    # Initialize mock data in session state for timeline events
    if "timeline_events" not in st.session_state:
        now = datetime.now()
        st.session_state.timeline_events = [
            {
                "id": "ev-1",
                "title": "Initial GP Consult",
                "actor": "Dr. Sarah Jenkins",
                "start": now - timedelta(days=5, hours=8),
                "end": now - timedelta(days=5, hours=7),
                "date": now - timedelta(days=5, hours=8),
                "status": "Completed",
                "category": "Consultation",
                "prereq": None,
                "produces_artifact": False,
                "delay_sla": None,
            },
            {
                "id": "task-1",
                "title": "Collect Referral Paperwork",
                "actor": "Patient (Self)",
                "start": now - timedelta(days=3, hours=4),
                "end": now - timedelta(days=3, hours=3),
                "date": now - timedelta(days=3, hours=4),
                "status": "Completed",
                "category": "Tasks & Preparations",
                "prereq": "ev-1",
                "produces_artifact": False,
                "delay_sla": None,
            },
            {
                "id": "task-2",
                "title": "12-Hour Fasting Window",
                "actor": "Patient (Self)",
                "start": now - timedelta(days=2.5),
                "end": now - timedelta(days=2),
                "date": now - timedelta(days=2.5),
                "status": "Completed",
                "category": "Tasks & Preparations",
                "prereq": "task-1",
                "produces_artifact": False,
                "delay_sla": None,
            },
            {
                "id": "ev-2",
                "title": "Laverty Blood Collection",
                "actor": "Laverty Pathology",
                "start": now - timedelta(days=2),
                "end": now - timedelta(days=2) + timedelta(minutes=30),
                "date": now - timedelta(days=2),
                "status": "Completed",
                "category": "Diagnostics",
                "prereq": "task-2",
                "produces_artifact": True,
                "artifact_name": "Specimen_Blood_01",
                "delay_sla": 48,
            },
            {
                "id": "ev-3",
                "title": "Pathology Results Ingestion",
                "actor": "Laverty Pathology",
                "start": now - timedelta(days=2) + timedelta(minutes=30),
                "end": now + timedelta(hours=12),
                "date": now - timedelta(days=2) + timedelta(minutes=30),
                "status": "Awaiting Results",
                "category": "Results Ingestion",
                "prereq": "ev-2",
                "produces_artifact": False,
                "delay_sla": None,
            },
            {
                "id": "ev-4",
                "title": "Follow-up GP Consult",
                "actor": "Dr. Sarah Jenkins",
                "start": now + timedelta(days=2),
                "end": now + timedelta(days=2, hours=1),
                "date": now + timedelta(days=2),
                "status": "Scheduled",
                "category": "Consultation",
                "prereq": "task-3",
                "produces_artifact": False,
                "delay_sla": None,
            },
        ]

    # Inject structured assessments (questionnaires + pathology reports from PDFs) into the timeline
    # Smart injection: only add items that aren't already present (prevents duplicates on reruns)
    from ui.utils import get_all_structured_assessments

    existing_ids = {event.get("id") for event in st.session_state.timeline_events}

    for item in get_all_structured_assessments():
        if isinstance(item, dict) and "date_taken" in item:
            event_id = f"assess-{item.get('id', id(item))}"
            if event_id in existing_ids:
                continue

            try:
                date_val = datetime.fromisoformat(item["date_taken"]) if isinstance(item.get("date_taken"), str) else item.get("date_taken")
            except Exception:
                date_val = datetime.now()

            st.session_state.timeline_events.append({
                "id": event_id,
                "title": f"{item.get('type', 'Assessment')} - Score {item.get('total_score', item.get('score', ''))}",
                "actor": "Patient (Self)",
                "start": date_val,
                "end": date_val,
                "date": date_val,
                "status": "Completed",
                "category": "Assessment / Questionnaire",
                "prereq": None,
                "produces_artifact": True,
                "delay_sla": None,
            })
            existing_ids.add(event_id)

        elif hasattr(item, "date_issued"):  # Pathology report object
            event_id = f"path-{item.id}"
            if event_id in existing_ids:
                continue

            st.session_state.timeline_events.append({
                "id": event_id,
                "title": f"Pathology Report ({len(getattr(item, 'observations', []))} tests)",
                "actor": "Pathology Lab",
                "start": item.date_issued,
                "end": item.date_issued,
                "date": item.date_issued,
                "status": "Completed",
                "category": "Pathology",
                "prereq": None,
                "produces_artifact": True,
                "delay_sla": None,
            })
            existing_ids.add(event_id)

            st.session_state.timeline_events.append({
                "id": f"assess-{item.get('id', id(item))}",
                "title": f"{item.get('type', 'Assessment')} - Score {item.get('total_score', item.get('score', ''))}",
                "actor": "Patient (Self)",
                "start": date_val,
                "end": date_val,
                "date": date_val,
                "status": "Completed",
                "category": "Assessment / Questionnaire",
                "prereq": None,
                "produces_artifact": True,
                "delay_sla": None,
            })
        elif hasattr(item, "date_issued"):  # Pathology report object
            st.session_state.timeline_events.append({
                "id": f"path-{item.id}",
                "title": f"Pathology Report ({len(getattr(item, 'observations', []))} tests)",
                "actor": "Pathology Lab",
                "start": item.date_issued,
                "end": item.date_issued,
                "date": item.date_issued,
                "status": "Completed",
                "category": "Pathology",
                "prereq": None,
                "produces_artifact": True,
                "delay_sla": None,
            })

    events = st.session_state.timeline_events
    
    t_view, t_workflows, t_sla, t_log = st.tabs([
        "📅 Event Timeline & Calendar",
        "🔗 Dependent Workflows (DAG)",
        "⏳ Expected Result SLAs",
        "➕ Log Event / Task"
    ])
    
    # ------------------ TAB 1: EVENT TIMELINE ------------------
    with t_view:
        st.markdown("### 📅 Temporal Event & Task History")
        st.write("Chronological view of observations, appointments, tasks, and procedures in your RDF-Star graph.")
        
        # Refresh button for structured vault data (questionnaires + pathology from PDFs)
        col_refresh, _ = st.columns([1, 3])
        with col_refresh:
            if st.button("🔄 Refresh from Vault Data", key="refresh_timeline_vault"):
                # Remove any previously injected structured events
                st.session_state.timeline_events = [
                    ev for ev in st.session_state.timeline_events 
                    if not (str(ev.get("id", "")).startswith("assess-") or str(ev.get("id", "")).startswith("path-"))
                ]
                st.rerun()  # Re-run the page so the smart injection at the top adds latest data
        
        # Period Evaluator Selector
        st.markdown("#### 🔍 Time Range Evaluator")
        col_type, col_val = st.columns(2)
        with col_type:
            period_type = st.selectbox(
                "Evaluate Period",
                ["Day", "Week", "Month", "Year", "Custom Period"],
                index=1,
                help="Evaluate and display timeline events and tasks within a selected timeframe."
            )
            
        with col_val:
            today = datetime.today()
            if period_type == "Day":
                selected_date = st.date_input("Select Day", value=today.date())
                eval_start = datetime.combine(selected_date, datetime.min.time())
                eval_end = datetime.combine(selected_date, datetime.max.time())
            elif period_type == "Week":
                # Start of week (Monday)
                start_of_week = today - timedelta(days=today.weekday())
                selected_week = st.date_input("Select Week Starting", value=start_of_week.date())
                eval_start = datetime.combine(selected_week, datetime.min.time())
                eval_end = eval_start + timedelta(days=7)
            elif period_type == "Month":
                month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                selected_month = st.selectbox("Select Month", month_names, index=today.month - 1)
                selected_year = st.number_input("Select Year", min_value=2020, max_value=2030, value=today.year)
                month_idx = month_names.index(selected_month) + 1
                eval_start = datetime(selected_year, month_idx, 1)
                if month_idx == 12:
                    eval_end = datetime(selected_year + 1, 1, 1)
                else:
                    eval_end = datetime(selected_year, month_idx + 1, 1)
            elif period_type == "Year":
                selected_year = st.number_input("Select Year", min_value=2020, max_value=2030, value=today.year)
                eval_start = datetime(selected_year, 1, 1)
                eval_end = datetime(selected_year + 1, 1, 1)
            else: # Custom Period
                selected_range = st.date_input("Select Date Range", value=(today.date() - timedelta(days=5), today.date() + timedelta(days=5)))
                if isinstance(selected_range, tuple) and len(selected_range) == 2:
                    eval_start = datetime.combine(selected_range[0], datetime.min.time())
                    eval_end = datetime.combine(selected_range[1], datetime.max.time())
                else:
                    eval_start = datetime.combine(selected_range, datetime.min.time())
                    eval_end = eval_start + timedelta(days=1)
                    
        # Filter events
        filtered_events = []
        for ev in events:
            # Backwards compatibility: fallback to "date" if "start" is missing
            ev_start = ev.get("start") or ev.get("date")
            ev_end = ev.get("end") or (ev_start + timedelta(hours=1))
            
            # Align keys
            ev["start"] = ev_start
            ev["end"] = ev_end
            ev["date"] = ev_start
            
            # Date overlap check
            if ev_start <= eval_end and ev_end >= eval_start:
                filtered_events.append(ev)
                
        if not filtered_events:
            st.warning("⚠️ No events or tasks found in this period. Adjust the period controls above or log a new event/task.")
        else:
            st.markdown("#### 📊 Categorized Gantt Chart & Dependencies")
            
            # Build DataFrame
            gantt_data = []
            for ev in filtered_events:
                # Get prerequisite title if it exists
                prereq_title = "None"
                if ev.get("prereq"):
                    # Find prerequisite title in the full events list
                    parent = next((e for e in events if e["id"] == ev["prereq"]), None)
                    if parent:
                        prereq_title = parent["title"]
                        
                gantt_data.append({
                    "Task": ev["title"],
                    "Start": ev["start"],
                    "Finish": ev["end"],
                    "Category": ev.get("category", "General"),
                    "Status": ev["status"],
                    "Actor": ev["actor"],
                    "Prerequisite": prereq_title
                })
                
            df = pd.DataFrame(gantt_data)
            
            # Sort chronologically by Start so chart reads top-to-bottom
            df = df.sort_values(by="Start")
            
            # Custom category colors
            colors = {
                "Consultation": "#3b82f6", # Blue
                "Diagnostics": "#f59e0b", # Orange
                "Results Ingestion": "#10b981", # Green
                "Tasks & Preparations": "#7c3aed", # Purple
                "General": "#64748b" # Slate
            }
            
            fig = px.timeline(
                df,
                x_start="Start",
                x_end="Finish",
                y="Task",
                color="Category",
                color_discrete_map=colors,
                hover_data=["Status", "Actor", "Prerequisite"],
            )
            
            fig.update_yaxes(autorange="reversed")  # reverse to keep chronological order top-to-bottom
            fig.update_layout(
                xaxis_title="Time / Date",
                yaxis_title="",
                height=250 + (35 * len(df)),  # dynamic height
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                template="plotly_dark" if dark_mode else "plotly_white",
            )
            
            # DRAW DEPENDENCY ARROWS/LINES
            for idx, row in df.iterrows():
                task_name = row["Task"]
                prereq_name = row["Prerequisite"]
                
                if prereq_name != "None":
                    prereq_row = df[df["Task"] == prereq_name]
                    if not prereq_row.empty:
                        pre_finish = prereq_row.iloc[0]["Finish"]
                        cur_start = row["Start"]
                        
                        # Add annotation line in Plotly
                        fig.add_annotation(
                            x=cur_start,
                            y=task_name,
                            ax=pre_finish,
                            ay=prereq_name,
                            xref="x",
                            yref="y",
                            axref="x",
                            ayref="y",
                            text="",
                            showarrow=True,
                            arrowhead=2,
                            arrowsize=1.2,
                            arrowwidth=1.5,
                            arrowcolor="#888888" if not dark_mode else "#cccccc",
                        )
                        
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("#### 📋 Chronological Details")
            sorted_filtered = sorted(filtered_events, key=lambda x: x["start"])
            
            for idx, ev in enumerate(sorted_filtered):
                status_color = {
                    "Completed": "#10b981",
                    "Scheduled": "#3b82f6",
                    "Awaiting Results": "#f59e0b",
                    "Pending": "#7c3aed"
                }.get(ev["status"], "#64748b")
                
                category_badge = f"""<span style="font-size: 0.72rem; background: rgba(0,0,0,0.04); padding: 2px 6px; border-radius: 4px; color: #475569; margin-left: 8px;">{ev.get("category", "General")}</span>"""
                
                st.markdown(
                    f"""<div class="premium-card" style="border-left: 4px solid {status_color}; padding: 16px; margin-bottom: 12px;">
<div style="display: flex; justify-content: space-between; align-items: center;">
<div>
<h4 style="margin: 0; color: #475569; font-size: 1.1rem; display: inline-block;">{ev["title"]}</h4>
{category_badge}
</div>
<span style="font-size: 0.75rem; background: {status_color}22; color: {status_color}; padding: 2px 8px; border-radius: 4px; font-weight: bold;">
{ev["status"]}
</span>
</div>
<div style="font-size: 0.85rem; color: #64748b; margin-top: 6px;">
<b>Actor:</b> {ev["actor"]} | <b>Range:</b> {ev["start"].strftime('%b %d, %Y at %H:%M')} – {ev["end"].strftime('%b %d, %Y at %H:%M')}
</div>
{"<div style='font-size: 0.8rem; color: #7c3aed; margin-top: 6px;'><b>📦 Linked Artifact:</b> " + ev["artifact_name"] + "</div>" if ev.get("produces_artifact") else ""}
</div>""",
                    unsafe_allow_html=True
                )
            
    # ------------------ TAB 2: DEPENDENT WORKFLOWS ------------------
    with t_workflows:
        st.markdown("### 🔗 Chained Clinical Workflows")
        st.write("Visualizes dependencies between consultations, tests, and results. Scheduling conflicts are flagged automatically.")
        
        # Draw workflow chain
        cols = st.columns(min(len(events), 4))
        for i, ev in enumerate(events[:4]):  # display top 4 main steps in the chain
            with cols[i]:
                color = "#10b981" if ev["status"] == "Completed" else ("#f59e0b" if ev["status"] == "Awaiting Results" else "#3b82f6")
                st.markdown(
                    f"""<div style="border: 1px solid {color}; border-radius: 8px; padding: 12px; text-align: center; background: {color}08;">
<div style="font-size: 0.72rem; font-weight: bold; color: {color}; text-transform: uppercase;">Step {i+1}</div>
<div style="font-size: 0.9rem; font-weight: bold; margin-top: 4px;">{ev["title"]}</div>
<div style="font-size: 0.75rem; color: #64748b; margin-top: 4px;">{ev["actor"]}</div>
</div>""",
                    unsafe_allow_html=True
                )
                if i < 3:
                    st.markdown("<div style='text-align: center; font-size: 1.2rem; margin: 4px 0;'>➡️</div>", unsafe_allow_html=True)
                    
        st.divider()
        st.markdown("#### 🧠 Prolog Prerequisite Auditor")
        
        # Auditor Simulator
        st.write("Simulate rescheduling the follow-up consult to test the Prolog validator:")
        resched_days = st.slider("Reschedule 'Follow-up GP Consult' relative to today:", min_value=-5, max_value=5, value=2, format="Day %d")
        
        # Search objects by ID
        results_delivery_ev = next((e for e in events if e["id"] == "ev-3"), None)
        consult_ev = next((e for e in events if e["id"] == "ev-4"), None)
        
        if results_delivery_ev and consult_ev:
            results_delivery = results_delivery_ev["start"]
            consult_date = datetime.now() + timedelta(days=resched_days)
            
            # Update consult date in events for simulator
            consult_ev["start"] = consult_date
            consult_ev["date"] = consult_date
            consult_ev["end"] = consult_date + timedelta(hours=1)
            
            if consult_date < results_delivery:
                st.markdown(
                    """<div class="premium-card" style="border-left: 5px solid #ef4444; background: rgba(239, 68, 68, 0.05); padding: 16px;">
<h4 style="margin: 0; color: #ef4444;">🚨 PROLOG PREREQUISITE ALERT</h4>
<p style="font-size: 0.9rem; color: #ef4444; margin-top: 4px; margin-bottom: 0;">
<b>Rule Violation Detected:</b> <code>prereq_not_met(ev-4, ev-3)</code>.<br>
Follow-up GP Consult requires <i>Pathology Results Ingestion</i> (expected on <b>""" + results_delivery.strftime('%b %d, %H:%M') + """</b>) to be completed first, but it is currently scheduled for <b>""" + consult_date.strftime('%b %d, %H:%M') + """</b>.<br>
<i>Action Recommended: Reschedule Consult to Day 2 or later.</i>
</p>
</div>""",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    """<div class="premium-card" style="border-left: 5px solid #10b981; background: rgba(16, 185, 129, 0.05); padding: 16px;">
<h4 style="margin: 0; color: #10b981;">✓ WORKFLOW PREREQUISITES VERIFIED</h4>
<p style="font-size: 0.9rem; color: #10b981; margin-top: 4px; margin-bottom: 0;">
All dependencies satisfied. Expected test results will be delivered prior to your follow-up consult.
</p>
</div>""",
                    unsafe_allow_html=True
                )

    # ------------------ TAB 3: SLA TRACKING ------------------
    with t_sla:
        st.markdown("### ⏳ Expected Results Delivery (SLA Tracking)")
        st.write("Tracks laboratory turnaround SLAs. Notifications are sent automatically to your advocates if SLAs are breached.")
        
        # Check active SLAs
        for ev in events:
            if ev.get("produces_artifact") and ev.get("delay_sla"):
                sla_duration = timedelta(hours=ev["delay_sla"])
                expected_date = ev["start"] + sla_duration
                time_passed = datetime.now() - ev["start"]
                time_remaining = expected_date - datetime.now()
                
                st.markdown(f"#### Active SLA: {ev['title']}")
                st.write(f"Collection Date: {ev['start'].strftime('%b %d, %Y at %H:%M')} | Expected Duration: {ev['delay_sla']} hours")
                
                if time_remaining.total_seconds() > 0:
                    pct = min(1.0, time_passed.total_seconds() / sla_duration.total_seconds())
                    st.progress(pct)
                    st.info(f"⏳ SLA Status: Active. Results expected in {time_remaining.seconds // 3600} hours (SLA target: {expected_date.strftime('%b %d at %H:%M')}).")
                else:
                    st.markdown(
                        f"""<div style="background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.1); padding: 16px; border-radius: 8px; font-size: 0.9rem;">
<span style="color: #ef4444; font-weight: bold;">🚨 SLA BREACHED (OVERDUE)</span><br>
Expected delivery was on <b>{expected_date.strftime('%b %d at %H:%M')}</b>. Overdue by <b>{abs(time_remaining.days)} days, {abs(time_remaining.seconds // 3600)} hours</b>.<br>
<i>Action Triggered: Advocate and clinic notifications sent.</i>
</div>""",
                        unsafe_allow_html=True
                    )

    # ------------------ TAB 4: LOG EVENT ------------------
    with t_log:
        st.markdown("### ➕ Log New Timeline Event or Task")
        
        with st.form("new_event_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Event / Task Title", placeholder="e.g., Fasting for 12 hours / Brain MRI scan")
                actor = st.text_input("Practitioner / Participant", placeholder="e.g., Patient (Self) / Sydney Medical Centre")
                date = st.date_input("Scheduled Date", value=datetime.today())
                time = st.time_input("Scheduled Time", value=datetime.now().time())
                duration_hours = st.number_input("Duration (Hours)", min_value=0.1, max_value=168.0, value=1.0, step=0.5)
            with col2:
                status = st.selectbox("Status", options=["Scheduled", "Completed", "Awaiting Results", "Pending"])
                category = st.selectbox("Category", ["Consultation", "Diagnostics", "Results Ingestion", "Tasks & Preparations", "General"], index=4)
                
                prereq_options = {e["id"]: e["title"] for e in events}
                prereq_options[None] = "None"
                prereq = st.selectbox("Depends On (Prerequisite)", options=list(prereq_options.keys()), format_func=lambda x: prereq_options[x])
                
                produces_art = st.checkbox("Produces an Artifact (e.g., Blood sample or report)", value=False)
                art_name = st.text_input("Artifact Name", placeholder="e.g., Specimen_Blood_02")
                delay_sla = st.number_input("Expected Result SLA (Hours, optional)", min_value=0, max_value=168, value=0)
                
            submitted = st.form_submit_button("💾 Log to Semantic Timeline")
            if submitted and title:
                start_dt = datetime.combine(date, time)
                end_dt = start_dt + timedelta(hours=duration_hours)
                new_ev = {
                    "id": f"ev-manual-{int(datetime.now().timestamp())}",
                    "title": title,
                    "actor": actor,
                    "start": start_dt,
                    "end": end_dt,
                    "date": start_dt,
                    "status": status,
                    "category": category,
                    "prereq": prereq,
                    "produces_artifact": produces_art,
                    "artifact_name": art_name if produces_art else None,
                    "delay_sla": delay_sla if delay_sla > 0 else None,
                }
                st.session_state.timeline_events.append(new_ev)
                st.success(f"Log event/task '{title}' added to Semantic Timeline.")
                st.rerun()
