"""CSV import + template helpers. Wide CSV in, normalised child rows out."""
import csv
import io

import frappe


@frappe.whitelist()
def marks_template(assessment):
    """Header row for wide-format marks: roll_no,name,<q_no>,..."""
    adoc = frappe.get_doc("Assessment", assessment)
    return "roll_no,name," + ",".join(q.q_no for q in adoc.questions) + "\n"


@frappe.whitelist()
def import_marks(assessment, csv_text):
    """Wide CSV (roll_no,name,q1,q2,...) -> Assessment Mark rows (roll_no,q_no,marks).

    Replaces existing marks on the assessment. Only columns matching defined
    question numbers are imported; blanks skipped.
    """
    adoc = frappe.get_doc("Assessment", assessment)
    valid_q = {q.q_no for q in adoc.questions}
    if not valid_q:
        frappe.throw("Define the assessment's questions (Q# -> CO) before importing marks.")
    reader = csv.DictReader(io.StringIO((csv_text or "").strip()))
    adoc.set("marks", [])
    added = 0
    for row in reader:
        roll = (row.get("roll_no") or "").strip()
        if not roll:
            continue
        for qno in valid_q:
            val = row.get(qno)
            if val not in (None, ""):
                adoc.append("marks", {"roll_no": roll, "q_no": qno, "marks": float(val)})
                added += 1
    adoc.save()
    return {"rows": added}


@frappe.whitelist()
def survey_template(course):
    """Header row for wide-format survey: roll_no,<CO>,..."""
    cos = [o.co_code for o in frappe.get_doc("OBE Course", course).outcomes]
    return "roll_no," + ",".join(cos) + "\n"


@frappe.whitelist()
def import_survey(survey, csv_text):
    """Wide CSV (roll_no,CO1,CO2,...) -> Survey Rating rows (roll_no,co_code,rating)."""
    sdoc = frappe.get_doc("Course Survey", survey)
    cos = {o.co_code for o in frappe.get_doc("OBE Course", sdoc.course).outcomes}
    reader = csv.DictReader(io.StringIO((csv_text or "").strip()))
    sdoc.set("ratings", [])
    added = 0
    for row in reader:
        roll = (row.get("roll_no") or "").strip()
        for co in cos:
            val = row.get(co)
            if val not in (None, ""):
                sdoc.append("ratings", {"roll_no": roll, "co_code": co, "rating": float(val)})
                added += 1
    sdoc.save()
    return {"rows": added}
