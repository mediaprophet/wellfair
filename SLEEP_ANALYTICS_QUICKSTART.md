# Sleep Analytics Dashboard - Quick Start Guide

## 🚀 Getting Started

### 1. Launch the Application

```bash
cd c:\Projects\health
.\.venv\Scripts\activate
streamlit run ui/app.py
```

The dashboard will open in your default browser at `http://localhost:8501`

### 2. Navigate to Sleep Analytics

In the main interface:
1. Look for the left sidebar navigation menu
2. Select **"Sleep Analytics 💤"** from the main tab options
3. Wait for data to load (progress indicator shows loading status)

## 📊 Dashboard Sections Overview

### Section 1: Sleep Quality Summary
**What it shows:** Four key KPI cards displaying your sleep health

- **💤 Sleep Score**: Overall quality metric (0-100)
  - Green highlight = Excellent (85+)
  - Yellow = Good (75-85)  
  - Orange = Fair (65-75)
  - Red = Poor (<65)

- **⏱️ Duration**: Average hours slept (7h 0m is ideal)
  - Green checkmark = Optimal
  - Warning icon = Needs attention

- **🎯 Efficiency**: Quality of sleep time (85%+ is target)
  - Measures: Time asleep / Time in bed
  
- **📅 Consistency**: Sleep schedule regularity (0-100%)
  - Higher % = More regular schedule

### Section 2: Personalized Insights
**What it shows:** Smart recommendations based on your sleep

- Up to 3 auto-generated insights appear as cards
- Each shows an icon, title, and actionable message
- Click "📋 Personalized Recommendations" to expand full list (usually 4 items)

**Example Insights:**
- ✅ "Good Sleep Duration" - Your sleep amount is optimal
- ⚠️ "Inconsistent Duration" - Add consistency to improve score
- 😴 "Sleep Below Optimal" - Try to add 30 more minutes

### Section 3: Sleep Trends & Analysis
**What it shows:** How your sleep is changing

- **Duration Trend**: ↑ Improving | → Stable | ↓ Declining
  - Shows change rate (minutes per night)
  
- **Week-over-Week**: Compares this week vs last week
  - ✅ Green = Improved from last week
  - ⚠️ Yellow/Orange = Declined from last week

### Section 4: Weekly Sleep Pattern
**What it shows:** Chart of sleep over the past 2 weeks

- **Bar chart** (blue) = Sleep duration in hours
- **Line graph** (green) = Sleep efficiency %
- **How to use**: Look for patterns and correlations
  - Does duration affect efficiency?
  - Which days have best/worst sleep?

### Section 5: Sleep Architecture
**What it shows:** Breakdown of sleep types

- **Pie Chart**: Percentage of REM, Deep, Light, and Awake time
  - Healthy REM: 20-25%
  - Healthy Deep: 15-20%
  - Healthy Light: 50-60%
  - Healthy Awake: <5%

- **Quality Indicators**: Target percentages with explanations
  - REM Sleep: Essential for memory and emotion
  - Deep Sleep: Physical recovery and growth
  - Light Sleep: Sleep transitions
  - Awake Time: Should be minimal (<5%)

### Section 6: Individual Night Analysis
**What it shows:** Detailed breakdown of a specific night

1. **Select a Night**: Dropdown menu showing available dates
2. **Hypnogram**: Visual timeline of sleep stages
   - Purple = Deep Sleep
   - Green = REM Sleep
   - Blue = Light Sleep
   - Red = Awake
3. **Night Metrics**:
   - Sleep Score for that night
   - Efficiency %
   - Total duration
   - REM time in minutes

## 💡 Using Insights to Improve Sleep

### If Your Score Is LOW (< 65):

1. **Check the Insights** - What's the main issue?
   - Consistency? → Establish fixed sleep time
   - Duration? → Aim for 7 hours
   - Efficiency? → Improve sleep environment

