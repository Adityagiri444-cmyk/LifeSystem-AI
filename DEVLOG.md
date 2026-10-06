# LifeSystem — Development Log

A running record of mistakes, bugs, gaps, and fixes, kept from Week 4 onward.
The goal isn't to hide these — it's to prove they were understood and resolved,
and to have a real reference for what broke and why.

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
- **Password containing `@` broke `DATABASE_URL`**: `Aditya@67` has an `@`
  inside it, colliding with the `user:pass@host` URL syntax. Fixed by
  URL-encoding it as `Aditya%4067`.

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
- **`PUT /quests/{id}` returned a raw `500`, not a clean `400`/`422`** on
  invalid input (bad `domain_id`/`difficulty`). **Known gap, deferred to
  Week 30 (testing/security/input validation).**

## Known, intentionally deferred gaps

- **Quest `prerequisites` are stored but not enforced** at completion time —
  needs real completion-history tracking, not just "last 24h."
- **Quest completion's 24h "already completed" check doubles as a
  pseudo-prerequisite check**, which isn't actually correct.

## Process/security notes

- Real secrets (DB password, JWT signing key) were typed into chat during
  setup but never committed (`.env` is gitignored throughout). Worth
  breaking the habit before deployment.
- **A commit (`beeb4ad`) was titled "Add DEVLOG.md" but the file itself was
  never actually created** — the evidence engine files got committed under
  that message, but DEVLOG.md was missing until this entry fixed it.

---

*This file is updated as new issues are found and fixed. Add new entries at
the top of the relevant section, dated, as the project continues.*