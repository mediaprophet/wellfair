import uuid
import json
import pandas as pd
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def _ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)

def generate_profile(profile_id: str,
                     base_weight: float, weight_var: float,
                     sleep_duration_base: int, sleep_efficiency_base: int, sleep_var: int,
                     hr_base: int, hr_var: int,
                     step_base: int, step_var: int):
                     
    out_dir = ROOT / "data" / "demo" / profile_id / "samsung_export"
    out_dir.mkdir(parents=True, exist_ok=True)
    jsons_dir = out_dir / "jsons"
    jsons_dir.mkdir(exist_ok=True)

    base = datetime(2026, 5, 1, 8, 0, tzinfo=timezone.utc)
    offset = 60

    # Weight
    weight_rows = []
    for i in range(14):
        t = base + timedelta(days=i, hours=7)
        weight_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(t),
            "end_time": _ms(t + timedelta(minutes=1)),
            "time_offset": offset,
            "weight": round(base_weight + (i % 3) * weight_var, 2),
            "body_fat": 18.5,
            "muscle_mass": 32.1,
            "body_water": 55.2,
            "skeletal_muscle": 30.5,
            "bmi": round(base_weight / 3.0, 1) # mock BMI
        })
    pd.DataFrame(weight_rows).to_csv(out_dir / "com.samsung.health.weight.20260525120000.csv", index=False)

    # Sleep
    sleep_rows = []
    for i in range(14):
        bed = base + timedelta(days=i, hours=23 - (i % 2)*sleep_var)
        duration = sleep_duration_base + (i % 3)*30 - 15
        wake = bed + timedelta(minutes=duration)
        sleep_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(bed),
            "end_time": _ms(wake),
            "time_offset": offset,
            "sleep_duration": duration,
            "efficiency": max(10, min(100, sleep_efficiency_base - (i % 3)*sleep_var)),
            "deep_sleep": duration // 5,
            "rem_sleep": duration // 4,
            "light_sleep": duration // 2,
            "wake_up_count": (i % 4) + sleep_var
        })
    pd.DataFrame(sleep_rows).to_csv(out_dir / "com.samsung.shealth.sleep.20260525120000.csv", index=False)

    # Heart Rate
    hr_rows = []
    for i in range(14):
        t = base + timedelta(days=i, hours=10)
        jname = f"hr_bin_{i}.json"
        with (jsons_dir / jname).open("w", encoding="utf-8") as f:
            json.dump({"bins": [{"bpm": hr_base + hr_var + j, "count": 5} for j in range(12)]}, f)
        hr_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(t),
            "time_offset": offset,
            "heart_rate": hr_base + (i % 2)*hr_var,
            "min": hr_base - 10,
            "max": hr_base + hr_var + 20,
            "heart_rate_zone": "rest",
            "binning_data": jname
        })
    pd.DataFrame(hr_rows).to_csv(out_dir / "com.samsung.health.heart_rate.20260525120000.csv", index=False)

    # Steps
    step_rows = []
    for i in range(14):
        day = base + timedelta(days=i)
        end = day + timedelta(hours=23, minutes=59)
        step_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(day),
            "end_time": _ms(end),
            "time_offset": offset,
            "count": step_base + (i % 3)*step_var,
            "calorie": 200,
            "distance": 4000
        })
    pd.DataFrame(step_rows).to_csv(out_dir / "com.samsung.health.pedometer_step_count.20260525120000.csv", index=False)
    print(f"Generated profile: {profile_id}")

def main():
    # gemini (Baseline)
    generate_profile("gemini", base_weight=70, weight_var=0.5, sleep_duration_base=480, sleep_efficiency_base=90, sleep_var=1, hr_base=65, hr_var=5, step_base=8000, step_var=1000)
    
    # michael (Rough sleeping)
    generate_profile("michael", base_weight=85, weight_var=2.0, sleep_duration_base=300, sleep_efficiency_base=50, sleep_var=3, hr_base=85, hr_var=20, step_base=4000, step_var=8000)
    
    # elena (Trauma recovery)
    generate_profile("elena", base_weight=55, weight_var=1.5, sleep_duration_base=240, sleep_efficiency_base=40, sleep_var=4, hr_base=95, hr_var=30, step_base=2000, step_var=10000)
    
    # rebecca (Riverbank autonomy)
    generate_profile("rebecca", base_weight=60, weight_var=1.0, sleep_duration_base=200, sleep_efficiency_base=35, sleep_var=5, hr_base=100, hr_var=15, step_base=10000, step_var=15000)
    
    # margaret (Elder abuse)
    generate_profile("margaret", base_weight=45, weight_var=0.2, sleep_duration_base=400, sleep_efficiency_base=60, sleep_var=2, hr_base=75, hr_var=25, step_base=1500, step_var=500)
    
    # robert (Cardiac neglect)
    generate_profile("robert", base_weight=80, weight_var=1.0, sleep_duration_base=350, sleep_efficiency_base=50, sleep_var=3, hr_base=90, hr_var=40, step_base=1000, step_var=200)
    
    # jordan (NDIS exploitation)
    generate_profile("jordan", base_weight=95, weight_var=0.5, sleep_duration_base=250, sleep_efficiency_base=45, sleep_var=2, hr_base=105, hr_var=15, step_base=800, step_var=400)

if __name__ == "__main__":
    main()
