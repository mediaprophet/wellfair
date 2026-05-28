**✅ Here is your requested output.**

You can copy everything below and save it directly as a Markdown file (e.g. `SYNTHETIC_DEMO_PERSONS_AND_APP_REVIEW.md`).

---

# Wellfair – Complete Functionality Review + Synthetic Demo Person Profiles

**Date:** 28 May 2026  
**Purpose:** This document provides a critical review of the **current complete functionality** of the wellfair application and supplies two initial synthetic demo person profiles. These profiles are designed as illustrative foundations for generating realistic synthetic Samsung Health export files (CSV + JSON) that can be used for testing, demonstration, and development of broader wellbeing analytics (including sleep, welfare evaluation against models such as Maslow’s hierarchy, and future Sanctuary Mode features).

---

## 1. Critical Review of Complete Current Functionality

### Core Purpose (as currently implemented)
wellfair is a **desktop-first Python + Streamlit application** that ingests Samsung Health exports (CSVs + optional JSONs) and converts them into **Solid-compatible RDF** (Turtle + JSON-LD) using a fully template-driven YAML ontology. It functions as a **Personal Wellbeing Informatics Vault** with strong emphasis on local processing, privacy, and semantic interoperability.

### Fully Implemented Functionality

**Data Ingestion & Processing**
- Loads Samsung Health export folders (auto-detects `com.samsung.health.*.csv` files and matching JSONs).
- Timezone-aware timestamp normalisation (`start_time` + `time_offset`).
- 100% **YAML-driven ontology** (`config/ontology_template.yaml`) – no code changes required to add or modify data types.
- Generates Solid-style POD structure: `/health/{type}/{YYYY-MM}.ttl` (plus JSON-LD).

**Visualisation & Analysis**
- Standard biometric charts/tables: weight, steps, heart rate.
- **Advanced Sleep Analytics Dashboard** (major recent addition):
  - Sleep Quality Score (0–100) – AI-derived from duration, efficiency, consistency.
  - Hypnogram visualisation (night-by-night sleep stages).
  - Sleep architecture breakdown (REM / Deep / Light) with optimal targets.
  - Trend analysis (improving / declining / stable) with daily change rates.
  - Week-over-week comparison.
  - Personalised context-aware insights.
  - Professional KPI cards.

**User Interface (Streamlit)**
- Cleaner navigation reduced to 5 core health data sections.
- Dedicated Settings panel (mentioned in documentation and `NAVIGATION_UPDATE.md`, but currently appears blank/unimplemented in the UI).
- Sidebar options (including clinical mode for optional SNOMED/LOINC/FHIR links).

**Development & Testing Support**
- Synthetic data generator: `scripts/generate_synthetic_export.py`.
- Existing small synthetic dataset in `data/synthetic_samsung_export/`.
- Tests for synthetic processing and sleep analytics.

**Technology Stack**
- Python + Streamlit (main app).
- Rust core compiled to WASM (for potential browser use).
- RDF handling with schema.org, QUDT, PROV-O, and custom `health:` namespace.

### What Is **Not Yet** Fully Implemented or Clearly Visible
- Settings panel remains blank despite navigation updates.
- No public mention or implementation of **Sanctuary Mode**.
- Broader welfare/wellbeing modelling (e.g. Maslow’s hierarchy evaluation) is not yet surfaced in the UI or analytics.
- Only Samsung Health data is supported (future extensions for pathology PDFs, Google Timeline, environmental data are planned but not active).
- The public narrative still heavily frames the project as “health-to-solid” rather than the broader wellfair vision.
- No clear separation documented between Solid-compatible features and wellfair-specific/local-first extensions.

**Overall Assessment**:  
The core pipeline and especially the new sleep analytics are quite sophisticated and production-ready for Samsung Health data. The app is technically strong but the **user-facing narrative, settings functionality, and broader wellbeing/welfare features** have not yet caught up with the expanded vision.

---

## 2. Synthetic Demo Person Profiles

These two profiles are **initial illustrative foundations**. They are written to be realistic, respectful, and detailed enough to generate meaningful synthetic Samsung Health data (sleep logs, activity, heart rate, weight, etc.) that reflect complex real-world wellbeing challenges. They can be expanded into full synthetic export files for testing sleep analytics, ontology mappings, welfare scoring, and future Sanctuary Mode logic.

### Profile 1: “Michael R.” (Male, 42 years old)

**Demographics**  
- Age: 42 | Gender: Male | Location: Currently rough-sleeping / temporary shelter in Sydney, Australia.

**Background**  
- Recently separated from long-term partner who has become seriously unwell (mental health crisis).  
- Has two children (ages 9 and 11) whom he is currently unable to see due to family court interim orders (he has a completely clean police record and no history of violence or substance issues).  
- Self-employed tradesperson (handyman / minor building repairs) – work has become extremely irregular.

