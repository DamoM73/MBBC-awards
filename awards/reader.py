import re
import pandas as pd

def clean_col(c: str) -> str:
    # Cleans and standardizes a column name:
    # - Removes unwanted characters and line breaks
    # - Removes "OG"
    # - Strips leading/trailing whitespace
    # - Replaces spaces with underscores
    c = str(c)
    c = c.replace("_x000D_", "").replace("\n", "")
    c = c.replace("OG", "").strip()
    c = re.sub(r"\s+", "_", c)
    return c

def extract_sem(colname: str):
    # Determines the semester for a subject column:
    # - If column ends with ".1", it's semester 2; otherwise semester 1
    # Returns (base column name, semester number)
    if colname.endswith(".1"):
        return colname[:-2], 2
    return colname, 1

def read_sheet_flex(path) -> pd.DataFrame:
    """
    Reads an Excel sheet, trying several possible header rows.
    Returns the first DataFrame whose columns contain 'Student'.
    If none match, returns the sheet with header=0.
    """
    for hdr in [0, 1, 2, None]:
        try:
            df = pd.read_excel(path, header=hdr)
            cols = [str(c) for c in df.columns]
            if any("Student" in c for c in cols):
                return df
        except Exception:
            pass
    return pd.read_excel(path, header=0)
