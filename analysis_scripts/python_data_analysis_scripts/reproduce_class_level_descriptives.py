#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproduce class-level descriptive contrasts for the teaching-evaluation workbook.

Usage:
  python reproduce_class_level_descriptives.py /path/to/deidentified_teaching_evaluation_dataset.xlsx

The source workbook is intentionally not distributed in this repository.
No student- or team-level treatment-effect p-values are calculated because
the intervention was allocated to intact classes and only three annual
class pairs are available.
"""
import argparse
import pandas as pd


def read_sheet(path, sheet_name):
    return pd.read_excel(path, sheet_name=sheet_name, header=2).dropna(how="all")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", help="Path to the approved de-identified teaching-evaluation workbook")
    args = parser.parse_args()

    students = read_sheet(args.workbook, "Student_Level_Data")
    teams = read_sheet(args.workbook, "Team_Level_Inquiry")
    students["Gain"] = students["Post_Test_Score"] - students["Pre_Test_Score"]

    student_class = students.groupby(["Academic_Year", "Cohort"]).agg(
        N=("Student_UID", "size"),
        Pre=("Pre_Test_Score", "mean"),
        Post=("Post_Test_Score", "mean"),
        Gain=("Gain", "mean"),
        SO1=("SO1_Achieved", "sum"),
        SO5=("SO5_Achieved", "sum"),
        SO6=("SO6_Achieved", "sum"),
    ).reset_index()

    team_class = teams.groupby(["Academic_Year", "Cohort"]).agg(
        Teams=("Team_ID", "nunique"),
        TeamModuleRows=("Unit_ID", "size"),
        ValidLoops=("Valid_Inquiry_Loops", "mean"),
        E4=("High_Difficulty_Task_Success", "sum"),
        E5=("Redesign_Passed", "sum"),
    ).reset_index()

    print("CLASS-LEVEL DESCRIPTIVES")
    print("Treatment allocation unit: intact class")
    print("No treatment-effect p-values are calculated.\n")

    for year in sorted(students["Academic_Year"].unique()):
        for cohort, label in [
            ("Challenge_Exp", "Experimental"),
            ("Control_Group", "Control"),
        ]:
            s = student_class.query(
                "Academic_Year == @year and Cohort == @cohort"
            ).iloc[0]
            t = team_class.query(
                "Academic_Year == @year and Cohort == @cohort"
            ).iloc[0]
            print(
                f"{year} | {label}: students={int(s.N)}, teams={int(t.Teams)}, "
                f"pre={s.Pre:.3f}, post={s.Post:.3f}, gain={s.Gain:.3f}, "
                f"valid_loops={t.ValidLoops:.3f}, "
                f"SO1={int(s.SO1)}/48, SO5={int(s.SO5)}/48, SO6={int(s.SO6)}/48, "
                f"E4={int(t.E4)}/36, E5={int(t.E5)}/36"
            )

    print("\nANNUAL EXPERIMENTAL-CONTROL CLASS CONTRASTS")
    for year in sorted(students["Academic_Year"].unique()):
        e = student_class.query(
            "Academic_Year == @year and Cohort == 'Challenge_Exp'"
        ).iloc[0]
        c = student_class.query(
            "Academic_Year == @year and Cohort == 'Control_Group'"
        ).iloc[0]
        et = team_class.query(
            "Academic_Year == @year and Cohort == 'Challenge_Exp'"
        ).iloc[0]
        ct = team_class.query(
            "Academic_Year == @year and Cohort == 'Control_Group'"
        ).iloc[0]
        print(
            f"{year}: pre_diff={e.Pre-c.Pre:+.3f}, "
            f"post_diff={e.Post-c.Post:+.3f}, "
            f"gain_diff={e.Gain-c.Gain:+.3f}, "
            f"valid_loop_diff={et.ValidLoops-ct.ValidLoops:+.3f}"
        )

    print(
        "\nCAUTION: only three annual class pairs are available; "
        "class-level randomization has not been documented. "
        "Interpret these results as descriptive contrasts, not causal estimates."
    )


if __name__ == "__main__":
    main()
