Run the following spec to completion per its instructions. Do not begin until you have read the full spec.

SPEC is CC_SPEC_N4H_UPLOAD_RENAME_FIX.md. Run this spec to completion per its instructions. When committed, create a detailed report and save it to /docs/REPORT_N4H_UPLOAD_RENAME_FIX.md.

For the report, use the following agents to help write it and invoke them explicitly. Use @technical-writer for overall report structure, clarity, and prose quality. Use @code-reviewer for accuracy of the technical details, issues section, and solutions. Also use the same agents that were used during implementation for their section of the agent ratings.

The report must include all of the following sections in order.

Section 1 is Overview. Describe what this fix was, why it existed, and what problem it solved. Explain the difference between the bulk-gen rename path (fixed in SMOKE2-FIX-D, Session 121) and the upload-flow rename path (fixed by this spec). Explain why upload-flow prompts were keeping UUID-based B2 filenames and what the SEO impact of that was.

Section 2 is Expectations. State what the spec required and whether those expectations were met. Cover: git archaeology completed, upload submit path mapped, async_task call added, b2_image_url guard in place, both tests added, full suite passed.

Section 3 is Improvements Made. Provide exact before/after code for every change made, organised by file. For upload_views.py show the exact lines added and their position relative to prompt.save(). For the test file show both new test functions in full.

Section 4 is Issues Encountered and Resolved. For every problem hit during implementation, state the root cause and the exact fix applied. If the git archaeology step revealed anything unexpected about the SMOKE2-FIX-D pattern, document it here.

Section 5 is Remaining Issues. For any issues not resolved, provide exact recommended solutions including the file name, the location in the file, and what specifically needs to change. If the manual production verification step (checking an actual uploaded prompt's b2_image_url after deploy) was not completed, list it here as a remaining verification step.

Section 6 is Concerns and Areas for Improvement. List any process or code quality concerns and for each one provide specific actionable guidance. Note whether there are any other upload-flow code paths (e.g. admin-side prompt creation, bulk import, or any other view that creates a Prompt with a B2 URL) that may also be missing the rename task queue call.

Section 7 is Agent Ratings. Provide a full table with agent name, score, key findings, and whether the findings were acted on. Include the round number. State the average score and whether it met the 8.0 threshold. Both @django-pro and @test-automator must appear in this table.

Section 8 is Recommended Additional Agents. List any agents that were not used but would have added value, and describe what each one would have reviewed.

Section 9 is How to Test. Provide both the automated test commands (isolated and full suite) with actual results, and the manual production verification steps from the spec (upload a prompt, check b2_image_url in shell, confirm SEO filename). State whether the manual verification was completed and what the result was.

Section 10 is Commits. List every commit hash and its description.

Section 11 is What to Work on Next. The first item must be the frozenset micro-spec (VALID_PROVIDERS, VALID_VISIBILITIES, create_test_gallery.py). The second item must be the Session 122 docs update spec (updating CLAUDE.md to remove the N4h blocker entry, plus CLAUDE_CHANGELOG.md, CLAUDE_PHASES.md, PROJECT_FILE_STRUCTURE.md for all session work). The third item must be the detect_b2_orphans management command spec. The fourth item must be the bulk job deletion spec.

The quality bar for this report is high. It will be used as project knowledge for future sessions so it must be precise, complete, and written as if a new developer is reading it cold. Vague sections are not acceptable. If something went wrong during implementation, state exactly what went wrong and exactly how it was fixed.
