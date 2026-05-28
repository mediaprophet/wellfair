from __future__ import annotations

from io import StringIO
from math import isnan
from typing import Dict, Any

import pandas as pd


PROFILE_OVERRIDES: Dict[str, Dict[str, Dict[str, list[Any]]]] = {
    "synthetic": {},
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
