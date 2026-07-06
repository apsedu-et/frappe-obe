# CLAUDE.md — obe (OBE / CO-PO attainment)

Frappe app that turns student marks into **CO → PO attainment** for NBA. Kept
**self-contained** (no ERPNext/Education dependency) so it installs on any bench
and can be open-sourced (AGPL-3.0). Frappe is the only runtime dependency.

## Where the logic lives

- **`obe/attainment.py`** — the whole attainment engine as **pure functions, no
  Frappe imports**. This is the accreditation-critical math; treat it as the
  source of truth and keep it Frappe-free so it stays unit-testable.
- **`obe/tests/test_attainment.py`** — hand-worked tests. Run:
  `python3 -m pytest obe/tests/test_attainment.py -q`. **Change the math → update
  these first.**
- **`obe/obe/doctype/attainment_run/attainment_run.py`** — the ONLY hand-written
  controller: gathers course/marks/survey data, calls the engine, writes the
  CO/PO result tables. All other controllers are empty stubs.
- **`obe/api.py`** — CSV import (wide format) + template helpers.

## DocTypes are generated, not hand-written

`scripts/gen_doctypes.py` holds a compact `SPECS` dict and emits the verbose
Frappe JSON + controller stub + `__init__.py` for all 15 doctypes.
**To change the schema: edit SPECS, then `python3 scripts/gen_doctypes.py`.**
The generator won't clobber a controller that already has real logic (guarded).

Parents: OBE Program, Program Outcome, OBE Course, Assessment, OBE Student,
Course Survey, Attainment Run. The rest are child tables.

## The flow

Program → POs (12 seeded via `fixtures/program_outcome.json`) + PSOs → OBE Course
→ Course Outcomes → CO-PO matrix → Assessment (tag each Q# → CO) → import marks +
survey CSV → Attainment Run "Compute" → PO attainment + gap → export.

## Compute model (all weights/rubric are settings on OBE Program)

direct = rubric(% students ≥ threshold), CIE/SEE blended · indirect = survey mean
· final = 0.8·direct + 0.2·indirect · PO = Σ(CO·strength)/Σ(strength) · gap =
attained − target (negative = shortfall).

## Deploy

Not stock frappe_docker-friendly: apps are baked into the image, so deployment
builds a **custom image** (erpnext + obe) and runs obe as a **dedicated site on
the ERPNext bench** (host-routed, same frontend). See `naac-software/obe.yml`
(`make obe`). The build needs **BuildKit** (`DOCKER_BUILDKIT=1`) — the layered
Containerfile uses `--mount`.

## Gotchas

- Keep `attainment.py` import-free of frappe, or the tests can't run standalone.
- Regenerate doctypes via the script; don't hand-edit the JSON.
- v1 computes correctly but the **exact NBA SAR table format (GAPC v4.0)** and the
  **PO set/count** must be validated against the current official manual before
  submission — that's the v2 task, not done here.
