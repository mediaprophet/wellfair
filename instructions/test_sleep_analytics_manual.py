#!/usr/bin/env python
"""Manual test for sleep analytics module."""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.sleep_analytics import SleepMetrics, SleepTrendAnalysis, SleepInsights, SleepPatterns

def test_sleep_metrics():
    """Test sleep metrics calculation."""
    print("=" * 60)
    print("Testing SleepMetrics...")
    print("=" * 60)
    
    # Test 1: Sleep score calculation
    duration = 420  # 7 hours
    efficiency = 85  # 85%
    consistency = 80  # 80%
    
    score = SleepMetrics.calculate_sleep_score(duration, efficiency, consistency)
    quality, msg = SleepMetrics.classify_sleep_quality(score)
    
    print(f"\n✓ Sleep Score: {score:.1f}/100")
    print(f"  Quality Level: {quality}")
    print(f"  Message: {msg}")
    
    # Test 2: Sleep debt calculation
    test_df = pd.DataFrame({
        "sleep_duration": [300, 360, 420, 450, 480, 390, 330]  # Variable durations
    })
    
    debt = SleepMetrics.calculate_sleep_debt(test_df)
    print(f"\n✓ Sleep Debt Analysis:")
    print(f"  Total Deficit: {debt['debt_minutes']} minutes")
    print(f"  Nights with Deficit: {debt['deficit_nights']}")
    print(f"  Avg Deficit: {debt['avg_deficit']:.1f} min/night")
    
    # Test 3: Consistency calculation
    dates = pd.date_range(start='2025-02-01', periods=7, freq='D')
    times = [datetime.combine(d.date(), datetime.strptime("23:30", "%H:%M").time()) for d in dates]
    times[3] = datetime.combine(dates[3].date(), datetime.strptime("22:15", "%H:%M").time())  # One irregular night
    
    test_df = pd.DataFrame({
        "start_datetime": times,
        "sleep_duration": [420] * 7
    })
    
    consistency = SleepMetrics.calculate_consistency_score(test_df)
    print(f"\n✓ Sleep Consistency Score: {consistency:.1f}%")
    print(f"  Interpretation: {'Regular' if consistency >= 70 else 'Variable'} sleep schedule")

def test_trend_analysis():
    """Test trend detection."""
    print("\n" + "=" * 60)
    print("Testing SleepTrendAnalysis...")
    print("=" * 60)
    
    # Create sample data with improving trend
    dates = pd.date_range(start='2025-02-01', periods=14, freq='D')
    durations = [300 + i * 5 for i in range(14)]  # Steadily increasing from 300 to 365 minutes
    
    test_df = pd.DataFrame({
        "start_datetime": dates,
        "sleep_duration": durations,
        "efficiency": [78 + i * 1 for i in range(14)]
    })
    
    trend = SleepTrendAnalysis.detect_trend(test_df, "sleep_duration", "start_datetime")
    print(f"\n✓ Sleep Duration Trend:")
    print(f"  Trend: {trend['trend']} {trend['direction']}")
    print(f"  Daily Change: {trend['change_per_day']:.1f} minutes/night")
    
    wow = SleepTrendAnalysis.weekly_comparison(test_df, "sleep_duration", "start_datetime")
    if "current" in wow:
        print(f"\n✓ Week-over-Week Comparison:")
        print(f"  Current Week Avg: {wow['current']:.0f} minutes")
        print(f"  Previous Week Avg: {wow['previous']:.0f} minutes")
        print(f"  Change: {wow['pct_change']:+.1f}%")

def test_insights():
    """Test insight generation."""
    print("\n" + "=" * 60)
    print("Testing SleepInsights...")
    print("=" * 60)
    
    dates = pd.date_range(start='2025-02-01', periods=7, freq='D')
    test_df = pd.DataFrame({
        "start_datetime": dates,
        "sleep_duration": [380, 420, 410, 360, 390, 370, 400],
        "efficiency": [82, 88, 85, 78, 81, 76, 84]
    })
    
    insights = SleepInsights.generate_insights(test_df, None)
    print(f"\n✓ Generated {len(insights)} insight(s):")
    for i, insight in enumerate(insights[:3], 1):
        print(f"  {i}. {insight['icon']} {insight['title']}")
        print(f"     {insight['message']}")
    
    score = 75
    recommendations = SleepInsights.get_recommendations(score, test_df)
    print(f"\n✓ Top Recommendations for score {score}:")
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"  {i}. {rec}")

def test_patterns():
    """Test pattern analysis."""
    print("\n" + "=" * 60)
    print("Testing SleepPatterns...")
    print("=" * 60)
    
    # Test sleep cycle stats
    test_stage_df = pd.DataFrame({
        "stage": [40001, 40002, 40003, 40004] * 100 + [40002, 40003]  # 402 records
    })
    
    stats = SleepPatterns.get_sleep_cycle_stats(test_stage_df)
    print(f"\n✓ Sleep Cycle Statistics:")
    print(f"  REM Sleep: {stats['rem_percentage']:.1f}%")
    print(f"  Deep Sleep: {stats['deep_sleep_percentage']:.1f}%")
    print(f"  Light Sleep: {stats['light_sleep_percentage']:.1f}%")
    print(f"  Awake Time: {stats['awake_percentage']:.1f}%")

if __name__ == "__main__":
    try:
        test_sleep_metrics()
        test_trend_analysis()
        test_insights()
        test_patterns()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
