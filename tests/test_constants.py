# tests/test_constants.py
import math
import importlib
import pytest


def _import_constants():
    try:
        return importlib.import_module("awards.constants")
    except ModuleNotFoundError as e:
        pytest.skip(f"awards.constants not found: {e}")


def test_grade_mapping_keys_and_types():
    c = _import_constants()
    assert hasattr(c, "GRADE_TO_POINTS"), "GRADE_TO_POINTS missing"
    mapping = c.GRADE_TO_POINTS
    assert isinstance(mapping, dict)
    # Spot-check expected keys; adjust if your constants differ
    for k in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "E", "NR", "N"]:
        assert k in mapping, f"{k} missing in mapping"
        assert isinstance(mapping[k], (int, float)), f"{k} value must be numeric"


def test_convert_grade_to_points_basic():
    c = _import_constants()
    if not hasattr(c, "convert_grade_to_points"):
        pytest.skip("convert_grade_to_points() not defined in awards.constants")
    f = c.convert_grade_to_points
    assert f("A+") == c.GRADE_TO_POINTS["A+"]
    # Unexpected tokens treated as NaN
    val = f("???")
    assert isinstance(val, float) and math.isnan(val)
    # Blank and None treated as NaN
    assert math.isnan(f(""))
    assert math.isnan(f(None))


def test_award_thresholds_and_ties():
    c = _import_constants()
    assert hasattr(c, "award_for"), "award_for() missing"
    f = c.award_for
    # From the provided logic
    assert f(96) == "Academic Excellence Award"
    assert f(95) == "Academic Excellence Award"   # tie included
    assert f(94) == "Special Merit Award"
    assert f(92) == "Special Merit Award"         # tie included
    assert f(90) == "Academic Award"
    assert f(86) == "Academic Award"              # tie included
    assert f(85.999) == ""
    assert f(float("nan")) == ""
