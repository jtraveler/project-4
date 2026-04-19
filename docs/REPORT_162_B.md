# REPORT_162_B — Avatar Templates B2-First

**Spec:** CC_SPEC_162_B_AVATAR_TEMPLATES_B2_FIRST.md
**Date:** April 19, 2026
**Status:** Partial (Sections 1–8, 11). Sections 9–10 filled after full suite.

---

## Section 1 — Overview

Before this spec, six avatar-rendering templates all dereferenced
`userprofile.avatar.url` (the Cloudinary CloudinaryField) directly. When
Session 161-E added `UserProfile.b2_avatar_url` and the migration
command's `_migrate_avatar()` method, zero templates read from the new
field — meaning even after a successful avatar migration run, no
visible UI would change.

The three-branch B2-first pattern (`b2_avatar_url` → Cloudinary
`avatar.url` → letter placeholder) prepares the rendering layer so
that when Session 163 F1 switches the avatar upload pipeline to B2,
avatars render from B2 from day one. Priority P1 because the spec is
a prerequisite for F1's visibility validation.

`edit_profile.html` was explicitly excluded — it uses the
`{% cloudinary %}` server-side face-crop transform that has no direct
B2 equivalent until the upload pipeline switch. Reserved for Session
164 F2.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| 6 files updated with three-branch pattern | ✅ Met |
| Surrounding markup (classes, width/height/alt/loading) preserved | ✅ Met |
| Letter-placeholder fallback intact | ✅ Met |
| `edit_profile.html` NOT modified | ✅ Met — verified via `git diff --stat` (0 lines) AND positive-negative test assertion |
| `python manage.py check` clean | ✅ Met |
| No new N+1 queries | ✅ Met — `b2_avatar_url` shares the same UserProfile row as `avatar`, already prefetched by view-level `select_related('user__userprofile')` |
| 18 tests (3 scenarios × 6 files) | ✅ Exceeded — 23 tests (7 structure + 16 render) |
| Real ORM instances, no SimpleNamespace | ✅ Met — `User.objects.create_user()` + `refresh_from_db()` |

## Section 3 — Changes Made

### 6 avatar templates (core scope)

Each file received a three-branch `{% if X.b2_avatar_url %} ... {% elif
X.avatar and X.avatar.url %} ... {% else %} letter placeholder {% endif %}`
pattern. The new B2 `<img>` branch copies the existing Cloudinary
branch's attributes verbatim (class, width, height, alt, loading,
onerror), differing only in the `src`. Placeholder `<div>`s match
existing surrounding styling.

- `prompts/templates/prompts/notifications.html` (~lines 80–115) —
  traversal: `notification.sender.userprofile`.
- `prompts/templates/prompts/partials/_notification_list.html`
  (~lines 16–40) — same traversal as notifications.html.
- `prompts/templates/prompts/user_profile.html` (~lines 589–618) —
  traversal: `profile`.
- `prompts/templates/prompts/collections_profile.html` (~lines 352–374)
  — same traversal.
- `prompts/templates/prompts/leaderboard.html` (~lines 95–123) —
  traversal: `creator.userprofile`.
- `prompts/templates/prompts/prompt_detail.html` (~lines 339–358) —
  traversal: `prompt.author.userprofile`.

### Cross-Spec Absorption (Session 162 Rule 2)

`@django-pro` and `@architect-review` flagged that
`user_profile.html` and `collections_profile.html` used `{% elif
profile.avatar.url %}` without the `profile.avatar and` double-guard
that the other four templates use. This was pre-existing but
architecturally inconsistent — a future change to field semantics
could make `.url` raise on an empty CloudinaryField. Both templates
updated in the same commit to:

```django
{% elif profile.avatar and profile.avatar.url %}
```

This absorption matches Session 162 Rule 2 criteria exactly: 2 lines
total, same files the spec was editing, related defensive consistency
with the other 4 templates, no new test scaffolding needed.

### prompts/tests/test_avatar_templates_b2_first.py (NEW, ~440 lines)

Two test classes, 23 tests:

