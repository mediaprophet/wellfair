# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# https://www.linkedin.com/in/ubiquitous/
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Advanced sleep analytics and metrics calculation.
Provides sleep quality scoring, trend analysis, and personalized insights.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
import numpy as np
import pandas as pd


class SleepMetrics:
    """Calculate comprehensive sleep metrics and quality scores."""
    
    OPTIMAL_SLEEP_DURATION = 420  # 7 hours in minutes
    MIN_SLEEP_DURATION = 300  # 5 hours
    MAX_SLEEP_DURATION = 600  # 10 hours
    TARGET_EFFICIENCY = 85  # %
    
    @staticmethod
    def calculate_sleep_score(
        duration_mins: float,
        efficiency: float,
        consistency_score: float = 50.0
    ) -> float:
        """
        Calculate overall sleep score (0-100).
        
        Weighted components:
        - Duration quality (40%): how close to optimal 7h
        - Efficiency (35%): percentage of time asleep vs in bed
        - Consistency (25%): regularity of sleep schedule
        """
        # Duration score: peak at 7h, decay outside range
        if duration_mins >= SleepMetrics.OPTIMAL_SLEEP_DURATION - 30 and duration_mins <= SleepMetrics.OPTIMAL_SLEEP_DURATION + 30:
            duration_score = 100
        else:
            # Calculate distance from optimal
            distance = abs(duration_mins - SleepMetrics.OPTIMAL_SLEEP_DURATION)
            duration_score = max(0, 100 - (distance / 5))  # -2 points per 10min deviation
        
        # Efficiency score: target 85%+
        efficiency_score = min(100, efficiency * (100 / SleepMetrics.TARGET_EFFICIENCY))
        
        # Consistency score (passed in)
        consistency_component = consistency_score
        
        # Weighted average
        sleep_score = (
            duration_score * 0.40 +
            efficiency_score * 0.35 +
            consistency_component * 0.25
        )
        
        return max(0, min(100, sleep_score))
    
    @staticmethod
    def calculate_consistency_score(df: pd.DataFrame, time_col: str = "start_datetime") -> float:
        """
        Calculate sleep consistency score (0-100).
        
        Based on:
        - Standard deviation of sleep times
        - Regularity of sleep/wake times across week
        """
        if df.empty or time_col not in df.columns:
            return 50.0
        
        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
            df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
        
        df = df.dropna(subset=[time_col])
        if len(df) < 3:
            return 50.0
        
        # Extract hour of sleep
        sleep_hours = df[time_col].dt.hour + df[time_col].dt.minute / 60
        hour_std = sleep_hours.std()
        
        # Score: lower std = higher consistency
        # Maximum std ~3 hours = 0 points, 0 std = 100 points
        consistency = max(0, 100 - (hour_std / 3 * 100))
        return float(consistency)
    
    @staticmethod
    def calculate_sleep_debt(df: pd.DataFrame, sleep_duration_col: str = "sleep_duration") -> dict:
        """
        Calculate accumulated sleep debt over recent period.
        
        Sleep debt = (optimal_duration - actual_duration) per night
        """
        if df.empty or sleep_duration_col not in df.columns:
            return {"debt_minutes": 0, "deficit_nights": 0, "avg_deficit": 0}
        
        df = df.copy()
        durations = df[sleep_duration_col].dropna()
        
        if durations.empty:
            return {"debt_minutes": 0, "deficit_nights": 0, "avg_deficit": 0}
        
        # Calculate debt
        deficits = [
            max(0, SleepMetrics.OPTIMAL_SLEEP_DURATION - d)
            for d in durations
        ]
        
        return {
            "debt_minutes": int(sum(deficits)),
            "deficit_nights": sum(1 for d in deficits if d > 0),
            "avg_deficit": float(np.mean(deficits)) if deficits else 0
        }
    
    @staticmethod
    def classify_sleep_quality(sleep_score: float) -> tuple[str, str]:
        """Classify sleep quality and provide summary."""
        if sleep_score >= 85:
            return "Excellent", "Your sleep quality is optimal. Maintain current habits."
        elif sleep_score >= 75:
            return "Good", "Sleep quality is good with room for minor improvements."
        elif sleep_score >= 65:
            return "Fair", "Consider addressing sleep consistency or duration."
        elif sleep_score >= 50:
            return "Poor", "Sleep quality needs attention. See recommendations below."
        else:
            return "Very Poor", "Significant sleep issues detected. Consult a healthcare provider."


