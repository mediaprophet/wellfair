# Sleep Analytics Dashboard - World-Class Update

## Overview

The Sleep Analytics Dashboard has been completely redesigned to provide enterprise-grade sleep monitoring and analysis capabilities. The new system combines advanced metrics, AI-driven insights, and beautiful visualizations to give users a comprehensive understanding of their sleep quality and patterns.

## New Features

### 1. Sleep Quality KPI Cards

Four key performance indicator cards display the most important sleep metrics at a glance:

- **💤 Sleep Score (0-100)**: AI-calculated quality metric based on:
  - Duration quality (40% weight): How close sleep duration is to optimal 7 hours
  - Efficiency (35% weight): Percentage of time actually asleep vs. in bed
  - Consistency (25% weight): Regularity of sleep schedule across the week
  
  Quality Classifications:
  - Excellent: 85+ (optimal habits, maintain current patterns)
  - Good: 75-85 (mostly good with minor improvements possible)
  - Fair: 65-75 (address consistency or duration)
  - Poor: 50-65 (significant improvements needed)
  - Very Poor: <50 (consider medical consultation)

- **⏱️ Duration**: Average sleep length with optimal/suboptimal indicator
  - Target: 7 hours (360-480 minutes)
  - Tracks: 7-day rolling average

- **🎯 Efficiency**: Sleep efficiency percentage
  - Target: 85%+
  - Reflects: Time asleep / Time in bed
  - Issues: Low efficiency often indicates frequent awakenings

- **📅 Consistency**: Sleep schedule regularity (0-100%)
  - Based on: Standard deviation of sleep start times
  - Higher: More regular sleep/wake cycle
  - Lower: Variable sleep times (may impact health)

### 2. Personalized Insights & Recommendations

The dashboard generates context-aware insights based on your sleep data:

**Example Insights:**
- Inconsistent sleep duration (>90 min variation) → Recommendation to maintain fixed schedule
- Sleep duration below optimal (<6h) → Suggestion to prioritize sleep
- Low efficiency (<80%) → Environmental optimization tips
- Limited deep sleep stages → Physical recovery concerns

**Personalized Recommendations:**
- Top 4 recommendations tailored to your sleep score
- Actions vary by sleep quality level
- Covers: Schedule, environment, habits, medical considerations

### 3. Advanced Trend Analysis

**Duration Trend:**
- Detects improving ↑ / stable → / declining ↓ trends
- Shows daily change rate in minutes
- Uses 14-day linear regression for accuracy

**Week-over-Week Comparison:**
- Compares current week vs. previous week average
- Shows percentage change and improvement indicator
- Requires minimum 7 days of data

### 4. Sleep Patterns Visualization

**Sleep Duration vs Efficiency Chart:**
- Dual-axis visualization showing:
  - Left axis: Sleep duration (hours) as bars
  - Right axis: Sleep efficiency (%) as line with markers
- Helps identify correlations between duration and quality
- Interactive hover details for each night

### 5. Sleep Architecture Analysis

**Sleep Stage Distribution:**
- Pie chart breakdown of sleep composition
- Displays percentages for:
  - REM Sleep (Dreams & memory consolidation)
  - Deep Sleep (Physical recovery & growth)
  - Light Sleep (Sleep transitions)
  - Awake Time (Should be <5% of night)

**Sleep Quality Indicators:**
- REM Sleep target: 20-25% of total sleep
- Deep Sleep target: 15-20% of total sleep
- Light Sleep: 50-60% of total sleep
- Awake Time: <5% of total night

### 6. Individual Night Analysis (Hypnogram)

**Features:**
- Select any available night for detailed analysis
- Visual sleep architecture timeline showing:
  - **Deep Sleep** (Purple): Restorative sleep, limited dreaming
  - **REM Sleep** (Green): Dream sleep, memory consolidation
  - **Light Sleep** (Blue): Lighter sleep stages
  - **Awake** (Red): Times when not sleeping

**Night-Level Metrics:**
- Sleep Score for that specific night
- Efficiency percentage
- Total sleep duration
- REM time in minutes

## Technical Implementation

### Core Module: `src/sleep_analytics.py`

#### SleepMetrics Class
Provides calculations for:
- `calculate_sleep_score()`: Weighted quality scoring (0-100)
- `calculate_consistency_score()`: Sleep schedule regularity (0-100)
- `calculate_sleep_debt()`: Accumulated sleep deficit
- `classify_sleep_quality()`: Quality level and explanation

#### SleepTrendAnalysis Class
Analyzes sleep patterns:
- `detect_trend()`: Trend detection (improving/declining/stable)
- `weekly_comparison()`: Week-over-week metrics comparison

#### SleepInsights Class
Generates personalized analysis:
- `generate_insights()`: Context-aware insights from data
- `get_recommendations()`: Personalized sleep recommendations

#### SleepPatterns Class
Analyzes sleep architecture:
- `get_sleep_heatmap_data()`: Weekly sleep pattern heatmap
- `get_sleep_cycle_stats()`: Sleep stage distribution

