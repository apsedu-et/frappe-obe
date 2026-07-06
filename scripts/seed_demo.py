import frappe, json

# ---------- Workspace (landing page) ----------
if frappe.db.exists("Workspace", "OBE"):
    frappe.delete_doc("Workspace", "OBE", force=True)
ws = frappe.new_doc("Workspace")
ws.title = "OBE"; ws.label = "OBE"; ws.public = 1; ws.module = "OBE"; ws.icon = "education"
cards = [
    ("Setup", ["OBE Program", "Program Outcome", "OBE Course"]),
    ("Assessment & Data", ["Assessment", "Course Survey", "OBE Student"]),
    ("Results", ["Attainment Run"]),
]
content = [{"type": "header", "data": {"text": "OBE / CO-PO Attainment", "col": 12}}]
for name, links in cards:
    ws.append("links", {"type": "Card Break", "label": name})
    for lt in links:
        ws.append("links", {"type": "Link", "label": lt, "link_type": "DocType", "link_to": lt})
    content.append({"type": "card", "data": {"card_name": name, "col": 4}})
ws.content = json.dumps(content)
ws.insert(ignore_permissions=True)

# ---------- Clean prior demo ----------
for dt in ["Attainment Run", "Assessment", "Course Survey"]:
    for n in frappe.get_all(dt, filters={"course": "CS201"}, pluck="name"):
        frappe.delete_doc(dt, n, force=True)
for dt, n in [("OBE Course", "CS201"), ("OBE Program", "B.E. CSE (Demo)")]:
    if frappe.db.exists(dt, n):
        frappe.delete_doc(dt, n, force=True)

# ---------- Program + rubric ----------
prog = frappe.new_doc("OBE Program")
prog.program_name = "B.E. CSE (Demo)"; prog.degree = "B.E."
prog.w_direct = 0.8; prog.w_indirect = 0.2; prog.w_cie = 0.5; prog.w_see = 0.5
prog.threshold_pct = 60; prog.target_level = 2.0
for mn, lv in [(70, 3), (60, 2), (50, 1), (0, 0)]:
    prog.append("rubric", {"min_pct": mn, "level": lv})
prog.insert(ignore_permissions=True)

# ---------- Course + COs + CO-PO matrix ----------
course = frappe.new_doc("OBE Course")
course.course_code = "CS201"; course.title = "Data Structures"; course.program = prog.name; course.semester = 3
for co, st in [("CO1", "Apply linear data structures"), ("CO2", "Apply trees & graphs"), ("CO3", "Analyse algorithm complexity")]:
    course.append("outcomes", {"co_code": co, "statement": st})
for co, po, s in [("CO1", "PO1", 3), ("CO1", "PO2", 2), ("CO2", "PO2", 3), ("CO2", "PO3", 2), ("CO3", "PO3", 3), ("CO3", "PO1", 1)]:
    course.append("co_po", {"co_code": co, "po": po, "strength": s})
course.insert(ignore_permissions=True)

for title, atype, qmax, marks in [
    ("CS201 CIE-1", "CIE", 10, {"R1": (8, 7, 6), "R2": (6, 9, 5), "R3": (9, 6, 8), "R4": (5, 8, 7), "R5": (7, 5, 9)}),
    ("CS201 SEE", "SEE", 20, {"R1": (15, 14, 11), "R2": (12, 18, 10), "R3": (17, 12, 16), "R4": (10, 15, 13), "R5": (14, 11, 18)}),
]:
    a = frappe.new_doc("Assessment")
    a.title = title; a.course = course.name; a.assessment_type = atype; a.max_marks = qmax * 3
    for q, co in [("Q1", "CO1"), ("Q2", "CO2"), ("Q3", "CO3")]:
        a.append("questions", {"q_no": q, "co_code": co, "max_marks": qmax})
    for roll, m in marks.items():
        for i, q in enumerate(["Q1", "Q2", "Q3"]):
            a.append("marks", {"roll_no": roll, "q_no": q, "marks": m[i]})
    a.insert(ignore_permissions=True)

surv = frappe.new_doc("Course Survey")
surv.title = "CS201 Course-Exit Survey"; surv.course = course.name; surv.scale_max = 3
for roll, c in {"R1": (3, 2, 3), "R2": (3, 3, 3), "R3": (2, 3, 2), "R4": (3, 2, 3)}.items():
    for i, co in enumerate(["CO1", "CO2", "CO3"]):
        surv.append("ratings", {"roll_no": roll, "co_code": co, "rating": c[i]})
surv.insert(ignore_permissions=True)

run = frappe.new_doc("Attainment Run")
run.title = "CS201 Attainment (Demo)"; run.course = course.name
run.insert(ignore_permissions=True)
run.compute()
frappe.db.commit()
print("DEMO OK", run.name)
for r in run.po_results:
    print("  PO", r.po, "attain=", r.attainment, "gap=", r.gap)
