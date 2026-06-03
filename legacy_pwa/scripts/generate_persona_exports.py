"""Generate synthetic Samsung Health exports for all wellfair demo personas."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEMO_ROOT = ROOT / "demo"


def _ms(dt: datetime) -> int:
    """Convert datetime to milliseconds since epoch."""
    return int(dt.timestamp() * 1000)


def generate_michael_r() -> None:
    """Michael R. – Homelessness & family separation stress."""
    out = DEMO_ROOT / "personas" / "michael_r" / "samsung_export"
    out.mkdir(parents=True, exist_ok=True)
    jsons = out / "jsons"
    jsons.mkdir(exist_ok=True)

    base = datetime(2026, 5, 1, 8, 0, tzinfo=timezone.utc)
    offset = 60

    # Sleep: Highly fragmented, poor efficiency
    sleep_rows = []
    for i in range(28):
        bed_time = base + timedelta(days=i, hours=23 + (i % 2) * 2)
        duration = 240 + (i % 3) * 30 - 60  # 4-5.5 hours
        wake_time = bed_time + timedelta(minutes=duration)
        sleep_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(bed_time),
            "end_time": _ms(wake_time),
            "time_offset": offset,
            "sleep_duration": duration,
            "efficiency": 45 + (i % 10),
            "deep_sleep": 15 + (i % 10),
            "rem_sleep": 40 + (i % 20),
            "light_sleep": duration - 55 - (i % 10),
            "wake_up_count": 4 + (i % 3),
        })
    pd.DataFrame(sleep_rows).to_csv(
        out / "com.samsung.shealth.sleep.20260528120000.csv", index=False
    )

    # Heart rate: Elevated, variable
    hr_rows = []
    for i in range(20):
        t = base + timedelta(days=i % 28, hours=10 + i % 12)
        jname = f"hr_bin_{i}.json"
        with (jsons / jname).open("w", encoding="utf-8") as f:
            json.dump({"bins": [{"bpm": 75 + j, "count": 3 + (j % 2)} for j in range(15)]}, f)
        hr_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(t),
            "time_offset": offset,
            "heart_rate": 78 + (i % 12),
            "min": 68 + (i % 10),
            "max": 130 + (i % 15),
            "heart_rate_zone": "rest" if i % 3 else "fat_burn",
            "binning_data": jname,
        })
    pd.DataFrame(hr_rows).to_csv(out / "com.samsung.health.heart_rate.20260528120000.csv", index=False)

    # Steps: Highly variable (work days vs shelter days)
    step_rows = []
    for i in range(28):
        day = base + timedelta(days=i)
        end = day + timedelta(hours=23, minutes=59)
        # Some days high (work), many days low (shelter)
        if i % 5 == 0:
            count = 12000 + (i % 3000)  # Work day
        elif i % 5 == 4:
            count = 500 + (i % 1000)  # Shelter day
        else:
            count = 4000 + (i % 3000)  # Mixed
        step_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(day),
            "end_time": _ms(end),
            "time_offset": offset,
            "count": count,
            "calorie": count // 20,
            "distance": count * 0.76,
        })
    pd.DataFrame(step_rows).to_csv(
        out / "com.samsung.health.pedometer_step_count.20260528120000.csv", index=False
    )

    # Weight: Gradual decline from stress/irregular eating
    weight_rows = []
    for i in range(14):
        t = base + timedelta(days=i * 2, hours=7)
        weight_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(t),
            "end_time": _ms(t + timedelta(minutes=1)),
            "time_offset": offset,
            "weight": round(82.0 - i * 0.35, 2),
            "body_fat": round(21.5 - i * 0.1, 1),
            "muscle_mass": 28.5,
            "body_water": 53.0,
            "skeletal_muscle": 27.0,
            "bmi": round(26.2 - i * 0.11, 1),
        })
    pd.DataFrame(weight_rows).to_csv(
        out / "com.samsung.health.weight.20260528120000.csv", index=False
    )


def generate_elena_v() -> None:
    """Elena V. – PTSD, trauma recovery, housing instability."""
    out = DEMO_ROOT / "personas" / "elena_v" / "samsung_export"
    out.mkdir(parents=True, exist_ok=True)
    jsons = out / "jsons"
    jsons.mkdir(exist_ok=True)

    base = datetime(2026, 5, 1, 8, 0, tzinfo=timezone.utc)
    offset = 60

    # Sleep: Severely fragmented, nightmares
    sleep_rows = []
    for i in range(28):
        bed_time = base + timedelta(days=i, hours=23 + (i % 3) * 1.5)
        duration = 200 + (i % 4) * 20 - 40  # 3.5-5 hours, irregular
        wake_time = bed_time + timedelta(minutes=duration)
        sleep_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(bed_time),
            "end_time": _ms(wake_time),
            "time_offset": offset,
            "sleep_duration": duration,
            "efficiency": 35 + (i % 15),
            "deep_sleep": 10 + (i % 8),
            "rem_sleep": 20 + (i % 40),  # Highly variable (nightmares)
            "light_sleep": duration - 30 - (i % 15),
            "wake_up_count": 6 + (i % 4),
        })
    pd.DataFrame(sleep_rows).to_csv(
        out / "com.samsung.shealth.sleep.20260528120000.csv", index=False
    )

    # Heart rate: Highly elevated and variable
    hr_rows = []
    for i in range(20):
        t = base + timedelta(days=i % 28, hours=10 + i % 12)
        jname = f"hr_bin_{i}.json"
        with (jsons / jname).open("w", encoding="utf-8") as f:
            json.dump({"bins": [{"bpm": 82 + j, "count": 2 + (j % 3)} for j in range(20)]}, f)
        hr_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(t),
            "time_offset": offset,
            "heart_rate": 85 + (i % 18),
            "min": 72 + (i % 12),
            "max": 140 + (i % 20),
            "heart_rate_zone": "fat_burn" if i % 2 else "cardio",
            "binning_data": jname,
        })
    pd.DataFrame(hr_rows).to_csv(out / "com.samsung.health.heart_rate.20260528120000.csv", index=False)

    # Steps: Erratic, volatile changes
    step_rows = []
    for i in range(28):
        day = base + timedelta(days=i)
        end = day + timedelta(hours=23, minutes=59)
        if i % 7 == 0:
            count = 1000 + (i % 500)  # Low activity day
        elif i % 7 == 4:
            count = 8000 + (i % 2000)  # High activity day (manic?stress?)
        else:
            count = 3000 + (i % 2500)  # Variable
        step_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(day),
            "end_time": _ms(end),
            "time_offset": offset,
            "count": count,
            "calorie": count // 15,
            "distance": count * 0.75,
        })
    pd.DataFrame(step_rows).to_csv(
        out / "com.samsung.health.pedometer_step_count.20260528120000.csv", index=False
    )

    # Weight: Significant fluctuations
    weight_rows = []
    for i in range(14):
        t = base + timedelta(days=i * 2, hours=7)
        weight = 68.0 + (i % 3) * 2 - i * 0.1  # Fluctuations +/- 2kg
        weight_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(t),
            "end_time": _ms(t + timedelta(minutes=1)),
            "time_offset": offset,
            "weight": round(weight, 2),
            "body_fat": round(24.0 + (i % 2) - i * 0.05, 1),
            "muscle_mass": 26.5,
            "body_water": 51.0,
            "skeletal_muscle": 25.0,
            "bmi": round(26.8 + (i % 2) - i * 0.03, 1),
        })
    pd.DataFrame(weight_rows).to_csv(
        out / "com.samsung.health.weight.20260528120000.csv", index=False
    )


def generate_rebecca_l() -> None:
    """Rebecca L. – Complex trauma, autonomy, river living."""
    out = DEMO_ROOT / "personas" / "rebecca_l" / "samsung_export"
    out.mkdir(parents=True, exist_ok=True)
    jsons = out / "jsons"
    jsons.mkdir(exist_ok=True)

    base = datetime(2026, 5, 1, 8, 0, tzinfo=timezone.utc)
    offset = 60

    # Sleep: Extremely poor
    sleep_rows = []
    for i in range(28):
        bed_time = base + timedelta(days=i, hours=22 + (i % 2))
        duration = 180 + (i % 5) * 15 - 30  # 3-4.5 hours
        wake_time = bed_time + timedelta(minutes=duration)
        sleep_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(bed_time),
            "end_time": _ms(wake_time),
            "time_offset": offset,
            "sleep_duration": duration,
            "efficiency": 25 + (i % 12),
            "deep_sleep": 5 + (i % 5),
            "rem_sleep": 15 + (i % 20),
            "light_sleep": duration - 20 - (i % 10),
            "wake_up_count": 7 + (i % 5),
        })
    pd.DataFrame(sleep_rows).to_csv(
        out / "com.samsung.shealth.sleep.20260528120000.csv", index=False
    )

    # Heart rate: Chronically elevated
    hr_rows = []
    for i in range(20):
        t = base + timedelta(days=i % 28, hours=10 + i % 12)
        jname = f"hr_bin_{i}.json"
        with (jsons / jname).open("w", encoding="utf-8") as f:
            json.dump({"bins": [{"bpm": 88 + j, "count": 2 + (j % 2)} for j in range(18)]}, f)
        hr_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(t),
            "time_offset": offset,
            "heart_rate": 90 + (i % 15),
            "min": 78 + (i % 10),
            "max": 145 + (i % 20),
            "heart_rate_zone": "cardio" if i % 2 else "fat_burn",
            "binning_data": jname,
        })
    pd.DataFrame(hr_rows).to_csv(out / "com.samsung.health.heart_rate.20260528120000.csv", index=False)

    # Steps: Periodic survival-related high activity
    step_rows = []
    for i in range(28):
        day = base + timedelta(days=i)
        end = day + timedelta(hours=23, minutes=59)
        if i % 9 == 0:
            count = 10000 + (i % 3000)  # High activity (survival tasks)
        elif i % 4 == 2:
            count = 500 + (i % 300)  # Very low activity
        else:
            count = 2000 + (i % 1500)  # Moderate
        step_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(day),
            "end_time": _ms(end),
            "time_offset": offset,
            "count": count,
            "calorie": count // 18,
            "distance": count * 0.75,
        })
    pd.DataFrame(step_rows).to_csv(
        out / "com.samsung.health.pedometer_step_count.20260528120000.csv", index=False
    )

    # Weight: Significant loss, irregular
    weight_rows = []
    for i in range(14):
        t = base + timedelta(days=i * 2, hours=7)
        weight_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(t),
            "end_time": _ms(t + timedelta(minutes=1)),
            "time_offset": offset,
            "weight": round(61.0 - i * 0.25, 2),
            "body_fat": round(19.5 - i * 0.08, 1),
            "muscle_mass": 23.5,
            "body_water": 50.0,
            "skeletal_muscle": 22.0,
            "bmi": round(22.8 - i * 0.09, 1),
        })
    pd.DataFrame(weight_rows).to_csv(
        out / "com.samsung.health.weight.20260528120000.csv", index=False
    )


def generate_margaret_t() -> None:
    """Margaret T. – Elder abuse, financial exploitation, isolation."""
    out = DEMO_ROOT / "personas" / "margaret_t" / "samsung_export"
    out.mkdir(parents=True, exist_ok=True)
    jsons = out / "jsons"
    jsons.mkdir(exist_ok=True)

    base = datetime(2026, 5, 1, 8, 0, tzinfo=timezone.utc)
    offset = 60

    # Sleep: Poor, anxiety-driven
    sleep_rows = []
    for i in range(28):
        bed_time = base + timedelta(days=i, hours=22 + (i % 1.5))
        duration = 300 + (i % 10) * 10 - 50  # 5-6.5 hours
        wake_time = bed_time + timedelta(minutes=duration)
        sleep_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(bed_time),
            "end_time": _ms(wake_time),
            "time_offset": offset,
            "sleep_duration": duration,
            "efficiency": 40 + (i % 10),
            "deep_sleep": 30 + (i % 15),
            "rem_sleep": 60 + (i % 20),
            "light_sleep": duration - 90 - (i % 10),
            "wake_up_count": 3 + (i % 3),
        })
    pd.DataFrame(sleep_rows).to_csv(
        out / "com.samsung.shealth.sleep.20260528120000.csv", index=False
    )

    # Heart rate: Elevated, anxiety spikes
    hr_rows = []
    for i in range(20):
        t = base + timedelta(days=i % 28, hours=10 + i % 12)
        jname = f"hr_bin_{i}.json"
        with (jsons / jname).open("w", encoding="utf-8") as f:
            json.dump({"bins": [{"bpm": 75 + j, "count": 4 + (j % 3)} for j in range(12)]}, f)
        hr_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(t),
            "time_offset": offset,
            "heart_rate": 76 + (i % 10),
            "min": 68 + (i % 8),
            "max": 125 + (i % 15),
            "heart_rate_zone": "rest" if i % 3 else "fat_burn",
            "binning_data": jname,
        })
    pd.DataFrame(hr_rows).to_csv(out / "com.samsung.health.heart_rate.20260528120000.csv", index=False)

    # Steps: Very low, sedentary
    step_rows = []
    for i in range(28):
        day = base + timedelta(days=i)
        end = day + timedelta(hours=23, minutes=59)
        count = 2000 + (i % 1200)  # Low activity
        step_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(day),
            "end_time": _ms(end),
            "time_offset": offset,
            "count": count,
            "calorie": count // 22,
            "distance": count * 0.76,
        })
    pd.DataFrame(step_rows).to_csv(
        out / "com.samsung.health.pedometer_step_count.20260528120000.csv", index=False
    )

    # Weight: Loss from stress/irregular eating
    weight_rows = []
    for i in range(14):
        t = base + timedelta(days=i * 2, hours=7)
        weight_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(t),
            "end_time": _ms(t + timedelta(minutes=1)),
            "time_offset": offset,
            "weight": round(67.0 - i * 0.2, 2),
            "body_fat": round(28.0 - i * 0.08, 1),
            "muscle_mass": 22.0,
            "body_water": 48.5,
            "skeletal_muscle": 20.0,
            "bmi": round(27.2 - i * 0.08, 1),
        })
    pd.DataFrame(weight_rows).to_csv(
        out / "com.samsung.health.weight.20260528120000.csv", index=False
    )


def generate_robert_k() -> None:
    """Robert K. – Elder abuse by partner, medical neglect."""
    out = DEMO_ROOT / "personas" / "robert_k" / "samsung_export"
    out.mkdir(parents=True, exist_ok=True)
    jsons = out / "jsons"
    jsons.mkdir(exist_ok=True)

    base = datetime(2026, 5, 1, 8, 0, tzinfo=timezone.utc)
    offset = 60

    # Sleep: Severely disrupted, breathing issues
    sleep_rows = []
    for i in range(28):
        bed_time = base + timedelta(days=i, hours=22 + (i % 2))
        duration = 200 + (i % 8) * 15 - 60  # 3-4.5 hours
        wake_time = bed_time + timedelta(minutes=duration)
        sleep_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(bed_time),
            "end_time": _ms(wake_time),
            "time_offset": offset,
            "sleep_duration": duration,
            "efficiency": 30 + (i % 10),
            "deep_sleep": 15 + (i % 10),
            "rem_sleep": 45 + (i % 15),
            "light_sleep": duration - 60 - (i % 8),
            "wake_up_count": 5 + (i % 4),
        })
    pd.DataFrame(sleep_rows).to_csv(
        out / "com.samsung.shealth.sleep.20260528120000.csv", index=False
    )

    # Heart rate: Highly irregular, dangerous patterns
    hr_rows = []
    for i in range(20):
        t = base + timedelta(days=i % 28, hours=10 + i % 12)
        jname = f"hr_bin_{i}.json"
        with (jsons / jname).open("w", encoding="utf-8") as f:
            json.dump({"bins": [{"bpm": 60 + j * 2, "count": 3 + (j % 4)} for j in range(20)]}, f)
        # Wide swings typical of unmanaged heart disease
        base_hr = 65 + (i % 20)
        hr_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(t),
            "time_offset": offset,
            "heart_rate": base_hr,
            "min": 55 + (i % 15),
            "max": 115 + (i % 30),  # Very wide range
            "heart_rate_zone": "rest" if i % 4 else "fat_burn",
            "binning_data": jname,
        })
    pd.DataFrame(hr_rows).to_csv(out / "com.samsung.health.heart_rate.20260528120000.csv", index=False)

    # Steps: Extremely low, mobility-limited
    step_rows = []
    for i in range(28):
        day = base + timedelta(days=i)
        end = day + timedelta(hours=23, minutes=59)
        count = 1200 + (i % 600)  # Very low
        step_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(day),
            "end_time": _ms(end),
            "time_offset": offset,
            "count": count,
            "calorie": count // 25,
            "distance": count * 0.76,
        })
    pd.DataFrame(step_rows).to_csv(
        out / "com.samsung.health.pedometer_step_count.20260528120000.csv", index=False
    )

    # Weight: Rapid loss from neglect
    weight_rows = []
    for i in range(14):
        t = base + timedelta(days=i * 2, hours=7)
        weight_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(t),
            "end_time": _ms(t + timedelta(minutes=1)),
            "time_offset": offset,
            "weight": round(76.0 - i * 0.5, 2),  # Faster decline
            "body_fat": round(24.0 - i * 0.12, 1),
            "muscle_mass": 25.0,
            "body_water": 49.0,
            "skeletal_muscle": 23.5,
            "bmi": round(26.5 - i * 0.17, 1),
        })
    pd.DataFrame(weight_rows).to_csv(
        out / "com.samsung.health.weight.20260528120000.csv", index=False
    )


def generate_jordan_m() -> None:
    """Jordan M. – NDIS exploitation, disability, systemic abuse."""
    out = DEMO_ROOT / "personas" / "jordan_m" / "samsung_export"
    out.mkdir(parents=True, exist_ok=True)
    jsons = out / "jsons"
    jsons.mkdir(exist_ok=True)

    base = datetime(2026, 5, 1, 8, 0, tzinfo=timezone.utc)
    offset = 60

    # Sleep: Poor, pain-related arousals
    sleep_rows = []
    for i in range(28):
        bed_time = base + timedelta(days=i, hours=22.5 + (i % 1.5))
        duration = 280 + (i % 15) * 10 - 60  # 4-6 hours
        wake_time = bed_time + timedelta(minutes=duration)
        sleep_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(bed_time),
            "end_time": _ms(wake_time),
            "time_offset": offset,
            "sleep_duration": duration,
            "efficiency": 35 + (i % 20),
            "deep_sleep": 20 + (i % 15),
            "rem_sleep": 50 + (i % 25),
            "light_sleep": duration - 70 - (i % 15),
            "wake_up_count": 4 + (i % 3),
        })
    pd.DataFrame(sleep_rows).to_csv(
        out / "com.samsung.shealth.sleep.20260528120000.csv", index=False
    )

    # Heart rate: Elevated and variable
    hr_rows = []
    for i in range(20):
        t = base + timedelta(days=i % 28, hours=10 + i % 12)
        jname = f"hr_bin_{i}.json"
        with (jsons / jname).open("w", encoding="utf-8") as f:
            json.dump({"bins": [{"bpm": 78 + j, "count": 3 + (j % 3)} for j in range(16)]}, f)
        hr_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(t),
            "time_offset": offset,
            "heart_rate": 80 + (i % 12),
            "min": 70 + (i % 10),
            "max": 135 + (i % 18),
            "heart_rate_zone": "fat_burn" if i % 2 else "rest",
            "binning_data": jname,
        })
    pd.DataFrame(hr_rows).to_csv(out / "com.samsung.health.heart_rate.20260528120000.csv", index=False)

    # Steps: Limited, good days vs. pain days
    step_rows = []
    for i in range(28):
        day = base + timedelta(days=i)
        end = day + timedelta(hours=23, minutes=59)
        if i % 5 == 0:
            count = 4000 + (i % 1500)  # Good day
        elif i % 5 == 3:
            count = 200 + (i % 300)  # Severe pain day
        else:
            count = 1500 + (i % 1200)  # Moderate
        step_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(day),
            "end_time": _ms(end),
            "time_offset": offset,
            "count": count,
            "calorie": count // 20,
            "distance": count * 0.75,
        })
    pd.DataFrame(step_rows).to_csv(
        out / "com.samsung.health.pedometer_step_count.20260528120000.csv", index=False
    )

    # Weight: Stress-related fluctuations
    weight_rows = []
    for i in range(14):
        t = base + timedelta(days=i * 2, hours=7)
        weight = 72.0 + (i % 2) * 1.5 - i * 0.15  # Slight fluctuations
        weight_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(t),
            "end_time": _ms(t + timedelta(minutes=1)),
            "time_offset": offset,
            "weight": round(weight, 2),
            "body_fat": round(26.0 + (i % 2) - i * 0.08, 1),
            "muscle_mass": 24.5,
            "body_water": 50.5,
            "skeletal_muscle": 23.0,
            "bmi": round(27.5 + (i % 2) - i * 0.06, 1),
        })
    pd.DataFrame(weight_rows).to_csv(
        out / "com.samsung.health.weight.20260528120000.csv", index=False
    )


def main() -> None:
    """Generate all persona exports."""
    print("Generating synthetic exports for all demo personas...")
    generate_michael_r()
    print("✓ Michael R. (Homelessness)")
    generate_elena_v()
    print("✓ Elena V. (PTSD/Trauma)")
    generate_rebecca_l()
    print("✓ Rebecca L. (Complex trauma/autonomy)")
    generate_margaret_t()
    print("✓ Margaret T. (Elder abuse)")
    generate_robert_k()
    print("✓ Robert K. (Elder abuse by partner)")
    generate_jordan_m()
    print("✓ Jordan M. (NDIS exploitation)")
    print("All persona exports generated successfully!")


if __name__ == "__main__":
    main()