class SleepTrendAnalysis:
    """Analyze sleep trends and patterns."""
    
    @staticmethod
    def detect_trend(df: pd.DataFrame, metric_col: str, time_col: str = "start_datetime") -> dict:
        """
        Detect trend in sleep metric (improving/declining/stable).
        
        Uses simple linear regression on recent 7-14 days.
        """
        if df.empty or metric_col not in df.columns or time_col not in df.columns:
            return {"trend": "insufficient_data", "slope": 0, "direction": "N/A"}
        
        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
            df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
        
        df = df.dropna(subset=[time_col, metric_col]).sort_values(time_col).tail(14)
        
        if len(df) < 3:
            return {"trend": "insufficient_data", "slope": 0, "direction": "N/A"}
        
        # Simple linear regression
        x = np.arange(len(df))
        y = df[metric_col].values
        
        slope, intercept = np.polyfit(x, y, 1)
        
        # Classify trend
        if abs(slope) < 0.5:
            trend = "stable"
            direction = "→"
        elif slope > 0:
            trend = "improving"
            direction = "↑"
        else:
            trend = "declining"
            direction = "↓"
        
        return {
            "trend": trend,
            "slope": float(slope),
            "direction": direction,
            "change_per_day": float(slope)
        }
    
    @staticmethod
    def weekly_comparison(df: pd.DataFrame, metric_col: str, time_col: str = "start_datetime") -> dict:
        """
        Compare current week vs previous week metrics.
        """
        if df.empty or metric_col not in df.columns or time_col not in df.columns:
            return {}
        
        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
            df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
        
        df = df.dropna(subset=[time_col, metric_col]).sort_values(time_col)
        
        if df.empty:
            return {}
        
        today = df[time_col].max().date()
        week_ago = today - timedelta(days=7)
        two_weeks_ago = today - timedelta(days=14)
        
        # Current week
        current_week = df[(df[time_col].dt.date >= week_ago) & (df[time_col].dt.date < today)]
        current_avg = current_week[metric_col].mean() if not current_week.empty else None
        
        # Previous week
        previous_week = df[(df[time_col].dt.date >= two_weeks_ago) & (df[time_col].dt.date < week_ago)]
        previous_avg = previous_week[metric_col].mean() if not previous_week.empty else None
        
        if current_avg is None or previous_avg is None:
            return {"current": current_avg, "previous": previous_avg, "change": None}
        
        change = current_avg - previous_avg
        pct_change = (change / previous_avg * 100) if previous_avg != 0 else 0
        
        return {
            "current": float(current_avg),
            "previous": float(previous_avg),
            "change": float(change),
            "pct_change": float(pct_change),
            "improvement": change > 0
        }


