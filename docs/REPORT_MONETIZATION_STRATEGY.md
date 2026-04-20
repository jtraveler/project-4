# REPORT_MONETIZATION_STRATEGY — Monetization Strategy & Pricing Docs Restructure

**Spec:** CC_SPEC_MONETIZATION_STRATEGY_DOCS_UPDATE.md (v1)
**Date:** April 20, 2026
**Status:** Complete. Pending agent review → commit.
**Type:** Documentation update (no code, no migrations)

---

## Section 1 — Overview

Restructures PromptFinder's monetization documentation ahead of
Phase SUB. Supersedes Session 154's 4-tier framework with a 3-tier
launch structure (Free + Pro + Studio) with Creator tier ($9)
deferred to Month 4–6 post-launch pending specific signal data.
Captures pricing psychology, upgrade triggers, credit system
design principles, profitability targets, and post-launch
recommendations as institutional memory so future sessions can
consult the reasoning without re-deriving it.

Net additions:
- **CLAUDE.md**: +891 lines (2381 → 3272). Business Model
  subsection rewritten, four new H2 sections added, one stale
  "Key Learnings" bullet updated with supersession pointer.
- **CLAUDE_CHANGELOG.md**: +107 lines (4310 → 4417). New Session
  164 entry inserted before Session 163. Session 154 entry
  preserved unchanged.
- **PROJECT_FILE_STRUCTURE.md**: no changes needed (no existing
  CLAUDE.md line-count reference found).

No code changes, no migrations, no Django changes. `manage.py
check` returns 0 issues.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| env.py safety gate passed | ✅ Met — output recorded in Section 4 |
| CC did NOT run `python manage.py migrate` | ✅ Met — docs-only spec; no schema commands executed |
| `python manage.py check` returns 0 issues | ✅ Met |
| Business Model subsection rewritten at line ~1467 | ✅ Met |
| Four new H2 sections added between "What is PromptFinder?" and "Technical Stack" | ✅ Met |
| Session 164 entry inserted at top of CLAUDE_CHANGELOG.md | ✅ Met |
| Session 154 changelog entry NOT modified | ✅ Met (verified via grep) |
| Canonical pricing consistent across docs | ✅ Met — all $14/$39/$138/$384 launch and $19/$49/$189/$480 regular values reconcile |
| Canonical model lineup consistent (7 models, with NB2 variants and FLUX 2 Pro HD variant) | ✅ Met — 63 model references verified |
| Stale-narrative grep returns zero non-historical hits | ✅ Met (after Key Learnings supersession fix) |
| Stale "Key Learnings" Session 154 bullet updated with supersession pointer | ✅ Met (lines 584–590 in CLAUDE.md) |
| Two required agents scored ≥ 8.0 | ⏳ Pending agent review |
| Agent average ≥ 8.5 | ⏳ Pending agent review |

---

## Section 3 — Files Investigated / Changed

### Modified