**Current Situation**  
- Homeless / insecure housing for the past 7 weeks.  
- Sleeping in a tent, car, or emergency shelter when available → highly disrupted sleep.  
- High stress and anxiety levels, feelings of helplessness and loss of purpose.  
- Struggling to maintain consistent work due to lack of stable address, transport, and personal presentation.  
- Pre-existing health conditions: mild Type 2 diabetes (managed poorly), chronic lower back pain from trade work, occasional asthma.

**Health & Wellbeing Indicators (for synthetic data)**  
- Irregular and poor-quality sleep (frequent awakenings, short duration, high restlessness).  
- Highly variable daily step count (some days very high when working, many days near zero).  
- Elevated resting heart rate due to chronic stress.  
- Weight loss from inconsistent eating.  
- Low physical activity consistency, disrupted circadian rhythm.  
- Potential data signals: frequent “light sleep” dominance, very low deep/REM percentages, high movement during sleep periods.

**Maslow Alignment (for future welfare modelling)**  
- Severe deficits in: Physiological needs (shelter, consistent food/sleep), Safety (housing, financial), Love/Belonging (family separation), Esteem (loss of provider identity).

---

### Profile 2: “Elena V.” (Female, 35 years old)

**Demographics**  
- Age: 35 | Gender: Female | Location: Unstable / unsafe housing in outer Sydney suburbs.

**Background**  
- Former sex worker (escort) for 12 years. Exited the industry 18 months ago.  
- Survived prolonged severe trauma (physical, sexual, and psychological) across multiple relationships and work environments.  
- Diagnosed PTSD and complex trauma.  
- History of substance use (alcohol and stimulants) as coping mechanism – currently in early recovery with relapses.

**Current Situation**  
- Struggling to maintain safe, stable accommodation (frequent moves between short-term rentals, couch-surfing, and women’s refuges).  
- Multiple attempts to secure stable housing have failed due to rental history, income instability, and discrimination.  
- Works casual / gig economy jobs when mentally able, but frequently unable to maintain regular employment.  
- Limited family support; social isolation is severe.

**Health & Wellbeing Indicators (for synthetic data)**  
- Extremely fragmented sleep with nightmares, night sweats, and hypervigilance awakenings.  
- Irregular heart rate patterns (high variability linked to anxiety/panic).  
- Weight fluctuations due to disordered eating and substance-related appetite changes.  
- Periods of very low activity followed by manic high-activity days.  
- Potential data signals: very high “awake” time during sleep periods, suppressed REM sleep, inconsistent step counts, frequent resting heart rate spikes at night.

**Maslow Alignment (for future welfare modelling)**  
- Critical deficits in: Safety (unstable/unsafe housing, trauma triggers), Love/Belonging (isolation), Esteem (stigma and shame), Self-actualisation (difficulty planning future).

---

These two profiles are intentionally contrasting yet complementary. They provide rich foundations for generating synthetic demo files that will stress-test the sleep analytics, ontology extensibility, and (in future) welfare evaluation and Sanctuary Mode features.


You can add this directly to the previous `SYNTHETIC_DEMO_PERSONS_AND_APP_REVIEW.md` file as the third profile.

---

### Profile 3: “Rebecca L.” (Female, 41 years old)

**Demographics**  
- Age: 41 | Gender: Female | Location: Intermittent rough sleeping / tent-based living along riverbanks and bushland in regional New South Wales, Australia (occasional short-term refuge stays).

**Background**  
Rebecca has a long history of complex trauma, including childhood and adult sexual abuse, which led to deep mistrust of institutions, government services, and support systems. For approximately seven years she was repeatedly offered stable housing and support services but consistently declined them, choosing instead to live autonomously in a tent on the banks of a river. She viewed many formal services as controlling or dominating rather than genuinely helpful.

Around 12 years ago (circa 2014), while living in the tent by the river, she gave birth to twins without medical assistance. One twin died shortly after birth; the surviving child was taken into care. This event profoundly deepened her trauma, grief, and resolve to remain outside mainstream systems.

**Current Situation (12+ years later)**  
Rebecca continues to live primarily in makeshift shelter (tent or basic bush camps), moving between riverine locations and occasional short stays in women’s refuges or crisis accommodation when conditions become too dangerous. She has very limited contact with formal support networks and survives largely through informal means, occasional casual work, and community goodwill. She carries significant unresolved grief over the loss of one twin and the separation from the surviving child. Her autonomy remains extremely important to her, even at the cost of safety and stability.