- `AvatarTemplateB2FirstStructureTests` (7 tests) — reads each template
  file as text, asserts: b2 branch present, elif Cloudinary branch
  present with correct `avatar and avatar.url` double-guard, old
  standalone `{% if ... avatar.url %}` pattern gone (negative
  assertion per CC_SPEC_TEMPLATE #9), ordering proof via
  `assertLess(idx_b2, idx_cloudinary)` in all six file tests. One test
  confirms `edit_profile.html` has zero `b2_avatar_url` references.
- `AvatarTemplateB2FirstRenderTests` (16 tests) — builds minimal
  `Template(source)` objects mirroring each file's avatar block,
  renders with 3 synthetic scenarios per block (B2 set / Cloudinary
  only / neither). Paired positive+negative assertions throughout.
  Uses real `User.objects.create_user()` + `refresh_from_db()` so the
  CloudinaryField resolves to a proper `CloudinaryResource` object
  with `.url` returning a real Cloudinary URL.

## Section 4 — Issues Encountered and Resolved

**Issue:** First test run had 4 failures — the Cloudinary-fallback
tests asserted `'cloudinary.com' in output` but output showed only
the placeholder div.
**Root cause:** `CloudinaryField` values become `CloudinaryResource`
objects with a proper `.url` attribute ONLY after a `refresh_from_db()`
roundtrip. Before refresh, the field is still a plain `str`, and
`{{ avatar.url }}` in Django templates returns empty string for a
plain string, causing the elif branch to fail and the else branch
(placeholder) to fire.
**Fix applied:** Added `self.user_*.refresh_from_db()` after each
`user.userprofile.save()` in `setUp()`. Documented the quirk in the
setUp docstring.
**File:** `prompts/tests/test_avatar_templates_b2_first.py` lines
178–206.

## Section 5 — Remaining Issues

**Issue:** `prompt_detail.html`'s letter-placeholder fallback uses
`<span class="avatar-letter">` without `role="img"` or `aria-label`,
unlike notifications.html and the profile templates which use
`role="img"`.
**Recommended fix:** Add `role="img" aria-label="{{ prompt.author.
username }}'s avatar"` to the span in both `{% elif %}` and `{% else %}`
branches.
**Priority:** P3
**Reason not resolved:** Pre-existing accessibility gap, not
introduced by 162-B. Flagged by @ui-visual-validator as a follow-up.

**Issue:** `collections_profile.html` omits `width`/`height` and
`loading="lazy"` on both `<img>` branches.
**Recommended fix:** Copy the `width="120" height="120" loading="lazy"`
attributes from user_profile.html.
**Priority:** P3
**Reason not resolved:** Pre-existing CWV optimization gap, not
introduced by 162-B. Flagged by @frontend-developer as future
optimization.

## Section 6 — Concerns and Areas for Improvement

**Concern:** The three-branch pattern will produce duplication when
this is ever consolidated. Once the CloudinaryField → CharField
migration runs (future session) and the Cloudinary branch becomes
dead, each file will need an editorial pass to delete the middle
branch. A shared `{% include 'partials/_avatar.html' %}` with
`{% with %}` parameterization was considered and correctly rejected
per spec's three-branch rationale (divergent surrounding markup +
pattern is temporary scaffolding).
**Impact:** Moderate — when Cloudinary is fully removed, six files
need a coordinated update.
**Recommended action:** Track as a single cleanup spec after
`CloudinaryField` is removed from models. Grep for `{% elif ...
avatar and ... avatar.url %}` to identify all six sites.

**Concern:** @django-pro and @tdd-orchestrator noted that the spec
target was "18 tests (3 scenarios × 6 files)." Delivered 23 tests
exceeded the target. Most of the overshoot is defensive — structure
tests guarantee file state; render tests guarantee behaviour. Not a
problem, but worth a self-awareness note.
**Impact:** None.
**Recommended action:** None.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 9.2/10 | Three-branch ordering correct, img attributes preserved, DOM adjacency for onerror handlers preserved. Noted pre-existing CWV gap in collections_profile | Noted in Section 5 |
| 1 | @code-reviewer | 9.0/10 | Per-file traversal correct, diff minimal, `edit_profile.html` exclusion verified. Nits: unused `_extract_avatar_block` helper; inconsistent `count` vs `find` in profile structure tests; collections_profile shared traversal comment could be explicit | Yes — helper removed; profile structure tests rewritten with explicit `find` ordering + paired negative assertion; collections tests added for all 3 scenarios |
| 1 | @django-pro | 8.1/10 | `b2_avatar_url` URLField default='' guarantees safe `{% if %}`. Four templates correctly use `avatar and avatar.url` double-guard; two profile templates missing it — architecturally inconsistent | Yes — absorbed via Rule 2. Both profile templates now use double-guard. PROFILE_BLOCK test template updated to match. |
| 1 | @tdd-orchestrator | 8.6/10 | Coverage meets spec intent, ordering assertion strong. Gaps: `assertNotIn` missing on profile structure tests; ordering `assertLess` only on notifications; unused helper | Yes — profile structure tests gained both the `assertNotIn` and `assertLess` checks; ordering checks added to all 5 templates that were missing them; unused helper removed |
| 1 | @ui-visual-validator | 9.2/10 | Alt text preserved, WCAG contrast maintained, DOM adjacency correct. Pre-existing gap noted: prompt_detail.html `<span>` lacks `role="img"` | Noted in Section 5 |
| 1 | @architect-review | 8.8/10 | Three-branch pattern correct given temporality and per-file markup divergence. `edit_profile.html` exclusion rationale sound. Flagged collections_profile double-guard inconsistency | Yes — absorbed via Rule 2 |
| **Average** | | **8.82/10** | | **Pass** ≥ 8.0 |