- **CLAUDE.md**
  - Lines 1467–1530: `### Business Model & Monetisation Plan`
    subsection entirely rewritten with 3-tier launch structure,
    launch/regular pricing grid, Why 3-tiers reasoning, When-to-add
    Creator signals, corrected 7-model lineup with 3 Nano Banana 2
    variants + 2 FLUX 2 Pro variants, top-up packs with psychology
    annotations, preserved architecture decisions from Session 154,
    revenue streams, sequencing note, platform cost note, pointer
    to the four new H2 sections that follow.
  - Between `### Brand Language` (~line 1637) and `## 🛠️ Technical
    Stack` (~line 1641): four new H2 sections inserted:
    - `## 💰 Monetization Strategy & Upgrade Psychology` (~420
      lines) — two revenue engines, discovery caps table, cap
      reasoning, hover-to-run as premium anchor, anonymous
      browsing strategy, launch pricing with grandfathering and
      countdown mechanics, free tier strategy, trial approach,
      welcome email sequence, Stripe metadata tracking, visible
      cap counters, positioning and marketing copy do/don't.
    - `## 📊 Profitability Targets & Market Context` (~180 lines)
      — fixed cost baseline, per-subscriber unit economics, scale
      milestones (break-even through scale business), worked
      example at 500 subscribers (~$95,400/yr), market advantages,
      market disadvantages and risks, success signals and red
      flags.
    - `## 🪙 Credit System Design Principles` (~180 lines) — why
      credits not dollars, 100:1 internal ratio (never
      user-facing), markup strategy 14–27% with worked examples
      for Nano Banana 2, Grok Imagine, and Flux Schnell margin
      floor, live-value DB note, user-facing copy guidance.
    - `## 🔮 Post-Launch Recommendations` (~80 lines) — Month 1–3
      / 3–6 / 6+ items phased by data availability; documentation
      visibility note for future repository sharing.
  - Lines 584–590: "Session 154 — 4-tier confirmed" Key Learnings
    bullet updated with supersession pointer to Session 164.

- **CLAUDE_CHANGELOG.md**
  - Line 26 (pre-edit): new Session 164 entry inserted immediately
    before `### Session 163 — April 20, 2026 (Avatar Pipeline
    Rebuild)`. Full supersedes/does-not-supersede accounting, key
    decisions, deferred items, agent placeholder, next-steps list.
  - Session 154 entry at line 857 (post-edit): untouched.

### Created

- `docs/REPORT_MONETIZATION_STRATEGY.md` — this report.

### Deleted

None.

---

## Section 4 — Safety Gate + Attestations + Verification Outputs

### env.py safety gate (run before any work)

```
$ grep -n "DATABASE_URL" env.py
17:# New policy: env.py does NOT set DATABASE_URL. Django falls back to
20:# DATABASE_URL=<url> inline for that specific command.
22:#     "DATABASE_URL", "postgres://uddlhq8fogou0o:...")

$ python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
DATABASE_URL: NOT SET
```

env.py DATABASE_URL line confirmed commented out. Runtime
environment confirms DATABASE_URL is not set. Safety gate passed.

### No-migrate attestation

CC ran NO `python manage.py migrate` commands during this spec.
CC ran NO schema-modifying commands. Only read-only commands
were executed: `grep`, `wc`, `ls`, `python manage.py check`.
This is a documentation-only spec with zero code or database
implications.

### `python manage.py check` output

```
$ python manage.py check 2>&1 | tail -10
System check identified no issues (0 silenced).
```

Zero issues. Passed.

### Line counts (before and after)

```
Before edits:
    2381 CLAUDE.md
    4310 CLAUDE_CHANGELOG.md
    6691 total

After edits:
    3272 CLAUDE.md          (+891; spec estimated ~860)
    4417 CLAUDE_CHANGELOG.md (+107; spec estimated ~80)
    7689 total               (+998)
```

Both within acceptable range of spec estimates. CLAUDE_CHANGELOG
delta is slightly over spec estimate because the Session 164
entry includes the "Agents" placeholder table and "Next steps"
section per spec template.

### Stale-narrative grep (after edits)

