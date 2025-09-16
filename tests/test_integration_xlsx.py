# tests/test_integration_xlsx.py
import importlib
import pytest


def _import_io_layer():
    # Expect a high-level function that reads an input path and returns a DataFrame
    for name in ("process_file", "process_path", "load_and_process"):
        for mod in ("awards.processing", "awards.process", "awards.io", "awards.pipeline"):
            try:
                m = importlib.import_module(mod)
                if hasattr(m, name):
                    return getattr(m, name)
            except ModuleNotFoundError:
                continue
    pytest.skip("No IO-layer function found: expected one of process_file/process_path/load_and_process in awards.*")


def test_process_year7_sample(sample_files):
    fn = sample_files["Year 7.xlsx"]
    process = _import_io_layer()
    df = process(str(fn))
    assert not df.empty
    # Output must start with these columns
    assert list(df.columns[:3]) == ["Student_Code", "Student_Name", "Award"]


def test_awards_distribution_present(sample_files):
    fn = sample_files["Year 10.xlsx"]
    process = _import_io_layer()
    df = process(str(fn))
    assert "Award" in df.columns
    assert df["Award"].dtype == object