### UI Integration: `ui/app.py`

The enhanced Sleep Analytics tab includes:

```
💤 World-Class Sleep Analytics Dashboard
├── 📊 Sleep Quality Summary (KPI Cards)
│   ├── Sleep Score
│   ├── Duration
│   ├── Efficiency
│   └── Consistency
├── 💡 Personalized Insights
│   ├── Auto-generated insights
│   └── Actionable recommendations
├── 📈 Sleep Trends & Analysis
│   ├── Duration trend detection
│   └── Week-over-week comparison
├── 📅 Weekly Sleep Pattern
│   └── Duration vs Efficiency chart
├── 🧬 Sleep Architecture
│   ├── Sleep stage distribution
│   └── Sleep quality indicators
└── 🔬 Individual Night Analysis
    ├── Night selection
    ├── Hypnogram visualization
    └── Night-level metrics
```

## Algorithm Details

### Sleep Score Calculation

```
Sleep Score = (Duration Quality × 0.40) + (Efficiency × 0.35) + (Consistency × 0.25)

Duration Quality:
  - Peak at 7 hours (420 minutes): 100 points
  - Decay: -2 points per 10-minute deviation
  - Range: 0-100

Efficiency:
  - Target: 85%
  - Score: min(100, actual_efficiency × (100/85))
  - Range: 0-100

Consistency:
  - Based: Standard deviation of sleep start times
  - Formula: 100 - (std_dev_hours / 3 × 100)
  - Range: 0-100
```

### Sleep Debt Calculation

```
Debt per night = max(0, Optimal Duration - Actual Duration)
Optimal Duration = 420 minutes (7 hours)

Total Debt = Sum of all nightly deficits
Deficit Nights = Count of nights with negative balance
Avg Deficit = Mean deficit per night
```

## Data Requirements

### Required Columns (Sleep Summary)
- `start_datetime` or `com.samsung.health.sleep.start_time`: When sleep started
- `sleep_duration`: Sleep duration in minutes
- `efficiency` (optional): Sleep efficiency percentage

### Optional Columns
- `sleep_score`: Pre-calculated sleep score
- `total_rem_duration`: REM sleep duration in minutes

### Sleep Stage Data
- `start_datetime` or `start_time`: Stage start time
- `end_datetime` or `end_time`: Stage end time
- `stage`: Stage code
  - `40001`: Awake
  - `40002`: Light Sleep
  - `40003`: Deep Sleep
  - `40004`: REM Sleep

## Best Practices

### For Accurate Metrics:
1. **Consistent data entry**: Enable automatic sleep tracking on device
2. **Regular measurements**: At least 7-14 days for trends
3. **Timezone awareness**: Ensure correct timezone in export
4. **Complete sleep data**: Include both duration and efficiency if available

### For Better Sleep:
1. **Consistent schedule**: Same bedtime and wake time daily (improves consistency score)
2. **7-hour target**: Aim for 420 minutes (improves duration score)
3. **High efficiency**: Minimize awakenings, optimize bedroom environment
4. **Sleep cycles**: Get 4-6 complete sleep cycles per night (90 minutes each)

## Visual Design

The dashboard uses a sophisticated color scheme aligned with health data:

- **Primary**: Teal (#0d9488) - Health metric accent
- **Secondary**: Cyan (#14b8a6) - Data highlights
- **Accent**: Orange (#f97316) - Call-to-action
- **Clinical**: Purple (#7c3aed) - Medical metrics

### Card Styling:
- Frosted glass effect with backdrop blur
- Smooth hover transitions
- Clear visual hierarchy
- Responsive layout (mobile-friendly)

## Future Enhancements

Planned features for next iterations:

1. **Sleep Report Export**: PDF/CSV exports with charts and recommendations
2. **Goal Tracking**: Set and track sleep goals
3. **Sleep Debt Recovery**: Recommendations for recovering from sleep deficit
4. **Circadian Analysis**: Detect optimal sleep window based on patterns
5. **Intervention Tracking**: Log sleep improvement actions and measure impact
6. **Comparative Analysis**: Compare with population benchmarks
7. **Integration with Health Apps**: Connect with other health data sources
8. **Smart Notifications**: Alerts for concerning sleep patterns

## Troubleshooting

### No Data Displayed:
- Ensure Samsung Health export contains sleep data
- Check that file format matches expected CSV structure
- Verify time columns are properly formatted

### Inconsistent Metrics:
- Ensure data is sorted by date
- Check for null/missing values
- Verify sleep duration is in minutes

### Visualization Issues:
- Clear browser cache
- Try different browser/incognito mode
- Check internet connection for plotly CDN

## Credits

Developed as part of the wellfair project for comprehensive sleep analytics integration with Solid-compatible personal health records.

---

**Version**: 1.0  
**Last Updated**: February 2025  
**License**: GNU General Public License v3.0 or later