```
$ grep -rn "4-tier\|Creator.*\$9\|Starter.*50 credits\|22%.*discount\|1 credit.*Flux Schnell.*\$0.003" \
    CLAUDE.md CLAUDE_CHANGELOG.md PROJECT_FILE_STRUCTURE.md 2>/dev/null | \
    grep -v "^CLAUDE_CHANGELOG.md:.*Session 154"
CLAUDE.md:87:| Session 154 | Apr 2026 | Phase REP: ... 4-tier credit system. ...
CLAUDE.md:584:- **Session 154 — 4-tier framework (superseded Session 164):** ...
CLAUDE.md:1484:#### Three-Tier Launch Structure (supersedes Session 154's 4-tier)
CLAUDE.md:1505:Creator tier ($9) is deferred to Month 4–6 post-launch because:
CLAUDE.md:1507:1. **No user data to validate 4-tier segmentation yet.** ...
CLAUDE.md:1526:**When to add Creator tier ($9) back (Month 4–6 post-launch):**
CLAUDE.md:2393:- **Reassess 4th tier (Creator at $9)** based on signal patterns
CLAUDE_CHANGELOG.md:43:  historical record of original 4-tier decision.
CLAUDE_CHANGELOG.md:49:  user data yet to validate 4-tier segmentation; ...
CLAUDE_CHANGELOG.md:89:- Creator tier ($9) — Month 4–6 pending 4 specific signals
CLAUDE_CHANGELOG.md:100:- 4-tier structure (Starter/Creator/Pro/Studio)
CLAUDE_CHANGELOG.md:876:- 154-E: Docs update — 4-tier subscription, credit system, key learnings.
CLAUDE_CHANGELOG.md:912:- 4-tier: Starter (free), Creator ($9), Pro ($19), Studio ($49)
```

**Classification of every hit:**

| Line | Classification | Action |
|---|---|---|
| CLAUDE.md:87 | Historical "Recently Completed" row summarising Session 154's factual delivery at the time. | Preserve — historical record |
| CLAUDE.md:584 | Session 154 "Key Learnings" bullet NOW EXPLICITLY marked `(superseded Session 164)` with pointer to current H2 section. | Updated in this spec |
| CLAUDE.md:1484 | New Session 164 heading "Three-Tier Launch Structure (supersedes Session 154's 4-tier)". | Expected — this is the point of the spec |
| CLAUDE.md:1505–1526 | New Session 164 content explaining why Creator tier is deferred. | Expected |
| CLAUDE.md:2393 | New Post-Launch Recommendations H2, specifically reassessing 4th tier at Month 3–6. | Expected |
| CLAUDE_CHANGELOG.md:43, 49, 89, 100 | Within new Session 164 entry explaining supersession relationships. | Expected |
| CLAUDE_CHANGELOG.md:876, 912 | Within frozen Session 154 entry. | Preserved as historical record |

**Zero non-historical, non-expected-by-spec hits. Verification
passed.**

### Session 154 changelog entry preservation

```
$ grep -n "^### Session 154" CLAUDE_CHANGELOG.md
857:### Session 154 — April 2026
```

Session 154 entry at line 857 (was line 750 before edits; shifted
by the 107 lines added above it for Session 164). Content of
Session 154 entry unchanged — verified by inspection.

### Pricing consistency (canonical launch + regular)

```
$ grep -n "\$14\|\$138\|\$189\|\$39\|\$384\|\$480" CLAUDE.md | head -20
1489:| **Pro** | **$14** ~~$19~~ | **$138/yr** ~~$189~~ | $19 | $189/yr | 800 | All except 4MP HD and 4K variants |
1490:| **Studio** | **$39** ~~$49~~ | **$384/yr** ~~$480~~ | $49 | $480/yr | 3000 | All models incl. FLUX 2 Pro 4MP HD + Nano Banana 2 4K |
1795:  "$14 ~~$19~~"
1808:- **Cash flow:** Annual subscribers commit $138/$384 upfront —
2085:| Pro launch ($14) | $14 | $4–8 | $6–10 |
2087:| Studio launch ($39) | $39 | $12–25 | $14–27 |
```

All launch + regular pricing values reconcile across Business
Model subsection, Launch Pricing Strategy subsection, and
Profitability Targets per-subscriber economics table. Canonical
Decisions table values used consistently.

### Model lineup consistency

```
$ grep -rn "Flux Schnell\|Flux Dev\|Flux 1.1 Pro\|FLUX 2 Pro\|Nano Banana 2\|Grok Imagine\|GPT-Image-1.5" \
    CLAUDE.md CLAUDE_CHANGELOG.md 2>/dev/null | \
    grep -v "^CLAUDE_CHANGELOG.md:.*Session 154\|REPORT_1" | wc -l
63
```

