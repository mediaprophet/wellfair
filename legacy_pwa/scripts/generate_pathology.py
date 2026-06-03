import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os
import shutil

# Config
PROFILES = ["michael", "elena", "rebecca", "margaret", "robert", "jordan"]
NUM_EPISODES = 20
YEARS = 3
TEMPLATE_FILE = r"C:\Projects\health\instructions\Pathology Example.xlsx - GeneralTests.csv"
OUTPUT_BASE = r"C:\Projects\health\data\demo"

def parse_template():
    # Read template skipping first 3 rows
    # The template has: Category (0), Test Name (1), empty (2), Date 1..12 (3..14), Units (15), Ref Int (16), Low (17), High (18), Desc (19)
    try:
        # We only need the test definitions, so we read all rows and skip the header stuff
        df = pd.read_csv(TEMPLATE_FILE, header=None, skiprows=3)
    except Exception as e:
        print(f"Error reading template: {e}")
        return None
        
    tests = []
    for _, row in df.iterrows():
        try:
            category = str(row[0]) if pd.notna(row[0]) else "General"
            name = str(row[1]) if pd.notna(row[1]) else "Unknown"
            
            # 15 is units, 16 is Ref, 17 is Low, 18 is High, 19 is Desc
            units = str(row[15]) if len(row) > 15 and pd.notna(row[15]) else ""
            ref_int = str(row[16]) if len(row) > 16 and pd.notna(row[16]) else ""
            
            low = float(row[17]) if len(row) > 17 and pd.notna(row[17]) and str(row[17]).replace('.','',1).isdigit() else 0.0
            high = float(row[18]) if len(row) > 18 and pd.notna(row[18]) and str(row[18]).replace('.','',1).isdigit() else 0.0
            
            desc = str(row[19]) if len(row) > 19 and pd.notna(row[19]) else ""
            
            if name != "Unknown" and name != "nan":
                # If high is 0, make up some reasonable bounds if low > 0, else just 0, 100
                if high <= low:
                    high = low * 1.5 if low > 0 else 100.0
                    
                tests.append({
                    "category": category,
                    "name": name,
                    "units": units,
                    "ref": ref_int,
                    "low": low,
                    "high": high,
                    "desc": desc
                })
        except Exception as e:
            print(f"Skipping row due to error: {e}")
            
    return tests

def generate_dates():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * YEARS)
    
    dates = []
    for _ in range(NUM_EPISODES):
        random_days = random.randint(0, (end_date - start_date).days)
        d = start_date + timedelta(days=random_days)
        dates.append(d)
        
    dates.sort()
    return dates

def generate_pathology(profile, tests):
    dates = generate_dates()
    
    # We want to format the output similar to the example, but clean
    # Columns: Category, Test Name, Units, Reference Interval, Low, High, Description, Date1, Date2...
    
    # Let's customize anomalies based on profile
    is_diabetic = profile in ["robert", "michael"]
    is_stressed = profile in ["jordan", "margaret"]
    has_infection = profile in ["rebecca"]
    
    output_rows = []
    for test in tests:
        row = [
            test["category"],
            test["name"],
            test["units"],
            test["ref"],
            test["low"],
            test["high"],
            test["desc"]
        ]
        
        # Base value within range
        base_val = test["low"] + (test["high"] - test["low"]) * random.uniform(0.3, 0.7)
        
        # Apply profile modifiers
        if is_diabetic and "Glucose" in test["name"]:
            base_val = test["high"] * random.uniform(1.1, 1.5) # Elevated
        if is_diabetic and "HbA1c" in test["name"]:
            base_val = test["high"] * random.uniform(1.05, 1.3)
            
        if is_stressed and "Cortisol" in test["name"]:
            base_val = test["high"] * random.uniform(1.1, 1.6)
            
        if has_infection and ("White" in test["name"] or "Leucocytes" in test["name"] or "CRP" in test["name"]):
            base_val = test["high"] * random.uniform(1.2, 2.0)
            
        for _ in dates:
            # Fluctuate around base value
            val = base_val * random.uniform(0.9, 1.1)
            
            # Occasional wild spike (5% chance)
            if random.random() < 0.05:
                val = val * random.uniform(1.2, 1.8)
                
            row.append(round(val, 2))
            
        output_rows.append(row)
        
    # Build dataframe
    header = ["Category", "Test Name", "Units", "Reference Interval", "Low", "High", "Description"]
    header.extend([d.strftime("%Y-%m-%d") for d in dates])
    
    df = pd.DataFrame(output_rows, columns=header)
    return df

def main():
    print("Parsing template...")
    tests = parse_template()
    if not tests:
        print("No tests found.")
        return
        
    print(f"Found {len(tests)} test definitions.")
    
    for profile in PROFILES:
        print(f"Generating for {profile}...")
        df = generate_pathology(profile, tests)
        
        out_dir = os.path.join(OUTPUT_BASE, profile)
        os.makedirs(out_dir, exist_ok=True)
        
        out_file = os.path.join(out_dir, "pathology.csv")
        df.to_csv(out_file, index=False)
        print(f"  -> Saved to {out_file}")
        
    print("Deleting template file...")
    try:
        os.remove(TEMPLATE_FILE)
        print("Template file deleted successfully.")
    except Exception as e:
        print(f"Could not delete template file: {e}")

if __name__ == "__main__":
    main()
