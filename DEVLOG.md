# LifeSystem — Development Log

A running record of mistakes, bugs, gaps, and fixes, kept from Week 4 onward.
The goal isn't to hide these — it's to prove they were understood and resolved,
and to have a real reference for what broke and why.

---

## Weeks 21-22 (recovery mode, content recommendations)

**In my own words (Weeks 21-22):** WRITE 3-4 SENTENCES HERE FROM MEMORY.

**Design decisions:**
- No free-text notes in check-ins (data minimization, per SAFETY.md).
- Recovery state is derived from the latest check-in (strain state within 24h),
  not a stored flag, so it can't get stuck on.
- Recovery mode only guides suggestions (easy quests, 20 minutes or less, 50 XP
  target). Quest completion is never blocked or penalised.
- The content catalog is JSON data plus pure ranking functions; a test scans
  the catalog text for clinical or treatment wording.

**Known gaps (deferred):**
- Recovery completions still count towards difficulty streaks, so a tired day on
  an easy quest can push the user up a level.
- Quests have no duration data, so recovery mode's "short quest" filter is weak
  (unknown duration is allowed).
- Content recommendations have no feedback loop yet (likes/dislikes in Week 28).
- The catalog is small and hand-written, with no real links.
- Profile `preferences` is an unvalidated JSON blob; unknown categories are
  silently ignored.

**Process (Week 20 commit):** `git add .` was run from `backend/`, which skipped
files outside it (DEVLOG.md, frontend/). *Lesson: run git commands from the repo root.*

---

## Weeks 17-20 (difficulty, bottlenecks, next action, explainability)

**In my own words (Week 20):** WRITE 3-4 SENTENCES HERE FROM MEMORY.

**Bug found and fixed (Week 20):** the explain endpoint labelled a hard quest
"high confidence" with `recommended_now: true` for an easy-level user. Fix:
confidence is capped at 0.6 on a difficulty mismatch, and `recommended_now`
now requires a level match. Verified in pytest (55 passed) and live in Swagger
(explain/3 = 0.6 medium false; explain/2 = 0.95 high true).
*Lesson: a score needs a hard "don't recommend" rule when a constraint is
violated. Score alone isn't enough.*

**Known gaps (deferred):**
- Confidence is a heuristic, not a calibrated probability: correlated factors
  (low score, active goal) are counted more than once.
- Quest catalog is thin at medium/hard (all Physical quests are easy; Career
  has one medium quest).
- Difficulty streak is uncapped once the user reaches "hard".
- Bottleneck "no activity" low-severity entries can appear as the 7-day
  window rolls.
- Pydantic `class Config` deprecation warning (harmless; switch to `ConfigDict`).
- A resubmitted assessment overwrites the previous one.

---

## Environment & tooling

- **`__init__.py` creation "error"**: VS Code's error tooltip rendered double
  underscores as markdown italics, making it look like a different, invalid
  filename. Not a real bug — just a confusing UI rendering quirk.
- **`.env.example` created as a folder, not a file**: used "New Folder" instead
  of "New File" in VS Code. Fixed by deleting and recreating correctly.
  *Lesson: a file with an expand-arrow (▸) in the Explorer is a folder.*
- **`.eve.example` typo**: mistyped the filename when creating it (missing "n").
  Fixed with a rename; re-committed.
- **`uvicorn` run from the wrong directory** (repeated several times):
  running `uvicorn app.main:app` from `LifeSystem/` instead of
  `LifeSystem/backend/` caused `ModuleNotFoundError: No module named 'app'`.
  *Lesson: `app.main:app` only resolves correctly from inside `backend/`.*
- **Forgot PostgreSQL password**: resolved by temporarily setting
  `pg_hba.conf` auth method to `trust`, resetting the password via `psql`,
  then reverting `pg_hba.conf` back to `scram-sha-256`.
- **Special characters in the DB password broke `DATABASE_URL`**: an `@` in
  the password collides with the `user:pass@host` URL syntax. Fixed by
  URL-encoding it as `%40`.

## Code mistakes (mostly from pasting at the wrong location)

- **`config.py` missing `from pydantic_settings import BaseSettings`**:
  import got dropped when editing. Caused `NameError`.
- **`main.py` duplicated imports/`include_router` calls** (happened twice):
  new code pasted at the cursor instead of replacing the whole file.
- **`routers/auth.py` — `login` function split in half**: a paste landed
  mid-function, interleaving `register`, `login`, and imports incorrectly.
- **`services/auth.py` — accidentally deleted `hash_password`/
  `verify_password`**: a replace-paste only included the new JWT function.
- **`models.py` missing `from sqlalchemy.orm import relationship`**: added
  a `relationship(...)` field without its import.
- **Lesson learned across all of the above**: select-all-then-paste for full
  file replacements, never paste at the cursor into an existing file.

## Design/logic bugs caught via testing

- **`NoReferencedTableError` on `goals.domain_id`**: no SQLAlchemy `Domain`
  model existed even though the table did in Postgres. Fixed by adding one.
- **Login endpoint JSON vs OAuth2 form mismatch**: Swagger's Authorize button
  expects OAuth2 form data, not JSON. Fixed by switching to
  `OAuth2PasswordRequestForm`.
- **`/quests/difficulty` returned 422**: shadowed by `/{quest_id}`. Fixed by
  declaring fixed-path routes before the parameterised one.
- **`PUT /quests/{id}` returned a raw `500`, not a clean `400`/`422`** on
  invalid input (bad `domain_id`/`difficulty`). **Known gap, deferred to
  Week 30 (testing/security/input validation).**

## Known, intentionally deferred gaps

- **Quest `prerequisites` are stored but not enforced** at completion time —
  needs real completion-history tracking, not just "last 24h."
- **Quest completion's 24h "already completed" check doubles as a
  pseudo-prerequisite check**, which isn't actually correct.

## Process/security notes

- **A real DB password was committed in an earlier version of this file**
  (commit 9c8c0ec). Redacted now. It remains in Git history, so it is treated as
  compromised and must be rotated (TODO: confirm rotated). `.env` itself is gitignored.
  *Lesson: never write real credentials in docs, logs, or chat.*
- **A commit (`beeb4ad`) was titled "Add DEVLOG.md" but the file itself was
  never actually created** — the evidence engine files got committed under
  that message, but DEVLOG.md was missing until a later commit fixed it.

---

*This file is updated as new issues are found and fixed. Add new entries at
the top of the relevant section, dated, as the project continues.*