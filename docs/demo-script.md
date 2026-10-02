# Jury Demo Script — SurakshaMind

**Time budget: 2 minutes**  
**URL:** `http://localhost:8000`  
**Audience:** SIH 2026 panel judges

---

## Before you start

- Server running: `uvicorn app.backend.main:app --host 0.0.0.0 --port 8000`
- Browser open to `http://localhost:8000`
- Status pill in top-right should show **● Online · dynamic-xgboost-v1.0**

---

## Screen 1 — Home (15 seconds)

**Say:**
> "This is SurakshaMind — an AI system for the Ministry of Social Justice that continuously monitors the mental health of atrocity victims. India has no such system today. Victims get legal and financial support, but nobody is watching whether they're okay between court dates.
>
> Our system monitors via five channels — chatbot, IVRS, SMS, app and web — and gives each victim a Dynamic Distress Score. The entire closed loop is: **Monitor → Detect → Alert → Intervene → Reassess.**"

**Point to:** KPI row showing 2,000 victims monitored, high-risk count, and the 5-channel strip.

---

## Screen 2 — Check-in (35 seconds)

**Click:** "Check-in" in the nav.

### Text tab (15 seconds)

**Say:**
> "A victim checks in via chatbot. Watch what happens."

**Click:** the **"High Risk"** preset button. This fills in:
```
I am afraid and cannot sleep. There have been threats again and the case
has been delayed for months. I have no money left.
```

**Click:** "🔍 Analyse Check-in"

**Point to the result and say:**
> "The AI scores this at around 68 — High risk. The top three contributing factors are: distress keywords detected, negative sentiment, and prolonged case delay. The system immediately recommends: priority counselling within 24 hours plus legal aid follow-up."

### Voice tab (20 seconds)

**Click:** the **"Voice Check-in (IVRS Simulated)"** tab.

**Say:**
> "For victims who can't type — rural areas, elderly, low literacy — we support IVRS phone calls. Watch a simulated call."

**Click:** "📞 Simulate IVRS Call"

*(3-second animation plays)*

**Point to the feature table and say:**
> "The system extracts MFCC2 and Loudness — validated cross-linguistic PTSD markers from Interspeech 2024 — along with pitch variance and pause ratio. These four features map to a DDS score, the same as the text check-in."

---

## Screen 3 — Counsellor Dashboard (20 seconds)

**Click:** "Dashboard" in the nav.

**Say:**
> "The counsellor sees all 50 highest-risk victims in one view. Sorted by distress score. Red is Critical, orange is High. Searchable, filterable."

**Click:** a red **Critical** row.

---

## Screen 4 — Victim Detail (15 seconds)

**Say:**
> "One click opens the full victim profile. This 30-day trend chart shows the distress score rising — the system detected escalation two interactions ago. Below is the SHAP panel — it tells the counsellor *why* the score rose: threats received is the biggest driver, followed by low social support."

**Point to:** case-stage progress bar showing the victim is in Trial stage.

---

## Screen 5 — Alert Panel (20 seconds)

**Click:** "Alerts" in the nav.

**Say:**
> "High and Critical cases immediately create a review flag. The counsellor sees the recommended action, the notification log showing SMS and email were delivered, and the source channel — IVRS, chatbot, or app.
>
> Crucially — the AI never acts autonomously. It flags. A human must acknowledge."

**Click:** "✅ Acknowledge" on an open alert. Fill in a note: *"Called victim; referred to district hospital counsellor."* Click **Confirm**.

**Say:**
> "Acknowledged. The case is now tracked."

---

## Screen 6 — Analytics (15 seconds)

**Click:** "Analytics" in the nav.

**Say:**
> "District officers and MoSJE get this view — average distress by state, risk distribution, case stage breakdown, and intervention success rate. This is the national oversight layer."

---

## Closing (0 seconds — you're on time)

**Say:**
> "Monitor → Detect → Alert → Intervene → Reassess. That's Sanjeevani."

---

## Fallback if server is down

Open `/docs` directly and show the live Swagger UI. Run `POST /demo/checkin` manually with the critical preset payload. The interactive API docs are a strong backup for a technical jury.

---

## Key numbers to remember

| Metric | Value |
|---|---|
| Synthetic benchmark R² | 0.943 |
| High/Critical Recall | 86.6% |
| Victims in demo DB | 2,000 |
| Interactions | 20,000 |
| Languages supported (v2) | 10 |
| API endpoints | 13 |
| Test pass rate | 10/10 |
