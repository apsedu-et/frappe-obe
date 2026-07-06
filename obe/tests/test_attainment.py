"""Hand-worked tests for the attainment engine — the accreditation-critical math.
Runs without Frappe: `python -m pytest obe/tests/test_attainment.py`
"""
from obe.attainment import (
    pct_to_level, co_direct_from_marks, blend, co_indirect_from_survey,
    co_final, po_attainment, gaps,
)

RUBRIC = [(70, 3), (60, 2), (50, 1), (0, 0)]  # % students attaining -> level


def test_pct_to_level():
    assert pct_to_level(75, RUBRIC) == 3
    assert pct_to_level(70, RUBRIC) == 3  # boundary inclusive
    assert pct_to_level(65, RUBRIC) == 2
    assert pct_to_level(55, RUBRIC) == 1
    assert pct_to_level(40, RUBRIC) == 0


def test_co_direct_from_marks():
    # 4 students, CO max 10, threshold 60% => attain if >=6.
    # scores 8,6,5,9 -> 3 of 4 attain -> 75% students -> level 3.
    assert co_direct_from_marks([8, 6, 5, 9], 10, 60, RUBRIC) == 3
    # 2 of 4 attain -> 50% -> level 1
    assert co_direct_from_marks([8, 6, 2, 3], 10, 60, RUBRIC) == 1
    assert co_direct_from_marks([], 10, 60, RUBRIC) == 0  # no data


def test_blend_cie_see():
    # CIE level 3, SEE level 2, weights 30/70 -> (0.3*3 + 0.7*2)/1 = 2.3
    assert blend(3, 2, 0.3, 0.7) == 2.3


def test_co_indirect_from_survey():
    assert co_indirect_from_survey([3, 3, 3]) == 3.0
    assert co_indirect_from_survey([0, 0, 0]) == 0.0
    assert co_indirect_from_survey([1, 2, 1, 2]) == 1.5  # avg 1.5 on /3 -> 1.5
    assert co_indirect_from_survey([]) == 0.0


def test_co_final():
    # direct 3, indirect 1.5, 80/20 -> 0.8*3 + 0.2*1.5 = 2.7
    assert co_final(3, 1.5) == 2.7


def test_po_attainment_weighted_by_strength():
    co_levels = {"CO1": 3.0, "CO2": 2.0}
    m = {("CO1", "PO1"): 3, ("CO2", "PO1"): 1, ("CO1", "PO2"): 2}
    r = po_attainment(co_levels, m)
    assert r["PO1"] == (3 * 3 + 2 * 1) / (3 + 1)   # 11/4 = 2.75
    assert r["PO2"] == 3.0                          # only CO1 maps
    # a CO with no marks/level is skipped
    assert po_attainment({}, m) == {}


def test_gaps_sign():
    g = gaps({"PO1": 2.75, "PO2": 1.5}, target=2.0)
    assert g["PO1"] == 0.75    # exceeds target
    assert g["PO2"] == -0.5    # shortfall (below target)
