#!/usr/bin/env python3
"""Reproduce within-class GEE analyses for the smartphone inquiry study.

Usage:
  python reproduce_within_class_analysis_v2.py "脱敏教学评估与实证数据集.xlsx"

Expected detail sheets: Student_Level_Data and Team_Level_Inquiry (header row 3).
Optional survey sheet is detected by the presence of Q1_Curiosity_Driver through
Q6_Engineering_Competence. The script analyses the condition labels supplied in
the workbook; it does not reconstruct the allocation sequence or rubric scoring.
"""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

SURVEY_COLS = [
    "Q1_Curiosity_Driver", "Q2_Sensor_Engagement", "Q3_DiffView_Scaffold",
    "Q4_Causal_Thinking", "Q5_Team_Role_Audit", "Q6_Engineering_Competence"
]
BINARY = [
    ("ABET SO1", "SO1_Achieved", "student"),
    ("ABET SO5", "SO5_Achieved", "student"),
    ("ABET SO6", "SO6_Achieved", "student"),
    ("E4 high-difficulty success", "High_Difficulty_Task_Success", "team"),
    ("E5 redesign success", "Redesign_Passed", "team"),
]

def read_sheet(path, name):
    return pd.read_excel(path, sheet_name=name, header=2).dropna(how="all").copy()

