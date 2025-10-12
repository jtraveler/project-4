# Cloudinary Asset Detection Management Command

## Overview

The `detect_orphaned_files` management command performs two critical checks:

1. **Orphaned Files**: Scans Cloudinary for files without database entries (waste storage)
2. **Missing Images**: Scans database for prompts with broken Cloudinary links (break UX)

## What Are Orphaned Files?

Orphaned files occur when:
- **Upload failures**: File uploaded to Cloudinary but database save failed
- **Manual deletions**: Database entry deleted but Cloudinary file remains
- **Development testing**: Test uploads that were never properly cleaned up
- **Code errors**: Exceptions during prompt creation after Cloudinary upload

## What Are Missing Images?

Missing images occur when:
- **Manual Cloudinary deletion**: Admin manually deleted files from Cloudinary dashboard
- **Cloudinary issues**: Files removed by Cloudinary (policy violation, error, etc.)
- **Data sync issues**: Database references assets that never made it to Cloudinary
- **Broken references**: Database has invalid public_ids

**Critical**: Missing images show as broken icon on homepage feed - bad UX!

## Features

- ✅ Scans all Cloudinary resources (images and videos)
- ✅ Scans database prompts for missing/broken Cloudinary references
- ✅ Compares against database records (including soft-deleted prompts)
- ✅ Supports date filtering (scan last N days or all files)
- ✅ Generates detailed two-section CSV reports
- ✅ Sends email summaries to admins with action items
- ✅ Monitors API rate limits
- ✅ Handles pagination automatically
- ✅ Detection only (does NOT delete files or prompts)
- ✅ Separate flags for targeted scans (--missing-only, --orphans-only)

## Usage

### Basic Scan (Both Checks, Last 30 Days)

```bash
python manage.py detect_orphaned_files
```

Runs both orphaned files check AND missing images check for last 30 days.

### Scan Last 7 Days

```bash
python manage.py detect_orphaned_files --days 7
```

### Scan Last 90 Days

```bash
python manage.py detect_orphaned_files --days 90
```

### Scan All Files (Entire Cloudinary Account)

```bash
python manage.py detect_orphaned_files --all
```

### Check Only Missing Images (Skip Orphaned Files)

```bash
python manage.py detect_orphaned_files --missing-only
```

**Use Case**: Quick check if any ACTIVE prompts have broken images on site.
**Performance**: Faster than full scan (no Cloudinary API calls for file listing).

### Check Only Orphaned Files (Skip Missing Images)

```bash
python manage.py detect_orphaned_files --orphans-only --days 7
```

**Use Case**: Weekly storage cleanup check without checking all prompt images.

### Custom Output Location

```bash
python manage.py detect_orphaned_files --output /tmp/asset_report.csv
```

### Less Verbose Output

```bash
python manage.py detect_orphaned_files --verbose=False
```

## Output Example

```
🔍 Starting Cloudinary Asset Detection
============================================================

Configuration:
- Scanning: Last 30 days
- Resource types: image, video
- Checks: Orphaned Files + Missing Images
- Started: 2025-10-13 01:00:00 UTC

Fetching Cloudinary files...
  Scanning images... ✓ 245 files found
  Scanning videos... ✓ 12 files found
  Total Cloudinary files: 257
  API calls used: 3/500 (0.6%)

Checking database for matches...
  ✓ Found 255 prompts in database
  Query time: 0.8s

Analyzing orphaned files...
  ✓ Valid files: 255
  ⚠️  Orphaned: 2 files found

🔍 Checking for prompts with missing images...
  Checking 257 prompts with media...
  - Prompt #123: 'Beautiful Sunset' by user1 [ACTIVE]
  - Prompt #456: 'Mountain View' by user2 [DELETED]
  ⚠️  Found 2 prompts with missing images!
  🚨 1 are ACTIVE (showing broken images on site!)

Results Summary:
============================================================
✅ Valid files: 255 (99.2%)
⚠️  Orphaned files: 2 (0.8%)
📊 Total size of orphans: 4.1 MB

🚨 CRITICAL: 2 prompts with missing images!
   ⚠️  1 are ACTIVE (showing broken images on site!)

📞 API calls used: 5/500 (1.0%)
💾 Rate limit remaining: 495/500 (99%)
⏱️  Execution time: 18.5 seconds

Orphaned Files Detected:
------------------------------------------------------------
1. prompts/sunset_abc123
   - Type: image
   - Uploaded: 2025-09-15T14:30:00Z
   - Size: 2.3 MB
   - Format: jpg

2. prompts/mountain_def456
   - Type: video
   - Uploaded: 2025-09-20T09:15:00Z
   - Size: 1.8 MB
   - Format: mp4

📄 Report saved: /path/to/reports/asset_detection_2025-10-13_010000.csv
📧 Email summary sent to 1 admin(s)

✅ Scan complete!
```

