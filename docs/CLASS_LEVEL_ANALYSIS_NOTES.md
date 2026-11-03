# Class-Level Analysis Notes

## Confirmed allocation structure

The teaching intervention was implemented at the intact-class level. The supplied workbook contains three academic years, with one experimental class and one control class in each year:

- 6 intact classes in total; 3 experimental and 3 control classes.
- 48 students per class, organized into 12 teams of four.
- 72 teams in total.
- Each team contributes three experiment-module records, giving 216 team–module rows.

The treatment-allocation unit is the **class**, not the student, team, or team–module row. The 288 student records and 216 team–module records are nested observations.

## Annual descriptive contrasts

All differences below are experimental class minus control class within the same academic year. They are descriptive contrasts, not causal effect estimates.

| Academic year | Pre-test difference | Post-test difference | Gain difference | Valid inquiry-loop mean difference |
|---|---:|---:|---:|---:|
| 2023–2024 | +1.88 | +9.08 | +7.20 | +1.97 |
| 2024–2025 | −0.42 | +12.27 | +12.69 | +1.81 |
| 2025–2026 | −0.26 | +11.97 | +12.23 | +1.97 |
| Three-year pooled descriptive difference | +0.40 | +11.11 | +10.71 | +1.92 |

The experimental class has a higher descriptive post-test mean, score gain, and valid inquiry-loop mean in each of the three annual pairs. This repeated direction is worth reporting, but it does not isolate the intervention from class-level differences or other unmeasured factors.

## Statistical interpretation

The earlier student-level independent-samples tests and team-cluster GEE models should not be used as primary evidence of intervention significance. Team-cluster GEE accounts for within-team dependence but does not account for the fact that all teams in a given class share the same treatment allocation. Treating students or team–module rows as independent treatment replications can understate uncertainty.

Only three annual class pairs are available. Class-level randomization has not been documented in the information supplied for this analysis. Consequently, this repository reports the annual class-pair contrasts descriptively and does not provide conventional treatment-effect p-values.

## Additional data checks

- The detail sheets contained no missing cells and no duplicate student UID or team-module Unit_ID values.
- The workbook's SO6 counts are 134/144 versus 100/144. The previous summary value for the unadjusted Pearson chi-square statistic did not match a recalculation from the detail rows; this student-level test is not recommended as treatment-effect inference under the class-level allocation.
- The E4 count 33/36 versus 23/36 maps to the Acoustic Sonar module in the supplied workbook; Wi-Fi CSI maps to 33/36 versus 24/36. Check any manuscript table that attributes the former pair to Wi-Fi CSI.
- The survey sheet contains experimental-group responses only. Its item variables have ratings of 3–5 only, and survey IDs do not match the achievement-data IDs. Do not claim an individual-level association between survey responses and achievement.

## Platform metric scope

The repository's valid inquiry-loop rule checks the E3 challenge stage, a parent run, exactly one changed parameter, and an explanation length of at least 15 characters. This is a rule-based process-compliance indicator; it does not automatically score the scientific correctness or depth of a student's explanation.

The supplied workbook contains aggregate valid-loop counts rather than the full anonymized run ledger. The aggregate counts therefore cannot be independently reconstructed from the workbook alone.

## Data privacy

The student-level source workbook and questionnaire-level records are not committed to this public repository. The public report and this note contain aggregate summaries only. Do not upload raw student records, individual questionnaire responses, names, student identifiers, or run-level records that could identify students.
