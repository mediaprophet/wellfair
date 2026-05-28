from __future__ import annotations

from io import StringIO
from math import isnan
from typing import Dict, Any

import pandas as pd


PROFILE_OVERRIDES: Dict[str, Dict[str, Dict[str, list[Any]]]] = {
    "synthetic": {},
    "michael": {
        "steps": {
            "count": [1200, 3600, 8200, 500, 10500, 900, 4100],
            "calorie": [45, 120, 265, 18, 320, 32, 135],
            "distance": [900, 2500, 5400, 350, 7200, 650, 2900],
        },
        "sleep": {
            "sleep_duration": [380, 260, 310, 220, 420, 360, 250],
            "efficiency": [62, 48, 55, 42, 66, 58, 46],
            "deep_sleep": [55, 30, 45, 28, 65, 48, 30],
            "rem_sleep": [70, 40, 60, 32, 75, 60, 38],
            "light_sleep": [255, 190, 205, 160, 280, 252, 182],
            "wake_up_count": [4, 6, 5, 8, 3, 5, 7],
        },
        "weight": {
            "weight": [72.0, 71.6, 71.2, 70.8, 70.4, 70.1, 69.8],
            "body_fat": [18.5, 18.3, 18.2, 18.0, 17.9, 17.8, 17.7],
            "bmi": [23.1, 22.9, 22.7, 22.5, 22.3, 22.2, 22.1],
        },
        "heart_rate": {
            "heart_rate": [82, 88, 90, 95, 85, 92, 94],
            "min": [70, 74, 76, 78, 72, 75, 76],
            "max": [130, 135, 138, 142, 134, 139, 141],
            "heart_rate_zone": ["stress", "stress", "stress", "stress", "stress", "stress", "stress"],
        },
    },
    "elena": {
        "steps": {
            "count": [400, 600, 14200, 500, 11800, 900, 3200],
            "calorie": [15, 20, 430, 18, 380, 28, 120],
            "distance": [280, 420, 9400, 320, 8800, 560, 2100],
        },
        "sleep": {
            "sleep_duration": [280, 190, 520, 210, 160, 480, 200],
            "efficiency": [58, 45, 62, 40, 38, 65, 44],
            "deep_sleep": [40, 25, 60, 30, 22, 62, 24],
            "rem_sleep": [48, 30, 80, 32, 28, 88, 30],
            "light_sleep": [192, 135, 380, 148, 110, 330, 146],
            "wake_up_count": [7, 9, 5, 8, 10, 6, 9],
        },
        "weight": {
            "weight": [63.0, 62.8, 63.6, 62.9, 62.4, 63.8, 62.6],
            "body_fat": [21.2, 21.0, 21.6, 21.1, 20.8, 21.7, 20.9],
            "bmi": [21.7, 21.6, 21.9, 21.7, 21.5, 22.0, 21.6],
        },
        "heart_rate": {
            "heart_rate": [90, 96, 105, 88, 110, 94, 102],
            "min": [72, 78, 80, 70, 82, 74, 78],
            "max": [140, 146, 156, 138, 160, 142, 150],
            "heart_rate_zone": ["anxious", "anxious", "panic", "anxious", "panic", "anxious", "panic"],
        },
    },
    "rebecca": {
        "steps": {
            "count": [800, 200, 5200, 150, 4800, 300, 2600],
            "calorie": [28, 6, 165, 5, 150, 10, 90],
            "distance": [520, 130, 3400, 100, 3200, 200, 1700],
        },
        "sleep": {
            "sleep_duration": [210, 180, 240, 170, 200, 190, 160],
            "efficiency": [44, 40, 48, 38, 45, 42, 37],
            "deep_sleep": [22, 18, 25, 16, 20, 18, 15],
            "rem_sleep": [28, 25, 30, 22, 25, 24, 21],
            "light_sleep": [160, 137, 185, 132, 155, 148, 124],
            "wake_up_count": [9, 10, 11, 10, 9, 11, 12],
        },
        "weight": {
            "weight": [58.0, 57.6, 57.3, 57.0, 56.8, 56.5, 56.3],
            "body_fat": [23.5, 23.2, 22.9, 22.6, 22.4, 22.1, 21.9],
            "bmi": [20.5, 20.3, 20.2, 20.0, 19.9, 19.7, 19.6],
        },
        "heart_rate": {
            "heart_rate": [95, 98, 102, 94, 100, 97, 103],
            "min": [80, 82, 86, 78, 84, 80, 85],
            "max": [145, 148, 152, 144, 150, 146, 154],
            "heart_rate_zone": ["alert", "alert", "alert", "alert", "alert", "alert", "alert"],
        },
    },
    "margaret": {
        "steps": {
            "count": [1800, 1600, 1900, 1500, 1700, 1400, 1650],
            "calorie": [60, 55, 63, 52, 58, 48, 56],
            "distance": [1200, 1080, 1260, 1000, 1120, 960, 1100],
        },
        "sleep": {
            "sleep_duration": [340, 320, 310, 300, 315, 330, 305],
            "efficiency": [60, 58, 56, 55, 57, 59, 55],
            "deep_sleep": [48, 44, 42, 40, 42, 46, 41],
            "rem_sleep": [60, 55, 53, 50, 53, 58, 52],
            "light_sleep": [232, 221, 215, 210, 220, 226, 212],
            "wake_up_count": [6, 7, 7, 8, 7, 6, 8],
        },
        "weight": {
            "weight": [68.0, 67.9, 67.8, 67.6, 67.5, 67.4, 67.3],
            "body_fat": [30.5, 30.4, 30.4, 30.3, 30.3, 30.2, 30.2],
            "bmi": [24.0, 23.9, 23.9, 23.8, 23.7, 23.7, 23.6],
        },
        "heart_rate": {
            "heart_rate": [88, 90, 92, 89, 91, 90, 93],
            "min": [70, 72, 74, 71, 73, 72, 74],
            "max": [128, 130, 132, 129, 131, 130, 133],
            "heart_rate_zone": ["stress", "stress", "stress", "stress", "stress", "stress", "stress"],
        },
    },
    "robert": {
        "steps": {
            "count": [900, 800, 700, 650, 600, 580, 620],
            "calorie": [30, 28, 25, 24, 22, 21, 22],
            "distance": [600, 540, 480, 450, 420, 405, 430],
        },
        "sleep": {
            "sleep_duration": [260, 250, 240, 230, 240, 235, 238],
            "efficiency": [52, 50, 49, 48, 49, 50, 49],
            "deep_sleep": [35, 33, 31, 30, 31, 32, 31],
            "rem_sleep": [38, 36, 34, 33, 34, 35, 34],
            "light_sleep": [187, 181, 175, 167, 175, 168, 173],
            "wake_up_count": [8, 9, 10, 9, 9, 8, 10],
        },
        "weight": {
            "weight": [75.0, 74.6, 74.2, 73.8, 73.4, 73.0, 72.6],
            "body_fat": [27.0, 26.8, 26.6, 26.4, 26.2, 26.0, 25.8],
            "bmi": [26.1, 25.9, 25.8, 25.6, 25.5, 25.3, 25.2],
        },
        "heart_rate": {
            "heart_rate": [102, 104, 106, 108, 110, 111, 113],
            "min": [84, 85, 86, 88, 89, 90, 91],
            "max": [155, 158, 160, 162, 164, 166, 168],
            "heart_rate_zone": ["cardiac", "cardiac", "cardiac", "cardiac", "cardiac", "cardiac", "cardiac"],
        },
    },
    "jordan": {
        "steps": {
            "count": [700, 600, 900, 500, 400, 2200, 450],
            "calorie": [24, 20, 30, 18, 15, 65, 16],
            "distance": [470, 400, 600, 320, 280, 1500, 300],
        },
        "sleep": {
            "sleep_duration": [300, 240, 310, 260, 280, 250, 230],
            "efficiency": [50, 46, 52, 48, 51, 47, 45],
            "deep_sleep": [36, 30, 38, 32, 35, 31, 29],
            "rem_sleep": [44, 36, 46, 40, 42, 38, 34],
            "light_sleep": [220, 174, 226, 188, 203, 181, 167],
            "wake_up_count": [8, 9, 8, 9, 8, 9, 10],
        },
        "weight": {
            "weight": [68.5, 68.3, 68.8, 68.0, 67.6, 68.7, 67.8],
            "body_fat": [26.0, 25.8, 26.2, 25.7, 25.4, 26.1, 25.5],
            "bmi": [23.8, 23.7, 23.9, 23.6, 23.4, 23.8, 23.5],
        },
        "heart_rate": {
            "heart_rate": [98, 100, 108, 102, 105, 110, 103],
            "min": [82, 84, 88, 85, 87, 90, 86],
            "max": [150, 152, 162, 158, 160, 165, 159],
            "heart_rate_zone": ["stress", "stress", "flare", "stress", "flare", "flare", "stress"],
        },
    },
}


