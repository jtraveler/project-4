# CC_SPEC_160_F_CLOUDINARY_MIGRATION.md
# Cloudinary → B2 Migration Management Command

**Spec Version:** 1.0
**Session:** 160
**Type:** Data Migration — management command only. Does NOT run automatically.
**Modifies UI/Templates:** No
**Migration Required:** No (Django migration not needed — field types unchanged)
**Agents Required:** 6 minimum

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2**
2. **Read `CC_REPORT_STANDARD.md`**
3. **This spec creates a management command only** — it does NOT run it.
   Developer runs it manually on Heroku after reviewing the output.
4. **This spec does NOT remove any Cloudinary code** — that is a future
   session after migration is confirmed working.
5. **Dry-run mode required** — command must support `--dry-run` flag that
   shows what would be migrated without making any changes.
6. **Cloudinary credentials confirmed:**
   - Cloud name: `dj0uufabo` (NOT `dj0uufabot` — old typo caused 404s)
   - Full URL: `cloudinary://469865711261693:lf5svAbaVI4C6807OU7KIYJas2U@dj0uufabo`
7. **Both images and videos** are on Cloudinary and must be migrated.

---

## 📋 CONTEXT

36 prompts have Cloudinary images in `featured_image` field.
Some prompts also have videos in `featured_video` field.
All stored as short Cloudinary public IDs (e.g. `813f07cc-da00-48a0-b2db-46d8e75e08bd_tfbn7j`).
The Cloudinary template tag builds the full URL at render time.

After this migration:
- `b2_image_url` will be populated for all migrated prompts
- `featured_image` field will still contain the Cloudinary ID (unchanged until
  field type migration in a future session)
- Prompts will display via B2 rather than Cloudinary

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Find existing management commands structure
ls prompts/management/commands/

# 2. Find the B2 upload service/utility used elsewhere in the codebase
grep -rn "b2.*upload\|upload.*b2\|B2Storage\|b2_upload" \
    prompts/services/ prompts/management/ --include="*.py" | head -20

# 3. Find how B2 URLs are structured (to build correct URLs after upload)
grep -n "B2_CUSTOM_DOMAIN\|b2_image_url\|media.promptfinder" \
    prompts/models.py prompts_manager/settings.py | head -10

# 4. Find Cloudinary URL construction (how template tag builds URLs)
grep -rn "cloudinary_url\|CloudinaryImage\|build_url\|res.cloudinary" \
    prompts/ --include="*.py" --include="*.html" | head -20

# 5. Find all fields that may contain Cloudinary data
grep -n "CloudinaryField\|featured_image\|featured_video\|avatar" \
    prompts/models.py | head -15

# 6. Find UserProfile model for avatar field
grep -n -A 5 "class UserProfile\|avatar" prompts/models.py | head -20

# 7. Check what b2_image_url, b2_thumb_url etc. fields exist on Prompt
grep -n "b2_.*url\|b2.*field" prompts/models.py | head -20
```

---

## 📁 STEP 1 — Create the management command

Create: `prompts/management/commands/migrate_cloudinary_to_b2.py`

```python
"""
Management command to migrate Cloudinary images and videos to Backblaze B2.

Usage:
    python manage.py migrate_cloudinary_to_b2 --dry-run
    python manage.py migrate_cloudinary_to_b2
    python manage.py migrate_cloudinary_to_b2 --model Prompt
    python manage.py migrate_cloudinary_to_b2 --model UserProfile
"""
```

**Command must:**

1. **Accept `--dry-run` flag** — show what would be migrated, make no changes
2. **Accept `--model` flag** — `Prompt` or `UserProfile` or `all` (default: all)
3. **Accept `--limit N` flag** — process only N records (for testing)
4. **For each Prompt with `featured_image` containing a Cloudinary public ID:**
   - Build the full Cloudinary URL:
     `https://res.cloudinary.com/dj0uufabo/image/upload/{public_id}.jpg`
     (try `.jpg` first, then `.png` if 404)
   - Download the image using `requests` with timeout=30
   - Upload to B2 using existing B2 upload utility
   - Update `b2_image_url` (and `b2_thumb_url`, `b2_large_url` if applicable)
   - Log success: `Migrated prompt {id}: {cloudinary_id} → {b2_url}`
5. **For each Prompt with `featured_video`** containing a Cloudinary public ID:
   - Build Cloudinary video URL:
     `https://res.cloudinary.com/dj0uufabo/video/upload/{public_id}`
   - Download and upload to B2
   - Update `b2_video_url`
