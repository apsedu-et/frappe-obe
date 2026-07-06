"""OBE / CO-PO attainment engine — PURE functions, no Frappe imports.

Kept dependency-free on purpose: this is the accreditation-critical math, so it
must be unit-testable in isolation (see obe/tests/test_attainment.py). The Frappe
DocType controllers call these; they hold no logic of their own.

Levels are on NBA's 0–3 scale throughout.
"""
from __future__ import annotations


def pct_to_level(pct: float, rubric: list[tuple[float, float]]) -> float:
    """Map a percentage to an attainment level via a rubric.

    rubric: list of (min_pct, level), e.g. [(70,3),(60,2),(50,1),(0,0)].
    Returns the level of the highest band whose min_pct <= pct.
    """
    for min_pct, level in sorted(rubric, key=lambda r: -r[0]):
        if pct >= min_pct:
            return float(level)
    return 0.0


def co_direct_from_marks(
    student_co_marks: list[float],
    co_max: float,
    threshold_pct: float,
    rubric: list[tuple[float, float]],
) -> float:
    """Direct attainment of ONE course outcome from one assessment.

    student_co_marks: each student's total marks on the questions tagged to this CO.
    co_max: max marks attainable for this CO in the assessment.
    threshold_pct: a student "attains" the CO if they score >= this % of co_max.
    Returns a level: (% of students who attained) mapped through the rubric.
    """
    if not student_co_marks or co_max <= 0:
        return 0.0
    attained = sum(1 for m in student_co_marks if (m / co_max) * 100 >= threshold_pct)
    pct_students = attained / len(student_co_marks) * 100
    return pct_to_level(pct_students, rubric)


def blend(cie_level: float, see_level: float, w_cie: float, w_see: float) -> float:
    """Blend internal (CIE) and semester-end (SEE) direct levels by weight."""
    total = w_cie + w_see
    if total == 0:
        return 0.0
    return (w_cie * cie_level + w_see * see_level) / total


def co_indirect_from_survey(ratings: list[float], scale_max: float = 3.0) -> float:
    """Indirect attainment of a CO from course-exit self-ratings.

    ratings on a 0..scale_max scale; returned normalised to the 0..3 level scale.
    """
    if not ratings:
        return 0.0
    return (sum(ratings) / len(ratings)) / scale_max * 3.0


def co_final(direct: float, indirect: float, w_direct: float = 0.8, w_indirect: float = 0.2) -> float:
    """Final CO attainment = weighted blend of direct and indirect (default 80/20)."""
    total = w_direct + w_indirect
    if total == 0:
        return 0.0
    return (w_direct * direct + w_indirect * indirect) / total


def po_attainment(co_levels: dict[str, float], co_po_map: dict[tuple[str, str], float]) -> dict[str, float]:
    """Roll CO attainment up to PO attainment through the CO-PO matrix.

    co_levels: {co_code: final_level}.
    co_po_map: {(co_code, po_code): strength(1..3)}; strength 0 = not mapped.
    PO attainment = sum(co_level * strength) / sum(strength) over all mapped COs.
    """
    num: dict[str, float] = {}
    den: dict[str, float] = {}
    for (co, po), strength in co_po_map.items():
        if strength <= 0 or co not in co_levels:
            continue
        num[po] = num.get(po, 0.0) + co_levels[co] * strength
        den[po] = den.get(po, 0.0) + strength
    return {po: num[po] / den[po] for po in num if den[po] > 0}


def gaps(po_levels: dict[str, float], target: float) -> dict[str, float]:
    """Per-PO headroom = attained - target. Negative => shortfall (below target)."""
    return {po: round(lvl - target, 3) for po, lvl in po_levels.items()}