class SleepInsights:
    """Generate actionable sleep insights and recommendations."""
    
    @staticmethod
    def generate_insights(
        sleep_df: pd.DataFrame,
        sleep_stage_df: Optional[pd.DataFrame] = None
    ) -> list[dict]:
        """Generate personalized insights from sleep data."""
        insights = []
        
        if sleep_df.empty:
            return [{"icon": "⚠️", "title": "No Data", "message": "Insufficient sleep data to generate insights."}]
        
        # Insight 1: Duration consistency
        if "sleep_duration" in sleep_df.columns:
            durations = sleep_df["sleep_duration"].dropna()
            if len(durations) >= 3:
                duration_std = durations.std()
                avg_duration = durations.mean()
                
                if duration_std > 90:  # >1.5 hours std dev
                    insights.append({
                        "icon": "📊",
                        "title": "Inconsistent Sleep Duration",
                        "message": f"Your sleep duration varies by ~{int(duration_std)} minutes. Try maintaining a consistent schedule.",
                        "severity": "warning"
                    })
                elif avg_duration < 360:  # <6 hours
                    insights.append({
                        "icon": "😴",
                        "title": "Sleep Duration Below Optimal",
                        "message": f"Average {int(avg_duration/60)}h {int(avg_duration%60)}m. Aim for 7 hours for optimal health.",
                        "severity": "warning"
                    })
                else:
                    insights.append({
                        "icon": "✅",
                        "title": "Good Sleep Duration",
                        "message": f"Averaging {int(avg_duration/60)}h {int(avg_duration%60)}m—excellent sleep amount.",
                        "severity": "success"
                    })
        
        # Insight 2: Efficiency
        if "efficiency" in sleep_df.columns:
            efficiency = sleep_df["efficiency"].dropna()
            if not efficiency.empty:
                avg_eff = efficiency.mean()
                if avg_eff < 80:
                    insights.append({
                        "icon": "🌙",
                        "title": "Low Sleep Efficiency",
                        "message": f"Sleep efficiency {int(avg_eff)}% suggests nighttime awakenings. Consider sleep environment improvements.",
                        "severity": "warning"
                    })
        
        # Insight 3: Sleep stages (if available)
        if sleep_stage_df is not None and not sleep_stage_df.empty and "stage" in sleep_stage_df.columns:
            stages = sleep_stage_df["stage"].value_counts()
            if 40004 in stages and 40003 not in stages:  # REM but no deep sleep
                insights.append({
                    "icon": "🧠",
                    "title": "Limited Deep Sleep",
                    "message": "Your sleep may lack sufficient deep sleep. Deep sleep is crucial for physical recovery.",
                    "severity": "warning"
                })
        
        return insights if insights else [
            {
                "icon": "⭐",
                "title": "Sleep Quality Excellent",
                "message": "Your sleep patterns look great! Keep up the good habits.",
                "severity": "success"
            }
        ]
    
    @staticmethod
    def get_recommendations(sleep_score: float, sleep_df: pd.DataFrame) -> list[str]:
        """Get personalized sleep recommendations."""
        recommendations = []
        
        if sleep_score < 60:
            recommendations.extend([
                "🛏️ Establish a consistent sleep schedule (same bedtime and wake time daily)",
                "🌙 Keep your bedroom cool, dark, and quiet",
                "📱 Avoid screens 30-60 minutes before bed",
                "☕ Limit caffeine after 2 PM"
            ])
        
        if sleep_score >= 75 and sleep_score < 85:
            recommendations.extend([
                "✨ Consider one targeted improvement: optimize bedtime consistency",
                "🏃 Add moderate exercise earlier in the day"
            ])
        
        if sleep_score >= 85:
            recommendations.append("🌟 Maintain your excellent sleep habits!")
        
        # Specific recommendations based on data
        if not sleep_df.empty and "sleep_duration" in sleep_df.columns:
            avg_duration = sleep_df["sleep_duration"].dropna().mean()
            if avg_duration < 300:
                recommendations.insert(0, "⏰ Prioritize getting more sleep—aim for 7 hours minimum")
        
        return recommendations[:4]  # Return top 4 recommendations


class SleepPatterns:
    """Analyze sleep patterns and generate visualizations."""
    
    @staticmethod
    def get_sleep_heatmap_data(sleep_df: pd.DataFrame, time_col: str = "start_datetime") -> pd.DataFrame:
        """
        Generate heatmap data: sleep duration by day of week.
        Returns DataFrame with day_of_week, week, duration for heatmap visualization.
        """
        if sleep_df.empty or time_col not in sleep_df.columns:
            return pd.DataFrame()
        
        df = sleep_df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
            df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
        
        df = df.dropna(subset=[time_col])
        if df.empty:
            return pd.DataFrame()
        
        # Add day of week and week number
        df["dow"] = df[time_col].dt.day_name()
        df["week"] = df[time_col].dt.isocalendar().week
        df["year"] = df[time_col].dt.year
        
        # Group by week and day
        if "sleep_duration" in df.columns:
            heatmap = df.groupby(["year", "week", "dow"])["sleep_duration"].mean().reset_index()
            heatmap["duration_hours"] = heatmap["sleep_duration"] / 60
            return heatmap
        
        return pd.DataFrame()
    
    @staticmethod
    def get_sleep_cycle_stats(sleep_stage_df: Optional[pd.DataFrame]) -> dict:
        """
        Calculate REM/Non-REM distribution and sleep cycle characteristics.
        """
        if sleep_stage_df is None or sleep_stage_df.empty or "stage" not in sleep_stage_df.columns:
            return {
                "total_cycles": 0,
                "rem_percentage": 0,
                "deep_sleep_percentage": 0,
                "light_sleep_percentage": 0,
                "awake_percentage": 0
            }
        
        stage_counts = sleep_stage_df["stage"].value_counts()
        total = len(sleep_stage_df)
        
        return {
            "total_cycles": total,
            "rem_percentage": float(stage_counts.get(40004, 0) / total * 100),  # 40004 = REM
            "deep_sleep_percentage": float(stage_counts.get(40003, 0) / total * 100),  # 40003 = Deep
            "light_sleep_percentage": float(stage_counts.get(40002, 0) / total * 100),  # 40002 = Light
            "awake_percentage": float(stage_counts.get(40001, 0) / total * 100)  # 40001 = Awake
        }
