from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from src.phr_models.social_work import (
    AssistanceCategory, UrgencyLevel, AssistanceStatus, AssistanceNeed,
    SocialSecurityStatus, PaymentFrequency, SocialSecurityRecord, GovernmentLetter
)
from ui.utils.components import render_info_banner

def render_social_work(dark_mode: bool):
    st.markdown("## 🤝 Social Work & Assistance Vault")
    
    render_info_banner(
        title="Social Support Systems & Sovereign Documentation",
        body="Track housing, food, and financial assistance programs. Securely store and audit government letters, review notices, and social security benefit payments in your RDF-Star graph.",
        accent_color="#0d9488",
        icon="🤝",
        dark_mode=dark_mode,
    )
    
    # Initialize mock data in session state
    now = datetime.now()
    if "assistance_needs" not in st.session_state:
        st.session_state.assistance_needs = [
            {
                "id": "need-1",
                "category": AssistanceCategory.HOUSING,
                "urgency": UrgencyLevel.HIGH,
                "description": "Sovereign transitional housing request submitted. Referral active for public housing allocation.",
                "date_logged": now - timedelta(days=12),
                "status": AssistanceStatus.PROGRAM_ACTIVE,
                "provider_name": "Link Housing NSW",
                "notes": "Spoke to Case worker. Placed on high priority register."
            },
            {
                "id": "need-2",
                "category": AssistanceCategory.FOOD,
                "urgency": UrgencyLevel.MODERATE,
                "description": "Emergency food relief vouchers for local food co-op support.",
                "date_logged": now - timedelta(days=25),
                "status": AssistanceStatus.RESOLVED,
                "provider_name": "Salvation Army Sydney",
                "notes": "Vouchers received and redeemed successfully."
            }
        ]
        
    if "social_security_payments" not in st.session_state:
        st.session_state.social_security_payments = [
            {
                "id": "pay-1",
                "agency_name": "Centrelink",
                "payment_type": "Disability Support Pension",
                "status": SocialSecurityStatus.ACTIVE,
                "amount": 1020.50,
                "frequency": PaymentFrequency.FORTNIGHTLY,
                "start_date": date(2025, 1, 8)
            },
            {
                "id": "pay-2",
                "agency_name": "Centrelink",
                "payment_type": "Rent Assistance",
                "status": SocialSecurityStatus.ACTIVE,
                "amount": 184.20,
                "frequency": PaymentFrequency.FORTNIGHTLY,
                "start_date": date(2025, 1, 8)
            }
        ]
        
    if "government_letters" not in st.session_state:
        st.session_state.government_letters = [
            {
                "id": "let-1",
                "title": "Disability Pension Eligibility Review Notice",
                "sender_agency": "Centrelink",
                "date_received": (now - timedelta(days=5)).date(),
                "summary": "Request to supply updated bank balances and asset statements to verify ongoing pension eligibility criteria.",
                "action_required": "Upload bank statement for April-May",
                "action_due_date": (now + timedelta(days=9)).date()
            },
            {
                "id": "let-2",
                "title": "Social Housing Priority Listing Confirmation",
                "sender_agency": "Department of Housing",
                "date_received": (now - timedelta(days=15)).date(),
                "summary": "Formal confirmation of priority status listing for two-bedroom accommodation allocation in Sydney metro zone.",
                "action_required": "None",
                "action_due_date": None
            }
        ]
        
    t_needs, t_payments, t_letters = st.tabs([
        "🏠 Support & Assistance Needs",
        "💰 Social Security Benefits",
        "✉️ Agency Letters & Notices"
    ])
    
    # ------------------ TAB 1: SUPPORT NEEDS ------------------
    with t_needs:
        st.markdown("### 🏠 Assistance & Support Logs")
        st.write("Track active requests, programs, and referrals for basic physiological and safety security (housing, food, legal).")
        
        col_needs_list, col_needs_add = st.columns([2, 1])
        
        with col_needs_list:
            st.markdown("#### Active Support Needs")
            for item in reversed(st.session_state.assistance_needs):
                urg_color = {
                    UrgencyLevel.CRITICAL: "#ef4444",
                    UrgencyLevel.HIGH: "#f97316",
                    UrgencyLevel.MODERATE: "#3b82f6",
                    UrgencyLevel.LOW: "#64748b"
                }.get(item["urgency"], "#64748b")
                
                status_color = {
                    AssistanceStatus.RESOLVED: "#10b981",
                    AssistanceStatus.PROGRAM_ACTIVE: "#8b5cf6",
                    AssistanceStatus.REFERRAL_SENT: "#3b82f6",
                    AssistanceStatus.IDENTIFIED: "#f59e0b"
                }.get(item["status"], "#64748b")
                
                st.markdown(
                    f"""<div class="premium-card" style="border-left: 4px solid {urg_color}; padding: 16px; margin-bottom: 12px;">
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-size:0.75rem; background:{urg_color}1a; color:{urg_color}; padding:2px 8px; border-radius:4px; font-weight:bold;">
{item["urgency"].upper()} URGENCY
</span>
<span style="font-size:0.75rem; background:{status_color}1a; color:{status_color}; padding:2px 8px; border-radius:4px; font-weight:bold;">
{item["status"].replace('-', ' ').upper()}
</span>
</div>
<h4 style="margin: 8px 0 4px 0; color:#475569;">Category: {item["category"].upper()}</h4>
<p style="font-size:0.88rem; color:#475569; margin: 4px 0;">{item["description"]}</p>
<div style="font-size:0.8rem; color:#64748b; margin-top:8px;">
<b>Provider:</b> {item["provider_name"] or "None Assigned"} | <b>Logged:</b> {item["date_logged"].strftime('%b %d, %Y')}
</div>
{"<div style='font-size:0.8rem; color:#7c3aed; margin-top:6px;'><b>Notes:</b> " + item["notes"] + "</div>" if item.get("notes") else ""}
</div>""",
                    unsafe_allow_html=True
                )
                
        with col_needs_add:
            st.markdown("#### Log New Assistance Need")
            with st.form("add_need_form", clear_on_submit=True):
                cat = st.selectbox("Category", [c.value for c in AssistanceCategory])
                urg = st.selectbox("Urgency", [u.value for u in UrgencyLevel], index=1)
                desc = st.text_area("Need Description / Details", placeholder="Specify what housing, food, or support assistance is required...")
                provider = st.text_input("Assigned Agency / Provider (Optional)", placeholder="e.g. Department of Housing")
                notes = st.text_area("Action Notes (Optional)")
                
                submitted = st.form_submit_button("💾 Log Need to Vault")
                if submitted and desc:
                    st.session_state.assistance_needs.append({
                        "id": f"need-{int(datetime.now().timestamp())}",
                        "category": AssistanceCategory(cat),
                        "urgency": UrgencyLevel(urg),
                        "description": desc,
                        "date_logged": datetime.now(),
                        "status": AssistanceStatus.IDENTIFIED,
                        "provider_name": provider if provider else None,
                        "notes": notes if notes else None
                    })
                    st.success("Assistance need logged successfully.")
                    st.rerun()

    # ------------------ TAB 2: SOCIAL SECURITY PAYMENTS ------------------
    with t_payments:
        st.markdown("### 💰 Social Security Benefits Tracker")
        st.write("Track ongoing income support, housing subsidies, and pension allocations.")
        
        col_pay_list, col_pay_chart = st.columns([1, 1])
        
        with col_pay_list:
            st.markdown("#### Active Payments & Allowances")
            for item in st.session_state.social_security_payments:
                st.markdown(
                    f"""<div class="premium-card" style="border-left: 4px solid #10b981; padding: 16px; margin-bottom: 12px;">
<div style="display:flex; justify-content:space-between; align-items:center;">
<h4 style="margin: 0; color:#475569; font-size:1.1rem;">{item["payment_type"]}</h4>
<span style="font-size:1.1rem; color:#10b981; font-weight:bold;">${item["amount"]:.2f}</span>
</div>
<div style="font-size:0.82rem; color:#64748b; margin-top:6px;">
<b>Agency:</b> {item["agency_name"]} | <b>Frequency:</b> {item["frequency"].upper()}
</div>
<div style="font-size:0.8rem; color:#64748b; margin-top:4px;">
<b>Started:</b> {item["start_date"].strftime('%b %d, %Y')} | <b>Status:</b> {item["status"].upper()}
</div>
</div>""",
                    unsafe_allow_html=True
                )
                
            # Log new payment inside list column
            with st.expander("➕ Log New Payment Stream"):
                with st.form("add_payment_form", clear_on_submit=True):
                    agency = st.text_input("Agency Name", value="Centrelink")
                    pay_type = st.text_input("Payment / Allowance Type", placeholder="e.g. Rent Assistance")
                    amount = st.number_input("Amount ($)", min_value=0.0, value=250.0)
                    freq = st.selectbox("Frequency", [f.value for f in PaymentFrequency])
                    start = st.date_input("Start Date", value=date.today())
                    
                    submitted_pay = st.form_submit_button("💾 Save Payment")
                    if submitted_pay and pay_type:
                        st.session_state.social_security_payments.append({
                            "id": f"pay-{int(datetime.now().timestamp())}",
                            "agency_name": agency,
                            "payment_type": pay_type,
                            "status": SocialSecurityStatus.ACTIVE,
                            "amount": amount,
                            "frequency": PaymentFrequency(freq),
                            "start_date": start
                        })
                        st.success(f"Payment '{pay_type}' logged.")
                        st.rerun()
                        
        with col_pay_chart:
            st.markdown("#### Payment Allocation Breakdown")
            if st.session_state.social_security_payments:
                df_pay = pd.DataFrame(st.session_state.social_security_payments)
                # Plotly Pie Chart
                fig = px.pie(
                    df_pay,
                    values="amount",
                    names="payment_type",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set2,
                    title="Fortnightly Benefit Distribution"
                )
                fig.update_layout(
                    template="plotly_dark" if dark_mode else "plotly_white",
                    margin=dict(l=10, r=10, t=40, b=10),
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No active payments logged to display allocation.")

    # ------------------ TAB 3: AGENCY LETTERS & NOTICES ------------------
    with t_letters:
        st.markdown("### ✉️ Government Correspondence & Notices")
        st.write("Track incoming letters, review notices, and compliance demands from social security or housing departments.")
        
        col_let_list, col_let_add = st.columns([2, 1])
        
        with col_let_list:
            st.markdown("#### Letters & Actions Inbox")
            for item in st.session_state.government_letters:
                action_due = item.get("action_due_date")
                
                # Check urgency of action
                action_alert = ""
                if action_due and item.get("action_required") != "None":
                    days_left = (action_due - date.today()).days
                    if days_left <= 3:
                        badge_color = "#ef4444"
                        days_text = f"CRITICAL: Due in {days_left} days"
                    elif days_left <= 7:
                        badge_color = "#f97316"
                        days_text = f"URGENT: Due in {days_left} days"
                    else:
                        badge_color = "#3b82f6"
                        days_text = f"Due in {days_left} days"
                        
                    action_alert = f"""<div style="margin-top: 10px; padding: 10px; border-radius: 8px; border-left: 4px solid {badge_color}; background: {badge_color}10;">
<div style="font-size:0.75rem; font-weight:bold; color:{badge_color}; text-transform:uppercase;">⚡ Action Required: {item["action_required"]}</div>
<div style="font-size:0.78rem; color:#64748b; margin-top:2px;"><b>Due Date:</b> {action_due.strftime('%b %d, %Y')} ({days_text})</div>
</div>"""
                
                st.markdown(
                    f"""<div class="premium-card" style="border-left: 4px solid #3b82f6; padding: 16px; margin-bottom: 12px;">
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-size:0.72rem; background:rgba(0,0,0,0.04); padding:2px 6px; border-radius:4px; color:#475569; font-weight:bold;">
{item["sender_agency"]}
</span>
<span style="font-size:0.72rem; color:#64748b;">
Received: {item["date_received"].strftime('%b %d, %Y')}
</span>
</div>
<h4 style="margin: 8px 0 4px 0; color:#475569; font-size:1.08rem;">{item["title"]}</h4>
<p style="font-size:0.85rem; color:#64748b; margin: 4px 0;">{item["summary"]}</p>
{action_alert}
</div>""",
                    unsafe_allow_html=True
                )
                
        with col_let_add:
            st.markdown("#### Ingest Government Notice")
            with st.form("add_letter_form", clear_on_submit=True):
                title = st.text_input("Notice / Letter Title", placeholder="e.g. Asset Review Notification")
                agency = st.text_input("Sender Agency / Department", placeholder="e.g. Centrelink")
                date_rec = st.date_input("Received Date", value=date.today())
                summary = st.text_area("Letter Summary / Extract", placeholder="Extract key paragraphs or describe details of the notice...")
                
                has_action = st.checkbox("Requires Action / Compliance Checklist", value=False)
                act_req = st.text_input("Action Required", placeholder="e.g. Submit updated rent certificate")
                act_due = st.date_input("Action Due Date", value=date.today() + timedelta(days=14))
                
                submitted_let = st.form_submit_button("📥 Ingest Letter to Vault")
                if submitted_let and title and summary:
                    st.session_state.government_letters.append({
                        "id": f"let-{int(datetime.now().timestamp())}",
                        "title": title,
                        "sender_agency": agency,
                        "date_received": date_rec,
                        "summary": summary,
                        "action_required": act_req if has_action else "None",
                        "action_due_date": act_due if has_action else None
                    })
                    st.success("Correspondence logged successfully.")
                    st.rerun()
