# obe — OBE / CO-PO Attainment

A [Frappe](https://frappeframework.com) app that turns student marks into
**Course-Outcome (CO) → Program-Outcome (PO) attainment** — the outcome numbers
NBA (and NAAC Criterion II) score an engineering programme on.

It is deliberately **self-contained**: it defines its own Program/Course/Student/
marks model and does **not** depend on ERPNext or the Frappe Education app, so it
installs on any bench and is reusable by any college. Frappe is the only runtime
dependency. Licensed **AGPL-3.0**.

- Repo: `apsedu-et/obe` — the repo name must stay `obe` (Frappe derives the app
  module name from the repo directory).
- Live instance: `https://obe-eng.apset.co.in` (deployed from `naac-software/obe.yml`).

---

## Concepts (for the non-NBA reader)

- **PO / PSO** — Programme Outcomes: the graduate attributes every student should
  have by graduation. The 12 standard NBA/Washington-Accord POs are seeded on
  install; PSOs (programme-specific) are added per programme.
- **CO** — Course Outcomes: 3–6 per course, what a specific course teaches.
- **CO-PO matrix** — how strongly each CO contributes to each PO (strength 1–3).
- **Attainment** — a 0–3 score of how well an outcome was actually achieved,
  computed from marks (**direct**) and course-exit surveys (**indirect**).

---

## Workflow

```
1. SETUP     OBE Program → (12 POs seeded) + PSOs → OBE Course → Course Outcomes → CO-PO matrix
2. DESIGN    Assessment (CIE / SEE): tag each question Q# → CO with its max marks
3. DATA IN   Import marks CSV (roll_no,name,q1,q2,…) + course-exit survey CSV (roll_no,CO1,…)
4. TARGETS   Set the attainment rubric (% students ≥ threshold → level 0-3) on the Program
5. COMPUTE   Attainment Run → "Compute attainment"
6. ANALYSE   PO attainment vs target; per-PO gap (negative = shortfall)
7. REPORT    Export the run's CO/PO tables (print / Excel)
```

In the UI, everything hangs off the **OBE workspace** (`/app/obe`).

---

## Data model

DocTypes are **generated from a compact spec** — edit `SPECS` in
`scripts/gen_doctypes.py` and run `python3 scripts/gen_doctypes.py` to regenerate
the JSON + controller stubs + `__init__.py`. Never hand-edit the JSON.

| DocType | Kind | Purpose |
|---|---|---|
| **OBE Program** | parent | Programme + attainment config (weights, threshold, target) + rubric child |
| **Rubric Band** | child | `% students ≥ threshold → level` rows |
| **Program Outcome** | parent | PO/PSO (12 POs seeded via `fixtures/program_outcome.json`) |
| **OBE Course** | parent | Course; holds Course Outcomes + CO-PO matrix children |
| **Course Outcome** | child | CO code + statement |
| **CO PO Map** | child | (CO, PO, strength 0–3) |
| **Assessment** | parent | CIE/SEE/Assignment; holds Question + Mark children |
| **Assessment Question** | child | Q# → CO, max marks |
| **Assessment Mark** | child | (roll_no, Q#, marks) |
| **OBE Student** | parent | roll_no, name, programme (optional; marks key on roll_no) |
| **Course Survey** | parent | course-exit survey; holds rating children + `scale_max` |
| **Survey Rating** | child | (roll_no, CO, rating) |
| **Attainment Run** | parent | one compute batch; holds result children + `computed_on` |
| **CO Attainment Row** / **PO Attainment Row** | child | computed results |

Only **`attainment_run.py`** has real logic; it gathers a course's data and calls
the engine. Every other controller is an empty `Document` subclass.

---

## Attainment math

All math lives in **`obe/attainment.py`** — pure functions, **no Frappe imports**,
so it is unit-tested in isolation:

```bash
python3 -m pytest obe/tests/test_attainment.py -q      # the accreditation-critical path
```

Levels are on the NBA **0–3** scale. Everything below is configurable on the
**OBE Program** (defaults shown):

1. **Direct, per CO, per assessment** — a student *attains* a CO if they score
   ≥ `threshold_pct` (60%) of that CO's marks in the assessment. The **% of
   students** who attained is mapped to a level via the **rubric**
   (e.g. `≥70→3, ≥60→2, ≥50→1, else 0`).
2. **Aggregate by exam type** — average the per-assessment levels within each type
   (CIE, SEE), then **blend**: `direct = (w_cie·CIE + w_see·SEE)/(w_cie+w_see)`
   (defaults `0.5/0.5`). Assignments fold into CIE.
3. **Indirect** — mean of the course-exit self-ratings for the CO, normalised to
   0–3.
4. **Final CO** — `(w_direct·direct + w_indirect·indirect)/(w_direct+w_indirect)`
   (defaults `0.8/0.2`).
5. **PO attainment** — `Σ(final_CO · strength) / Σ(strength)` over every (CO, PO)
   pair in the matrix.
6. **Gap** — `attained − target` per PO. **Negative = shortfall.**

> **Gotcha — a CIE-only course reads low.** With `w_see=0.5` and no SEE
> assessment yet, `SEE=0` halves the blended direct score. Either enter both CIE
> and SEE, or set the programme's `w_see=0` / `w_cie=1` while only internals exist.

---

## CSV import

Wide format in, normalised rows out (see `obe/api.py`). Each form has
**Download template** and **Import (paste CSV)** buttons.

- **Marks** (on an Assessment): `roll_no,name,q1,q2,…` — one column per Q# defined
  in that assessment. Re-importing replaces the assessment's marks.
- **Survey** (on a Course Survey): `roll_no,CO1,CO2,…` — one column per CO.

---

## Output / reports

An **Attainment Run** stores the CO table (direct / indirect / final) and the PO
table (attainment / target / gap). Print or export those via Frappe's built-in
report/print. A 1:1 official **NBA SAR** print format is a v2 item (see Roadmap).

---

## Install & deploy

### Production here — `naac-software/obe.yml` (`make obe USER=ubuntu`)

frappe_docker **bakes apps into the image**, so this app is added by building a
**custom image** and running OBE as its **own isolated compose project** (its own
DB/Redis, published on `127.0.0.1:8150`, reverse-proxied by the host nginx). Key
points that took a few iterations to get right:

- Build with **`images/custom/Containerfile`** (not `layered`), passing the app
  list as a **BuildKit secret**: `--secret id=apps_json,src=apps.json`. Needs
  **BuildKit** → install `docker-buildx`.
- `apps.json` lists erpnext + this repo; the URL's last path segment **must** be
  `obe` (= the module name), which is why the repo is named `obe`.
- The playbook **asserts the built image contains `erpnext` + `obe`** before
  bringing anything up (a mis-built image once took ERPNext offline — never again).
- Isolated project means a bad OBE build can't touch the shared ERPNext stack.

### Plain bench (dev / standalone site)

```bash
bench get-app https://github.com/apsedu-et/obe
bench new-site obe.localhost --install-app obe
```

### Workspace + demo

The **OBE workspace** and a **worked demo** (a programme, a course with COs + a
CO-PO matrix, CIE/SEE marks, a survey, and a computed Attainment Run) are seeded
by a runtime script (`scripts/seed_demo.py`, run via `bench console`). They live
in the site DB, so they survive restarts but not a full site reinstall — baking
the workspace into the app as a fixture is a small follow-up.

---

## Development

- **Schema:** edit `scripts/gen_doctypes.py` → `python3 scripts/gen_doctypes.py`.
- **Math:** edit `obe/attainment.py`; update `obe/tests/test_attainment.py` first.
- **Frappe scripting gotcha:** `bench console` runs stdin as an IPython REPL, and
  names defined at top level aren't visible inside `def`s under `exec`. For
  seed/migration scripts, keep logic at top level (loops, no functions) or pass
  everything as parameters.

---

## Roadmap (v2)

- Connectors: pull marks from Moodle / ERPNext Education, surveys from LimeSurvey.
- **NBA SAR print formats validated 1:1** against the current GAPC v4.0 manual.
- Confirm the seeded **PO set/count** against the current NBA manual (GAPC v4.0
  reportedly consolidates the 12 POs — verify before relying on the seeded set).
- Bake the workspace + fixtures into the app so a fresh install is turnkey.

## Caveat

v1 **computes** attainment correctly (unit-tested) and exports clean tables, but
the exact NBA SAR table **format** is accreditation-critical and version-drifting.
**Do not submit v1 output to NBA unchecked** — validate the format and PO set
against the current manual first.
