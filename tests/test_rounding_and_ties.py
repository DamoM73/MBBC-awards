# tests/test_rounding_and_ties.py
import importlib
import decimal
import pytest


def test_gpa_rounding_half_up_to_2dp():
    # If a rounding helper exists, test it; else skip and rely on integration checks.
    try:
        r = importlib.import_module("awards.rounding")
    except ModuleNotFoundError:
        pytest.skip("awards.rounding module not found; if GPA rounding is inline, cover via integration tests.")

    if not hasattr(r, "round_half_up"):
        pytest.skip("round_half_up() not exposed")

    f = r.round_half_up
    assert f(95.005, 2) == decimal.Decimal("95.01")
    assert f(95.004, 2) == decimal.Decimal("95.00")
