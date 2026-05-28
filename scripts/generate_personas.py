import uuid
import json
import math
import random
import pandas as pd
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent

def _ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)

def generate_profile(profile_id: str, days: int, base_date: datetime):
    print(f"Generating 3 years of data for {profile_id}...")
    out_dir = ROOT / "data" / "demo" / profile_id / "samsung_export"
    out_dir.mkdir(parents=True, exist_ok=True)
    jsons_dir = out_dir / "jsons"
    jsons_dir.mkdir(exist_ok=True)

    offset = 600  # AEST (UTC+10)

    weight_rows = []
    sleep_rows = []
    hr_rows = []
    step_rows = []

    # Persona-specific state variables
    weight = 70.0
    if profile_id == "michael": weight = 85.0
    elif profile_id == "elena": weight = 55.0
    elif profile_id == "rebecca": weight = 60.0
    elif profile_id == "margaret": weight = 55.0
    elif profile_id == "robert": weight = 80.0
    elif profile_id == "jordan": weight = 95.0

    for i in tqdm(range(days)):
        day = base_date + timedelta(days=i)
        
        # Determine seasonality (Winter in Australia is approx days 30-120 and 395-485 etc)
        # We can use a sine wave where peak is summer (Jan) and trough is winter (July)
        # day of year (1-365)
        doy = day.timetuple().tm_yday
        # shift so peak is Jan 15th
        season_modifier = math.sin((doy + 167) * 2 * math.pi / 365) # ranges -1 to 1 (winter = -1)

        # Baseline noise
        daily_noise = random.uniform(-1, 1)

        # Persona-specific logic
        if profile_id == "gemini":
            # Baseline normal
            steps = int(8000 + 2000 * season_modifier + daily_noise * 1500)
            sleep_duration = 450 + int(daily_noise * 45)
            sleep_efficiency = min(95, max(75, 88 + int(season_modifier * 3 + daily_noise * 5)))
            hr_rest = 65 - int(season_modifier * 2 + daily_noise * 3)
            weight += daily_noise * 0.05
            
        elif profile_id == "michael":
            # Rough sleeper, highly affected by winter
            is_working = random.random() < 0.4 # Works 40% of the time
            steps = int(12000 + daily_noise * 3000) if is_working else int(3000 + daily_noise * 1000)
            
            # Sleep plummets in winter
            sleep_duration = 360 + int(season_modifier * 60 + daily_noise * 60)
            sleep_efficiency = min(100, max(10, 65 + int(season_modifier * 20 + daily_noise * 10)))
            hr_rest = 75 - int(season_modifier * 10 + daily_noise * 5)
            weight += daily_noise * 0.1 - 0.01 # slight downward drift over 3 years
            
        elif profile_id == "elena":
            # Trauma recovery, erratic
            manic = random.random() < 0.15
            depressed = random.random() < 0.25
            
            if manic:
                steps = int(15000 + daily_noise * 2000)
                sleep_duration = 180 + int(daily_noise * 30)
                hr_rest = 90 + int(daily_noise * 5)
            elif depressed:
                steps = int(1500 + daily_noise * 500)
                sleep_duration = 600 + int(daily_noise * 100)
                hr_rest = 70 + int(daily_noise * 5)
            else:
                steps = int(6000 + daily_noise * 2000)
                sleep_duration = 360 + int(daily_noise * 60)
                hr_rest = 80 + int(daily_noise * 5)
                
            sleep_efficiency = min(100, max(10, 50 + int(daily_noise * 25))) # highly fragmented
            weight += daily_noise * 0.2 # high fluctuation
            
        elif profile_id == "rebecca":
            # Riverbank autonomy
            steps = int(10000 + 4000 * season_modifier + daily_noise * 3000)
            sleep_duration = 240 + int(season_modifier * 40 + daily_noise * 40)
            sleep_efficiency = min(100, max(10, 45 + int(season_modifier * 15 + daily_noise * 10)))
            hr_rest = 85 - int(season_modifier * 10 + daily_noise * 10)
            weight += daily_noise * 0.05
            
        elif profile_id == "margaret":
            # Elder abuse (financial/psychological) - gradual deterioration
            deterioration_factor = i / days # 0.0 to 1.0 over 3 years
            steps = int(3500 * (1 - deterioration_factor*0.8) + daily_noise * 500)
            sleep_duration = int(420 * (1 - deterioration_factor*0.3) + daily_noise * 40)
            sleep_efficiency = min(100, max(10, 70 - int(deterioration_factor * 30) + int(daily_noise * 10)))
            hr_rest = 72 + int(deterioration_factor * 25) + int(daily_noise * 4)
            weight -= 0.015 + daily_noise * 0.05 # steady weight loss
            
        elif profile_id == "robert":
            # Cardiac neglect - rapid deterioration and spikes
            deterioration_factor = (i / days) ** 1.5
            steps = int(2500 * (1 - deterioration_factor*0.9) + daily_noise * 300)
            sleep_duration = int(360 - deterioration_factor*120 + daily_noise * 50)
            sleep_efficiency = min(100, max(10, 60 - int(deterioration_factor * 40) + int(daily_noise * 15)))
            
            # Cardiac spikes
            is_spike = random.random() < (0.05 + deterioration_factor * 0.2)
            hr_rest = 85 + int(deterioration_factor * 30)
            if is_spike:
                hr_rest += 35 + int(daily_noise * 15)
                
            weight -= 0.02 + daily_noise * 0.04
            
        elif profile_id == "jordan":
            # NDIS exploitation - flat but poor
            steps = max(0, int(800 + daily_noise * 400))
            sleep_duration = 300 + int(daily_noise * 60)
            sleep_efficiency = min(100, max(10, 45 + int(daily_noise * 10)))
            hr_rest = 95 + int(daily_noise * 8)
            weight += 0.005 + daily_noise * 0.08 # slight gain
        else:
            steps = 5000; sleep_duration = 400; sleep_efficiency = 80; hr_rest = 70;

        # Constrain variables
        steps = max(0, steps)
        sleep_duration = max(30, sleep_duration)
        hr_rest = max(40, min(200, hr_rest))
        
        # Generate Rows
        # 1. Weight (sampled roughly every 3 days)
        if i % 3 == 0:
            wt_time = day + timedelta(hours=8)
            weight_rows.append({
                "uuid": str(uuid.uuid4()),
                "start_time": _ms(wt_time),
                "end_time": _ms(wt_time + timedelta(minutes=1)),
                "time_offset": offset,
                "weight": round(weight, 2),
                "body_fat": round(20.0 + daily_noise, 1),
                "muscle_mass": round(30.0 + daily_noise, 1),
                "body_water": round(50.0 + daily_noise, 1),
                "skeletal_muscle": round(28.0 + daily_noise, 1),
                "bmi": round(weight / ((1.75)**2), 1)
            })
            
        # 2. Steps
        step_end = day + timedelta(hours=23, minutes=59)
        step_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(day),
            "end_time": _ms(step_end),
            "time_offset": offset,
            "count": steps,
            "calorie": int(steps * 0.04),
            "distance": int(steps * 0.7)
        })
        
        # 3. Sleep
        bed_time = day + timedelta(hours=22 + daily_noise)
        wake_time = bed_time + timedelta(minutes=sleep_duration)
        wake_count = int(1 + (100 - sleep_efficiency)/15 + max(0, daily_noise*2))
        
        sleep_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(bed_time),
            "end_time": _ms(wake_time),
            "time_offset": offset,
            "sleep_duration": sleep_duration,
            "efficiency": sleep_efficiency,
            "deep_sleep": int(sleep_duration * (sleep_efficiency/100) * 0.2),
            "rem_sleep": int(sleep_duration * (sleep_efficiency/100) * 0.25),
            "light_sleep": int(sleep_duration * (sleep_efficiency/100) * 0.55),
            "wake_up_count": wake_count
        })
        
        # 4. Heart Rate
        hr_time = day + timedelta(hours=12)
        jname = f"hr_bin_{i}.json"
        
        # Generate realistic binning JSON
        bins = []
        for b in range(12):
            bin_bpm = hr_rest - 10 + b*2
            bins.append({"bpm": int(bin_bpm), "count": int(max(0, 10 - abs(6 - b)*2 + daily_noise*3))})
            
        with (jsons_dir / jname).open("w", encoding="utf-8") as f:
            json.dump({"bins": bins}, f)
            
        hr_rows.append({
            "uuid": str(uuid.uuid4()),
            "start_time": _ms(hr_time),
            "time_offset": offset,
            "heart_rate": int(hr_rest),
            "min": int(hr_rest - 15 - max(0, daily_noise*5)),
            "max": int(hr_rest + 25 + max(0, daily_noise*15)),
            "heart_rate_zone": "rest" if hr_rest < 85 else "fat_burn",
            "binning_data": jname
        })

    # Save to CSV
    pd.DataFrame(weight_rows).to_csv(out_dir / "com.samsung.health.weight.20260525120000.csv", index=False)
    pd.DataFrame(step_rows).to_csv(out_dir / "com.samsung.health.pedometer_step_count.20260525120000.csv", index=False)
    pd.DataFrame(sleep_rows).to_csv(out_dir / "com.samsung.shealth.sleep.20260525120000.csv", index=False)
    pd.DataFrame(hr_rows).to_csv(out_dir / "com.samsung.health.heart_rate.20260525120000.csv", index=False)

def main():
    days = 1095 # 3 years
    base_date = datetime(2023, 5, 1, tzinfo=timezone.utc)
    
    profiles = ["gemini", "michael", "elena", "rebecca", "margaret", "robert", "jordan"]
    for p in profiles:
        generate_profile(p, days, base_date)

if __name__ == "__main__":
    main()
