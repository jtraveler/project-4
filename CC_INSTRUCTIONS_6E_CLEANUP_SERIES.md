# CC Instructions — 6E Cleanup Series (CLEANUP-1, CLEANUP-2, CLEANUP-3)

Run the following three specs in strict order. Do not start any spec until the previous one is fully committed.

---

**SPEC 1** is `CC_SPEC_BULK_GEN_6E_CLEANUP_1.md`. Run this spec to completion per its instructions. Isolated tests only — do NOT run the full suite. When committed, create a detailed report and save it to `/docs/REPORT_BULK_GEN_6E_CLEANUP_1.md`.

**SPEC 2** is `CC_SPEC_BULK_GEN_6E_CLEANUP_2.md`. Only begin after Spec 1 is committed. Confirm the CLEANUP-1 commit is in `git log` before starting. Isolated tests only — do NOT run the full suite. When committed, create a detailed report and save it to `/docs/REPORT_BULK_GEN_6E_CLEANUP_2.md`.

**SPEC 3** is `CC_SPEC_BULK_GEN_6E_CLEANUP_3.md`. Only begin after Spec 2 is committed. Confirm the CLEANUP-2 commit is in `git log` before starting. Run the **full test suite** after committing and include the count in the report. Save the report to `/docs/REPORT_BULK_GEN_6E_CLEANUP_3.md`.

---

For each report, use the following agents to help write it and invoke them explicitly. Use @technical-writer for overall report structure, clarity, and prose quality. Use @code-reviewer for accuracy of the technical details, issues section, and solutions. Also use the same agents that were used during implementation for their section of the agent ratings.

Each report must include all of the following sections in order.

Section 1 is Overview. Describe what this spec was, why it existed, and what gap it closed. For CLEANUP-2, explain why the sub-split was necessary and what the line count was before and after. For CLEANUP-3, describe all four items fixed and why each was flagged.

Section 2 is Expectations. State what each touch point required and whether it was met. Use the touch point numbering from the spec (TP1, TP2, etc.).

Section 3 is Improvements Made. Provide exact before/after code for every change made, organised by file. For CLEANUP-2, list every function extracted with its approximate line count. For CLEANUP-3, show the exact before/after for all four touch points — do not summarise.

Section 4 is Issues Encountered and Resolved. For every problem hit during implementation, state the root cause and the exact fix applied.

Section 5 is Remaining Issues. For any issues not resolved, provide the exact file, the location, and what specifically needs to change. For the CLEANUP-3 report, confirm explicitly that the cancel-path staleness issue is fully closed.

Section 6 is Concerns and Areas for Improvement. List any concerns and provide specific actionable guidance for each. The CLEANUP-2 report must state the final line counts of both `bulk-generator-ui.js` and the new `bulk-generator-gallery.js`. The CLEANUP-3 report must state the final line count of `bulk-generator-ui.js` after the cleanup changes and confirm it is well below the 780-line threshold.

Section 7 is Agent Ratings. Provide a full table with agent name, score, key findings, and whether the findings were acted on. Include the round number. State the average score and whether it met the 8.0 threshold. All required agents for that spec must appear in this table.

Section 8 is Recommended Additional Agents. List any agents that were not used but would have added value, and describe what each one would have reviewed.

Section 9 is How to Test. For CLEANUP-1 and CLEANUP-2, provide the isolated test commands from the spec. For CLEANUP-3, include the full suite command and the actual result, plus the three manual browser tests (Tests A, B, C) with expected outcomes.

Section 10 is Commits. List every commit hash and its description. The CLEANUP-3 report must include a full series summary table showing all commits from CLEANUP-1 through CLEANUP-3 in order.

Section 11 is What to Work on Next. For CLEANUP-1 and CLEANUP-2, the first item must be the next spec in this series. For the CLEANUP-3 report, the first item must be the Session 122 docs update spec (updating CLAUDE.md, CLAUDE_CHANGELOG.md, CLAUDE_PHASES.md, PROJECT_FILE_STRUCTURE.md for all work done this session including the full 6E series and both hardening passes and cleanup series). The second item must be the N4h upload-flow rename investigation. The third item must be the `detect_b2_orphans` command spec (prerequisite before bulk job deletion).

The quality bar for these reports is high. Section 3 must show exact before/after code — not prose descriptions. Vague sections are not acceptable.
