# Cleanup Deleted Prompts Management Command

## Overview

The `cleanup_deleted_prompts` management command permanently deletes expired trashed prompts based on user retention periods. This command is designed to run daily via Heroku Scheduler to automatically clean up the trash bin.

## Retention Periods

- **Free Users**: 5 days
- **Premium Users**: 30 days

## Features

- ✅ Identifies expired prompts based on user tier
- ✅ Deletes assets from Cloudinary (images and videos)
- ✅ Removes prompts from database
- ✅ Tracks success/failure statistics
- ✅ Sends email summary to admins
- ✅ Supports dry-run mode for testing
- ✅ Comprehensive logging
- ✅ Graceful error handling (continues on individual failures)

## Usage

### Run Cleanup (Production)

```bash
python manage.py cleanup_deleted_prompts
```

### Test Without Deleting (Dry Run)

```bash
python manage.py cleanup_deleted_prompts --dry-run
```

## Output Example

```
Starting cleanup of deleted prompts...
Dry-run mode: OFF
Cutoff dates:
  - Free users: 2025-10-07 12:00:00 UTC
  - Premium users: 2025-09-12 12:00:00 UTC

Processing prompt ID 123: 'Beautiful Sunset' (deleted 6 days ago)
✓ Successfully deleted prompt ID 123

Processing prompt ID 456: 'Mountain View' (deleted 8 days ago)
✗ Failed to delete prompt ID 456: Cloudinary API error

==================================================
Summary:
- Total processed: 2
- Successful: 1
- Failed: 1
- Free users: 2
- Premium users: 0

Failed deletions:
  - ID 456: 'Mountain View' - Cloudinary API error

Email summary sent to 1 admin(s)

Cleanup complete!
```

## Heroku Scheduler Setup

### 1. Add Scheduler Add-on

```bash
heroku addons:create scheduler:standard --app mj-project-4
```

### 2. Configure Job

```bash
heroku addons:open scheduler --app mj-project-4
```

In the Scheduler dashboard:
- **Command**: `python manage.py cleanup_deleted_prompts`
- **Frequency**: Daily at 3:00 AM UTC
- **Dyno Size**: Standard-1X (uses Eco Dyno hours)

### 3. Set Environment Variable (Optional)

Configure admin email for notifications:

```bash
heroku config:set ADMIN_EMAIL=admin@promptfinder.net --app mj-project-4
```

## Email Notifications

The command sends an email summary to all addresses in `settings.ADMINS` after each run.

### Email Contents

- Run timestamp
- Total prompts processed
- Successful deletions count
- Failed deletions count
- Breakdown by user tier (free vs premium)
- Detailed list of failed deletions (if any)

### Configure ADMINS in settings.py

```python
ADMINS = [
    ('Admin Name', os.environ.get('ADMIN_EMAIL', 'admin@example.com')),
]
```

### Email Backend

The command uses Django's configured email backend. In development, this is `console.EmailBackend`, which prints emails to the console instead of sending them.

For production, configure a proper email backend (SendGrid, Mailgun, etc.).

## Error Handling

- Each prompt deletion is wrapped in try-except
- Failed deletions are logged but don't stop processing
- Failed deletions are collected and included in email summary
- Cloudinary errors are logged with full stack traces
- Database errors are handled gracefully

## Logging

The command uses Django's logging system with the logger name `__name__` (resolves to `prompts.management.commands.cleanup_deleted_prompts`).

### Log Levels

- **INFO**: Command start, successful deletions, email sent
- **WARNING**: No admins configured, dry-run mode
- **ERROR**: Failed deletions, email sending failures

### View Logs on Heroku

```bash
heroku logs --tail --source app --app mj-project-4
```

## Testing

### Test Locally

```bash
# Dry run (safe)
python manage.py cleanup_deleted_prompts --dry-run

# Real run (be careful!)
python manage.py cleanup_deleted_prompts
```

### Test on Heroku

```bash
# Dry run
heroku run python manage.py cleanup_deleted_prompts --dry-run --app mj-project-4

# Real run
heroku run python manage.py cleanup_deleted_prompts --app mj-project-4
```

## Cost

- **Heroku Scheduler**: Uses spare Eco Dyno hours (included in plan)
- **Execution Time**: ~1-5 minutes depending on number of prompts
- **Monthly Cost**: $0 (uses existing dyno allocation)

## Safety Features

1. **Dry-run mode**: Test without deleting anything
2. **Timezone-aware**: Uses Django's timezone utilities
3. **Premium detection**: Safely checks for `is_premium` attribute
4. **Partial success**: Continues processing even if some deletions fail
5. **Comprehensive logging**: All actions are logged for audit trail
6. **Email notifications**: Admins are notified of all cleanup runs

## Dependencies

- `django.core.management.base.BaseCommand`
- `django.utils.timezone`
- `django.core.mail.send_mail`
- `django.conf.settings`
- `datetime.timedelta`
- `logging`
- `prompts.models.Prompt`

## Related Files

- **Model**: `prompts/models.py` (Prompt.hard_delete() method)
- **Settings**: `prompts_manager/settings.py` (ADMINS configuration)
- **Logging**: Configured in `settings.LOGGING`

## Troubleshooting

### Command not found

Ensure the directory structure is correct:
```
prompts/
  management/
    __init__.py
    commands/
      __init__.py
      cleanup_deleted_prompts.py
```

### No prompts deleted

Check that:
- Prompts have `deleted_at` set
- Prompts exceed retention period (5 or 30 days)
- Prompts are using `all_objects` manager (includes soft-deleted)

### Email not sent

Check that:
- `settings.ADMINS` is configured
- Email backend is properly configured
- No email exceptions in logs

### Cloudinary deletion fails

Check that:
- `CLOUDINARY_URL` environment variable is set
- Cloudinary credentials are valid
- Assets exist in Cloudinary (may already be deleted)

## Future Enhancements

Potential improvements for Phase 3+:

- [ ] Batch processing for large datasets
- [ ] Rate limiting for Cloudinary API calls
- [ ] Slack/Discord notifications in addition to email
- [ ] Admin dashboard integration
- [ ] Metrics tracking (total deleted, total storage saved)
- [ ] User notifications before deletion (Day 4 warning)

## Questions?

Contact the development team or refer to:
- **CLAUDE.md**: Project documentation
- **Phase D.5**: Trash bin system specification
