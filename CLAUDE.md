# CLAUDE.md — obe (Outcome-Based Education / CO-PO attainment)

Frappe app that turns student marks into **Course Outcome (CO) → Programme
Outcome (PO) attainment** for Outcome-Based Education (OBE) reporting. Kept
**self-contained** (no ERPNext/Education dependency) so it installs on any bench
and is framework-agnostic. Frappe is the only runtime dependency. AGPL-3.0.

Abbreviations: OBE = Outcome-Based Education · CO = Course Outcome · PO =
Programme Outcome · PSO = Programme-Specific Outcome · CIE = Continuous Internal
Evaluation · SEE = Semester-End Examination.

## Where the logic lives

- **`obe/attainment.py`** — the whole attainment engine as **pure functions, no
  Frappe imports**. This is the core computation; keep it Frappe-free so it stays
  unit-testable and treat it as the source of truth.
- **`obe/tests/test_attainment.py`** — hand-worked tests. Run:
  `python3 -m pytest obe/tests/test_attainment.py -q`. **Change the math → update
  these first.**
- **`obe/obe/doctype/attainment_run/attainment_run.py`** — the ONLY hand-written
  controller: gathers course/marks/survey data, calls the engine, writes the
  CO/PO result tables. All other controllers are empty stubs.
- **`obe/api.py`** — CSV import (wide format) + template helpers.
- **`scripts/seed_demo.py`** — creates the OBE workspace + a worked demo (run via
  `bench console`).

## DocTypes are generated, not hand-written

`scripts/gen_doctypes.py` holds a compact `SPECS` dict and emits the verbose
Frappe JSON + controller stub + `__init__.py` for all doctypes.
**To change the schema: edit SPECS, then `python3 scripts/gen_doctypes.py`.**
The generator won't clobber a controller that already has real logic (guarded).

Parents: OBE Program, Program Outcome, OBE Course, Assessment, OBE Student,
Course Survey, Attainment Run. The rest are child tables.

## The flow

Program → POs (12 seeded via `fixtures/program_outcome.json`; replace with your
framework's set) + PSOs → OBE Course → Course Outcomes → CO-PO matrix →
Assessment (tag each Q# → CO) → import marks + survey CSV → Attainment Run
"Compute" → PO attainment + gap → export.

## Compute model (all weights/rubric are settings on OBE Program)

direct = rubric(% students ≥ threshold), CIE/SEE blended · indirect = survey mean
· final = 0.8·direct + 0.2·indirect · PO = Σ(CO·strength)/Σ(strength) · gap =
attained − target (negative = shortfall). Note: a CIE-only course reads low
because SEE=0 halves the blend — set `w_see=0` until SEE marks exist.

## Deploy

Not stock frappe_docker-friendly: apps are baked into the image, so deployment
builds a **custom image** (erpnext + obe) via `images/custom/Containerfile` with
`apps.json` passed as a **BuildKit secret**, and runs obe as its **own isolated
frappe_docker project** (own DB/Redis, port 8150). See `naac-software/obe.yml`
(`make obe`). Needs `docker-buildx` (BuildKit). The repo must be named `obe` so
`bench` resolves the module.

## Gotchas

- Keep `attainment.py` import-free of frappe, or the tests can't run standalone.
- Regenerate doctypes via the script; don't hand-edit the JSON.
- `bench console` runs stdin as an IPython REPL and top-level names aren't visible
  inside `def`s under `exec` — keep seed/migration scripts at top level (loops,
  no functions).
- The seeded PO set and any report format are framework-specific — validate them
  against your own requirements before a formal submission. That's the v2 work.