2. **Follow Recommendations** - Expand the recommendation section
   - Usually 4 specific, actionable tips
   - Prioritize #1-2 first

3. **Monitor Trend** - Check back in 3-4 days
   - See if changes are helping
   - Consistency (⬆️ trend) usually takes 1-2 weeks

### If Your Score Is GOOD (65-85):

1. **Identify the Gap** - What's preventing "Excellent"?
   - Look at individual KPI cards
   - Focus on lowest metric

2. **Make One Change** - Don't overwhelm yourself
   - Example: Move bedtime 15 minutes earlier
   - Track impact over 1 week

3. **Celebrate Progress** - You're already sleeping well!
   - Small improvements = big health impact

### If Your Score Is EXCELLENT (85+):

1. **Maintain Current Habits** - You're doing great!
2. **Track Consistency** - Watch for seasonal changes
3. **Note What Works** - Remember your routine

## 🔍 Troubleshooting

### "No sleep summary data found"
- ❌ Your Samsung Health export lacks sleep data
- ✅ Solution: Ensure sleep tracking is enabled on your device
- ✅ Export Samsung Health again and reload the app

### Charts look empty
- ❌ Not enough days of data (need 3+ days for trends)
- ✅ Solution: Check back after more data accumulates
- ✅ Wait 7-14 days for best trend detection

### Metrics seem off
- ❌ Check timezone - must match your actual location
- ❌ Verify sleep duration is in minutes (not hours)
- ✅ Solution: Re-export Samsung Health with correct settings

### Sleep Score seems too low/high
- This is calculated based on sleep science principles
- Duration + Efficiency + Consistency = your score
- Compare against the quality levels (Excellent/Good/Fair/Poor)

## 📈 Tips for Better Sleep Score

### Immediate Impact (1-3 days):
1. ✅ Sleep 7 hours (420 minutes)
   - Even one night helps
   - Consistency matters

2. ✅ Avoid nighttime awakenings
   - Cool, dark room
   - White noise helps
   - Phone on silent

### Short Term (1-2 weeks):
3. ✅ Establish consistent bedtime
   - Same time every day (even weekends)
   - Consistency score will improve
   - Better circadian rhythm

4. ✅ Optimize sleep environment
   - 65-68°F (18-20°C) is ideal
   - Blackout curtains
   - No screens 30-60 minutes before bed

### Long Term (4+ weeks):
5. ✅ Build sleep routine
   - Same morning wake time
   - Exercise earlier in day
   - Limit caffeine after 2 PM

6. ✅ Track improvements
   - Use the trends section
   - Watch Week-over-Week % change
   - Notice pattern improvements

## 🎯 Reading the Hypnogram (Night Analysis)

The hypnogram shows your sleep architecture through the night:

```
Typical 8-hour sleep pattern:
Light Sleep ─────┐
                ╭─┴─╮
Deep Sleep   ──╯    ╰──╮
                        ╭──╮
REM Sleep  ──────────╯   ╰──╮
                             ╰──
Awake   ─────────────────────────  (should be minimal)

Time →  Bed  1h  2h  3h  4h  5h  6h  7h  8h  Wake
```

**What to Look For:**
- ✅ Good: Cycles repeating every 90 minutes
- ✅ Good: More deep sleep in first half of night
- ✅ Good: More REM in second half
- ⚠️ Bad: Too much time awake (red sections)
- ⚠️ Bad: Cycles disrupted (fragmented pattern)

## 🔐 Data Privacy Note

All sleep analytics are calculated locally on your device. No data is sent to external servers. Your sleep data remains private and secure.

---

## Need More Help?

See **SLEEP_ANALYTICS_GUIDE.md** for:
- Detailed algorithm explanations
- Advanced features and settings
- Troubleshooting guide
- Future features roadmap

Happy sleeping! 😴💤

---

**Last Updated**: February 26, 2025  
**Version**: 1.0  
**Status**: Production Ready ✅
