import numpy as np
import pandas as pd
from .constants import POINTS
from .reader import clean_col, extract_sem

def convert_grade_to_points(val):
    if pd.isna(val):
        return np.nan
    return POINTS.get(str(val).strip().upper(), np.nan)

def _per_subject_avgs(df: pd.DataFrame, subject_cols: dict) -> dict:
    """Return {subject: series_of_points_avg} using available semesters."""
    out = {}
    for base, sems in subject_cols.items():
        s1 = sems.get(1)
        s2 = sems.get(2)
        p1 = df[s1].map(convert_grade_to_points) if s1 in df else pd.Series(np.nan, index=df.index)
        p2 = df[s2].map(convert_grade_to_points) if s2 in df else pd.Series(np.nan, index=df.index)
        if s1 in df and s2 in df:
            subj_avg = (p1 + p2) / 2.0
        else:
            subj_avg = p1 if s1 in df else p2
        out[base] = subj_avg
    return out

def _arts_composite(year_level: int, df: pd.DataFrame, subject_avgs: dict, subject_cols: dict) -> dict:
    """For Years 7–8 replace ART, DRA, MUS with composite 'Arts' averaged across available components."""
    if year_level not in (7, 8):
        return subject_avgs
    art = subject_avgs.get("ART", pd.Series(np.nan, index=df.index))
    dra = subject_avgs.get("DRA", pd.Series(np.nan, index=df.index))

    mus_s1 = subject_cols.get("MUS", {}).get(1)
    mus_s2 = subject_cols.get("MUS", {}).get(2)
    m1 = df[mus_s1].map(convert_grade_to_points) if mus_s1 in df else pd.Series(np.nan, index=df.index)
    if mus_s2 in df:
        m2 = df[mus_s2].map(convert_grade_to_points)
        mus_avg = (m1 + m2) / 2.0
    else:
        mus_avg = m1

    arts_vals = pd.concat([art, dra, mus_avg], axis=1)
    arts = arts_vals.mean(axis=1, skipna=True)
    subject_avgs = subject_avgs.copy()
    subject_avgs["Arts"] = arts
    for comp in ["ART", "DRA", "MUS"]:
        subject_avgs.pop(comp, None)
    return subject_avgs

def process_year(df: pd.DataFrame, year_level: int):
    """Return (out_df_with_awards, subject_avgs_df)."""
    df = df.copy()
    df.columns = [clean_col(c) for c in df.columns]

    # Identify and validate name column, then drop rows without a student name
    name_cols = [c for c in df.columns if c.lower().startswith("student_name")]
    if not name_cols:
        raise ValueError("No Student Name column found")
    name_col = name_cols[0]
    df = df.dropna(subset=[name_col])
    df = df[df[name_col].astype(str).str.strip() != ""]

    # Identify student code column (optional)
    id_cols = [c for c in df.columns if c.lower().startswith("student_code")]
    keep_cols = id_cols + name_cols

    # Map base subject -> {semester: column}
    subject_cols = {}
    for c in df.columns:
        if c in keep_cols:
            continue
        base, sem = extract_sem(c)
        subject_cols.setdefault(base, {})[sem] = c

    # Per-subject averages (points)
    subject_avgs = {}
    for base, sems in subject_cols.items():
        s1 = sems.get(1)
        s2 = sems.get(2)
        p1 = df[s1].map(convert_grade_to_points) if s1 in df else pd.Series(np.nan, index=df.index)
        p2 = df[s2].map(convert_grade_to_points) if s2 in df else pd.Series(np.nan, index=df.index)
        if s1 in df and s2 in df:
            subj_avg = (p1 + p2) / 2.0
        else:
            subj_avg = p1 if s1 in df else p2
        subject_avgs[base] = subj_avg

    # Arts composite for Y7–8: average available ART, MUS, DRA
    if year_level in (7, 8):
        art = subject_avgs.get("ART", pd.Series(np.nan, index=df.index))
        dra = subject_avgs.get("DRA", pd.Series(np.nan, index=df.index))
        mus_s1 = subject_cols.get("MUS", {}).get(1)
        mus_s2 = subject_cols.get("MUS", {}).get(2)
        m1 = df[mus_s1].map(convert_grade_to_points) if mus_s1 in df else pd.Series(np.nan, index=df.index)
        if mus_s2 in df:
            m2 = df[mus_s2].map(convert_grade_to_points)
            mus_avg = (m1 + m2) / 2.0
        else:
            mus_avg = m1
        arts_vals = pd.concat([art, dra, mus_avg], axis=1)
        arts = arts_vals.mean(axis=1, skipna=True)
        subject_avgs["Arts"] = arts
        for comp in ["ART", "DRA", "MUS"]:
            subject_avgs.pop(comp, None)

    subj_df = pd.DataFrame(subject_avgs)

    # Grade Point: sum top 7 if >=7 subjects else extrapolate avg * 7
    def calc_grade_point(row):
        vals = row.dropna().sort_values(ascending=False)
        if len(vals) == 0:
            return np.nan, 0
        if len(vals) >= 7:
            return float(vals.iloc[:7].sum()), len(vals)
        avg = vals.mean()
        return float(avg * 7), len(vals)

    gp_list, count_list = [], []
    for _, row in subj_df.iterrows():
        gp, cnt = calc_grade_point(row)
        gp_list.append(gp)
        count_list.append(cnt)

    grade_points = pd.Series(gp_list, index=subj_df.index)
    counts = pd.Series(count_list, index=subj_df.index)

    # Award bands
    def award_for(gp):
        if pd.isna(gp):
            return ""
        if gp >= 95:
            return "Academic Excellence Award"
        if gp >= 92:
            return "Special Merit Award"
        if gp >= 86:
            return "Academic Award"
        return ""

    awards = grade_points.map(award_for)
    notes = np.where(counts < 7, "Extrapolated from fewer than 7 subjects", "")

    out = df.copy()
    out["Grade Point"] = grade_points.round(2)
    out["Award"] = awards
    out["Note"] = notes

    return out, subj_df
