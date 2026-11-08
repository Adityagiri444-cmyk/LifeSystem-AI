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

## Safety layer (Week 23)
Implemented in `backend/app/services/safety.py`, with all wording and rules in
`backend/app/data/safety_policy.json` so they can be reviewed without reading code.

**Input checks** (`POST /safety/check`): user-written text is classified in memory as
- `escalate` (crisis or self-harm language): supportive message, "contact your local
  emergency number", and a list of free helplines. No attempt to resolve or analyse it.
- `redirect` (asks for a diagnosis, or for medication/treatment advice): a plain
  refusal that points to a qualified professional, then offers low-pressure activities.
- `none`: nothing detected.
The most serious category always wins. The checked text is never stored or logged.

**Output gate** (`safe_output`): any generated text (Week 24 LLM, templates) must pass
a banned-pattern filter before it is shown: no diagnosis ("you have depression"), no
treatment or cure claims, no medication or dosage advice, no "you don't need a
doctor". If it fails, a safe fallback is shown instead. The backend, not the model,
is the authority.

**Support prompt**: three or more strain check-ins within 72 hours (and the latest is
not "okay") adds a gentle "talk to someone you trust" prompt to `/recovery/status`.

**Known limits** (be honest about these):
- Pattern matching is not understanding. It misses indirect or novel wording and will
  occasionally over-flag (for example a joke like "I want to die laughing"). It errs
  towards showing support.
- Only English is covered.
- Helpline numbers must be re-verified before any public deployment (Week 31).
- This is a productivity tool, not a medical or crisis service.

## LLM integration (Week 24)
Implemented in `backend/app/services/guidance.py` and `llm.py`. The LLM is optional and
only ever drafts one short wording line. The backend stays the authority.

- **Minimal data out:** the prompt contains only four facts: mode (recovery/growth),
  a feeling label from a fixed list, the title of the quest the backend chose, and the
  title of one catalog activity. No names, emails, user-written text, or history.
- **The LLM never chooses actions:** quests and activities come from the rule-based
  engines. The model cannot add, change or invent recommendations.
- **Strict output schema:** JSON `{message, tone}` only. Message must be plain text,
  280 characters or fewer, one line, no links; tone must be from a fixed list.
- **Safety gate on every reply:** the Week 23 output filter runs on the model's text.
  A diagnosis, treatment claim, or "you don't need a doctor" is blocked.
- **Always a fallback:** missing key, timeout, HTTP error, bad JSON, schema failure or
  safety block all return a deterministic template instead. The response says which
  (`source` and `fallback_reason`). Errors never reach the user.
- **Support prompt and safety note** are added by the backend, verbatim, never by the model.
- **Secrets:** the API key lives only in `.env`, is sent only as a request header, and is
  never logged or returned.
- **Caching:** identical facts reuse a reply for 10 minutes to stay inside free-tier limits.

**Known limits:**
- Free-tier providers can change limits, models or terms, and may use prompts to improve
  their products. Only the minimal facts above are sent for that reason.
- The output filter is pattern-based; a cleverly worded harmful reply could pass. The
  tight schema, short length and minimal facts reduce that risk but don't remove it.

## Status
Living document. Next: Phase 6 (React UI) must show the safety note and support prompt
on every guidance screen, and call `/safety/check` on any free-text field.