import re
from pathlib import Path
import pandas as pd
from .constants import YEAR_RANGE
from .reader import read_sheet_flex
from .processor import process_year

def infer_year_from_filename(p: Path) -> int | None:
    m = re.search(r"Year\s*(\d+)", p.stem, flags=re.IGNORECASE)
    return int(m.group(1)) if m else None

def process_file(path: Path, out_dir: Path, log_cb=print):
    from openpyxl.utils import get_column_letter
    import pandas as pd

    def _reorder_award(out_df: pd.DataFrame) -> pd.DataFrame:
        cols = list(out_df.columns)
        try:
            name_idx = next(i for i, c in enumerate(cols) if c.lower().startswith("student_name"))
        except StopIteration:
            return out_df
        if "Award" not in cols:
            return out_df
        cols.remove("Award")
        cols.insert(name_idx + 1, "Award")
        return out_df[cols]

    def _autofit(ws):
        for col_cells in ws.columns:
            max_len = 0
            for cell in col_cells:
                v = "" if cell.value is None else str(cell.value)
                if len(v) > max_len:
                    max_len = len(v)
            width = min(max(10, int(max_len * 1.2)), 60)
            ws.column_dimensions[get_column_letter(col_cells[0].column)].width = width

    try:
        year = infer_year_from_filename(path)
        if year is None:
            log_cb(f"[SKIP] {path.name}: could not infer year from filename")
            return None
        if year not in YEAR_RANGE:
            log_cb(f"[SKIP] {path.name}: year {year} not in 7–10")
            return None

        df = read_sheet_flex(path)
        out, subj_df = process_year(df, year)

        # place Award after Student Name
        out = _reorder_award(out)

        out_path = out_dir / f"{path.stem} - Awards.xlsx"
        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            out.to_excel(writer, index=False, sheet_name="Raw+Awards")
            subj_df.to_excel(writer, index=False, sheet_name="Subject_Averages")
            wb = writer.book
            _autofit(wb["Raw+Awards"])
            _autofit(wb["Subject_Averages"])

        log_cb(f"[OK]   {path.name} → {out_path.name}")
        return out_path
    except Exception as e:
        log_cb(f"[ERR]  {path.name}: {e}")
        return None