6. **For each UserProfile with `avatar`** containing a Cloudinary public ID:
   - Same download → B2 upload flow
   - Update the avatar B2 field (confirm field name from Step 0)
7. **Progress tracking:** print progress every 10 records
8. **Error handling:** on per-record failure, log error and continue (don't abort)
9. **Summary at end:** total processed, succeeded, failed, skipped (already B2)

**B2 key prefix for migrated files:** `migrated/{model}/{id}/`
to distinguish from fresh uploads.

---

## 📁 STEP 2 — MANDATORY VERIFICATION

```bash
# 1. Confirm command file created
ls prompts/management/commands/migrate_cloudinary_to_b2.py

# 2. Confirm --dry-run flag exists
grep -n "dry.run\|dry_run" \
    prompts/management/commands/migrate_cloudinary_to_b2.py | head -5

# 3. Django check — confirms command is syntactically valid
python manage.py check

# 4. Confirm command appears in help
python manage.py help | grep migrate

# 5. Run syntax check only (no actual migration)
python manage.py migrate_cloudinary_to_b2 --help
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Command file created at correct path ✓
- [ ] `--dry-run` flag shows plan without making changes ✓
- [ ] `--limit N` flag for safe testing ✓
- [ ] Correct Cloudinary cloud name `dj0uufabo` (not `dj0uufabot`) ✓
- [ ] Both images AND videos handled ✓
- [ ] UserProfile avatars handled ✓
- [ ] Per-record error handling (continues on failure) ✓
- [ ] Summary output at end ✓
- [ ] Uses existing B2 upload utility (not raw boto3 calls) ✓
- [ ] `python manage.py check` passes ✓

---

## 🤖 AGENT REQUIREMENTS

**Minimum 6 agents. Average 8.5+. All must score 8.0+.**

### 1. @backend-security-coder
- Is downloading from Cloudinary URLs safe? SSRF risk?
  (Cloudinary URLs are trusted — `res.cloudinary.com` is a known safe domain)
- Are any credentials logged accidentally?
- Rating: 8.0+/10

### 2. @django-pro
- Is the management command structure correct (BaseCommand, add_arguments)?
- Does it handle database transactions correctly per record?
- Rating: 8.0+/10

### 3. @python-pro
- Is the download → upload flow efficient? Memory usage for large videos?
  (Stream download for videos rather than loading into memory)
- Rating: 8.0+/10

### 4. @code-reviewer
- Is the dry-run mode complete — does it truly make no changes?
- Is the progress logging useful for a 36-record + videos migration?
- Rating: 8.0+/10

### 5. @tdd-orchestrator
- Should there be a test for the management command?
- At minimum, a test that `--dry-run` makes no DB changes.
- Rating: 8.0+/10

### 6. @architect-review
- Is the B2 key prefix `migrated/{model}/{id}/` the right structure?
- Should the command be idempotent (safe to run twice)?
  Yes — check if `b2_image_url` already populated before re-migrating.
- Rating: 8.0+/10

### ⛔ MINIMUM REJECTION CRITERIA
- Wrong cloud name (`dj0uufabot` instead of `dj0uufabo`)
- No `--dry-run` flag
- Command aborts on first error (must continue and log)
- Videos not handled
- `python manage.py check` fails

---

## 🧪 TESTING (Developer runs manually on Heroku)

```bash
# Step 1: Dry run first — see what would be migrated
heroku run "python manage.py migrate_cloudinary_to_b2 --dry-run" \
    --app mj-project-4

# Step 2: Test with just 3 records
heroku run "python manage.py migrate_cloudinary_to_b2 --limit 3" \
    --app mj-project-4

# Step 3: Verify those 3 records now have B2 URLs and images load
# (Check site — the 3 migrated prompts should show images)

# Step 4: Run full migration
heroku run "python manage.py migrate_cloudinary_to_b2" \
    --app mj-project-4

# Step 5: Verify all 36 prompts now display correctly
```

---

## 💾 COMMIT MESSAGE

```
feat(migration): Cloudinary → B2 migration management command

- migrate_cloudinary_to_b2 command for images, videos, avatars
- --dry-run flag (safe preview), --limit N (test batches)
- Idempotent: skips records already on B2
- Per-record error handling with summary output
- Cloud name: dj0uufabo (corrected from old typo dj0uufabot)

Agents: 6 agents, avg X/10, all passed 8.0+ threshold
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_160_F.md`

---

**END OF SPEC**
