from __future__ import annotations
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from src.phr_models.pathology import DiagnosticReport, PathologyObservation, DiagnosticReportStatus
from src.phr_models.proxy_consent import PrivacyMode
from ui.utils.components import render_info_banner, render_simple_metric_card

def get_gauge_html(value: float, low: float | None, high: float | None) -> str:
    """Renders a custom HTML/CSS reference range slider gauge."""
    low_color = "#f97316"  # Orange
    norm_color = "#10b981" # Teal/Green
    high_color = "#ef4444" # Red
    
    if low is not None and high is not None:
        total_range = high - low
        if total_range <= 0:
            total_range = 1.0
        
        # Map value to percentage (0 to 100) where low is 30% and high is 70%
        if value < low:
            pct = max(0, min(29, (value / (low if low != 0 else 1.0)) * 30))
        elif value > high:
            pct = min(100, max(71, 70 + ((value - high) / (high * 0.5 if high > 0 else (0.5 if high == 0 else 1))) * 30))
        else:
            pct = 30 + ((value - low) / total_range) * 40
            
        status_label = "NORMAL"
        status_color = norm_color
        if value < low:
            status_label = "LOW"
            status_color = low_color
        elif value > high:
            status_label = "HIGH"
            status_color = high_color
            
        return f"""
        <div style="margin: 8px 0; font-family: 'Outfit', sans-serif;">
            <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #64748b; margin-bottom: 3px;">
                <span>Ref Low: <b>{low}</b></span>
                <span style="color: {status_color}; font-weight: 700; letter-spacing: 0.05em; font-size: 0.8rem;">{status_label}</span>
                <span>Ref High: <b>{high}</b></span>
            </div>
            <div style="position: relative; width: 100%; height: 10px; background: #e2e8f0; border-radius: 5px; overflow: hidden; display: flex;">
                <div style="width: 30%; height: 100%; background: #ffedd5;"></div> <!-- Orange low -->
                <div style="width: 40%; height: 100%; background: #d1fae5; border-left: 1px solid #ffffff; border-right: 1px solid #ffffff;"></div> <!-- Green normal -->
                <div style="width: 30%; height: 100%; background: #fee2e2;"></div> <!-- Red high -->
                <div style="position: absolute; left: calc({pct}% - 5px); top: 1px; width: 8px; height: 8px; background: #0f172a; border: 2px solid #ffffff; border-radius: 50%; box-shadow: 0 1px 3px rgba(0,0,0,0.3);"></div>
            </div>
        </div>
        """
    elif high is not None:
        if value <= high:
            pct = max(0, min(59, (value / (high if high > 0 else 1.0)) * 60)) if high > 0 else 30
        else:
            pct = min(100, max(61, 60 + ((value - high) / (high * 0.5 if high > 0 else 1.0)) * 40))
            
        status_label = "NORMAL"
        status_color = norm_color
        if value > high:
            status_label = "HIGH"
            status_color = high_color
            
        return f"""
        <div style="margin: 8px 0; font-family: 'Outfit', sans-serif;">
            <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #64748b; margin-bottom: 3px;">
                <span>Normal: <b>&le; {high}</b></span>
                <span style="color: {status_color}; font-weight: 700; letter-spacing: 0.05em; font-size: 0.8rem;">{status_label}</span>
                <span>Limit: <b>{high}</b></span>
            </div>
            <div style="position: relative; width: 100%; height: 10px; background: #e2e8f0; border-radius: 5px; overflow: hidden; display: flex;">
                <div style="width: 60%; height: 100%; background: #d1fae5;"></div> <!-- Green normal -->
                <div style="width: 40%; height: 100%; background: #fee2e2; border-left: 1px solid #ffffff;"></div> <!-- Red high -->
                <div style="position: absolute; left: calc({pct}% - 5px); top: 1px; width: 8px; height: 8px; background: #0f172a; border: 2px solid #ffffff; border-radius: 50%; box-shadow: 0 1px 3px rgba(0,0,0,0.3);"></div>
            </div>
        </div>
        """
    elif low is not None:
        if value >= low:
            pct = min(100, max(41, 40 + ((value - low) / (low * 0.5 if low > 0 else 1.0)) * 60))
        else:
            pct = max(0, min(39, (value / (low if low > 0 else 1.0)) * 40)) if low > 0 else 15
            
        status_label = "NORMAL"
        status_color = norm_color
        if value < low:
            status_label = "LOW"
            status_color = low_color
            
        return f"""
        <div style="margin: 8px 0; font-family: 'Outfit', sans-serif;">
            <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #64748b; margin-bottom: 3px;">
                <span>Limit: <b>{low}</b></span>
                <span style="color: {status_color}; font-weight: 700; letter-spacing: 0.05em; font-size: 0.8rem;">{status_label}</span>
                <span>Normal: <b>&ge; {low}</b></span>
            </div>
            <div style="position: relative; width: 100%; height: 10px; background: #e2e8f0; border-radius: 5px; overflow: hidden; display: flex;">
                <div style="width: 40%; height: 100%; background: #ffedd5;"></div> <!-- Orange low -->
                <div style="width: 60%; height: 100%; background: #d1fae5; border-left: 1px solid #ffffff;"></div> <!-- Green normal -->
                <div style="position: absolute; left: calc({pct}% - 5px); top: 1px; width: 8px; height: 8px; background: #0f172a; border: 2px solid #ffffff; border-radius: 50%; box-shadow: 0 1px 3px rgba(0,0,0,0.3);"></div>
            </div>
        </div>
        """
    else:
        return f"""
        <div style="margin: 8px 0; font-family: 'Outfit', sans-serif;">
            <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #64748b; margin-bottom: 3px;">
                <span>Reference Range: <b>N/A</b></span>
                <span style="color: #6366f1; font-weight: 700; letter-spacing: 0.05em; font-size: 0.8rem;">RECORDED</span>
            </div>
            <div style="position: relative; width: 100%; height: 10px; background: #cbd5e1; border-radius: 5px;"></div>
        </div>
        """