## CSV Report Format

The generated CSV contains **two sections**:

### Section 1: Orphaned Cloudinary Files

| Column | Description |
|--------|-------------|
| `public_id` | Cloudinary public ID (unique identifier) |
| `resource_type` | 'image' or 'video' |
| `size_bytes` | File size in bytes |
| `size_mb` | File size in megabytes (formatted) |
| `format` | File format (jpg, png, mp4, etc.) |
| `uploaded_at` | Upload timestamp (ISO format) |
| `cloudinary_url` | Full Cloudinary URL |

### Section 2: Prompts with Missing Images

| Column | Description |
|--------|-------------|
| `prompt_id` | Database prompt ID |
| `prompt_title` | Prompt title |
| `author` | Username of prompt author |
| `media_type` | 'image' or 'video' |
| `public_id` | Broken Cloudinary public ID |
| `created_at` | When prompt was created |
| `status` | 'ACTIVE' (live on site) or 'DELETED' (in trash) |
| `prompt_url` | Direct link to prompt detail page |

**Example:**
```csv
ORPHANED CLOUDINARY FILES
public_id,resource_type,size_bytes,size_mb,format,uploaded_at,cloudinary_url
prompts/sunset_abc123,image,2411520,2.30,jpg,2025-09-15T14:30:00Z,https://res.cloudinary.com/...


PROMPTS WITH MISSING IMAGES
prompt_id,prompt_title,author,media_type,public_id,created_at,status,prompt_url
123,Beautiful Sunset,user1,image,prompts/missing_abc,2025-10-01 14:30:00,ACTIVE,https://mj-project-4.herokuapp.com/prompt/beautiful-sunset/
456,Mountain View,user2,image,prompts/gone_def,2025-09-28 10:15:00,DELETED,https://mj-project-4.herokuapp.com/prompt/mountain-view/
```

## Email Notifications

### When Are Emails Sent?

- `settings.ADMINS` is configured
- At least 1 orphaned file OR 1 missing image is found
- Email sending succeeds

### Email Contents

- Scan date and range
- Total files scanned
- **Orphaned files section** (if any found):
  - Valid vs orphaned counts
  - List of orphaned files (first 20)
  - Storage wasted
- **Missing images section** (if any found):
  - Total missing count
  - ACTIVE vs DELETED breakdown
  - List with prompt details (first 20)
  - Critical UX warning
  - Recommended actions
- API usage statistics
- Path to CSV report

### Sample Email

```
Subject: PromptFlow: Cloudinary Asset Detection Report

Cloudinary Asset Detection Report
============================================================

Scan Date: 2025-10-13 01:00:00 UTC
Scan Range: Last 30 days

Summary:
--------
Total Cloudinary Files Scanned: 257
Orphaned Files Found: 2
Missing Images Found: 2

Orphaned Files:
---------------
Valid Files: 255 (99.2%)
Orphaned Files: 2 (0.8%)
Total Orphan Size: 4.1 MB

  1. prompts/sunset_abc123 (image, 2.3 MB)
  2. prompts/mountain_def456 (video, 1.8 MB)

Prompts with Missing Images:
-----------------------------
Total Missing: 2
ACTIVE (showing broken images): 1 🚨
DELETED (in trash): 1

  • Prompt #123: 'Beautiful Sunset'
    Author: user1 | Type: image | [ACTIVE]

  • Prompt #456: 'Mountain View'
    Author: user2 | Type: image | [DELETED]

⚠️  CRITICAL: These prompts show broken images on the site!

Recommended Actions:
1. Review prompts - are they in trash already?
2. For ACTIVE prompts: Contact users or soft-delete
3. For DELETED prompts: Hard delete to remove from feed
4. Check why images are missing (manual deletion? Cloudinary issue?)

API Usage:
----------
Calls Used: 5/500 (1.0%)
Execution Time: 18.5 seconds

Full report: /path/to/reports/asset_detection_2025-10-13_010000.csv

--
Automated report from PromptFlow asset detection
```

## Cloudinary API Usage

### Rate Limits

- **Free tier**: 500 API calls per hour
- **This command**: Typically 2-10 calls depending on file count
- **Pagination**: 500 results per call

