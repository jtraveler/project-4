# Cloudinary Webhook Setup for AWS Rekognition Moderation

This document explains how to configure the Cloudinary webhook to receive AWS Rekognition moderation results.

## Overview

The moderation flow uses **two methods** to ensure reliability:

### Method 1: Webhook (Primary)
1. **Upload**: User submits content → CloudinaryField uploads with `moderation='aws_rek'`
2. **Async Processing**: AWS Rekognition analyzes the content (takes a few seconds)
3. **Webhook Callback**: Cloudinary sends 'upload' notification to our webhook
4. **Fetch Results**: Webhook calls `cloudinary.api.resource()` to get moderation data
5. **Auto-Publish/Flag**: Webhook updates Prompt status based on results:
   - **Approved** → Set status=1 (Published)
   - **Rejected** → Keep status=0 (Draft), create ContentFlag

### Method 2: Polling Command (Backup)
If webhook fails or moderation data isn't immediately available:
1. **Cron Job**: Runs `check_pending_moderation` every 5 minutes
2. **Query**: Finds all prompts with `moderation_status='pending'`
3. **API Check**: Calls `cloudinary.api.resource()` for each pending prompt
4. **Update**: Publishes approved prompts or flags rejected ones
5. **Ensures**: All prompts are processed within 5-10 minutes maximum

## Webhook Endpoint

**URL**: `https://yourdomain.com/webhooks/cloudinary-moderation/`

This endpoint:
- Accepts POST requests from Cloudinary
- Validates incoming data
- Updates Prompt based on moderation results
- Returns JSON response

## Cloudinary Dashboard Configuration

