# References — SurakshaMind

**AI-Powered Dynamic Mental Health Monitoring System**  
Problem Statement 26094 · SIH 2026

All citations are to published or officially released sources. Each entry includes a one-line statement of relevance to this prototype.

---

## Voice Biomarkers & PTSD

1. **Kathan et al.**, "Cross-Linguistic Acoustic Markers for PTSD," *Interspeech 2024* — Identifies MFCC2 and Loudness as validated cross-linguistic acoustic markers for PTSD screening; reports 70.1% AUC, directly informing our voice feature selection.

2. **IEEE Open Journal of Engineering in Medicine and Biology (OJEMB), 2023** — Introduces the "digital emotional twin" concept for longitudinal PTSD screening using passive digital phenotyping; conceptual basis for our personalised distress baseline approach.

---

## Indian Language NLP

3. **Sahani & Firos**, "MuRIL-based Mental Health Classification for Hindi Social Media," *Communications on Applied Nonlinear Analysis*, Vol. 33 (2026) — Benchmarks multilingual Indian language encoders; MuRIL achieves best Hindi encoder performance (F1 = 0.58), justifying our planned MuRIL/IndicBERT integration for Hindi check-in text.

4. **Srivastava et al.**, "IndiEMH: A Hinglish Mental Health Dataset," *LREC-COLING 2026* — Releases a Hinglish mental health dataset and annotation schema; directly applicable to training our text-based distress classifier on code-mixed Indian language inputs.

---

## Predictive Modeling

5. **Fu et al.**, "Prophet-LSTM Hybrid for Mental Health Risk Prediction," *Frontiers in Public Health*, 2025 — Demonstrates that combining temporal decomposition (Prophet) with sequence modelling (LSTM) outperforms standalone models for longitudinal mental health risk; informs our roadmap for an LSTM distress forecaster in v2.

---

## Explainable AI

6. **ScienceDirect Review, 2026** — Systematic review of XAI methods in mental health AI; finds SHAP and LIME dominate 70% of studies, with SHAP preferred in clinical-adjacent systems due to mathematical consistency guarantees. Justifies our choice of SHAP TreeExplainer over LIME for per-prediction attribution.

---

## Privacy & Compliance

7. **Digital Personal Data Protection (DPDP) Act, 2023** — Government of India legislation requiring that consent for personal data collection must be free, specific, informed and revocable at any time (§6); foundational to our consent-first design and planned DPDP consent manager module.

8. **IndiaAI Governance Guidelines, 2025** — Ministry of Electronics and Information Technology (MeitY) guidelines for responsible AI deployment in public services; requires human oversight for high-stakes AI outputs, directly implemented via our human-review-required flag and counsellor acknowledgment workflow.

---

## Government Infrastructure

9. **PIB Release 1780741 (2021)** — Press Information Bureau release announcing the National Helpline for Atrocity Affected (NHAA) helpline number 14566 and docket-based tracking system for victim complaints; our alert panel is designed to integrate with this existing infrastructure.

10. **PIB Release 2177389 (2025)** — Announces Tele-MANAS (national telecounselling service), Asmi AI chatbot and coverage across 10 regional languages; informs our multilingual check-in design and planned integration with Tele-MANAS referral pathways.

11. **PIB Release 2317515 (2026)** — Announces SAMBAL scheme and 217 Exclusive Special Courts for atrocity cases; provides policy context for the case-stage feature (Investigation → Chargesheet → Trial → Judgment → Compensation → Rehabilitation) used in our distress model.

---

## Field Evidence

12. **Seshu et al.**, "IVRS for Perinatal Depression Screening in Rural Bihar," *International Journal of Social Psychiatry*, 2021 — Demonstrates feasibility and uptake of Interactive Voice Response System (IVRS)-based mental health screening in a low-resource Indian rural context; validates our IVRS channel as a viable reach mechanism for victims in areas with low smartphone penetration.

---

## Notes

- Citations marked *(planned)* in the roadmap refer to capabilities not yet implemented in the prototype.
- All academic references are to published peer-reviewed work or official government releases.
- This prototype's synthetic benchmark is not a substitute for clinical validation against real-world data.