def _read_csv(text: str | None) -> pd.DataFrame:
    if not text:
        return pd.DataFrame()
    return pd.read_csv(StringIO(text))


def _apply_offset(series: pd.Series, offset_minutes: pd.Series | int | float | None) -> pd.Series:
    timestamp = pd.to_datetime(series, unit="ms", utc=True, errors="coerce")
    if offset_minutes is None:
        return timestamp
    if isinstance(offset_minutes, (int, float)):
        return timestamp + pd.to_timedelta(offset_minutes, unit="m")
    # assume Series with same index
    offset = pd.to_timedelta(offset_minutes.fillna(0), unit="m")
    return timestamp + offset


def _format_date_index(index: pd.Index) -> list[str]:
    return [pd.Timestamp(x).strftime("%Y-%m-%d") for x in index]


def _safe_value(value: Any, precision: int = 1) -> str:
    try:
        if value is None:
            return "-"
        if isinstance(value, (float, int)):
            if isinstance(value, float) and isnan(value):
                return "-"
            fmt = "{:." + str(precision) + "f}"
            return fmt.format(value)
        return str(value)
    except Exception:
        return "-"


def _sleep_hours(minutes: pd.Series) -> pd.Series:
    return (minutes.fillna(0) / 60).round(2)


def _apply_overrides(df: pd.DataFrame, overrides: Dict[str, list[Any]]) -> pd.DataFrame:
    if not overrides or df.empty:
        return df
    df = df.copy()
    for column, values in overrides.items():
        if column not in df:
            continue
        limit = min(len(df), len(values))
        df.iloc[:limit, df.columns.get_loc(column)] = values[:limit]
    return df


