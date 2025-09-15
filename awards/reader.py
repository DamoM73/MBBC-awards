import re
import pandas as pd

def clean_col(c: str) -> str:
    c = str(c)
    c = c.replace("_x000D_", "").replace("\n", "")
    c = c.replace("OG", "").strip()
    c = re.sub(r"\s+", "_", c)
    return c

def extract_sem(colname: str):
    # trailing ".1" => semester 2; otherwise semester 1
    if colname.endswith(".1"):
        return colname[:-2], 2
    return colname, 1

def read_sheet_flex(path) -> pd.DataFrame:
    """Try several header rows. Prefer one that already contains 'Student' columns."""
    for hdr in [0, 1, 2, None]:
        try:
            df = pd.read_excel(path, header=hdr)
            cols = [str(c) for c in df.columns]
            if any("Student" in c for c in cols):
                return df
        except Exception:
            pass
    return pd.read_excel(path, header=0)