### Step 1: Access Settings
1. Log in to [Cloudinary Console](https://console.cloudinary.com/)
2. Go to **Settings** → **Notifications** → **Webhooks**

### Step 2: Create Moderation Webhook
1. Click **Add Webhook**
2. Configure:
   - **Notification URL**: `https://yourdomain.com/webhooks/cloudinary-moderation/`
   - **Notification Type**: Select **Moderation**
   - **Status**: Enable the webhook

### Step 3: Configure AWS Rekognition Add-on
1. Go to **Add-ons** → **Amazon Rekognition AI Moderation**
2. Enable the add-on
3. Set moderation confidence level (default: 0.5)
4. Configure categories to check:
   - Explicit Nudity ✓
   - Suggestive ✓
   - Violence ✓
   - Visually Disturbing ✓
   - Drugs/Alcohol/Tobacco ✓
   - Hate Symbols ✓
   - Gambling ✓

### Step 4: Test the Webhook
1. Upload a test image through your app
2. Check logs for webhook callback:
   ```bash
   # View Django logs
   tail -f logs/django.log | grep "Received Cloudinary webhook"
   ```
3. Verify the Prompt status updates correctly

## Webhook Payload Format

Cloudinary sends POST requests with this structure:

```json
{
  "notification_type": "moderation",
  "public_id": "prompts/xyz123",
  "moderation_status": "approved",
  "moderation": [
    {
      "kind": "aws_rek",
      "status": "approved",
      "response": {
        "moderation_labels": [
          {
            "Name": "Explicit Nudity",
            "Confidence": 85.5,
            "ParentName": ""
          }
        ]
      }
    }
  ]
}
```

## Security (TODO)

Currently the webhook accepts all requests. For production:

1. **Add Signature Validation**:
   - Cloudinary signs webhook requests
   - Validate signature using shared secret
   - Reject invalid signatures

2. **Update webhook view** in `prompts/views.py`:
   ```python
   # TODO: Uncomment when webhook is configured
   # signature = request.headers.get('X-Cloudinary-Signature')
   # if not validate_signature(signature, request.body):
   #     return JsonResponse({'error': 'Invalid signature'}, status=403)
   ```

## Troubleshooting

### Webhook Not Receiving Calls
1. Check Cloudinary webhook settings are enabled
2. Verify URL is publicly accessible (not localhost)
3. Check for HTTPS requirement
4. Review Cloudinary webhook logs in dashboard

### Moderation Not Working
1. Verify AWS Rekognition add-on is enabled
2. Check Cloudinary API key/secret are correct
3. Review upload logs for `moderation='aws_rek'` parameter
4. Ensure sufficient credits for Rekognition API calls

### Status Not Updating
1. Check Django logs for webhook errors
2. Verify Prompt public_id matching logic
3. Test with `force=True` in admin panel
4. Check database permissions

## Polling Command Setup

The polling command provides a backup mechanism to ensure all prompts are moderated within 5-10 minutes.

### Manual Testing

Run the command manually to check pending prompts:

```bash
# Basic usage
python manage.py check_pending_moderation

# Verbose output (shows details for each prompt)
python manage.py check_pending_moderation --verbose

# Check only prompts from last 30 minutes
python manage.py check_pending_moderation --max-age-minutes 30
```

### Automated Cron Job Setup

#### Option 1: Django-cron (Recommended)

1. **Install django-cron**:
   ```bash
   pip install django-cron
   ```

2. **Add to INSTALLED_APPS** in `settings.py`:
   ```python
   INSTALLED_APPS = [
       # ...
       'django_cron',
   ]
   ```

3. **Create cron class** in `prompts/cron.py`:
   ```python
   from django_cron import CronJobBase, Schedule
   from django.core.management import call_command

   class CheckPendingModerationCronJob(CronJobBase):
       RUN_EVERY_MINS = 5
       schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
       code = 'prompts.check_pending_moderation'

       def do(self):
           call_command('check_pending_moderation')
   ```

4. **Run cron in background**:
   ```bash
   python manage.py runcrons
   ```

#### Option 2: System Crontab

Add to your crontab (`crontab -e`):

```bash
# Run every 5 minutes
*/5 * * * * cd /path/to/project && /path/to/venv/bin/python manage.py check_pending_moderation >> /path/to/logs/moderation_cron.log 2>&1
```

Example for production:
```bash
*/5 * * * * cd /var/www/myapp && /var/www/myapp/venv/bin/python manage.py check_pending_moderation >> /var/log/myapp/moderation.log 2>&1
```

#### Option 3: Celery Beat (For existing Celery setup)

In `celery.py`:
```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'check-pending-moderation': {
        'task': 'prompts.tasks.check_pending_moderation',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}
```

### Monitoring

Check logs to ensure the command runs successfully:

```bash
# View recent moderation checks
tail -f /var/log/django.log | grep "check_pending_moderation"

# Check for errors
grep "Error checking moderation" /var/log/django.log
```

## Development/Testing

For local testing without public URL:

1. **Use ngrok** to expose local server:
   ```bash
   ngrok http 8000
   ```

2. **Update Cloudinary webhook** to ngrok URL:
   ```
   https://abc123.ngrok.io/webhooks/cloudinary-moderation/
   ```

3. **Test upload** and watch ngrok request inspector

4. **Test polling command**:
   ```bash
   # Create a test prompt that's pending
   # Then run the command
   python manage.py check_pending_moderation --verbose
   ```

## Code References

- **Webhook Handler**: `prompts/views.py:cloudinary_moderation_webhook()`
- **Polling Command**: `prompts/management/commands/check_pending_moderation.py`
- **URL Config**: `prompts/urls.py` (line 27)
- **Custom CloudinaryField**: `prompts/models.py` (lines 8-17)
- **Orchestrator Logic**: `prompts/services/orchestrator.py` (lines 105-124)

## Next Steps

- [ ] Add webhook signature validation
- [ ] Configure Cloudinary dashboard webhook
- [ ] Set up cron job for polling command (every 5 minutes)
- [ ] Test with SFW and NSFW images
- [ ] Monitor webhook success rate
- [ ] Monitor polling command logs
- [ ] Set up alerting for failed webhooks
