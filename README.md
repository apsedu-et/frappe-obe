# obe — Outcome-Based Education (OBE) / CO-PO Attainment

A [Frappe](https://frappeframework.com) app that turns student marks into
**Course Outcome (CO) → Programme Outcome (PO) attainment** — the outcome scores
used for Outcome-Based Education (OBE) reporting and programme quality reviews.

Abbreviations used throughout:

- **OBE** — Outcome-Based Education
- **CO** — Course Outcome (what a single course teaches; 3–6 per course)
- **PO** — Programme Outcome (a graduate attribute the whole programme targets)
- **PSO** — Programme-Specific Outcome (a PO specific to one programme)
- **CIE** — Continuous Internal Evaluation (internal/in-semester assessments)
- **SEE** — Semester-End Examination (the final/external exam)

It is deliberately **self-contained**: it defines its own programme / course /
student / marks model and does **not** depend on ERPNext or the Frappe Education
app, so it installs on any bench and is reusable by any institution. Frappe is the
only runtime dependency. Licensed **AGPL-3.0**.

- Repo: `apsedu-et/obe` — the repo name must stay `obe` (Frappe derives the app
  module name from the repo directory).
- Live instance: `https://obe-eng.apset.co.in` (deployed from `naac-software/obe.yml`).

---

## Concepts

- **PO / PSO** — the graduate attributes every student should have by graduation.
  A **default set of 12 Programme Outcomes** (the common engineering
  graduate-attribute set) is seeded on install; **replace or extend it with the
  outcomes your own framework defines**, and add PSOs per programme.
- **CO** — the outcomes of an individual course.
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
python3 -m pytest obe/tests/test_attainment.py -q      # the core computation
```

Levels are on a **0–3** scale. Everything below is configurable on the
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
report/print. Producing report templates that match a specific review body's
format is left to you (see Roadmap).

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
  bringing anything up (a mis-built image once took the shared stack offline).
- Isolated project means a bad OBE build can't touch other apps' stacks.

### Plain bench (dev / standalone site)

```bash
bench get-app https://github.com/apsedu-et/obe
bench new-site obe.localhost --install-app obe
```

### Workspace + demo

The **OBE workspace** and a **worked demo** (a programme, a course with COs + a
CO-PO matrix, CIE/SEE marks, a survey, and a computed Attainment Run) are seeded
by `scripts/seed_demo.py`, run via `bench console`. They live in the site DB, so
they survive restarts but not a full site reinstall — baking the workspace into
the app as a fixture is a small follow-up.

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
- Printable outcome-report templates matching your review body's format.
- Make the seeded PO set configurable per framework; ship as an editable fixture.
- Bake the workspace + fixtures into the app so a fresh install is turnkey.

## Caveat

v1 **computes** attainment correctly (unit-tested) and exports clean tables, but
report **formats** and the exact outcome set differ by framework and change over
time. Validate the output format and the PO set against your own requirements
before relying on it for a formal submission.