def render_pathology(dark_mode: bool):
    st.markdown("## 🔬 Lab & Pathology Results")
    
    render_info_banner(
        title="Diagnostic & Lab Observational Informatics",
        body="Track clinically validated laboratory results, pathology panels, and custom bio-measurements. Use the trending engine to map values chronologically and verify references. All records adhere to strict privacy controls.",
        accent_color="#0d9488",
        icon="🧪",
        dark_mode=dark_mode,
    )

    # Initialize reports list if missing
    if "diagnostic_reports" not in st.session_state:
        st.session_state.diagnostic_reports = []
        
    reports = st.session_state.diagnostic_reports
    
    # Summary Metrics Row
    c_met1, c_met2, c_met3 = st.columns(3)
    
    # Calculate some summary stats
    total_obs = sum(len(r.observations) for r in reports)
    sensitive_tests = sum(1 for r in reports if r.privacy_mode == PrivacyMode.MODE_A_STRICT)
    
    # Find latest Fasting Glucose
    latest_glucose = "N/A"
    glucose_obs = []
    for r in reports:
        for o in r.observations:
            if "glucose" in o.test_name.lower():
                glucose_obs.append((r.date_issued, o))
    if glucose_obs:
        glucose_obs.sort(key=lambda x: x[0])
        val = glucose_obs[-1][1].value
        unit = glucose_obs[-1][1].unit
        latest_glucose = f"{val} {unit}"
        
    with c_met1:
        render_simple_metric_card(
            title="Diagnostic Reports",
            value=f"{len(reports)} Reports",
            subtitle=f"{total_obs} Total test observations",
        )
    with c_met2:
        render_simple_metric_card(
            title="Fasting Blood Glucose",
            value=latest_glucose,
            subtitle="Latest glycemic biochemistry",
        )
    with c_met3:
        render_simple_metric_card(
            title="Protected Diagnostics",
            value=f"{sensitive_tests} Secured",
            subtitle="Strict Privacy Mode A activated",
        )
        
    tab_timeline, tab_trends, tab_add = st.tabs([
        "📅 Reports Timeline",
        "📈 Biomarker Trends",
        "➕ Log Lab Results"
    ])
    
    # ------------------ TAB 1: TIMELINE ------------------
    with tab_timeline:
        st.markdown("### 📁 Pathology Reports Archive")
        if not reports:
            st.info("No diagnostic reports in vault yet. Log results manually or process reports in the Ingestion tab.")
        else:
            # Sort reports chronologically desc
            sorted_reports = sorted(reports, key=lambda x: x.date_issued, reverse=True)
            
            for idx, r in enumerate(sorted_reports):
                title_lbl = f"📄 Pathology Report — {r.pdf_attachment_uri.split('/')[-1].replace('.enc', '')}"
                org_name = "Laverty Pathology" if "laverty" in r.pdf_attachment_uri.lower() else ("Douglas Hanly Moir" if "dhm" in r.pdf_attachment_uri.lower() else ("Sydney Sexual Health Centre" if "sshc" in r.pdf_attachment_uri.lower() else "Unknown Lab"))
                
                priv_tag = "🔒 STRICT (MODE A)" if r.privacy_mode == PrivacyMode.MODE_A_STRICT else "🛡️ PRIVILEGED (MODE B)"
                priv_color = "#ef4444" if r.privacy_mode == PrivacyMode.MODE_A_STRICT else "#0d9488"
                
                with st.expander(f"{title_lbl} ({r.date_issued.strftime('%Y-%m-%d')})", expanded=(idx==0)):
                    col_det, col_priv = st.columns([2, 1])
                    with col_det:
                        st.markdown(
                            f"""
                            **Issuing Lab:** {org_name}<br>
                            **Date Issued:** {r.date_issued.strftime('%B %d, %Y')}<br>
                            **Diagnostic Status:** `{r.status.value.upper()}`<br>
                            **Attachment:** `{r.pdf_attachment_uri}`
                            """,
                            unsafe_allow_html=True
                        )
                    with col_priv:
                        st.markdown(f"<div style='color: {priv_color}; font-weight: bold;'>Privacy Level: {priv_tag}</div>", unsafe_allow_html=True)
                        st.caption("Change privacy bounds:")
                        new_priv = st.selectbox(
                            "Privacy Setting",
                            options=[PrivacyMode.MODE_A_STRICT, PrivacyMode.MODE_B_PRIVILEGED, PrivacyMode.MODE_C_SHARED],
                            format_func=lambda x: x.name,
                            index=[PrivacyMode.MODE_A_STRICT, PrivacyMode.MODE_B_PRIVILEGED, PrivacyMode.MODE_C_SHARED].index(r.privacy_mode),
                            key=f"rep_priv_{r.id}_{idx}"
                        )
                        if new_priv != r.privacy_mode:
                            r.privacy_mode = new_priv
                            # Update observation privacy modes in report
                            for o in r.observations:
                                o.privacy_mode = new_priv
                            st.success("Privacy mode updated!")
                            st.rerun()
                            
                    st.divider()
                    st.markdown("#### 🔬 Extracted Biomarkers")
                    
                    if not r.observations:
                        st.warning("No observations found in this report.")
                    else:
                        for o in r.observations:
                            c_name, c_val, c_gauge = st.columns([1.5, 1, 2.5])
                            
                            c_name.markdown(f"**{o.test_name}**")
                            c_val.markdown(f"### {o.value} <span style='font-size: 0.9rem; color: #64748b;'>{o.unit}</span>", unsafe_allow_html=True)
                            
                            gauge_html = get_gauge_html(o.value, o.reference_range_low, o.reference_range_high)
                            c_gauge.markdown(gauge_html, unsafe_allow_html=True)
                            st.markdown("<hr style='margin: 8px 0px; border-color: rgba(0,0,0,0.05);'/>", unsafe_allow_html=True)
                            
    # ------------------ TAB 2: TRENDS ------------------
    with tab_trends:
        st.markdown("### 📈 Chronological Biomarker Trending")
        st.write("Trend individual biomarkers chronologically across all diagnostics committed to the vault.")
        
        # Get all unique test names
        all_test_names = set()
        for r in reports:
            for o in r.observations:
                all_test_names.add(o.test_name)
                
        if not all_test_names:
            st.info("Log results to unlock trending tools.")
        else:
            selected_test = st.selectbox("Select Biomarker to Trend", sorted(list(all_test_names)))
            
            # Gather chronological values
            trend_data = []
            test_low = None
            test_high = None
            test_unit = ""
            
            for r in reports:
                for o in r.observations:
                    if o.test_name == selected_test:
                        trend_data.append({
                            "Date": r.date_issued,
                            "Value": o.value,
                            "Report": r.pdf_attachment_uri.split('/')[-1]
                        })
                        if o.reference_range_low is not None:
                            test_low = o.reference_range_low
                        if o.reference_range_high is not None:
                            test_high = o.reference_range_high
                        test_unit = o.unit
                        
            trend_df = pd.DataFrame(trend_data).sort_values("Date")
            
            if trend_df.empty:
                st.warning("No data points found for the selected biomarker.")
            else:
                # Plotly Chart
                fig = go.Figure()
                
                # Shaded reference range region if we have limits
                if test_low is not None and test_high is not None:
                    # Shaded box for normal range
                    fig.add_vrect(
                        x0=trend_df["Date"].min(),
                        x1=trend_df["Date"].max(),
                        fillcolor="rgba(16, 185, 129, 0.1)", # transparent teal
                        layer="below",
                        line_width=0,
                        annotation_text="Normal Range",
                        annotation_position="inside top left"
                    )
                    # Add reference range dashed lines
                    fig.add_hline(y=test_low, line_dash="dash", line_color="#f97316", annotation_text=f"Low limit ({test_low})")
                    fig.add_hline(y=test_high, line_dash="dash", line_color="#ef4444", annotation_text=f"High limit ({test_high})")
                elif test_high is not None:
                    # Only high limit
                    fig.add_hrect(
                        y0=0,
                        y1=test_high,
                        fillcolor="rgba(16, 185, 129, 0.1)",
                        layer="below",
                        line_width=0,
                        annotation_text="Normal Range",
                        annotation_position="inside top left"
                    )
                    fig.add_hline(y=test_high, line_dash="dash", line_color="#ef4444", annotation_text=f"High limit ({test_high})")
                elif test_low is not None:
                    # Only low limit
                    fig.add_hline(y=test_low, line_dash="dash", line_color="#f97316", annotation_text=f"Low limit ({test_low})")
                
                # Main line trend
                fig.add_trace(
                    go.Scatter(
                        x=trend_df["Date"],
                        y=trend_df["Value"],
                        mode="lines+markers",
                        name=selected_test,
                        line=dict(color="#0d9488", width=3),
                        marker=dict(size=8, color="#1e293b", line=dict(color="#14b8a6", width=2)),
                        text=trend_df["Report"],
                        hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Value:</b> %{y} " + test_unit + "<br><b>Source:</b> %{text}<extra></extra>"
                    )
                )
                
                fig.update_layout(
                    title=f"Chronological Trend: {selected_test}",
                    xaxis_title="Date",
                    yaxis_title=f"Value ({test_unit})",
                    template="plotly_white",
                    height=400,
                    margin=dict(l=20, r=20, t=50, b=20)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Render tabular values
                st.markdown("#### 📋 Diagnostic Records Table")
                disp_df = trend_df.copy()
                disp_df["Date"] = disp_df["Date"].dt.strftime('%Y-%m-%d')
                st.dataframe(disp_df, use_container_width=True)
                
    # ------------------ TAB 3: LOG RESULTS ------------------
    with tab_add:
        st.markdown("### ➕ Record Manual Lab Findings")
        st.write("Directly log external pathology results or self-measurements into the vault. Custom ranges are verified instantly.")
        
        # Init dynamic rows state
        if "man_obs_count" not in st.session_state:
            st.session_state.man_obs_count = 1
            
        col_meta1, col_meta2 = st.columns(2)
        with col_meta1:
            man_lab = st.text_input("Laboratory / Provider", value="Douglas Hanly Moir", placeholder="e.g. Laverty Pathology")
            man_date = st.date_input("Date of Collection", value=datetime.now())
        with col_meta2:
            man_status = st.selectbox("Status", options=[s.value for s in DiagnosticReportStatus], index=1)
            man_priv = st.selectbox("Privacy Level", options=[PrivacyMode.MODE_A_STRICT, PrivacyMode.MODE_B_PRIVILEGED, PrivacyMode.MODE_C_SHARED], format_func=lambda x: x.name, index=1)
            
        st.markdown("#### Observations")
        
        manual_obs_list = []
        
        for idx in range(st.session_state.man_obs_count):
            st.markdown(f"##### Test #{idx + 1}")
            c_o1, c_o2, c_o3, c_o4, c_o5 = st.columns([2, 1, 1, 1.2, 1.2])
            
            t_name = c_o1.text_input("Biomarker Name", placeholder="e.g. Blood Glucose", key=f"man_name_{idx}")
            t_val = c_o2.number_input("Value", value=0.0, step=0.1, key=f"man_val_{idx}")
            t_unit = c_o3.text_input("Unit", placeholder="mmol/L", value="mmol/L", key=f"man_unit_{idx}")
            
            # Optional range bounds
            has_low = c_o4.checkbox("Has Low Limit", value=False, key=f"man_has_low_{idx}")
            t_low = None
            if has_low:
                t_low = c_o4.number_input("Low Bound", value=0.0, step=0.1, key=f"man_low_{idx}")
                
            has_high = c_o5.checkbox("Has High Limit", value=False, key=f"man_has_high_{idx}")
            t_high = None
            if has_high:
                t_high = c_o5.number_input("High Bound", value=0.0, step=0.1, key=f"man_high_{idx}")
                
            if t_name:
                manual_obs_list.append(
                    PathologyObservation(
                        id=f"man-obs-{idx}-{int(datetime.now().timestamp())}",
                        test_name=t_name,
                        value=t_val,
                        unit=t_unit,
                        reference_range_low=t_low,
                        reference_range_high=t_high,
                        privacy_mode=man_priv
                    )
                )
            st.markdown("<hr style='margin: 10px 0px; border-color: rgba(0,0,0,0.05);'/>", unsafe_allow_html=True)
            
        c_btn1, c_btn2 = st.columns(2)
        if c_btn1.button("➕ Add Another Test Row"):
            st.session_state.man_obs_count += 1
            st.rerun()
            
        if c_btn2.button("➖ Remove Last Row") and st.session_state.man_obs_count > 1:
            st.session_state.man_obs_count -= 1
            st.rerun()
            
        st.divider()
        if st.button("💾 Save Report to Vault", type="primary"):
            if not manual_obs_list:
                st.error("Please add at least one valid Biomarker observation.")
            else:
                new_report = DiagnosticReport(
                    id=f"man-rep-{int(datetime.now().timestamp())}",
                    patient_id="patient-self",
                    date_issued=datetime(man_date.year, man_date.month, man_date.day),
                    status=DiagnosticReportStatus(man_status),
                    pdf_attachment_uri=f"vault://docs/manual-{man_lab.lower().replace(' ', '-')}-{int(datetime.now().timestamp())}.pdf.enc",
                    privacy_mode=man_priv,
                    observations=manual_obs_list
                )
                st.session_state.diagnostic_reports.append(new_report)
                
                # Reset counts
                st.session_state.man_obs_count = 1
                st.success("Successfully logged pathology report to Vault!")
                st.rerun()
