# obe — OBE / CO-PO Attainment (Frappe app)

Turns student marks into **Course-Outcome → Program-Outcome attainment** for NBA
accreditation. Self-contained Frappe app (no ERPNext/Education dependency) so it
installs on any bench and is reusable by any college. To be open-sourced (AGPL-3.0).

## The flow

```
1. SETUP    OBE Program → (11/12 POs seeded) + PSOs → OBE Courses → Course Outcomes → CO-PO matrix
2. DESIGN   Assessment (CIE/SEE): tag each question Q# → CO with max marks
3. DATA IN  Import marks CSV (roll_no,name,q1,q2,…) + course-exit survey CSV (roll_no,CO1,…)
4. TARGETS  Set the attainment rubric (% students ≥ threshold → level 0-3) on the Program
5. COMPUTE  Attainment Run → "Compute attainment"
6. ANALYSE  PO attainment vs target, per-PO gap (negative = shortfall)
7. REPORT   Export the run's CO/PO tables (print / Excel)
```

## Attainment math

All in `obe/attainment.py` — **pure functions, no Frappe imports, unit-tested**
(`obe/tests/test_attainment.py`). Direct (marks vs threshold → rubric level,
CIE/SEE blended), indirect (survey mean), final = 0.8·direct + 0.2·indirect
(configurable), PO = Σ(CO·strength)/Σ(strength) through the CO-PO matrix.

```bash
python3 -m pytest obe/tests/test_attainment.py -q     # the money path
```

## Data model

DocTypes are generated from a compact spec: edit `scripts/gen_doctypes.py`, run
`python3 scripts/gen_doctypes.py`. Parents: OBE Program, Program Outcome, OBE
Course, Assessment, OBE Student, Course Survey, Attainment Run (+ child tables).
The Attainment Run controller (`.../attainment_run.py`) is the only hand-written
one — it gathers inputs and calls the engine.

## Install (on a Frappe bench)

```bash
bench get-app https://github.com/apsedu-et/frappe-obe
bench new-site obe-eng.apset.co.in
bench --site obe-eng.apset.co.in install-app obe
```
Deployed here via `naac-software/obe.yml` (`make obe`) — see that repo.

## Caveat

v1 computes attainment correctly and exports clean tables, but the **exact NBA
SAR table format (GAPC v4.0)** must be validated 1:1 against the official manual
before submission, and the seeded PO set/count should be confirmed against the
current manual. That validation is v2.
