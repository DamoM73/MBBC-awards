import numpy as np
import pandas as pd
from .constants import POINTS
from .reader import clean_col, extract_sem

def convert_grade_to_points(val):
    # Converts a grade value to its corresponding points using the POINTS mapping.
    # Returns NaN if the value is missing or not found in POINTS.
    if pd.isna(val):
        return np.nan
    return POINTS.get(str(val).strip().upper(), np.nan)

def _per_subject_avgs(df: pd.DataFrame, subject_cols: dict) -> dict:
    """
    Calculates per-subject average points for each student using available semesters.
    Returns a dictionary: {subject: series_of_points_avg}
    """
    out = {}
    for base, sems in subject_cols.items():
        s1 = sems.get(1)  # Semester 1 column name
        s2 = sems.get(2)  # Semester 2 column name
        # Convert grades to points for each semester, or fill with NaN if missing
        p1 = df[s1].map(convert_grade_to_points) if s1 in df else pd.Series(np.nan, index=df.index)
        p2 = df[s2].map(convert_grade_to_points) if s2 in df else pd.Series(np.nan, index=df.index)
        # Average both semesters if available, otherwise use whichever exists
        if s1 in df and s2 in df:
            subj_avg = (p1 + p2) / 2.0
        else:
            subj_avg = p1 if s1 in df else p2
        out[base] = subj_avg
    return out

def _arts_composite(year_level: int, df: pd.DataFrame, subject_avgs: dict, subject_cols: dict) -> dict:
    """
    For Years 7–8, replaces ART, DRA, MUS with a composite 'Arts' average across available components.
    Returns a new subject_avgs dictionary with 'Arts' and without ART, DRA, MUS.
    """
    if year_level not in (7, 8):
        return subject_avgs
    # Get ART and DRA averages, or fill with NaN if missing
    art = subject_avgs.get("ART", pd.Series(np.nan, index=df.index))
    dra = subject_avgs.get("DRA", pd.Series(np.nan, index=df.index))

    # Get semester columns for Music (MUS)
    mus_s1 = subject_cols.get("MUS", {}).get(1)
    mus_s2 = subject_cols.get("MUS", {}).get(2)
    # Convert Music semester 1 grades to points, or fill with NaN if missing
    m1 = df[mus_s1].map(convert_grade_to_points) if mus_s1 in df else pd.Series(np.nan, index=df.index)
    # If semester 2 exists, average both semesters; otherwise, use semester 1 only
    if mus_s2 in df:
        m2 = df[mus_s2].map(convert_grade_to_points)
        mus_avg = (m1 + m2) / 2.0
    else:
        mus_avg = m1

    # Combine ART, DRA, and MUS averages into a single DataFrame
    arts_vals = pd.concat([art, dra, mus_avg], axis=1)
    # Compute the mean across the three arts subjects for each student, skipping NaNs
    arts = arts_vals.mean(axis=1, skipna=True)
    subject_avgs = subject_avgs.copy()
    subject_avgs["Arts"] = arts
    # Remove the individual ART, DRA, and MUS subjects from the averages dictionary
    for comp in ["ART", "DRA", "MUS"]:
        subject_avgs.pop(comp, None)
    return subject_avgs

def process_year(df: pd.DataFrame, year_level: int):
    """
    Main function to process a year's data.
    Returns a tuple: (output DataFrame with awards, DataFrame of subject averages).
    """
    df = df.copy()
    # Clean column names for consistency
    df.columns = [clean_col(c) for c in df.columns]

    # Identify and validate the student name column, drop rows without a student name
    name_cols = [c for c in df.columns if c.lower().startswith("student_name")]
    if not name_cols:
        raise ValueError("No Student Name column found")
    name_col = name_cols[0]
    df = df.dropna(subset=[name_col])
    df = df[df[name_col].astype(str).str.strip() != ""]

    # Identify student code column (optional) and columns to keep
    id_cols = [c for c in df.columns if c.lower().startswith("student_code")]
    keep_cols = id_cols + name_cols

    # Map base subject to {semester: column}
    subject_cols = {}
    for c in df.columns:
        if c in keep_cols:
            continue
        base, sem = extract_sem(c)
        subject_cols.setdefault(base, {})[sem] = c

    # Calculate per-subject averages (points)
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

    # For Years 7–8, create a composite 'Arts' average from ART, DRA, and MUS subjects
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

    # Create a DataFrame of subject averages for all students
    subj_df = pd.DataFrame(subject_avgs)

    # Calculate Grade Point for each student:
    # - If 7 or more subjects, sum the top 7 subject averages
    # - If fewer than 7, extrapolate the average to 7 subjects
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

    # Assign award bands based on Grade Point
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
    # Add a note if the Grade Point was extrapolated from fewer than 7 subjects
    notes = np.where(counts < 7, "Extrapolated from fewer than 7 subjects", "")

    # Prepare the output DataFrame with awards and notes
    out = df.copy()
    out["Grade Point"] = grade_points.round(2)
    out["Award"] = awards
    out["Note"] = notes

    # Return the output DataFrame and the subject averages DataFrame
    return out, subj_df