No agent scored below 8.0 on first pass — no mandatory re-run. Fixable
findings were addressed in-session to improve consistency and close
paired-assertion gaps.

## Section 8 — Recommended Additional Agents

All required agents ran (the frontend substitution of `@django-pro`
per CC_COMMUNICATION_PROTOCOL for UI-heavy specs was explicitly
overridden by the spec's listed agent set, which kept @django-pro).
The six-agent baseline covered ORM semantics, code quality, Python
idiom, TDD, visual/a11y, and architecture. No additional agents
would have added material value.

## Section 9 — How to Test

### Automated

```bash
python manage.py test prompts.tests.test_avatar_templates_b2_first --verbosity=2
# Expected: 23 tests (7 structure + 16 render), 0 failures.

python manage.py test prompts --verbosity=1
# Expected (session 162a final state): 1316 tests passing, 12 skipped.

python manage.py check
# Expected: 0 issues.
```

### Structure verification

```bash
# B2 branch present in each of 6 target files:
grep -c "b2_avatar_url" prompts/templates/prompts/notifications.html \
    prompts/templates/prompts/partials/_notification_list.html \
    prompts/templates/prompts/user_profile.html \
    prompts/templates/prompts/collections_profile.html \
    prompts/templates/prompts/leaderboard.html \
    prompts/templates/prompts/prompt_detail.html
# Expected: 2 per file (one `{% if %}`, one `{{ }}`).

grep -c "b2_avatar_url" prompts/templates/prompts/edit_profile.html
# Expected: 0 (explicitly out of scope).
```

### Manual browser (after Session 163 F1 ships)

After Session 163 F1 switches the avatar upload pipeline to B2:
1. Upload an avatar via `/settings/profile/`.
2. Visit any of these pages authored/acted-on by that user:
   - `/` (user_profile via profile link)
   - `/prompt/<slug>/` (prompt_detail)
   - `/leaderboard/` (leaderboard)
   - `/notifications/` (notifications)
   - `/users/<username>/collections/` (collections_profile)
3. Right-click the avatar → Inspect → confirm `src` is the B2 CDN URL,
   not a Cloudinary URL.

For the current pre-F1 state, the templates are forward-compatible —
no rendered change should occur until F1 populates `b2_avatar_url`.

## Section 10 — Commits

| Hash | Message |
|------|---------|
| ad94533 | feat(templates): avatar templates prefer b2_avatar_url over Cloudinary |

## Section 11 — What to Work on Next

1. **162-C next** — vision_moderation public_id fix. Independent of
   162-B's template work; no dependency.
2. **Session 163 F1 (the downstream work this spec unblocks)** —
   switch the `edit_profile` form + view + upload service to write
   `b2_avatar_url`. Once F1 lands, these templates will render from
   B2 with zero additional template changes.
3. **Session 164 F2 (further downstream)** — replace `edit_profile.
   html`'s `{% cloudinary %}` server-side face-crop transform with
   CSS `object-fit: cover` + a `<img>` tag consuming
   `profile.b2_avatar_url`. Depends on F1.
4. **Future cleanup spec** — when `CloudinaryField` is fully removed
   from `UserProfile`, delete the middle `{% elif ... avatar and
   ... avatar.url %}` branch from all 6 templates. Grep target:
   `{% elif.*avatar and.*avatar.url %}` returns exactly 6 sites.
5. **P3 polish (optional, deferrable)** — add `role="img" aria-label`
   to `prompt_detail.html`'s `<span class="avatar-letter">` for
   screen-reader parity; add `width="120" height="120" loading="lazy"`
   to `collections_profile.html` for CWV parity with user_profile.html.