**Health & Wellbeing Indicators (for synthetic data)**  
- **Sleep**: Extremely fragmented and poor quality. Frequent hypervigilance awakenings, nightmares related to past trauma and the river birth, and irregular sleep/wake cycles due to outdoor living and environmental factors (weather, noise, safety concerns). Samsung Health would likely show very low sleep efficiency, minimal deep/REM sleep, high restlessness scores, and frequent “awake” periods during the night.
- **Activity**: Highly variable step counts — some days involve significant walking/movement for survival (foraging, relocating camp, seeking resources), while other periods show near-zero activity due to exhaustion, depression, or injury.
- **Heart Rate**: Chronically elevated resting heart rate with frequent spikes, consistent with long-term PTSD, anxiety, and hyperarousal. Night-time heart-rate variability is likely poor.
- **Other biometrics**: Weight fluctuations linked to inconsistent nutrition and high stress. Possible chronic pain (back, joints) from years of tent living and physical hardship. Low overall physical recovery due to ongoing environmental exposure.
- **Data patterns**: Strong signals of circadian rhythm disruption, seasonal worsening in colder/wetter months, and occasional “recovery” periods if she accesses temporary shelter.

**Maslow Alignment (for future welfare modelling)**  
- **Physiological needs**: Partially met through basic survival strategies, but consistently compromised (exposure, inconsistent food/sleep).  
- **Safety**: Critically unmet — ongoing physical danger from location and lack of secure shelter, compounded by trauma history.  
- **Love/Belonging**: Severe isolation; loss of one child and separation from the other creates profound grief and disconnection.  
- **Esteem**: Damaged by stigma, loss of autonomy struggles, and societal judgment.  
- **Self-actualisation**: Extremely limited; survival and autonomy take precedence over longer-term personal growth or stability.

---

**Notes for synthetic data generation**  
This profile is particularly valuable for testing extreme long-term trauma + environmental exposure scenarios. It will produce very challenging sleep analytics data (persistent poor sleep architecture, high stress markers) and highlight gaps in current welfare modelling. It can be used to explore how wellfair’s ontology and future Sanctuary Mode might handle deeply complex autonomy vs. safety trade-offs.

---

Profile 4: “Margaret T.” (Female, 78 years old) – Single Woman Experiencing Elder Abuse
Demographics

Age: 78 | Gender: Female | Location: Lives alone in her long-term family home in western Sydney suburbs.

Background
Margaret is a widow who has lived independently for 15 years. She has two adult children who are now her primary source of “support.” Over the past four years, one child (a son) has gradually taken control of her finances, medication, and daily decisions while subjecting her to psychological and financial abuse. This includes coercing her into signing over property documents, restricting her access to money, and emotionally manipulating her with threats of abandonment or institutionalisation if she complains.
Current Situation
Margaret is experiencing ongoing elder abuse in the form of financial exploitation, psychological control, and neglect. She is socially isolated, rarely leaves the house, and lives in fear of upsetting her son. She has hidden the worst of the abuse from neighbours and services out of shame and fear of losing her home. Her physical health has declined rapidly under the stress and poor management of her chronic conditions (hypertension, arthritis, and early-stage dementia).
Health & Wellbeing Indicators (for synthetic data)

Sleep: Highly disrupted with frequent night-time awakenings due to anxiety and worry. Samsung Health would show poor sleep efficiency, low deep sleep, and elevated resting heart rate during sleep periods.
Activity: Very low daily step count (often under 2,000 steps), minimal movement due to fear of leaving the house and physical pain. Occasional short bursts when trying to manage household tasks alone.
Heart Rate: Chronically elevated resting heart rate with frequent spikes linked to stress and panic when interacting with her son.
Other patterns: Weight loss from irregular eating (son controls shopping and often withholds food as punishment), irregular medication adherence (tracked via Samsung Health if she has a wearable), and increasing periods of sedentary behaviour.

Maslow Alignment (for future welfare modelling)

Physiological needs: Compromised (inconsistent nutrition, medication, and rest).
Safety: Severely threatened (financial abuse, fear of homelessness, loss of autonomy).
Love/Belonging: Damaged by betrayal from her own child and resulting isolation.
Esteem: Deeply eroded by feelings of helplessness, shame, and loss of dignity.
Self-actualisation: Almost non-existent.


Profile 5: “Robert K.” (Male, 82 years old) – Elder Abuse by Partner
Demographics

Age: 82 | Gender: Male | Location: Lives with his wife in a retirement unit in coastal New South Wales.

