#!/usr/bin/env python3
"""Generate Frappe DocType folders (json + controller + __init__) from a compact
spec. Run from repo root:  python3 scripts/gen_doctypes.py

Hand-writing Frappe's verbose DocType JSON is error-prone; this keeps the schema
declarative in one place. Re-run after editing SPECS to regenerate.
"""
import json
import os

TS = "2026-01-01 00:00:00"
MODULE = "OBE"
ROOT = os.path.join(os.path.dirname(__file__), "..", "obe", "obe", "doctype")


def f(fn, ft, label=None, options=None, reqd=0, unique=0, lv=0, default=None, ro=0):
    d = {"fieldname": fn, "fieldtype": ft, "label": label or fn.replace("_", " ").title()}
    if options:
        d["options"] = options
    if reqd:
        d["reqd"] = 1
    if unique:
        d["unique"] = 1
    if lv:
        d["in_list_view"] = 1
    if default is not None:
        d["default"] = default
    if ro:
        d["read_only"] = 1
    return d


# name -> dict(istable, autoname, title_field, fields=[...])
SPECS = {
    "Program Outcome": dict(autoname="field:code", fields=[
        f("code", "Data", reqd=1, unique=1, lv=1),
        f("po_type", "Select", "Type", options="PO\nPSO", default="PO", lv=1),
        f("statement", "Small Text", lv=1),
    ]),
    "Rubric Band": dict(istable=1, fields=[
        f("min_pct", "Float", "Min % students", reqd=1, lv=1),
        f("level", "Float", reqd=1, lv=1),
    ]),
    "OBE Program": dict(autoname="field:program_name", title_field="program_name", fields=[
        f("program_name", "Data", reqd=1, unique=1, lv=1),
        f("degree", "Data", lv=1),
        f("w_direct", "Float", "Direct weight", default="0.8"),
        f("w_indirect", "Float", "Indirect weight", default="0.2"),
        f("w_cie", "Float", "CIE weight", default="0.5"),
        f("w_see", "Float", "SEE weight", default="0.5"),
        f("threshold_pct", "Float", "Attainment threshold %", default="60"),
        f("target_level", "Float", default="2.0"),
        f("rubric", "Table", "Attainment rubric", options="Rubric Band"),
    ]),
    "Course Outcome": dict(istable=1, fields=[
        f("co_code", "Data", "CO", reqd=1, lv=1),
        f("statement", "Small Text", lv=1),
    ]),
    "CO PO Map": dict(istable=1, fields=[
        f("co_code", "Data", "CO", reqd=1, lv=1),
        f("po", "Link", "PO", options="Program Outcome", reqd=1, lv=1),
        f("strength", "Int", "Strength (0-3)", default="0", lv=1),
    ]),
    "OBE Course": dict(autoname="field:course_code", title_field="title", fields=[
        f("course_code", "Data", reqd=1, unique=1, lv=1),
        f("title", "Data", lv=1),
        f("program", "Link", options="OBE Program", reqd=1, lv=1),
        f("semester", "Int"),
        f("outcomes", "Table", "Course Outcomes", options="Course Outcome"),
        f("co_po", "Table", "CO-PO Matrix", options="CO PO Map"),
    ]),
    "Assessment Question": dict(istable=1, fields=[
        f("q_no", "Data", "Q#", reqd=1, lv=1),
        f("co_code", "Data", "CO", reqd=1, lv=1),
        f("max_marks", "Float", reqd=1, lv=1),
    ]),
    "Assessment Mark": dict(istable=1, fields=[
        f("roll_no", "Data", reqd=1, lv=1),
        f("q_no", "Data", "Q#", reqd=1, lv=1),
        f("marks", "Float", default="0", lv=1),
    ]),
    "Assessment": dict(autoname="hash", title_field="title", fields=[
        f("title", "Data", reqd=1, lv=1),
        f("course", "Link", options="OBE Course", reqd=1, lv=1),
        f("assessment_type", "Select", "Type", options="CIE\nSEE\nAssignment", default="CIE", lv=1),
        f("max_marks", "Float"),
        f("questions", "Table", "Questions (Q# -> CO)", options="Assessment Question"),
        f("marks", "Table", "Marks", options="Assessment Mark"),
    ]),
    "OBE Student": dict(autoname="field:roll_no", title_field="student_name", fields=[
        f("roll_no", "Data", reqd=1, unique=1, lv=1),
        f("student_name", "Data", lv=1),
        f("program", "Link", options="OBE Program", lv=1),
        f("batch", "Data"),
    ]),
    "Survey Rating": dict(istable=1, fields=[
        f("roll_no", "Data", lv=1),
        f("co_code", "Data", "CO", reqd=1, lv=1),
        f("rating", "Float", reqd=1, lv=1),
    ]),
    "Course Survey": dict(autoname="hash", title_field="title", fields=[
        f("title", "Data", reqd=1, lv=1),
        f("course", "Link", options="OBE Course", reqd=1, lv=1),
        f("scale_max", "Float", "Rating scale max", default="3"),
        f("ratings", "Table", options="Survey Rating"),
    ]),
    "CO Attainment Row": dict(istable=1, fields=[
        f("co_code", "Data", "CO", lv=1),
        f("direct", "Float", lv=1),
        f("indirect", "Float", lv=1),
        f("final", "Float", lv=1),
    ]),
    "PO Attainment Row": dict(istable=1, fields=[
        f("po", "Data", lv=1),
        f("attainment", "Float", lv=1),
        f("target", "Float", lv=1),
        f("gap", "Float", lv=1),
    ]),
    "Attainment Run": dict(autoname="hash", title_field="title", fields=[
        f("title", "Data", reqd=1, lv=1),
        f("course", "Link", options="OBE Course", reqd=1, lv=1),
        f("computed_on", "Datetime", ro=1),
        f("co_results", "Table", "CO Attainment", options="CO Attainment Row", ro=1),
        f("po_results", "Table", "PO Attainment", options="PO Attainment Row", ro=1),
    ]),
}

