# tests/conftest.py
import pathlib
import pytest

DATA_DIR = pathlib.Path(__file__).parent / "data"

@pytest.fixture(scope="session")
def sample_files():
    candidates = ["Year 7.xlsx", "Year 8.xlsx", "Year 9.xlsx", "Year 10.xlsx"]
    files = {name: DATA_DIR / name for name in candidates}
    missing = [str(p) for p in files.values() if not p.exists()]
    if missing:
        pytest.skip(
            "Sample XLSX files are missing under tests/data. "
            "Place Year 7.xlsx, Year 8.xlsx, Year 9.xlsx, Year 10.xlsx there to run integration tests."
        )
    return files