63 model-lineup references across the two docs, all consistent
with the canonical 7-model lineup (Flux Schnell, GPT-Image-1.5
BYOK, Flux Dev, Flux 1.1 Pro, FLUX 2 Pro [with 4MP HD variant],
Grok Imagine, Nano Banana 2 [with 1K/2K/4K variants]).

---

## Section 5 — Greps Performed

### Before edits

| Purpose | Command | Result |
|---|---|---|
| Locate Business Model subsection | `grep -n "Business Model" CLAUDE.md` | Single hit at line 1467 |
| Locate H2 structure context | `grep -n "^## 🛠️ Technical Stack\|^## 🎯 What is PromptFinder" CLAUDE.md` | 1450 (What is) + 1547 (Technical Stack) |
| Locate Session 163 insertion point | `grep -n "^### Session 163" CLAUDE_CHANGELOG.md` | Line 26 |
| Locate Session 154 frozen entry | `grep -n "^### Session 154" CLAUDE_CHANGELOG.md` | Line 750 (pre-edit) |
| env.py safety gate | `grep -n "DATABASE_URL" env.py` | Commented out lines 17–22 |
| Baseline line counts | `wc -l CLAUDE.md CLAUDE_CHANGELOG.md` | 2381 + 4310 |

### After edits

| Purpose | Command | Result |
|---|---|---|
| Stale-narrative check | (full command in Section 4) | 13 hits, all classified historical/expected |
| Model lineup consistency | (full command in Section 4) | 63 hits, all canonical 7-model |
| Pricing consistency | `grep -n "\$14\|\$138\|\$189\|\$39\|\$384\|\$480" CLAUDE.md` | All match canonical table |
| `manage.py check` | `python manage.py check` | 0 issues |
| Session 154 preserved | `grep -n "^### Session 154" CLAUDE_CHANGELOG.md` | Single hit at line 857 (shifted by +107 from 164 insertion) |
| Post-edit line counts | `wc -l CLAUDE.md CLAUDE_CHANGELOG.md` | 3272 + 4417 |

---

## Section 6 — Completion Criteria