### API Call Calculation

```
API Calls = ⌈ (image_count / 500) ⌉ + ⌈ (video_count / 500) ⌉
```

**Examples:**
- 250 images, 10 videos = 1 + 1 = 2 API calls
- 1200 images, 50 videos = 3 + 1 = 4 API calls
- 2500 images, 1500 videos = 5 + 3 = 8 API calls

### Rate Limit Protection

The command includes built-in protection:
- **Warning at 80%** (400/500 calls): Yellow warning displayed
- **Stop at 95%** (475/500 calls): Scan stops to prevent hitting limit
- **Small delays**: 0.1s pause between API calls

## Performance

### Typical Execution Times

| Files Scanned | API Calls | Execution Time |
|---------------|-----------|----------------|
| 100 | 1-2 | 2-5 seconds |
| 500 | 2-3 | 5-10 seconds |
| 1,000 | 3-5 | 10-15 seconds |
| 5,000 | 10-15 | 30-45 seconds |
| 10,000 | 20-30 | 60-90 seconds |

### Optimization Tips

1. **Use date filters**: Scan recent files first (`--days 7`)
2. **Run during off-peak**: Less chance of rate limit conflicts
3. **Schedule daily scans**: Catch orphans early (last 1-7 days)
4. **Full scans monthly**: Deep cleanup (`--all`)

## What to Do with Orphaned Files

### Option 1: Manual Review (Recommended)

1. Open the CSV report
2. Check each orphaned file in Cloudinary dashboard
3. Verify it's truly orphaned (not used elsewhere)
4. Delete manually from Cloudinary

### Option 2: Bulk Deletion Script

Create a follow-up script to delete confirmed orphans:

```python
# Future Phase 3 feature
python manage.py delete_orphaned_files --input orphaned_files_2025-10-12.csv --confirm
```

### Option 3: Keep for Investigation

- Orphaned files from recent dates (< 7 days) might indicate bugs
- Review application logs around upload timestamp
- Fix underlying issues before deleting

## What to Do with Missing Images

### Critical: ACTIVE Prompts with Broken Images

**These show broken image icons on the homepage - immediate action required!**

1. **Check the CSV Report** - Filter to `status = ACTIVE`
2. **Review Each Prompt:**
   - Visit the prompt URL (provided in CSV)
   - Confirm image is actually broken
3. **Take Action:**
   - **Option A**: Soft-delete the prompt (moves to trash)
   - **Option B**: Contact user to reupload image
   - **Option C**: If prompt has value, assign a placeholder image

**Quick Soft-Delete:**
```bash
# Access Django shell
python manage.py shell

# Soft-delete specific prompt
from prompts.models import Prompt
prompt = Prompt.objects.get(id=123)
prompt.soft_delete(user=None)  # Or pass admin user
```

### Low Priority: DELETED Prompts with Missing Images

**These are already in trash, lower priority:**

1. **If Expiring Soon**: Let automatic cleanup handle it
2. **If Want to Clean Now**: Hard delete via admin panel or shell:

```bash
# Hard delete (permanent)
from prompts.models import Prompt
prompt = Prompt.all_objects.get(id=456)  # Use all_objects to include deleted
prompt.hard_delete()  # Removes from database
```

### Investigation

**Common Causes:**
- Admin manually deleted from Cloudinary dashboard
- Cloudinary removed for policy violation
- Prompt created during Cloudinary outage

**Prevention:**
- Always use `prompt.hard_delete()` instead of manual Cloudinary deletion
- Never delete files directly from Cloudinary dashboard
- Use this command to catch issues early

## Scheduling Recommendations

### Development/Testing

```bash
# Run manually when needed
python manage.py detect_orphaned_files --days 7
```

### Production

**Daily Scan (Last 7 Days):**
```bash
# Heroku Scheduler: Daily at 4:00 AM
python manage.py detect_orphaned_files --days 7
```

**Weekly Deep Scan (Last 30 Days):**
```bash
# Heroku Scheduler: Weekly on Sunday at 3:00 AM
python manage.py detect_orphaned_files --days 30
```

**Monthly Full Scan:**
```bash
# Heroku Scheduler: First day of month at 2:00 AM
python manage.py detect_orphaned_files --all
```

## Heroku Scheduler Setup

### Add Jobs

```bash
# Open scheduler dashboard
heroku addons:open scheduler --app mj-project-4
```

### Daily Job Configuration