PERM = {"create": 1, "delete": 1, "email": 1, "export": 1, "print": 1, "read": 1,
        "report": 1, "role": "System Manager", "share": 1, "write": 1}


def snake(name):
    return name.lower().replace(" ", "_")


def klass(name):
    return name.replace(" ", "")


def main():
    for name, spec in SPECS.items():
        fields = spec["fields"]
        doc = {
            "actions": [], "creation": TS, "doctype": "DocType", "engine": "InnoDB",
            "field_order": [x["fieldname"] for x in fields], "fields": fields,
            "index_web_pages_for_search": 1, "links": [], "modified": TS,
            "modified_by": "Administrator", "module": MODULE, "name": name,
            "owner": "Administrator", "permissions": [] if spec.get("istable") else [PERM],
            "sort_field": "modified", "sort_order": "DESC", "states": [],
        }
        if spec.get("istable"):
            doc["istable"] = 1
        else:
            doc["autoname"] = spec.get("autoname", "hash")
        if spec.get("title_field"):
            doc["title_field"] = spec["title_field"]

        d = os.path.join(ROOT, snake(name))
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, snake(name) + ".json"), "w") as fh:
            json.dump(doc, fh, indent=1)
            fh.write("\n")
        open(os.path.join(d, "__init__.py"), "w").close()
        py = os.path.join(d, snake(name) + ".py")
        if not os.path.exists(py):  # don't clobber controllers with real logic
            with open(py, "w") as fh:
                fh.write("import frappe  # noqa: F401\n")
                fh.write("from frappe.model.document import Document\n\n\n")
                fh.write(f"class {klass(name)}(Document):\n    pass\n")
    open(os.path.join(ROOT, "__init__.py"), "w").close()
    print(f"generated {len(SPECS)} doctypes under {os.path.relpath(ROOT)}")


if __name__ == "__main__":
    main()
