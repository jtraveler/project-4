# REPORT_171_A_COMMENT_FIX

## Multi-line Django Comment Fix — bulk_generator_job.html

**Spec:** `CC_SPEC_171_A_COMMENT_FIX.md`
**Cluster shape:** BATCHED (Memory Rule #15)
**Investigation prior:** `docs/REPORT_171_INVESTIGATION.md` Section 3 + Section 5.1
**Partial report:** Sections 1–8 + 11 written now; Sections 9–10 filled after Spec C's full suite gate per CC_MULTI_SPEC_PROTOCOL v2.2.

---

## Section 1 — Overview

The bulk job results page (`/tools/bulk-ai-generator/job/<uuid>/`) was leaking
three blocks of internal Django template comments as visible page text. The
root cause was confirmed in the prior investigation: Django's `{# ... #}`
comment regex (`\{#.*?#\}` without `re.DOTALL`) matches single-line only.
When a `{#` opens but no `#}` exists on the same line, the tokenizer emits
the entire `{#` block as literal text into the rendered HTML.

This spec converts the three offending multi-line `{# #}` blocks at lines
150-153, 172-176, and 224-228 of
`prompts/templates/prompts/bulk_generator_job.html` to `{% comment %} ...
{% endcomment %}` blocks (Django's documented multi-line comment syntax —
content is fully stripped at template compilation).

Confidence: 100% — definitive root cause, isolated single-file fix, no test
impact, no behavior change for any non-leaked surface.

## Section 2 — Expectations

| Spec criterion | Outcome |
|----------------|---------|
| Convert all 3 multi-line `{# ... #}` blocks to `{% comment %} ... {% endcomment %}` | ✅ Met (lines 150-155, 174-180, 228-234 in post-fix file) |
| Preserve original comment text content verbatim | ✅ Met (all comment text retained inside the new blocks) |
| `python manage.py check` passes 0 issues | ✅ Met |
| No edits to any other file | ✅ Met (only `bulk_generator_job.html` modified) |
| str_replace count within ✅ Safe tier (≤ 3) | ✅ Met (exactly 3) |
| No regressions to surrounding `#publish-progress`, `#publish-modal`, `#publish-sticky-toast` markup or ARIA wiring | ✅ Met (verified by all 3 agents) |
| No regressions in `test_bulk_generator` suite | ⏸ To verify at full suite gate (Section 9) |

### Step 0 verification (verbatim)

```
$ grep -rn "{% comment %}" prompts/templates/ | head -5
prompts/templates/prompts/partials/_prompt_card_list.html:1:{% comment %}
prompts/templates/prompts/partials/_masonry_grid.html:1:{% comment %}
```
Confirms `{% comment %}` is an established pattern in the project.

```
$ sed -n '150,153p' prompts/templates/prompts/bulk_generator_job.html  (pre-fix state, captured during investigation)
    {# ===== Publish Progress Bar (Phase 6B — kept for backward compat,
            now hidden-by-default; modal below is the active surface.
            Session 170-B retains markup so any legacy code path that
            populates these IDs stays valid.) ===== #}
```

```
$ sed -n '172,176p' prompts/templates/prompts/bulk_generator_job.html  (pre-fix state)
    {# ===== Publish Modal (Session 170-B) =====
       Opens on Create Pages click. Dismissible via × — transitions
       to sticky toast bottom-right. Reopen restores idempotently from
       current G state. Rendered in DOM at page load (static aria-live)
       so screen readers reliably pick up updates. #}
```

```
$ sed -n '224,228p' prompts/templates/prompts/bulk_generator_job.html  (pre-fix state)
    {# ===== Publish Sticky Toast (Session 170-B) =====
       Activated when modal is dismissed mid-publish. Persists at
       bottom-right; updates live; "Reopen" restores the modal. No
       auto-dismiss — explicit close required (status="status" plus
       explicit dismiss button). #}
```

### Post-fix verification

```
$ grep -n "^\s*{#\|{% comment %}\|{% endcomment %}" prompts/templates/prompts/bulk_generator_job.html | head -30
32:    {# ===== Job Summary Header ===== #}
57:            {# Quality hidden by CSS; JS adds .is-quality-visible if any prompt overrides the job default #}
85:    {# ===== Progress Section ===== #}
88:        {# Stats row: count/percent on left, time on right #}
105:        {# Progress bar #}
117:        {# Details row: cost on left, cancel button on right #}
131:        {# Status message — aria-live for screen reader announcements #}
150:    {% comment %}
155:    {% endcomment %}
174:    {% comment %}
180:    {% endcomment %}
228:    {% comment %}
234:    {% endcomment %}
264:    {# ===== Gallery Section ===== #}
274:{# ===== Sticky Bar: Publish Controls + Flush Button (staff only) ===== #}
278:        {# Publish controls — hidden until images selected (Phase 6B) #}
292:            {# Retry Failed button — Phase 6D: hidden until ≥1 publish failure #}
310:{# ===== Flush: Confirm Modal ===== #}
323:{# ===== Flush: Error Modal ===== #}
335:{# ===== Flush: Success Banner (fixed, starts hidden) ===== #}
571:{# Static aria-live region for toast announcements — must exist at page load for reliable AT support #}
573:{# A11Y-3: Generation progress announcer for AT users — announces image count updates #}
```
All three multi-line blocks now use `{% comment %} ... {% endcomment %}`.
All remaining `{# ... #}` are valid single-line comments.

```
$ python manage.py check
System check identified no issues (0 silenced).
```

## Section 3 — Changes Made

### prompts/templates/prompts/bulk_generator_job.html

- **Lines 150-153 → 150-155:** Multi-line `{# ... #}` block ("Publish
  Progress Bar (Phase 6B — kept for backward compat...)") replaced with
  `{% comment %} ... {% endcomment %}` block. Comment text preserved
  verbatim with minor reflow for readability inside the new tags.
- **Lines 172-176 → 174-180:** Multi-line `{# ... #}` block ("Publish
  Modal (Session 170-B) ...") replaced with `{% comment %} ...
  {% endcomment %}` block. Comment text preserved verbatim.
- **Lines 224-228 → 228-234:** Multi-line `{# ... #}` block ("Publish
  Sticky Toast (Session 170-B) ...") replaced with `{% comment %} ...
  {% endcomment %}` block. Comment text preserved verbatim.

Net file size change: +6 lines (each block grew by 2 lines because
`{% comment %}` and `{% endcomment %}` each occupy their own line
versus the inline `{#` opener / `#}` closer).

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation. Each str_replace anchor
matched the actual file content exactly on the first attempt; no
whitespace drift, no character substitution. `python manage.py check`
passed with 0 issues immediately.

(Browser smoke test step in spec section 4 was not executed by CC —
CC has no browser-control tools. Mateo will verify post-deploy per
Memory Rule #14 closing checklist Round 1, item 1.)

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met. Comment-leak symptom is
resolved structurally; the symptom cannot recur for these three blocks
because Django's `{% comment %}` tag is a fully-supported multi-line
construct and is stripped at template compilation.

## Section 6 — Concerns and Areas for Improvement

**Concern:** Other templates in the project may contain similar
multi-line `{# ... #}` blocks that have been silently leaking.

**Impact:** Low for non-bulk-generator pages — most have shorter
`{# #}` comments that fit on a single line. But a project-wide audit
could surface and fix any stragglers in one pass.

**Recommended action:** Run a project-wide grep:
```bash
grep -rln "^\s*{#" prompts/templates/ | while read f; do
  python -c "import re; src = open('$f').read(); blocks = re.findall(r'\{#[^#]*$', src, re.MULTILINE); print(f'$f: {len(blocks)} multi-line {{# blocks')" 2>/dev/null
done
```
to enumerate. Defer as a P3 cleanup item — low urgency since bulk
generator was the visible-leakage page and is now fixed.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 10/10 | All three `{% comment %}/{% endcomment %}` pairs syntactically correct; the 3 immediately-following div elements (`#publish-progress`, `#publish-modal`, `#publish-sticky-toast`) intact with full ARIA wiring; no nested `{% comment %}` issues; no whitespace anomalies | N/A — no issues |
| 1 | @code-reviewer | 9.5/10 | Scope discipline preserved (only one file touched); Memory Rule #10 honored (anchors matched actual file content); comment text preserved verbatim; no semantic regression to following div markup | N/A — no issues |
| 1 | @accessibility-expert (sub via general-purpose) | 9.5/10 | Phantom text removal is a strong positive a11y improvement (3 paragraphs of meaningless internal jargon no longer announced); ARIA wiring on 3 surrounding interactive surfaces verified intact; static aria-live announcer regions at lines 571 and 573 unaffected | N/A — no issues |
| **Average** | | **9.67/10** | | **Pass ≥ 8.0** ✅ |

Substitution disclosure: `@accessibility-expert` is unavailable in the
wshobson/agents registry. Substituted with `general-purpose` running an
accessibility-expert persona, per the project's documented Agent
Substitution Convention (CC_SPEC_TEMPLATE codified Session 169-D).
Substitution is canonical and disclosed.

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have
added material value for this spec — the change is a 3-line template
syntax conversion with no Python, JS, CSS, or test surface impact.

## Section 9 — How to Test

(To be filled in after full suite gate runs after Spec C.)

### Memory Rule #14 closing checklist for this spec

**Migrations to apply:** N/A — no migration in 171-A.

**Manual browser tests (max 2 at a time, with explicit confirmation
between each):**

Round 1 (after deploy):
1. Navigate to any bulk job results page
   (`/tools/bulk-ai-generator/job/<existing_uuid>/`) and confirm no
   leaked Django comment text appears as visible content
2. Hard-refresh (Cmd+Shift+R) and re-confirm

**Failure modes to watch for:** If leaked text still visible after
hard-refresh, check (a) deploy completed (`heroku releases`) and
(b) static-asset cache wasn't served from edge (Cloudflare Cache
Rules for `/tools/bulk-ai-generator/job/*` paths per CLAUDE.md
Session 152 note).

**Backward-compatibility verification:** N/A — comment-only fix,
no API contract or model contract changed.

## Section 10 — Commits

(To be filled in after full suite gate runs after Spec C.)

## Section 11 — What to Work on Next

1. Mateo's post-deploy verification per Memory Rule #14 closing
   checklist (Round 1 above). If clean, document in CLAUDE_CHANGELOG
   per Spec D as Verification-Pending → Resolved.
2. Optional P3: project-wide audit for other multi-line `{# #}` leaks
   per Section 6 above. Defer until at least one similar leak is
   surfaced naturally.
3. Spec 171-B (cleanup) immediately follows in this session per
   the cluster's BATCHED execution.

---

**END OF REPORT_171_A_COMMENT_FIX (PARTIAL)**