Background
Robert has been married for 54 years. He has multiple chronic health conditions (advanced heart disease, mobility issues after a stroke, and early dementia). His wife (age 79) has become increasingly resentful of the caregiving burden. Over the past three years she has begun actively manipulating his care, medication, and medical appointments with the apparent goal of hastening his decline and death so she is no longer responsible for looking after him.
Current Situation
Robert is experiencing a insidious form of elder abuse through neglect, emotional manipulation, and medical coercion by his partner. His wife deliberately skips or alters his medication, discourages medical treatment, restricts his access to phones and support services, and uses guilt-tripping language (“You’re a burden”, “I wish this would just end”). She presents a caring public image while privately undermining his health and independence. Robert is aware of the situation but feels trapped and powerless.
Health & Wellbeing Indicators (for synthetic data)

Sleep: Poor quality with frequent awakenings, breathlessness (due to heart condition), and anxiety. Data would show very low sleep efficiency, minimal restorative sleep, and high heart-rate variability at night.
Activity: Extremely low step count and prolonged sedentary periods. Occasional attempts at movement are often discouraged or unsupported by his wife.
Heart Rate: Highly irregular and frequently elevated, with dangerous patterns consistent with poorly managed heart disease and chronic stress.
Other patterns: Rapid weight loss, irregular medication adherence logs (if tracked), frequent “resting” periods during the day, and declining overall physical function. Samsung Health would likely flag consistent deterioration trends.

Maslow Alignment (for future welfare modelling)

Physiological needs: Actively undermined (medication, nutrition, and medical care are being sabotaged).
Safety: Critical risk — direct threat to life through neglect and manipulation.
Love/Belonging: Profound betrayal within the primary relationship.
Esteem: Severe loss of dignity and self-worth.
Self-actualisation: Effectively eliminated by dependency and control.


**✅ Here is the new synthetic demo person profile** (Profile 6).

You can add this directly to your `SYNTHETIC_DEMO_PERSONS_AND_APP_REVIEW.md` file as **Profile 6**.

---

### Profile 6: “Jordan M.” (Non-binary, 37 years old) – NDIS Funding Exploitation & Systemic Abuse

**Demographics**  
- Age: 37 | Gender: Non-binary | Location: Social housing unit in south-western Sydney, New South Wales.

**Background**  
Jordan lives with multiple serious and intersecting disabilities: acquired brain injury from a workplace accident, complex PTSD, chronic pain syndrome, mobility impairment requiring a wheelchair for longer distances, and severe anxiety/depression. They were approved for the National Disability Insurance Scheme (NDIS) five years ago. While the NDIS funding was intended to provide genuine support for independent living, Jordan has become trapped in a cycle of exploitation by several service providers.

**Current Situation**  
Multiple NDIS providers (support coordinators, allied health therapists, and daily living assistance agencies) are systematically exploiting Jordan’s funding package. Key issues include:
- Providers regularly billing for services that were never delivered or were significantly below the agreed standard.
- Falsified progress notes and attendance records claiming hours of support that did not occur.
- Coercion into using specific “preferred” providers who have financial kickback arrangements.
- Support workers frequently cancelling or shortening visits but still claiming full funding.
- Little to no actual improvement in Jordan’s quality of life despite high funding utilisation.
- Attempts by Jordan to change providers or raise complaints have been met with gaslighting, threats of reduced support, and further falsified records portraying Jordan as “difficult” or “non-compliant.”

Jordan feels powerless, trapped in a system that was designed to help but is instead extracting funds while providing minimal genuine care. This has led to deep distrust of institutions and worsening mental health.

**Health & Wellbeing Indicators (for synthetic data)**  
- **Sleep**: Extremely poor and fragmented. Chronic pain and anxiety cause frequent awakenings, nightmares, and very low sleep efficiency. Samsung Health data would show consistently low deep and REM sleep percentages, high restlessness, and elevated heart rate during sleep.
- **Activity**: Highly variable and generally low. Some days involve minimal movement due to pain and fatigue; other days show short bursts of activity when attempting self-care or attending appointments. Overall step count is low, with prolonged sedentary periods.
- **Heart Rate**: Chronically elevated resting heart rate with frequent spikes linked to anxiety, pain, and stress from interactions with exploitative providers.
- **Other patterns**: Weight fluctuations due to stress-related eating issues and irregular medication adherence (some medications are not being properly supported by providers). Data would likely show clear deterioration trends over time despite high NDIS funding being spent.

**Maslow Alignment (for future welfare modelling)**  
- **Physiological needs**: Only partially met — pain management, nutrition, and rest are compromised by inadequate or fraudulent support.  
- **Safety**: Severely undermined — financial exploitation, falsified records, and loss of autonomy create ongoing risk and instability.  
- **Love/Belonging**: High isolation; distrust of services and exhaustion have eroded social connections.  
- **Esteem**: Deeply damaged by feelings of being used, powerless, and treated as a funding source rather than a person.  
- **Self-actualisation**: Almost entirely blocked; survival and navigating exploitation consume all energy.

---
