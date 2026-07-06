import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from obe.attainment import (
    co_direct_from_marks, blend, co_indirect_from_survey, co_final,
    po_attainment, gaps,
)

DEFAULT_RUBRIC = [(70, 3), (60, 2), (50, 1), (0, 0)]


def _avg(xs):
    return sum(xs) / len(xs) if xs else 0.0


class AttainmentRun(Document):
    @frappe.whitelist()
    def compute(self):
        """Pull all data for the course, run the attainment engine, store results.

        All math lives in obe.attainment (pure + unit-tested); this method only
        gathers inputs and writes the CO/PO result tables.
        """
        course = frappe.get_doc("OBE Course", self.course)
        program = frappe.get_doc("OBE Program", course.program)
        rubric = [(b.min_pct, b.level) for b in program.rubric] or DEFAULT_RUBRIC
        threshold = program.threshold_pct or 60.0
        co_codes = [o.co_code for o in course.outcomes]

        # --- direct: per assessment, marks -> per-CO level, grouped by CIE/SEE ---
        by_type = {}  # {assessment_type: {co: [levels]}}
        for a in frappe.get_all("Assessment", filters={"course": self.course}, pluck="name"):
            adoc = frappe.get_doc("Assessment", a)
            q_co = {q.q_no: q.co_code for q in adoc.questions}
            co_max, co_student = {}, {}
            for q in adoc.questions:
                co_max[q.co_code] = co_max.get(q.co_code, 0.0) + (q.max_marks or 0.0)
            for m in adoc.marks:
                co = q_co.get(m.q_no)
                if not co:
                    continue
                co_student.setdefault(co, {})
                co_student[co][m.roll_no] = co_student[co].get(m.roll_no, 0.0) + (m.marks or 0.0)
            for co, per_student in co_student.items():
                lvl = co_direct_from_marks(list(per_student.values()), co_max.get(co, 0.0), threshold, rubric)
                by_type.setdefault(adoc.assessment_type, {}).setdefault(co, []).append(lvl)

        cie = {co: _avg(v) for co, v in by_type.get("CIE", {}).items()}
        see = {co: _avg(v) for co, v in by_type.get("SEE", {}).items()}
        for co, v in by_type.get("Assignment", {}).items():  # fold assignments into CIE
            cie[co] = _avg([cie[co], _avg(v)]) if co in cie else _avg(v)

        direct = {co: blend(cie.get(co, 0.0), see.get(co, 0.0), program.w_cie, program.w_see) for co in co_codes}

        # --- indirect: course-exit survey self-ratings ---
        co_ratings, smax = {}, 3.0
        for s in frappe.get_all("Course Survey", filters={"course": self.course}, pluck="name"):
            sdoc = frappe.get_doc("Course Survey", s)
            smax = sdoc.scale_max or 3.0
            for r in sdoc.ratings:
                co_ratings.setdefault(r.co_code, []).append(r.rating)
        indirect = {co: co_indirect_from_survey(co_ratings.get(co, []), smax) for co in co_codes}

        # --- final CO, then PO rollup + gap ---
        final = {co: co_final(direct.get(co, 0.0), indirect.get(co, 0.0), program.w_direct, program.w_indirect) for co in co_codes}
        co_po = {(m.co_code, m.po): m.strength for m in course.co_po}
        po_levels = po_attainment(final, co_po)
        g = gaps(po_levels, program.target_level)

        self.set("co_results", [])
        for co in co_codes:
            self.append("co_results", {"co_code": co, "direct": round(direct.get(co, 0), 3),
                                       "indirect": round(indirect.get(co, 0), 3), "final": round(final.get(co, 0), 3)})
        self.set("po_results", [])
        for po in sorted(po_levels):
            self.append("po_results", {"po": po, "attainment": round(po_levels[po], 3),
                                       "target": program.target_level, "gap": g[po]})
        self.computed_on = now_datetime()
        self.save()
        frappe.msgprint(f"Computed {len(self.co_results)} COs and {len(self.po_results)} POs.")
        return True
