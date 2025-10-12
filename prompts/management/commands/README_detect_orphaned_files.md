# Detect Orphaned Files Management Command

## Overview

The `detect_orphaned_files` management command scans Cloudinary for files that don't have corresponding database entries. These "orphaned" files waste storage space and increase costs.

## What Are Orphaned Files?

Orphaned files occur when:
- **Upload failures**: File uploaded to Cloudinary but database save failed
- **Manual deletions**: Database entry deleted but Cloudinary file remains
- **Development testing**: Test uploads that were never properly cleaned up
- **Code errors**: Exceptions during prompt creation after Cloudinary upload

## Features

- ✅ Scans all Cloudinary resources (images and videos)
- ✅ Compares against database records (including soft-deleted prompts)
- ✅ Supports date filtering (scan last N days or all files)
- ✅ Generates detailed CSV reports
- ✅ Sends email summaries to admins
- ✅ Monitors API rate limits
- ✅ Handles pagination automatically
- ✅ Detection only (does NOT delete files)

## Usage

### Basic Scan (Last 30 Days)

```bash
python manage.py detect_orphaned_files
```

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

### Custom Output Location

```bash
python manage.py detect_orphaned_files --output /tmp/orphans_report.csv
```

### Less Verbose Output

```bash
python manage.py detect_orphaned_files --verbose=False
```

## Output Example

```
🔍 Starting Cloudinary Orphaned File Detection
============================================================

Configuration:
- Scanning: Last 30 days
- Resource types: image, video
- Started: 2025-10-12 22:00:00 UTC

Fetching Cloudinary files...
  Scanning images... ✓ 245 files found
  Scanning videos... ✓ 12 files found
  Total Cloudinary files: 257
  API calls used: 3/500 (0.6%)

Checking database for matches...
  ✓ Found 255 prompts in database
  Query time: 0.8s

Analyzing files...
  ✓ Valid files: 255
  ⚠️  Orphaned files: 2

Results Summary:
============================================================
✅ Valid files: 255 (99.2%)
⚠️  Orphaned files: 2 (0.8%)
📊 Total size of orphans: 4.1 MB
📞 API calls used: 5/500 (1.0%)
💾 Rate limit remaining: 495/500 (99%)
⏱️  Execution time: 12.3 seconds

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

📄 Report saved: /path/to/reports/orphaned_files_2025-10-12_220000.csv
📧 Email summary sent to 1 admin(s)

✅ Scan complete!
```

## CSV Report Format

The generated CSV contains the following columns:

| Column | Description |
|--------|-------------|
| `public_id` | Cloudinary public ID (unique identifier) |
| `resource_type` | 'image' or 'video' |
| `size_bytes` | File size in bytes |
| `size_mb` | File size in megabytes (formatted) |
| `format` | File format (jpg, png, mp4, etc.) |
| `uploaded_at` | Upload timestamp (ISO format) |
| `cloudinary_url` | Full Cloudinary URL |

**Example:**
```csv
public_id,resource_type,size_bytes,size_mb,format,uploaded_at,cloudinary_url
prompts/sunset_abc123,image,2411520,2.30,jpg,2025-09-15T14:30:00Z,https://res.cloudinary.com/...
prompts/mountain_def456,video,1887436,1.80,mp4,2025-09-20T09:15:00Z,https://res.cloudinary.com/...
```

## Email Notifications

### When Are Emails Sent?

- `settings.ADMINS` is configured
- At least 1 orphaned file is found
- Email sending succeeds

### Email Contents

- Scan date and range
- Total files scanned
- Valid vs orphaned counts
- List of orphaned files (first 20)
- API usage statistics
- Path to CSV report
- Recommended actions

### Sample Email

```
Subject: PromptFlow: Orphaned Files Detection Report

Orphaned Cloudinary Files Report
============================================================

Scan Date: 2025-10-12 22:00:00 UTC
Scan Range: Last 30 days

Summary:
--------
Total Cloudinary Files: 257
Valid Files: 255 (99.2%)
Orphaned Files: 2 (0.8%)
Total Orphan Size: 4.1 MB

Orphaned Files:
---------------
1. prompts/sunset_abc123 (image, 2.3 MB)
2. prompts/mountain_def456 (video, 1.8 MB)

API Usage:
----------
Calls Used: 5/500 (1.0%)
Execution Time: 12.3 seconds

Action Required:
----------------
Review the CSV report and decide whether to:
1. Delete orphaned files manually from Cloudinary
2. Investigate why files are orphaned
3. Keep files if they're needed for other purposes

Full report: /path/to/reports/orphaned_files_2025-10-12_220000.csv

--
Automated report from PromptFlow orphaned file detection
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
