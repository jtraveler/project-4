# Heroku Scheduler Setup Guide - PromptFlow

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Job Configuration](#job-configuration)
5. [Scheduled Jobs](#scheduled-jobs)
6. [Cost Analysis](#cost-analysis)
7. [Monitoring & Logs](#monitoring--logs)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)
10. [Configuration Checklist](#configuration-checklist)

---

## Overview

This guide walks through setting up Heroku Scheduler to automate daily maintenance tasks for the PromptFlow platform.

### Automated Tasks

| Task | Command | Schedule | Purpose |
|------|---------|----------|---------|
| **Trash Cleanup** | `cleanup_deleted_prompts` | Daily 03:00 UTC | Delete expired prompts (5-30 days) |
| **Orphan Detection** | `detect_orphaned_files --days 7` | Daily 04:00 UTC | Find Cloudinary files without database entries |
| **Deep Scan** | `detect_orphaned_files --days 90` | Weekly Sunday 05:00 UTC | Comprehensive orphan detection |

### Benefits

- ✅ Automatic Cloudinary cleanup (reduce storage costs)
- ✅ Maintain database hygiene
- ✅ Email notifications for admins
- ✅ No manual intervention required
- ✅ Zero additional cost (uses spare dyno hours)

---

## Prerequisites

Before setting up Heroku Scheduler, ensure:

### 1. Heroku CLI Installed

```bash
# Check if installed
heroku --version

# Install if needed (macOS)
brew tap heroku/brew && brew install heroku

# Install if needed (Windows)
# Download from: https://devcenter.heroku.com/articles/heroku-cli
```

### 2. Logged In to Heroku

```bash
heroku login
```

### 3. App Configuration

Verify your app name and credentials:

```bash
# Check current app
heroku apps:info --app mj-project-4

# Verify environment variables
heroku config --app mj-project-4 | grep -E "(DATABASE_URL|CLOUDINARY_URL|ADMIN_EMAIL)"
```

### 4. Email Configuration

Ensure `settings.ADMINS` is configured for notifications:

```python
# In settings.py
ADMINS = [
    ('Admin Name', os.environ.get('ADMIN_EMAIL', 'admin@example.com')),
]
```

Set the admin email:

```bash
heroku config:set ADMIN_EMAIL=your-email@example.com --app mj-project-4
```

---

## Installation

### Step 1: Add Scheduler Add-on

The Scheduler add-on is free for all Heroku apps:

```bash
heroku addons:create scheduler:standard --app mj-project-4
```

**Expected output:**
```
Creating scheduler:standard on ⬢ mj-project-4... free
To manage scheduled jobs run:
  heroku addons:open scheduler
```

### Step 2: Verify Installation

```bash
heroku addons --app mj-project-4
```

You should see:
```
heroku-scheduler (scheduler:standard)  free
```

### Step 3: Open Scheduler Dashboard

**Option A: Command Line**
```bash
heroku addons:open scheduler --app mj-project-4
```

**Option B: Web Dashboard**
1. Go to https://dashboard.heroku.com/apps/mj-project-4
2. Click "Resources" tab
3. Click "Heroku Scheduler" add-on

---

## Job Configuration

### Accessing the Scheduler

Once in the Scheduler dashboard, you'll see a list of scheduled jobs. Click **"Create job"** to add a new job.

### Job Settings Explained

| Setting | Options | Recommendation |
|---------|---------|----------------|
| **Schedule** | Every 10 minutes, Every hour, Daily, Custom | Daily or Custom |
| **Time (UTC)** | 00:00 - 23:50 | Stagger jobs (03:00, 04:00, 05:00) |
| **Dyno Size** | Standard-1X, Standard-2X | Standard-1X (sufficient) |
| **Command** | Bash command | See jobs below |

### Important Notes

- ⏰ **All times are UTC** (convert from your local timezone)
- 🔄 **Jobs run on Eco dynos** (uses spare dyno hours from your plan)
- 📊 **Execution limit**: 10 minutes per job (our jobs run 10-60 seconds)
- 💰 **Cost**: $0/month (included in Eco plan)

---

## Scheduled Jobs

### Job 1: Daily Trash Cleanup ✅ REQUIRED

**Purpose:** Permanently delete prompts that have exceeded their retention period.

**Configuration:**
```
Command:    python manage.py cleanup_deleted_prompts
Schedule:   Daily
Time:       03:00 UTC
Dyno Size:  Standard-1X
```

**What it does:**
- Scans for expired trashed prompts (5 days for free users, 30 days for premium)
- Deletes assets from Cloudinary (images/videos)
- Removes database entries
- Sends email summary to admins

**Expected output:**
```
Starting cleanup of deleted prompts...
Total processed: 5
Successful: 5
Failed: 0
Email summary sent to 1 admin(s)
```

**Runtime:** ~10-30 seconds (depends on number of expired prompts)

---

### Job 2: Daily Orphan Detection ✅ REQUIRED

**Purpose:** Detect Cloudinary files without corresponding database entries.

**Configuration:**
```
Command:    python manage.py detect_orphaned_files --days 7
Schedule:   Daily
Time:       04:00 UTC
Dyno Size:  Standard-1X
```

**What it does:**
- Scans Cloudinary for files uploaded in last 7 days
- Compares against database records
- Identifies orphaned files
- Generates CSV report in `reports/` directory
- Sends email summary if orphans found

**Expected output:**
```
🔍 Starting Cloudinary Orphaned File Detection
Total Cloudinary files: 157
Valid files: 155 (98.7%)
Orphaned files: 2 (1.3%)
📄 Report saved: orphaned_files_2025-10-12_040000.csv
📧 Email summary sent to 1 admin(s)
```

**Runtime:** ~10-20 seconds (for 7-day scan)

**Why 7 days?**
- Catches recent orphans quickly
- Low API usage (~2-5 calls)
- Fast execution
- Good for daily monitoring

---

### Job 3: Weekly Deep Scan 🔵 OPTIONAL

**Purpose:** Comprehensive orphan detection for older files.

**Configuration:**
```
Command:    python manage.py detect_orphaned_files --days 90
Schedule:   Weekly (Sunday)
Time:       05:00 UTC
Dyno Size:  Standard-1X
```

**What it does:**
- Scans Cloudinary for files uploaded in last 90 days
- More thorough than daily scans
- Catches older orphans that might have been missed
- Generates comprehensive CSV report

**Expected output:**
```
🔍 Starting Cloudinary Orphaned File Detection
Total Cloudinary files: 1,247
Valid files: 1,245 (99.8%)
Orphaned files: 2 (0.2%)
API calls used: 8/500 (1.6%)
```

**Runtime:** ~30-60 seconds (for 90-day scan)

**Why Sunday at 05:00 UTC?**
- Low traffic time
- Won't interfere with daily jobs
- Good for weekly deep cleaning

---

## Cost Analysis

### Heroku Scheduler Costs

| Component | Cost | Notes |
|-----------|------|-------|
| **Add-on** | $0/month | Free for all apps |
| **Dyno Hours** | $0/month | Uses spare Eco dyno hours |
| **Total** | **$0/month** | Fully covered by existing plan |

### Dyno Hour Calculation

Your **Eco Dyno Plan** includes:
- 1000 dyno hours/month (~720 hours needed for 24/7 web dyno)
- **Spare hours available:** ~280 hours/month

**Scheduled jobs usage:**
```
Daily Cleanup:      30 seconds × 30 days = 15 minutes/month
Daily Detection:    20 seconds × 30 days = 10 minutes/month
Weekly Deep Scan:   60 seconds × 4 runs  = 4 minutes/month
────────────────────────────────────────────────────────────
Total:                                   = 29 minutes/month
                                         = 0.48 hours/month
                                         = 0.17% of spare hours
```

**Verdict:** ✅ Negligible impact on dyno hours

### Cloudinary API Costs

| Job | API Calls/Run | Runs/Month | Total Calls |
|-----|---------------|------------|-------------|
| Daily Detection (7 days) | 2-5 | 30 | 60-150 |
| Weekly Deep Scan (90 days) | 8-12 | 4 | 32-48 |
| **Monthly Total** | | | **92-198** |

**Cloudinary Free Tier:** 500 calls/hour, unlimited hours

**Verdict:** ✅ Well within free tier limits

---

## Monitoring & Logs

### View Recent Job Runs

**Via Dashboard:**
1. Open Heroku Scheduler add-on
2. Each job shows:
   - Last run time
   - Next scheduled run
   - Status (Success/Failed)

**Via Command Line:**
```bash
# View all scheduler jobs
heroku run:detached --help --app mj-project-4
```

### View Job Execution Logs

**Real-time logs:**
```bash
# Watch all logs
heroku logs --tail --app mj-project-4

# Filter for specific job
heroku logs --tail --source app --app mj-project-4 | grep "cleanup_deleted_prompts"
heroku logs --tail --source app --app mj-project-4 | grep "detect_orphaned_files"
```

**Historical logs (last 1500 lines):**
```bash
heroku logs -n 1500 --app mj-project-4 > logs.txt
```

**Search for specific job runs:**
```bash
# Find cleanup runs
heroku logs --app mj-project-4 | grep "Starting cleanup of deleted prompts"

# Find detection runs
heroku logs --app mj-project-4 | grep "Starting Cloudinary Orphaned File Detection"
```

### Email Notifications

Both jobs send email summaries to admins configured in `settings.ADMINS`.

**Cleanup email includes:**
- Total prompts processed
- Successful/failed deletions
- Free vs premium user breakdown
- Failed deletion details

**Detection email includes:**
- Total files scanned
- Valid vs orphaned counts
- List of orphaned files (first 20)
- API usage statistics
- Path to CSV report

**Expected frequency:**
- Cleanup: Daily (if expired prompts exist)
- Detection: Daily (only if orphans found)

### CSV Reports

Orphan detection generates CSV reports in the `reports/` directory:

```bash
# List reports (if running locally)
ls -lh reports/

# Download report from Heroku
heroku run bash --app mj-project-4
$ ls reports/
$ cat reports/orphaned_files_2025-10-12_040000.csv
```

**Note:** Reports are stored on the dyno filesystem and are **ephemeral** (lost on dyno restart). For permanent storage, consider:
- AWS S3 integration (Phase 3+)
- Emailing reports to admins (current solution)

---

## Testing

### Test Jobs Manually

Before scheduling, test each job manually to ensure they work:

#### Test Cleanup Command

```bash
# Dry run (safe - doesn't delete anything)
heroku run python manage.py cleanup_deleted_prompts --dry-run --app mj-project-4

# Real run (careful!)
heroku run python manage.py cleanup_deleted_prompts --app mj-project-4
```

**Expected output:**
```
Starting cleanup of deleted prompts...
Dry-run mode: ON
...
[DRY RUN] Would delete prompt ID 123
```

#### Test Detection Command

```bash
# Test with 1 day (fast)
heroku run python manage.py detect_orphaned_files --days 1 --app mj-project-4

# Test with 7 days (normal daily run)
heroku run python manage.py detect_orphaned_files --days 7 --app mj-project-4
```

**Expected output:**
```
🔍 Starting Cloudinary Orphaned File Detection
...
✅ Scan complete!
```

#### Test Weekly Deep Scan

```bash
# Test with 90 days (weekly run)
heroku run python manage.py detect_orphaned_files --days 90 --app mj-project-4
```

### Verify Email Delivery

After running tests, check:
1. Admin email inbox
2. Spam/junk folder (first time)
3. Heroku logs for email sending confirmation

```bash
heroku logs --tail --app mj-project-4 | grep "Email summary sent"
```

### Test Scheduler Execution

After adding jobs to scheduler:

1. **Set job to run in 5 minutes:**
   - Edit job time to current UTC time + 5 minutes
   - Save and wait

2. **Monitor logs:**
   ```bash
   heroku logs --tail --app mj-project-4
   ```

3. **Verify execution:**
   - Check logs for command output
   - Check email inbox
   - Verify job status in dashboard

4. **Reset to production schedule:**
   - Edit job back to normal time (03:00, 04:00, 05:00 UTC)

---

## Troubleshooting

### Job Shows "Failed" Status

**Check logs:**
```bash
heroku logs --tail --app mj-project-4
```

**Common causes:**

1. **Database connection timeout**
   - Solution: Retry usually succeeds
   - Heroku Postgres occasionally has brief unavailability

2. **Cloudinary API error**
   - Solution: Check `CLOUDINARY_URL` config var
   - Verify credentials are valid

3. **Module import errors**
   - Solution: Verify all dependencies in `requirements.txt`
   - Run `heroku run pip list --app mj-project-4`

4. **Timeout (>10 minutes)**
   - Solution: Optimize query or reduce scan range
   - 10-minute limit is hard Heroku limit

### Job Not Running at Scheduled Time

**Check UTC conversion:**
```bash
# Show current UTC time
date -u

# Convert local to UTC
# Your time - UTC offset = UTC time
# Example: 10:00 PM PST (UTC-8) = 06:00 AM UTC
```

**Verify job is enabled:**
- Open Scheduler dashboard
- Ensure job has checkmark (not paused)

**Scheduler delay:**
- Jobs may run 0-5 minutes after scheduled time
- This is normal Heroku behavior

### Email Not Received

**1. Check ADMINS configuration:**
```bash
heroku run python manage.py shell --app mj-project-4
>>> from django.conf import settings
>>> print(settings.ADMINS)
[('Admin Name', 'admin@example.com')]
```

**2. Check email backend:**
```bash
heroku run python manage.py shell --app mj-project-4
>>> from django.conf import settings
>>> print(settings.EMAIL_BACKEND)
django.core.mail.backends.console.EmailBackend  # Development
```

**Note:** In development, emails print to console. For production, configure a proper email backend:
- SendGrid
- Mailgun
- AWS SES
- Postmark

**3. Check spam folder:**
- First emails often go to spam
- Mark as "Not Spam" to whitelist

### "Must supply cloud_name" Error

**Error in logs:**
```
cloudinary.exceptions.Error: Must supply cloud_name
```

**Solution:**
```bash
# Verify CLOUDINARY_URL is set
heroku config:get CLOUDINARY_URL --app mj-project-4

# If missing, add it
heroku config:set CLOUDINARY_URL="cloudinary://..." --app mj-project-4
```

### CSV Reports Not Found

**Remember:** Heroku dynos have ephemeral filesystems.

**Reports are lost when:**
- Dyno restarts
- App deploys
- Scheduler job completes

**Solutions:**
1. **Email reports** (current): Admin receives email with summary
2. **S3 storage** (Phase 3+): Upload reports to permanent storage
3. **Database storage** (Phase 3+): Store orphan data in database

### High API Usage Warning

**Warning in logs:**
```
⚠️  Warning: Used 420/500 API calls (>80%)
```

**Causes:**
- Multiple scans running simultaneously
- Very large file count in Cloudinary

**Solutions:**
1. **Reduce scan frequency:**
   - Change daily detection from 7 days to 3 days
   - Skip weekly deep scan temporarily

2. **Stagger job times:**
   - Ensure jobs don't overlap
   - Current schedule (03:00, 04:00, 05:00) is good

3. **Contact Cloudinary:**
   - Paid plans have higher rate limits
   - Request limit increase if needed

---

## Configuration Checklist

Use this checklist to verify your setup:

### ✅ Pre-Setup

- [ ] Heroku CLI installed and logged in
- [ ] App name verified: `mj-project-4`
- [ ] Database URL configured
- [ ] Cloudinary URL configured
- [ ] Admin email set: `heroku config:set ADMIN_EMAIL=...`
- [ ] `settings.ADMINS` configured in `settings.py`

### ✅ Commands Tested Locally

- [ ] `python manage.py cleanup_deleted_prompts --dry-run` works
- [ ] `python manage.py detect_orphaned_files --days 1` works
- [ ] Both commands tested on Heroku with `heroku run`

### ✅ Scheduler Add-on

- [ ] Scheduler add-on installed: `heroku addons:create scheduler:standard`
- [ ] Scheduler dashboard accessible
- [ ] Add-on shows in resources tab

### ✅ Job 1: Trash Cleanup (Required)

- [ ] Command: `python manage.py cleanup_deleted_prompts`
- [ ] Schedule: Daily
- [ ] Time: 03:00 UTC (or adjust for your preference)
- [ ] Dyno Size: Standard-1X
- [ ] Job saved and enabled

### ✅ Job 2: Orphan Detection (Required)

- [ ] Command: `python manage.py detect_orphaned_files --days 7`
- [ ] Schedule: Daily
- [ ] Time: 04:00 UTC
- [ ] Dyno Size: Standard-1X
- [ ] Job saved and enabled

### ✅ Job 3: Weekly Deep Scan (Optional)

- [ ] Command: `python manage.py detect_orphaned_files --days 90`
- [ ] Schedule: Weekly (Sunday)
- [ ] Time: 05:00 UTC
- [ ] Dyno Size: Standard-1X
- [ ] Job saved and enabled

### ✅ Monitoring Setup

- [ ] Know how to view logs: `heroku logs --tail`
- [ ] Email notifications working (test email received)
- [ ] Scheduler dashboard bookmarked for quick access
- [ ] Reports directory created (if running locally)

### ✅ Documentation

- [ ] Team knows where to find logs
- [ ] Admin email recipients documented
- [ ] Troubleshooting steps reviewed
- [ ] Escalation process defined (who to contact if jobs fail)

---

## Quick Reference Commands

```bash
# Installation
heroku addons:create scheduler:standard --app mj-project-4
heroku addons:open scheduler --app mj-project-4

# Testing
heroku run python manage.py cleanup_deleted_prompts --dry-run --app mj-project-4
heroku run python manage.py detect_orphaned_files --days 1 --app mj-project-4

# Monitoring
heroku logs --tail --app mj-project-4
heroku logs --tail --source app --app mj-project-4 | grep "cleanup"
heroku logs --tail --source app --app mj-project-4 | grep "orphaned"

# Configuration
heroku config:get ADMIN_EMAIL --app mj-project-4
heroku config:set ADMIN_EMAIL=your-email@example.com --app mj-project-4
heroku config:get CLOUDINARY_URL --app mj-project-4

# Scheduler Management
heroku addons:info scheduler --app mj-project-4
heroku addons:open scheduler --app mj-project-4

# View recent runs (check logs)
heroku logs -n 1500 --app mj-project-4 | grep "cleanup_deleted_prompts\|detect_orphaned_files"
```

---

## Support Resources

### Documentation

- **Heroku Scheduler Docs**: https://devcenter.heroku.com/articles/scheduler
- **Heroku CLI Reference**: https://devcenter.heroku.com/articles/heroku-cli
- **Project Docs**: See `CLAUDE.md` (Phase D.5)

### Command-Specific Docs

- **cleanup_deleted_prompts**: `prompts/management/commands/README_cleanup_deleted_prompts.md`
- **detect_orphaned_files**: `prompts/management/commands/README_detect_orphaned_files.md`

### Getting Help

1. **Check logs first**: `heroku logs --tail --app mj-project-4`
2. **Review troubleshooting section** in this document
3. **Check command-specific READMEs** for detailed troubleshooting
4. **Contact Heroku support** (if add-on issues)
5. **Review Django documentation** (if command errors)

---

## Next Steps

After completing setup:

1. **Monitor first 7 days:**
   - Check logs daily
   - Verify emails arrive
   - Review CSV reports

2. **Optimize if needed:**
   - Adjust scan ranges (7 days → 3 days if too slow)
   - Modify schedules (shift times if conflicts)
   - Fine-tune email notifications

3. **Phase 3 enhancements:**
   - Add S3 storage for CSV reports
   - Build admin dashboard for viewing orphans
   - Implement automatic orphan deletion (with safety checks)
   - Add Slack/Discord notifications

---

**Setup Complete!** 🎉

Your automated maintenance system is now running. The platform will:
- ✅ Clean up expired trash automatically
- ✅ Detect orphaned Cloudinary files
- ✅ Send email reports to admins
- ✅ Maintain database and storage hygiene
- ✅ Cost you $0/month in additional fees

**Questions?** Refer to the troubleshooting section or command-specific READMEs.