- **Command**: `python manage.py detect_orphaned_files --days 7`
- **Frequency**: Daily at 4:00 AM UTC
- **Dyno Size**: Standard-1X

### Weekly Job Configuration

- **Command**: `python manage.py detect_orphaned_files --days 30`
- **Frequency**: Weekly on Sunday at 3:00 AM UTC
- **Dyno Size**: Standard-1X

## Troubleshooting

### Cloudinary Configuration Error

**Error message:**
```
Must supply cloud_name
```

**Cause:**
- Cloudinary credentials not properly configured
- `CLOUDINARY_STORAGE` dictionary missing in settings

**Solution:**
The command automatically configures Cloudinary from `settings.CLOUDINARY_STORAGE`. Ensure your `settings.py` has:

```python
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'your-cloud-name',
    'API_KEY': 'your-api-key',
    'API_SECRET': 'your-api-secret',
}
```

Or check that `CLOUDINARY_URL` environment variable is set:
```bash
heroku config:get CLOUDINARY_URL --app mj-project-4
```

### No Files Found

**Possible causes:**
- Date filter too restrictive (try `--all`)
- No files in Cloudinary
- Cloudinary credentials issue

**Solution:**
```bash
# Test with broader range
python manage.py detect_orphaned_files --all
```

### API Rate Limit Errors

**Error message:**
```
Error fetching image resources: Rate limit exceeded
```

**Solution:**
- Wait 1 hour for rate limit to reset
- Run during off-peak hours
- Contact Cloudinary to increase limits (paid plans)

### Database Connection Errors

**Error message:**
```
Database query failed: connection timeout
```

**Solution:**
- Check database connection settings
- Verify Heroku Postgres is accessible
- Try again in a few minutes

### CloudinaryField Extraction Errors

**Error message:**
```
Could not extract image public_id from prompt 123
```

**Cause:**
- Malformed CloudinaryField data
- Database corruption

**Solution:**
- These are logged as warnings (scan continues)
- Review specific prompt in Django admin
- Fix manually if needed

### Email Not Sent

**Possible causes:**
- `settings.ADMINS` not configured
- No orphans found (expected behavior)
- Email backend misconfigured

**Solution:**
```python
# Check settings.py
ADMINS = [
    ('Admin Name', 'admin@example.com'),
]
```

## Cost Analysis

### Cloudinary API Costs

- **Free tier**: 500 calls/hour = $0
- **Paid tiers**: No additional cost for API calls

### Storage Cost Savings

**Example:**
- 100 orphaned files × 2 MB average = 200 MB wasted
- Cloudinary free tier: 25 GB total
- Cleanup saves: 0.8% of free tier capacity

**At scale:**
- 1,000 orphans × 2 MB = 2 GB saved
- 10,000 orphans × 2 MB = 20 GB saved (potentially avoiding paid tier)

### Heroku Dyno Costs

- Uses spare Eco Dyno hours (included in plan)
- Daily scan: ~10 seconds = ~5 minutes/month
- Monthly cost: $0 (within existing allocation)

## Security Considerations

### API Credentials

- Command uses existing `CLOUDINARY_URL` from environment
- No credentials stored in code
- All API calls use secure HTTPS

### Report Files

- CSV files contain public_ids (not sensitive)
- Stored in `reports/` directory (gitignored)
- Can be safely shared with team

### Email Contents

- No sensitive data in emails
- Public_ids are not user-identifiable
- Safe to send via standard email

## Integration with Trash Bin System

This command complements the trash bin cleanup:

1. **Trash Cleanup** (5-30 days): Deletes expired prompts + Cloudinary files
2. **Orphan Detection** (periodic): Finds files without database entries
3. **Together**: Complete asset lifecycle management

**Workflow:**
```
Daily Cleanup (3 AM)     → Delete expired trash
Daily Detection (4 AM)   → Find new orphans
Weekly Review            → Admin reviews orphan reports
Manual Cleanup           → Delete confirmed orphans
```

## Future Enhancements

Potential improvements for Phase 3+:

- [ ] Automatic deletion of orphans older than X days
- [ ] Admin dashboard integration (view orphans in web UI)
- [ ] Slack/Discord notifications
- [ ] Whitelist for intentional non-database files
- [ ] Historical tracking (orphan trends over time)
- [ ] Automatic bug reports when orphans spike

## Questions?

Contact the development team or refer to:
- **CLAUDE.md**: Project documentation (Phase D.5)
- **cleanup_deleted_prompts.py**: Related cleanup command