def add_keys(df):
    needed = ["Academic_Year", "Class_ID", "Cohort", "Team_ID"]
    missing = [x for x in needed if x not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    d = df.copy()
    d["Class_Key"] = d["Academic_Year"].astype(str) + "|" + d["Class_ID"].astype(str)
    d["Treat"] = (d["Cohort"].astype(str) == "Challenge_Exp").astype(int)
    d["Team_Cluster"] = d["Class_Key"] + "|" + d["Cohort"].astype(str) + "|" + d["Team_ID"].astype(str)
    return d

def gee(formula, data, family=None):
    return smf.gee(
        formula, groups="Team_Cluster", data=data,
        cov_struct=sm.cov_struct.Exchangeable(),
        family=family or sm.families.Gaussian()
    ).fit()

def result_row(label, scale, model, exp_beta=False):
    b, se = float(model.params["Treat"]), float(model.bse["Treat"])
    lo, hi = b - 1.96 * se, b + 1.96 * se
    if exp_beta:
        estimate, lo, hi = np.exp([b, lo, hi])
    else:
        estimate = b
    return {
        "Outcome": label, "Effect scale": scale, "Estimate": float(estimate),
        "95% CI low": float(lo), "95% CI high": float(hi),
        "p-value": float(model.pvalues["Treat"]), "Holm-adjusted p": np.nan,
        "Model": "GEE; exchangeable working correlation; robust sandwich SE"
    }

def survey_summary(path):
    for sheet in pd.ExcelFile(path).sheet_names:
        try:
            d = read_sheet(path, sheet)
        except Exception:
            continue
        if set(SURVEY_COLS).issubset(d.columns):
            rows = []
            for col in SURVEY_COLS:
                v = pd.to_numeric(d[col], errors="coerce").dropna()
                rows.append({
                    "Dataset variable": col, "N": len(v), "Mean": v.mean(),
                    "SD": v.std(ddof=1), "Ratings 4-5 n": int(v.ge(4).sum()),
                    "Ratings 4-5 %": v.ge(4).mean(), "Rating 3 n": int(v.eq(3).sum()),
                    "Rating 4 n": int(v.eq(4).sum()), "Rating 5 n": int(v.eq(5).sum()),
                    "Ratings 1-2 n": int(v.le(2).sum())
                })
            return pd.DataFrame(rows), sheet
    return pd.DataFrame(), None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workbook", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=Path("WithinClass_Reproduced_Results.xlsx"))
    args = ap.parse_args()
    if not args.workbook.exists():
        raise FileNotFoundError(args.workbook)

    stu = add_keys(read_sheet(args.workbook, "Student_Level_Data"))
    team = add_keys(read_sheet(args.workbook, "Team_Level_Inquiry"))
    for c in ["Pre_Test_Score", "Post_Test_Score", "SO1_Achieved", "SO5_Achieved", "SO6_Achieved"]:
        if c not in stu.columns: raise ValueError(f"Student_Level_Data missing {c}")
    for c in ["Experiment_Module", "Valid_Inquiry_Loops", "High_Difficulty_Task_Success", "Redesign_Passed"]:
        if c not in team.columns: raise ValueError(f"Team_Level_Inquiry missing {c}")

    models = {
        "Pre-test": gee("Pre_Test_Score ~ Treat + C(Class_Key)", stu),
        "Post-test": gee("Post_Test_Score ~ Treat + Pre_Test_Score + C(Class_Key)", stu),
        "Valid inquiry loops": gee("Valid_Inquiry_Loops ~ Treat + C(Class_Key) + C(Experiment_Module)", team),
        "Valid inquiry loops (count model)": gee(
            "Valid_Inquiry_Loops ~ Treat + C(Class_Key) + C(Experiment_Module)", team, sm.families.Poisson()
        ),
    }
    rows = [
        result_row("Pre-test score", "Mean difference", models["Pre-test"]),
        result_row("Post-test score", "Mean difference", models["Post-test"]),
        result_row("Valid inquiry loops", "Mean difference", models["Valid inquiry loops"]),
        result_row("Valid inquiry loops (count model)", "Incidence-rate ratio", models["Valid inquiry loops (count model)"], True),
    ]
    binary_models = {}
    for label, outcome, level in BINARY:
        if level == "student":
            data = stu
            formula = f"{outcome} ~ Treat + Pre_Test_Score + C(Class_Key)"
        else:
            data = team
            formula = f"{outcome} ~ Treat + C(Class_Key) + C(Experiment_Module)"
        m = gee(formula, data, sm.families.Binomial())
        binary_models[label] = m
        rows.append(result_row(label, "Odds ratio", m, True))
    results = pd.DataFrame(rows)
    mask = results["Outcome"].isin([x[0] for x in BINARY])
    results.loc[mask, "Holm-adjusted p"] = multipletests(results.loc[mask, "p-value"], method="holm")[1]

    # Descriptive group summaries.
    desc = []
    for cohort, label in [("Challenge_Exp", "Smartphone inquiry"), ("Control_Group", "Laboratory-equipment control")]:
        s, t = stu[stu.Cohort == cohort], team[team.Cohort == cohort]
        row = {
            "Condition": label, "Students": len(s), "Teams": t.Team_Cluster.nunique(),
            "Pre-test mean": s.Pre_Test_Score.mean(), "Pre-test SD": s.Pre_Test_Score.std(ddof=1),
            "Post-test mean": s.Post_Test_Score.mean(), "Post-test SD": s.Post_Test_Score.std(ddof=1),
            "Gain mean": (s.Post_Test_Score-s.Pre_Test_Score).mean(),
            "Gain SD": (s.Post_Test_Score-s.Pre_Test_Score).std(ddof=1),
            "Valid loops mean": t.Valid_Inquiry_Loops.mean(), "Valid loops SD": t.Valid_Inquiry_Loops.std(ddof=1),
            "Valid loops total": int(t.Valid_Inquiry_Loops.sum())
        }
        for col, label2 in [("SO1_Achieved","SO1"),("SO5_Achieved","SO5"),("SO6_Achieved","SO6")]:
            n=int(s[col].sum()); row[label2]=f"{n}/{len(s)} ({n/len(s):.1%})"
        for col, label2 in [("High_Difficulty_Task_Success","E4"),("Redesign_Passed","E5")]:
            n=int(t[col].sum()); row[label2]=f"{n}/{len(t)} ({n/len(t):.1%})"
        desc.append(row)
    desc = pd.DataFrame(desc)

    module = team.groupby(["Experiment_Module","Cohort"]).agg(
        Teams=("Team_Cluster","nunique"), Valid_Loops_Mean=("Valid_Inquiry_Loops","mean"),
        Valid_Loops_SD=("Valid_Inquiry_Loops","std"), E4_Success=("High_Difficulty_Task_Success","sum"),
        E4_N=("High_Difficulty_Task_Success","count"), E5_Success=("Redesign_Passed","sum"),
        E5_N=("Redesign_Passed","count")
    ).reset_index()
    module["E4_Rate"] = module.E4_Success/module.E4_N
    module["E5_Rate"] = module.E5_Success/module.E5_N

    survey, survey_sheet = survey_summary(args.workbook)
    class_counts = stu.groupby("Class_Key").size()
    cell_counts = stu.groupby(["Class_Key","Cohort"]).size()
    audit = pd.DataFrame([
        ("Academic years", stu.Academic_Year.nunique(), "Expected: 3"),
        ("Natural classes", stu.Class_Key.nunique(), "Expected: 6"),
        ("Students", len(stu), "Expected: 288"),
        ("Students per class", str(sorted(class_counts.unique().tolist())), "Expected: [48]"),
        ("Students per class × condition", str(sorted(cell_counts.unique().tolist())), "Expected: [24]"),
        ("Teams", team.Team_Cluster.nunique(), "Expected: 72"),
        ("Team-module records", len(team), "Expected: 216"),
        ("Missing student cells", int(stu.isna().sum().sum()), "Expected: 0"),
        ("Missing team-module cells", int(team.isna().sum().sum()), "Expected: 0"),
        ("Survey responses", len(survey) if not survey.empty else 0, survey_sheet or "No matching survey sheet detected")
    ], columns=["Check","Observed","Interpretation"])

    # Exploratory condition-by-module interaction; inspect before reporting in the paper.
    interaction = gee("Valid_Inquiry_Loops ~ Treat * C(Experiment_Module) + C(Class_Key)", team)
    names = [n for n in interaction.params.index if ":" in n and "Treat" in n]
    interaction_df = pd.DataFrame()
    if names:
        R = np.zeros((len(names), len(interaction.params)))
        for i, name in enumerate(names): R[i, list(interaction.params.index).index(name)] = 1
        wt = interaction.wald_test(R)
        interaction_df = pd.DataFrame([{
            "Test":"Treat × Experiment_Module", "Terms":"; ".join(names),
            "Wald chi-square":float(np.asarray(wt.statistic).squeeze()), "df":len(names),
            "p-value":float(np.asarray(wt.pvalue).squeeze()),
            "Note":"Exploratory; verify specification before manuscript reporting"
        }])

    with pd.ExcelWriter(args.output, engine="openpyxl") as xw:
        audit.to_excel(xw, sheet_name="Data_Audit", index=False)
        desc.to_excel(xw, sheet_name="Group_Descriptives", index=False)
        results.to_excel(xw, sheet_name="GEE_Models", index=False)
        module.to_excel(xw, sheet_name="Module_Breakdown", index=False)
        if not survey.empty: survey.to_excel(xw, sheet_name="Survey_Descriptives", index=False)
        if not interaction_df.empty: interaction_df.to_excel(xw, sheet_name="Interaction_Check", index=False)

    print(f"Saved: {args.output.resolve()}")
    print(results.to_string(index=False))
    if not interaction_df.empty: print("\nExploratory interaction:\n", interaction_df.to_string(index=False))

if __name__ == "__main__":
    main()
