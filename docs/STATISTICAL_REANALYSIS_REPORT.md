# Statistical Reanalysis Report: Intact-Class Allocation

## Study allocation structure

The intervention was implemented at the intact-class level. The supplied workbook covers three academic years, with one experimental class and one control class in each year: six classes and three year-matched class pairs. Each class contains 48 students in 12 four-member teams. Each team contributes three experiment-module records.

The treatment-allocation unit is the **class**, not the student, team, or team–module row. The 288 student records, 72 teams, and 216 team–module rows are nested observations.

## Necessary correction to the previous analysis

The earlier team-cluster GEE models accounted for within-team dependence but did not account for the fact that all teams in a class shared the same treatment allocation. Therefore, the earlier very small p-values should not be used as evidence of statistically significant intervention effects. Student-level independent-samples tests and team–module row-level tests also fail to respect the class-level allocation.

Only three annual class pairs are available. Class-level randomization has not been documented in the information supplied for this analysis. Accordingly, this repository reports descriptive annual class-pair contrasts and does not report conventional treatment-effect p-values.

## Annual descriptive contrasts

Differences are experimental class minus control class within the same academic year.

| Academic year | Pre-test difference (points) | Post-test difference (points) | Gain difference (points) | Valid inquiry-loop mean difference |
|---|---:|---:|---:|---:|
| 2023–2024 | +1.877 | +9.081 | +7.204 | +1.972 |
| 2024–2025 | −0.421 | +12.273 | +12.694 | +1.806 |
| 2025–2026 | −0.258 | +11.973 | +12.231 | +1.972 |
| Pooled descriptive difference | +0.399 | +11.109 | +10.710 | +1.917 |

Across all three annual pairs, the experimental classes had higher descriptive post-test means, score gains, and valid inquiry-loop means. These are consistent descriptive patterns, not causal effect estimates. Class-specific characteristics and other unmeasured factors cannot be ruled out.

## Data checks and interpretation limits

- The detail sheets contained no missing cells and no duplicate student UID or team-module Unit_ID values.
- SO6 counts in the supplied workbook are 134/144 versus 100/144. The previous summary's unadjusted Pearson chi-square value did not match recalculation from the detail rows. This student-level test is not recommended as treatment-effect inference under class-level allocation.
- The E4 count 33/36 versus 23/36 maps to Acoustic Sonar in the supplied workbook. Wi-Fi CSI maps to 33/36 versus 24/36. Check manuscript module labels if the former pair is attributed to Wi-Fi CSI.
- The survey contains experimental-group responses only. Its six item variables have ratings of 3–5 only; survey IDs do not match achievement-data IDs. Individual-level survey–achievement associations cannot be analysed from the supplied workbook.
- The platform's valid inquiry-loop rule checks the E3 challenge stage, a parent run, exactly one changed parameter, and an explanation length of at least 15 characters. It is a rule-based process-compliance indicator and does not automatically assess the scientific correctness or depth of the explanation.
- The workbook contains aggregate valid-loop counts, not the full anonymized run ledger. The counts cannot be independently reconstructed from the workbook alone.

## Suggested manuscript wording

### Methods — allocation and analysis

The intervention was implemented at the intact-class level. One experimental class and one control class were included in each of three academic years, yielding six classes and three year-matched class pairs. Each class comprised 48 students organized into 12 four-member teams. Accordingly, students and teams were treated as nested observational units rather than independent treatment replications. Given the small number of class-level units and the absence of documented class-level randomization, student- or team-level significance tests were not used to support the intervention effect. Results are presented as descriptive contrasts for each annual class pair.

### Results — descriptive comparison

Across the three annual class pairs, the experimental classes showed higher mean post-test scores than the corresponding control classes, with differences of 9.08, 12.27, and 11.97 points. The corresponding differences in pre-to-post score gains were 7.20, 12.69, and 12.23 points. Mean valid inquiry-loop counts were also higher in each experimental class, with annual class-level contrasts of 1.97, 1.81, and 1.97 loops per team–module record. These results describe a consistent pattern across the three cohorts; they should not be interpreted as causal estimates because treatment was assigned to intact classes and only three annual class pairs were available.

### Limitations

Because only one experimental class and one control class were included in each academic year, class-specific characteristics could not be separated from the intervention effect. Although pre-test scores were available, adjustment for measured baseline performance cannot eliminate unmeasured class-level confounding. The small number of class pairs also precludes reliable conventional cluster-level significance testing. The findings should therefore be interpreted as quasi-experimental descriptive evidence unless class-level randomization can be documented.

## Privacy

The student-level source workbook and questionnaire-level records are not committed to this public repository. Only aggregate class-level summaries are included. Do not upload raw student records, questionnaire-level responses, names, student identifiers, or potentially identifying run-level records.
