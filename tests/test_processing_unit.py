# tests/test_processing_unit.py
import importlib
import pandas as pd
import pytest


def _import_processing():
    # Try common module names
    for mod in ("awards.processing", "awards.process", "awards.core"):
        try:
            return importlib.import_module(mod)
        except ModuleNotFoundError:
            continue
    pytest.skip("No processing module found. Expected awards.processing/process/core.")


def test_arts_bucket_year7_mock():
    p = _import_processing()
    func = getattr(p, "process_dataframe", None)
    if func is None:
        pytest.skip("process_dataframe(df, year_level) not found")

    # Minimal mock DataFrame for Year 7
    df = pd.DataFrame({
        "Student Code": [1, 2],
        "Student Name": ["Alpha", "Beta"],
        "ART": ["A", "B"],
        "DRA": ["B+", None],
        "MUS": ["A-", "B-"],  # single MUS column allowed
    })

    out = func(df.copy(), year_level=7)
    arts_col = next((c for c in out.columns if c.lower() == "arts"), None)
    assert arts_col is not None, "Arts average column missing after processing"


def test_under_7_subjects_flag_mock():
    p = _import_processing()
    func = getattr(p, "process_dataframe", None)
    if func is None:
        pytest.skip("process_dataframe(df, year_level) not found")

    df = pd.DataFrame({
        "Student Code": [1],
        "Student Name": ["Gamma"],
        "ENG": ["A"],
        "MAT": ["A"],
        "SCI": ["A"],  # only 3 subjects
    })
    out = func(df.copy(), year_level=9)

    gp_col = next((c for c in out.columns if c.lower().startswith("grade point")), None)
    note_col = next((c for c in out.columns if "note" in c.lower()), None)
    assert gp_col, "Grade Point not present"
    assert note_col, "Note column missing"
    assert any("fewer than 7" in str(x).lower() for x in out[note_col]), "Under-7 note expected"
