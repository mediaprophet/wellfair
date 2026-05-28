# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# https://www.linkedin.com/in/ubiquitous/
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Generate synthetic Samsung Health export for local testing."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "synthetic_samsung_export"


def _ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    jsons = OUT / "jsons"
    jsons.mkdir(exist_ok=True)

    base = datetime(2026, 5, 1, 8, 0, tzinfo=timezone.utc)
    offset = 60  # UTC+1

    # Weight — 14 days
    weight_rows = []
    for i in range(14):
        t = base + timedelta(days=i, hours=7)
        weight_rows.append(
            {
                "uuid": str(uuid.uuid4()),
                "start_time": _ms(t),
                "end_time": _ms(t + timedelta(minutes=1)),
                "time_offset": offset,
                "weight": round(72.0 + i * 0.15 - (i % 3) * 0.2, 2),
                "body_fat": round(18.5 + i * 0.1, 1),
                "muscle_mass": 32.1,
                "body_water": 55.2,
                "skeletal_muscle": 30.5,
                "bmi": round(23.1 + i * 0.05, 1),
            }
        )
    pd.DataFrame(weight_rows).to_csv(
        OUT / "com.samsung.health.weight.20260525120000.csv", index=False
    )

    # Sleep — 7 nights
    sleep_rows = []
    for i in range(7):
        bed = base + timedelta(days=i, hours=23)
        wake = bed + timedelta(hours=7, minutes=20 + i * 5)
        duration = int((wake - bed).total_seconds() / 60)
        sleep_rows.append(
            {
                "uuid": str(uuid.uuid4()),
                "start_time": _ms(bed),
                "end_time": _ms(wake),
                "time_offset": offset,
                "sleep_duration": duration,
                "efficiency": min(95, 78 + i * 2),
                "deep_sleep": 90 + i * 5,
                "rem_sleep": 110,
                "light_sleep": duration - 200,
                "wake_up_count": i % 3,
            }
        )
    pd.DataFrame(sleep_rows).to_csv(
        OUT / "com.samsung.shealth.sleep.20260525120000.csv", index=False
    )

    # Heart rate — with binning JSON
    hr_rows = []
    for i in range(10):
        t = base + timedelta(days=i % 7, hours=10 + i)
        jname = f"hr_bin_{i}.json"
        with (jsons / jname).open("w", encoding="utf-8") as f:
            json.dump(
                {"bins": [{"bpm": 60 + j, "count": 5} for j in range(12)]},
                f,
            )
        hr_rows.append(
            {
                "uuid": str(uuid.uuid4()),
                "start_time": _ms(t),
                "time_offset": offset,
                "heart_rate": 68 + i,
                "min": 58 + i,
                "max": 120 + i,
                "heart_rate_zone": "fat_burn" if i % 2 else "rest",
                "binning_data": jname,
            }
        )
    pd.DataFrame(hr_rows).to_csv(
        OUT / "com.samsung.health.heart_rate.20260525120000.csv", index=False
    )

    # Exercise
    ex_rows = []
    for i in range(5):
        start = base + timedelta(days=i * 2, hours=18)
        end = start + timedelta(minutes=35 + i * 5)
        ex_rows.append(
            {
                "uuid": str(uuid.uuid4()),
                "start_time": _ms(start),
                "end_time": _ms(end),
                "time_offset": offset,
                "duration": int((end - start).total_seconds() / 60),
                "calorie": 280 + i * 40,
                "distance": 4200 + i * 500,
                "exercise_type": "running" if i % 2 else "walking",
            }
        )
    pd.DataFrame(ex_rows).to_csv(
        OUT / "com.samsung.health.exercise.20260525120000.csv", index=False
    )

    # Steps — daily
    step_rows = []
    for i in range(14):
        day = base + timedelta(days=i)
        end = day + timedelta(hours=23, minutes=59)
        step_rows.append(
            {
                "uuid": str(uuid.uuid4()),
                "start_time": _ms(day),
                "end_time": _ms(end),
                "time_offset": offset,
                "count": 6500 + i * 420,
                "calorie": 210 + i * 15,
                "distance": 4800 + i * 300,
            }
        )
    pd.DataFrame(step_rows).to_csv(
        OUT / "com.samsung.health.pedometer_step_count.20260525120000.csv",
        index=False,
    )

    print(f"Synthetic export written to {OUT}")


if __name__ == "__main__":
    main()
