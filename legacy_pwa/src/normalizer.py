# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# https://www.linkedin.com/in/ubiquitous/
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Timestamp, unit, and column normalization for Samsung Health exports."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from src.utils import clean_column_name, data_type_from_filename

_UTC_OFFSET_RE = re.compile(
    r"^UTC(?P<sign>[+-])(?P<hours>\d{2})(?P<minutes>\d{2})?$",
    re.IGNORECASE,
)


def parse_time_offset_minutes(time_offset: Any) -> int:
    """
    Parse Samsung time_offset: integer minutes, or strings like UTC+1000 (+10:00).
    """
    if time_offset is None or (isinstance(time_offset, float) and pd.isna(time_offset)):
        return 0
    if isinstance(time_offset, (int, float)):
        return int(time_offset)

    text = str(time_offset).strip()
    if not text:
        return 0

    m = _UTC_OFFSET_RE.match(text)
    if m:
        sign = 1 if m.group("sign") == "+" else -1
        hours = int(m.group("hours"))
        mins = int(m.group("minutes") or 0)
        return sign * (hours * 60 + mins)

    try:
        return int(float(text))
    except (TypeError, ValueError):
        return 0


def parse_samsung_datetime(value: Any, time_offset: Any = 0) -> datetime | None:
    """
    Parse Samsung start/end time: Unix ms integer OR 'YYYY-MM-DD HH:MM:SS.sss' string.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    offset_mins = parse_time_offset_minutes(time_offset)
    tz = timezone(timedelta(minutes=offset_mins)) if offset_mins else timezone.utc

    # Unix epoch milliseconds
    try:
        ms_int = int(float(value))
        if ms_int > 1_000_000_000_000:
            utc_dt = datetime.fromtimestamp(ms_int / 1000.0, tz=timezone.utc)
            if offset_mins:
                local = utc_dt.astimezone(tz)
                return local
            return utc_dt
        if ms_int > 1_000_000_000:
            return datetime.fromtimestamp(ms_int, tz=tz)
    except (TypeError, ValueError):
        pass

    try:
        dt = pd.to_datetime(value, utc=False)
        if pd.isna(dt):
            return None
        py = dt.to_pydatetime()
        if py.tzinfo is None:
            return py.replace(tzinfo=tz)
        return py
    except (TypeError, ValueError):
        return None


def ms_to_aware_datetime(
    ms: Any,
    time_offset: Any = 0,
) -> datetime | None:
    """Convert Samsung time + offset to timezone-aware datetime."""
    return parse_samsung_datetime(ms, time_offset)


def ms_to_iso_with_offset(row: dict[str, Any], col: str = "start_time") -> str | None:
    """ISO 8601 string from row start_time + time_offset."""
    dt = parse_samsung_datetime(
        row.get(col) or row.get(f"com.samsung.health.{col}"),
        row.get("time_offset"),
    )
    return dt.isoformat() if dt else None


def minutes_to_iso_duration(minutes: Any) -> str | None:
    if minutes is None or (isinstance(minutes, float) and pd.isna(minutes)):
        return None
    try:
        m = int(float(minutes))
    except (TypeError, ValueError):
        return None
    if m <= 0:
        return None
    return f"PT{m}M"


def normalize_dataframe(df: pd.DataFrame, data_type: str | None = None) -> pd.DataFrame:
    """Clean column names and add derived datetime columns."""
    out = df.copy()
    out.columns = [clean_column_name(c) for c in out.columns]

    if "start_time" in out.columns:
        offsets = out["time_offset"] if "time_offset" in out.columns else 0
        out["start_datetime"] = [
            parse_samsung_datetime(st, off)
            for st, off in zip(out["start_time"], offsets)
        ]

    if "end_time" in out.columns:
        offsets = out["time_offset"] if "time_offset" in out.columns else 0
        out["end_datetime"] = [
            parse_samsung_datetime(et, off)
            for et, off in zip(out["end_time"], offsets)
        ]

    if data_type:
        out.attrs["data_type"] = data_type
    return out


def normalize_export(loaded: dict[str, Any], progress_cb=None) -> dict[str, Any]:
    """Normalize all DataFrames in a load_export() result."""
    frames: dict[str, pd.DataFrame] = {}
    total = len(loaded.get("dataframes", {}))
    
    for idx, (key, df) in enumerate(loaded.get("dataframes", {}).items()):
        if progress_cb:
            progress_cb(idx, total, f"Normalizing: {key}")
            
        dtype = data_type_from_filename(key) if key.endswith(".csv") else key
        if not key.endswith(".csv"):
            dtype = key
        frames[key] = normalize_dataframe(df, dtype)
        
    if progress_cb and total > 0:
        progress_cb(total, total, "Normalization complete.")

    return {
        **loaded,
        "dataframes": frames,
    }
