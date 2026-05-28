from __future__ import annotations

from typing import Dict, List

import pandas as pd

from .selectors import find_df_by_datatype, find_df_by_keyword


def get_dashboard_metrics(normalized: dict) -> dict:
    metrics = {
        "steps": {"value": "No Data", "subtitle": "Daily average steps"},
        "sleep": {"value": "No Data", "subtitle": "Average sleep duration"},
        "weight": {"value": "No Data", "subtitle": "Latest body weight"},
        "heart_rate": {"value": "No Data", "subtitle": "Average active HR"},
    }
    
    weight_df = find_df_by_keyword(normalized, "weight")
    if weight_df is not None and not weight_df.empty:
        if "weight" in weight_df.columns:
            if "start_datetime" in weight_df.columns:
                weight_df = weight_df.sort_values("start_datetime")
            latest_w = weight_df["weight"].dropna().iloc[-1]
            metrics["weight"]["value"] = f"{latest_w:.1f} kg"
            
    steps_df = find_df_by_keyword(normalized, "pedometer_day_summary")
    if steps_df is not None and not steps_df.empty:
        col_name = "count" if "count" in steps_df.columns else ("step_count" if "step_count" in steps_df.columns else None)
        if col_name:
            avg_steps = steps_df[col_name].dropna().mean()
            metrics["steps"]["value"] = f"{int(avg_steps):,} steps"
    elif (steps_df := find_df_by_keyword(normalized, "step_daily_trend")) is not None and not steps_df.empty:
        col_name = "count" if "count" in steps_df.columns else ("step_count" if "step_count" in steps_df.columns else None)
        if col_name:
            avg_steps = steps_df[col_name].dropna().mean()
            metrics["steps"]["value"] = f"{int(avg_steps):,} steps"
    elif (steps_df := find_df_by_keyword(normalized, "pedometer_step_count")) is not None and not steps_df.empty:
        col_name = "count" if "count" in steps_df.columns else ("step_count" if "step_count" in steps_df.columns else None)
        if col_name:
            avg_steps = steps_df[col_name].dropna().mean()
            metrics["steps"]["value"] = f"{int(avg_steps):,} steps"
            
    sleep_df = find_df_by_datatype(normalized, "com.samsung.shealth.sleep")
    if sleep_df is not None and not sleep_df.empty:
        if "sleep_duration" in sleep_df.columns:
            avg_mins = sleep_df["sleep_duration"].dropna().mean()
            hrs = int(avg_mins // 60)
            mins = int(avg_mins % 60)
            metrics["sleep"]["value"] = f"{hrs}h {mins}m"
        elif "efficiency" in sleep_df.columns:
            avg_eff = sleep_df["efficiency"].dropna().mean()
            metrics["sleep"]["value"] = f"{avg_eff:.1f}% efficiency"
            
    hr_df = find_df_by_keyword(normalized, "heart_rate")
    if hr_df is not None and not hr_df.empty:
        hr_col = "heart_rate" if "heart_rate" in hr_df.columns else ("pulse" if "pulse" in hr_df.columns else None)
        if hr_col:
            avg_hr = hr_df[hr_col].dropna().mean()
            metrics["heart_rate"]["value"] = f"{int(avg_hr)} BPM"
            
    return metrics


def extract_timeline_events(normalized: dict) -> list[dict]:
    events = []
    
    def get_col_val(row, alternatives):
        for alt in alternatives:
            if alt in row:
                return row[alt]
        for key in row.keys():
            for alt in alternatives:
                if key.endswith("." + alt):
                    return row[key]
        return None

    def parse_samsung_time(raw_val):
        if pd.isna(raw_val) or raw_val is None:
            return None
        try:
            if isinstance(raw_val, (int, float)):
                dt = pd.to_datetime(raw_val, unit='ms')
            else:
                dt = pd.to_datetime(raw_val)
            if dt.year < 2000:
                return None
            return dt
        except Exception:
            return None

    exercise_df = find_df_by_keyword(normalized, "exercise")
    if exercise_df is not None and not exercise_df.empty:
        for _, row_pd in exercise_df.iterrows():
            row = row_pd.to_dict()
            dt = parse_samsung_time(get_col_val(row, ["start_datetime", "start_time"]))
            if dt is None:
                continue
            
            ex_type_code = get_col_val(row, ["exercise_type"])
            ex_type_map = {
                1001: "Walking 🚶",
                1002: "Running 🏃",
                1003: "Cycling 🚴",
                1004: "Swimming 🏊",
                10026: "Stretching 🧘",
                10027: "Strength Training 🏋️",
                13001: "Hiking 🥾",
                14001: "Aerobics 💃",
                15001: "Yoga 🧘",
            }
            try:
                ex_code_val = int(float(ex_type_code)) if ex_type_code is not None and not pd.isna(ex_type_code) else 0
            except ValueError:
                ex_code_val = 0
            ex_name = ex_type_map.get(ex_code_val, "Workout 🏃")
            
            duration = get_col_val(row, ["duration"])
            dur_mins = 0
            if duration is not None and not pd.isna(duration):
                try:
                    dur_val = float(duration)
                    if dur_val > 10000:
                        dur_mins = int(dur_val / 60000)
                    else:
                        dur_mins = int(dur_val)
                except ValueError:
                    pass
                    
            calories = get_col_val(row, ["calorie"])
            distance = get_col_val(row, ["distance"])
            
            desc_parts = []
            if dur_mins > 0:
                desc_parts.append(f"⏱️ **Duration:** {dur_mins} mins")
            if calories is not None and not pd.isna(calories) and float(calories) > 0:
                desc_parts.append(f"🔥 **Calories:** {int(float(calories))} kcal")
            if distance is not None and not pd.isna(distance) and float(distance) > 0:
                dist_km = float(distance) / 1000.0
                desc_parts.append(f"📏 **Distance:** {dist_km:.2f} km")
                
            desc = " | ".join(desc_parts) if desc_parts else "Exercise session logged."
            
            events.append({
                "datetime": dt,
                "title": f"Workout: {ex_name}",
                "category": "Activity",
                "emoji": "🏃",
                "color": "#3b82f6",
                "description": desc,
                "raw": row
            })
            
    badge_df = find_df_by_keyword(normalized, "badge")
    if badge_df is not None and not badge_df.empty:
        for _, row_pd in badge_df.iterrows():
            row = row_pd.to_dict()
            dt = parse_samsung_time(get_col_val(row, ["start_time", "create_time", "update_time"]))
            if dt is None:
                continue
            
            key_name = get_col_val(row, ["key"]) or "badge"
            friendly_name = str(key_name).replace("_", " ").title()
            
            events.append({
                "datetime": dt,
                "title": f"Badge Achieved: {friendly_name}",
                "category": "Achievement",
                "emoji": "🏅",
                "color": "#fbbf24",
                "description": f"Earned the **{friendly_name}** badge for health achievements.",
                "raw": row
            })
            
    ecg_df = find_df_by_keyword(normalized, "ecg")
    if ecg_df is not None and not ecg_df.empty:
        for _, row_pd in ecg_df.iterrows():
            row = row_pd.to_dict()
            dt = parse_samsung_time(get_col_val(row, ["start_datetime", "start_time"]))
            if dt is None:
                continue
            
            hr = get_col_val(row, ["mean_heart_rate"])
            hr_str = f" {int(float(hr))} BPM" if hr is not None and not pd.isna(hr) else ""
            
            events.append({
                "datetime": dt,
                "title": "ECG Recording completed",
                "category": "Cardiovascular",
                "emoji": "🩺",
                "color": "#ef4444",
                "description": f"Electrocardiogram recording completed.{f' Mean heart rate was **{hr_str}**.' if hr_str else ''}",
                "raw": row
            })
            
    weight_df = find_df_by_keyword(normalized, "weight")
    if weight_df is not None and not weight_df.empty:
        for _, row_pd in weight_df.iterrows():
            row = row_pd.to_dict()
            dt = parse_samsung_time(get_col_val(row, ["start_datetime", "start_time"]))
            if dt is None:
                continue
            
            w = get_col_val(row, ["weight"])
            bmi = get_col_val(row, ["bmi"])
            desc_parts = []
            if w is not None and not pd.isna(w):
                desc_parts.append(f"⚖️ **Weight:** {float(w):.1f} kg")
            if bmi is not None and not pd.isna(bmi) and float(bmi) > 0:
                desc_parts.append(f"📊 **BMI:** {float(bmi):.1f}")
            
            events.append({
                "datetime": dt,
                "title": "Body Weight Logged",
                "category": "Body / Profile",
                "emoji": "⚖️",
                "color": "#10b981",
                "description": " | ".join(desc_parts) if desc_parts else "Weight log recorded.",
                "raw": row
            })
            
    alert_df = find_df_by_keyword(normalized, "alerted_heart_rate")
    if alert_df is not None and not alert_df.empty:
        for _, row_pd in alert_df.iterrows():
            row = row_pd.to_dict()
            dt = parse_samsung_time(get_col_val(row, ["start_datetime", "start_time"]))
            if dt is None:
                continue
            
            hr = get_col_val(row, ["heart_rate"])
            events.append({
                "datetime": dt,
                "title": f"Heart Rate Alert: {int(float(hr))} BPM",
                "category": "Cardiovascular",
                "emoji": "⚠️",
                "color": "#b91c1c",
                "description": f"High or low heart rate alert triggered. Wearable sensor registered **{int(float(hr))} BPM**.",
                "raw": row
            })
            
    for ev in events:
        if hasattr(ev["datetime"], "to_pydatetime"):
            ev["datetime"] = ev["datetime"].to_pydatetime()
        if ev["datetime"].tzinfo is not None:
            ev["datetime"] = ev["datetime"].replace(tzinfo=None)
            
    events = sorted(events, key=lambda x: x["datetime"], reverse=True)
    return events