def _apply_profile_overrides(
    steps: pd.DataFrame,
    sleep: pd.DataFrame,
    weight: pd.DataFrame,
    heart_rate: pd.DataFrame,
    profile_id: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    overrides = PROFILE_OVERRIDES.get(profile_id, {})
    return (
        _apply_overrides(steps, overrides.get("steps", {})),
        _apply_overrides(sleep, overrides.get("sleep", {})),
        _apply_overrides(weight, overrides.get("weight", {})),
        _apply_overrides(heart_rate, overrides.get("heart_rate", {})),
    )


def build_demo_dashboard(csv_map: Dict[str, str], profile_id: str = "synthetic") -> Dict[str, Any]:
    """Return structured dashboard data for the browser demo.

    Parameters
    ----------
    csv_map: dict[str, str]
        Mapping of dataset key -> CSV text.

    Returns
    -------
    dict
        JSON-serialisable payload with KPI cards, chart data, insights and timeline.
    """

    steps_df = _read_csv(csv_map.get("steps"))
    weight_df = _read_csv(csv_map.get("weight"))
    sleep_df = _read_csv(csv_map.get("sleep"))
    hr_df = _read_csv(csv_map.get("heart_rate"))

    steps_df, sleep_df, weight_df, hr_df = _apply_profile_overrides(
        steps_df, sleep_df, weight_df, hr_df, profile_id
    )

    payload: Dict[str, Any] = {
        "kpis": [],
        "charts": {},
        "insights": [],
        "timeline": [],
    }

    # Steps summary ---------------------------------------------------------
    if not steps_df.empty:
        steps_local = _apply_offset(steps_df["end_time"], steps_df.get("time_offset"))
        steps_df = steps_df.assign(local_end=steps_local, local_date=steps_local.dt.date)
        daily_steps = (
            steps_df.groupby("local_date")["count"].sum().reset_index(drop=False)
        )
        payload["charts"]["steps"] = {
            "labels": _format_date_index(daily_steps["local_date"]),
            "values": daily_steps["count"].round(0).astype(int).tolist(),
            "unit": "steps",
        }
        total_steps = int(daily_steps["count"].sum())
        avg_steps = float(daily_steps["count"].mean()) if not daily_steps.empty else 0.0
        payload["kpis"].append(
            {
                "id": "steps",
                "label": "Weekly Steps",
                "primary": f"{total_steps:,}",
                "secondary": f"Avg {avg_steps:,.0f} steps/day",
                "icon": "👣",
                "accent": "#2563eb",
            }
        )
        latest_steps = daily_steps.iloc[-1]
        payload["timeline"].append(
            {
                "title": "Steps logged",
                "date": pd.Timestamp(latest_steps["local_date"]).strftime("%Y-%m-%d"),
                "description": f"{int(latest_steps['count']):,} steps recorded.",
                "category": "activity",
            }
        )

    # Sleep summary --------------------------------------------------------
    if not sleep_df.empty:
        sleep_local_end = _apply_offset(sleep_df["end_time"], sleep_df.get("time_offset"))
        sleep_df = sleep_df.assign(local_end=sleep_local_end, local_date=sleep_local_end.dt.date)
        sleep_df["sleep_hours"] = _sleep_hours(sleep_df["sleep_duration"])
        daily_sleep = sleep_df.groupby("local_date")["sleep_hours"].sum().reset_index(drop=False)
        payload["charts"]["sleep"] = {
            "labels": _format_date_index(daily_sleep["local_date"]),
            "values": daily_sleep["sleep_hours"].round(2).tolist(),
            "unit": "hours",
        }
        avg_sleep = daily_sleep["sleep_hours"].mean()
        latest_eff = float(sleep_df.iloc[-1]["efficiency"])
        payload["kpis"].append(
            {
                "id": "sleep",
                "label": "Sleep Quality",
                "primary": f"{avg_sleep:.1f} hrs/night",
                "secondary": f"Efficiency {latest_eff:.0f}%",
                "icon": "💤",
                "accent": "#7c3aed",
            }
        )
        payload["timeline"].append(
            {
                "title": "Sleep session",
                "date": pd.Timestamp(sleep_df.iloc[-1]["local_date"]).strftime("%Y-%m-%d"),
                "description": f"{sleep_df.iloc[-1]['sleep_hours']:.1f} hours, efficiency {latest_eff:.0f}%.",
                "category": "sleep",
            }
        )
        if avg_sleep < 7:
            payload["insights"].append(
                "Average sleep is below 7 hours. Consider winding down earlier to reach the target."  # noqa: E501
            )
        elif avg_sleep >= 8:
            payload["insights"].append(
                "Consistent 8h+ sleep pattern detected — great recovery routine."  # noqa: E501
            )

    # Weight summary --------------------------------------------------------
    if not weight_df.empty:
        weight_local = _apply_offset(weight_df["end_time"], weight_df.get("time_offset"))
        weight_df = weight_df.assign(local_end=weight_local, local_date=weight_local.dt.date)
        payload["charts"]["weight"] = {
            "labels": _format_date_index(weight_df["local_date"]),
            "values": weight_df["weight"].round(2).tolist(),
            "unit": "kg",
        }
        latest_weight = weight_df.iloc[-1]["weight"]
        first_weight = weight_df.iloc[0]["weight"]
        delta = latest_weight - first_weight
        payload["kpis"].append(
            {
                "id": "weight",
                "label": "Body Weight",
                "primary": f"{latest_weight:.1f} kg",
                "secondary": f"Δ {delta:+.1f} kg from start",
                "icon": "⚖️",
                "accent": "#10b981",
            }
        )
        payload["timeline"].append(
            {
                "title": "Weight check-in",
                "date": pd.Timestamp(weight_df.iloc[-1]["local_date"]).strftime("%Y-%m-%d"),
                "description": f"Latest measurement {latest_weight:.1f} kg.",
                "category": "body",
            }
        )
        if abs(delta) >= 0.5:
            direction = "increase" if delta > 0 else "decrease"
            payload["insights"].append(
                f"Weight trend shows a {direction} of {abs(delta):.1f} kg this week."
            )

    # Heart rate summary ----------------------------------------------------
    if not hr_df.empty:
        hr_local = _apply_offset(hr_df["start_time"], hr_df.get("time_offset"))
        hr_df = hr_df.assign(local_start=hr_local, local_date=hr_local.dt.date)
        payload["charts"]["heart_rate"] = {
            "labels": _format_date_index(hr_df["local_date"]),
            "values": hr_df["heart_rate"].round(0).astype(int).tolist(),
            "unit": "bpm",
        }
        avg_hr = hr_df["heart_rate"].mean()
        payload["kpis"].append(
            {
                "id": "heart_rate",
                "label": "Resting HR",
                "primary": f"{avg_hr:.0f} bpm",
                "secondary": "Rest/Fat-burn zones alternated",
                "icon": "💓",
                "accent": "#ef4444",
            }
        )

    # Ordering: keep KPI cards consistent order
    kpi_order = ["steps", "sleep", "weight", "heart_rate"]
    payload["kpis"].sort(key=lambda item: kpi_order.index(item["id"]) if item["id"] in kpi_order else 99)

    # Timeline newest first
    payload["timeline"].sort(key=lambda item: item["date"], reverse=True)

    return payload
