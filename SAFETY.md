# LifeSystem Safety & Boundaries

This document records the safety boundaries LifeSystem's assessment and
guidance features are designed around, starting from Week 9 of development.

## No clinical or diagnostic content
- No question in the assessment asks about clinical symptoms, self-harm
  ideation, or medical/psychiatric history.
- Mental Wellness and Emotional domain questions are framed as general
  self-reported wellness check-ins, never as screening for a diagnosable
  condition.
- The system never outputs a diagnosis, clinical judgment, or treatment
  recommendation.

## Handling distress signals
- Open-text responses are not scored numerically, but are reserved for
  future crisis-language detection (planned: Week 23, Safety layer).
- If a response suggests serious/crisis-level distress, the system's role
  is to surface a supportive message pointing to real crisis resources —
  never to attempt to resolve, minimize, or diagnose the issue itself.

## Data minimization
- Only the minimum profile/assessment data needed to personalize the
  experience is collected.
- Passwords are hashed (bcrypt) and never stored or logged in plain text.
- Secrets (DB credentials, JWT signing key) live only in `.env`, which is
  gitignored and never committed.

## Status
This is a living document. It will be expanded significantly in Week 23
(Safety layer) with explicit boundaries, refusal patterns, and escalation
language before any LLM-generated content (Week 24) is introduced.