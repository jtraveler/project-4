# CC Instructions — Phase 6E Series (6E-A, 6E-B, 6E-C)

Run the following three specs in order. Do not start the next spec until the previous one is fully committed.

---

**SPEC 1** is `CC_SPEC_BULK_GEN_PHASE_6E_A.md`. Run this spec to completion per its instructions. When committed, create a detailed report and save it to `/docs/REPORT_BULK_GEN_PHASE_6E_A.md`. Do NOT run the full test suite — isolated tests only as specified in the spec.

**SPEC 2** is `CC_SPEC_BULK_GEN_PHASE_6E_B.md`. Only begin after Spec 1 is committed. Confirm the 6E-A commit is present in `git log` before starting. Run this spec to completion per its instructions. When committed, create a detailed report and save it to `/docs/REPORT_BULK_GEN_PHASE_6E_B.md`. Do NOT run the full test suite — isolated tests only as specified in the spec.

**SPEC 3** is `CC_SPEC_BULK_GEN_PHASE_6E_C.md`. Only begin after Spec 2 is committed. Confirm both the 6E-A and 6E-B commits are present in `git log` before starting. Run this spec to completion per its instructions. When committed, run the full test suite and report the total count. Save the report to `/docs/REPORT_BULK_GEN_PHASE_6E_C.md`.

---

For each report, use the following agents to help write it and invoke them explicitly. Use @technical-writer for overall report structure, clarity, and prose quality. Use @code-reviewer for accuracy of the technical details, issues section, and solutions. Also use the same agents that were used during implementation for their section of the agent ratings.

Each report must include all of the following sections in order.

Section 1 is Overview. Describe what this spec was, why it existed, and what problem it solved. Include where it fits in the three-part 6E series.

Section 2 is Expectations. State what the spec required across all touch points and whether each expectation was met. Use the touch point numbering from the spec.

Section 3 is Improvements Made. Provide a detailed list of every change made, organized by file. For model changes include the exact field definition. For JS changes include exact before/after of any function signatures or guard conditions that changed. For backend changes include the exact validation pattern used.

Section 4 is Issues Encountered and Resolved. For every problem hit during implementation, state the root cause and the exact fix applied.

Section 5 is Remaining Issues. For any issues not resolved, provide exact recommended solutions including the file name, the location in the file, and what specifically needs to change.

Section 6 is Concerns and Areas for Improvement. List any process or code quality concerns, and for each one provide specific actionable guidance on how to improve it. The 6E-A and 6E-C reports must include the final line count of `bulk-generator-ui.js` and state whether it is approaching the 780-line alert threshold.

Section 7 is Agent Ratings. Provide a full table with agent name, score, key findings, and whether the findings were acted on. Include the round number. State the average score and whether it met the 8.0 threshold. All required agents for that spec must appear in this table.

Section 8 is Recommended Additional Agents. List any agents that were not used but would have added value, and describe what each one would have reviewed.

Section 9 is How to Test. Provide manual browser steps and automated test commands that are specific and actionable. The 6E-A report must include a step for testing a mixed-size job. The 6E-C report must include the full suite result and a step for testing a job where different prompts have different image counts and confirming the gallery renders each group with the correct number of slots.

Section 10 is Commits. List every commit hash and its description.

Section 11 is What to Work on Next. For the 6E-A and 6E-B reports, the first item must be the next spec in the series. For the 6E-C report, the first item must reference the `bulk-generator-ui.js` line count and whether a sub-split is now needed, and the second item must be the N4 upload-flow rename investigation.

The quality bar for these reports is high. They will be used as project knowledge for future sessions so they must be precise, complete, and written as if a new developer is reading them cold. Vague sections are not acceptable. Section 3 must include exact before/after code for any function signature changes or guard condition changes — do not summarise them.