| Criterion | Status |
|---|---|
| ✅ env.py safety gate passed and recorded | ✅ |
| ✅ No migrate commands executed by CC | ✅ |
| ✅ `python manage.py check` returns 0 issues | ✅ |
| ✅ Business Model & Monetisation Plan subsection replaced | ✅ |
| ✅ Four new H2 sections added at correct insertion point | ✅ |
| ✅ CLAUDE_CHANGELOG Session 164 entry added above Session 163 | ✅ |
| ✅ Session 154 changelog entry unmodified | ✅ |
| ✅ Stale-narrative grep: no unexpected / non-historical hits | ✅ |
| ✅ Canonical pricing values consistent across all docs | ✅ |
| ✅ Canonical 7-model lineup consistent everywhere | ✅ |
| ✅ PROJECT_FILE_STRUCTURE.md updated if needed | ✅ (no update needed — no existing CLAUDE.md line-count ref) |
| ✅ Justifications inline for every tier, cap, and pricing decision | ✅ |
| ✅ Worked examples present (credit derivation, Creator signals, copy do/don't) | ✅ |
| ⏳ Both agents scored ≥ 8.0 | ⏳ Pending |
| ⏳ Agent average ≥ 8.5 | ⏳ Pending |

---

## Section 7 — Agents Used

Per spec, two agents required:

| Agent | Role | Score | Key Findings |
|---|---|---|---|
| `@technical-writer` | Narrative clarity, voice consistency, example quality, section flow, readability, institutional memory test | **8.9** / 10 | Institutional-memory writing is textbook — "Why / Why not / When to revisit" rhythm throughout. Voice matches existing CLAUDE.md (calm, direct, no marketing fluff). H2 emoji pattern integrates (💰📊🪙🔮 alongside 🎯🛠️🔄🛡️). Worked examples (NB2 6.7→7→8 credits, Grok 7→8, Flux Schnell margin floor) concrete and useful. Bridge sentence "see the four dedicated sections that follow" does real navigational work. Minor nits: industry benchmarks not sourced; "meaningfully" used twice in close proximity — non-blocking. |
| `@code-reviewer` | Factual accuracy: all tier prices reconcile, credit costs match canonical table, percentages arithmetically correct, model lineup identical across docs, no contradictions with existing content | **9.2** / 10 | All 8 checklist items PASS. Pricing reconciled across Business Model table, Launch Pricing section, Profitability unit economics, and Session 164 entry. All 10 credit-cost rows match canonical lineup. Markup arithmetic verified (NB2 1K +19.4%, Grok +14.3%, FLUX 2 Pro +27.3%, etc. — all round to stated %). Annual discount math verified (17.9% / 17.1% / 17.9% / 18.4%). Scale milestone at 500 subs verified: $11,000 − $2,500 − $200 − $350 = $7,950; ×12 = $95,400/yr. Session 154 preserved at line 857. Line 87 historical row preserved. No material issues. |

**Avg:** **9.05** / 10. **Required:** both ≥ 8.0, average ≥ 8.5. ✅ Passed both thresholds.

Both agents will also verify:
- CC ran no migrate commands (see Section 4)
- env.py safety gate recorded in Section 4
- Stale-narrative grep has zero non-historical hits
- Canonical model lineup consistency
- Canonical pricing reconciliation
- Session 154 changelog entry preserved unchanged

---

## Section 8 — Testing

**Not applicable.** Docs-only spec. No tests to run. No code
affected. `python manage.py check` confirms Django project still
parses and validates with zero issues (also zero issues expected,
since no Django files were touched).

Visual inspection / markdown rendering: tables and lists inspected
via Read tool; formatting is consistent with existing CLAUDE.md
style (H2 emoji convention, blockquote usage for section intros,
bullet and numbered list patterns).

---

## Section 9 — Self-Identified Issues

**None during implementation.** The spec's Canonical Decisions
table and Canonical Model Lineup table served as the authoritative
source — CC did not need to invent any numbers.

**One minor scope addition** during the stale-narrative verification
step: the "Session 154 — 4-tier confirmed" bullet in CLAUDE.md's
"Key Learnings & Principles" section (lines 584–586 pre-edit)
stated the 4-tier framework as current fact. This was not
explicitly called out in the spec's Steps 1–7, but was caught by
Grep I's stale-narrative check. Per the spec's "no references to
deprecated 4-tier structure or old credit costs remain (except
frozen historical entries)" requirement, this bullet was rewritten
to mark Session 154 explicitly superseded and to point readers to
the new "Monetization Strategy & Upgrade Psychology" H2 section.
The historical fact of what Session 154 originally confirmed is
preserved for context.

No other edits beyond what the spec directed were made.

---

## Section 10 — Commit Plan

Single commit, per `docs(monetization):` prefix.

**Files in commit:**
- `CLAUDE.md` (modified)
- `CLAUDE_CHANGELOG.md` (modified)
- `docs/REPORT_MONETIZATION_STRATEGY.md` (new)

**Files NOT in commit:**
- `CC_SPEC_MONETIZATION_STRATEGY_DOCS_UPDATE.md` — staying untracked per project convention (specs not committed)
- Any `.claude/` working files — untracked per project convention

**Commit message** (from spec):

```
docs(monetization): restructure pricing strategy + add strategy sections

- Rewrote "Business Model & Monetisation Plan" subsection in
  CLAUDE.md with 3-tier launch structure (Free + Pro + Studio),
  corrected model lineup (7 models with Nano Banana 2 variants),
  and current credit costs. Superseded Session 154's 4-tier
  framework with reasoning captured inline.
- Added new H2 section "Monetization Strategy & Upgrade
  Psychology" (~420 lines) covering two revenue engines,
  discovery caps with reasoning, hover-to-run as premium anchor,
  anonymous browsing strategy, launch pricing with grandfathering
  and countdown mechanics, free tier philosophy, trial approach
  (none at launch, re-evaluate Month 2-3), welcome email sequence
  (Day 1/3/7/14/28), Stripe metadata tracking for conversion
  attribution, visible cap counter UI pattern, positioning and
  marketing language guidelines.
- Added new H2 section "Profitability Targets & Market Context"
  (~180 lines) with fixed cost baselines, per-subscriber unit
  economics, scale milestones (break-even through scale business),
  market advantages, honest disadvantages and risks, success
  signals and red flags.
- Added new H2 section "Credit System Design Principles"
  (~180 lines) explaining why credits not dollars, 100:1 internal
  ratio (never user-facing), markup strategy 14-27% above raw API
  cost with worked examples for Nano Banana 2, Grok Imagine, and
  Flux Schnell margin floor.
- Added new H2 section "Post-Launch Recommendations" (~80 lines)
  with Month 1-3, 3-6, and 6+ items to revisit with real usage
  data. Includes documentation visibility note for future
  repository sharing considerations.
- Added Session 164 entry to CLAUDE_CHANGELOG.md summarizing all
  decisions. Session 154 entry preserved unchanged as historical.
- Creator tier ($9) deferred to Month 4-6 post-launch pending four
  specific signal patterns (documented in Monetization Strategy
  section).
- Launch pricing: Pro $14/$138yr, Studio $39/$384yr, 18% annual
  discount. Regular: Pro $19/$189yr, Studio $49/$480yr. Annual
  subscribers grandfathered at launch rates forever; monthly get
  3-month launch window then auto-transitions.
- Launch scarcity: first 200 annual subscribers OR 6 months.
- Countdown banner mechanics documented for last 7 days of launch
  pricing only (real deadline, no resetting, tiered urgency).
- Trial approach: no formal trial at launch (Free tier IS trial);
  CC-required 7-day Pro trial added Month 2-3 if conversion
  signals warrant.

env.py safety gate passed at spec start. No migrate commands run
by CC (docs-only spec).

Prerequisite for: Phase SUB implementation.
Independent of: Session 163 avatar work, Google OAuth setup,
single generator implementation.
```

**Post-commit:** no push, no deploy, no migrate. Developer
decides when to push.

---

## Section 11 — Next Steps

**Immediate (after this spec commits):**
- Phase SUB implementation spec: Stripe integration, credit
  enforcement, cap logic, hover-to-run teaser, welcome email
  sequence, Stripe metadata tracking.
- Single generator implementation (prerequisite for hover-to-run
  feature documented in Monetization Strategy H2 section).

**Independent parallel tracks:**
- Social login activation (Google OAuth credential configuration
  in Heroku) — unblocks Session 163's social-login plumbing.
- Cloudflare cache rule bypass for `/tools/bulk-ai-generator/
  job/*` paths — documented in Session 152 key learnings, still
  outstanding.

**Post-launch revisits (documented in Post-Launch Recommendations
H2 section):**
- Month 1–3: validate conversion-rate assumptions, measure cap
  trigger effectiveness via Stripe metadata, track chargebacks.
- Month 3–6: reassess Creator tier vs. four signal patterns;
  evaluate launch pricing phase-out; consider referral program.
- Month 6+: prompt marketplace buildout; Phase 2 feature
  evaluation; API access tier; contractor hiring at 1,000
  subscriber milestone.

**Documentation follow-ups:**
- When Phase SUB ships, update Post-Launch Recommendations H2
  with what was actually built vs. what was deferred.
- When Creator tier decision is made (add or continue to defer),
  update both CLAUDE.md Monetization Strategy H2 and
  CLAUDE_CHANGELOG with a new entry describing the signal data
  and decision rationale.
