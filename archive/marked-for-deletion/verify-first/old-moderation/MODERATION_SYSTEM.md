# PromptFinder Content Moderation System

## Overview

PromptFinder now includes a comprehensive **3-layer AI content moderation system** that automatically checks all uploaded images, videos, and text content for policy violations.

### Moderation Layers

1. **Layer 1: AWS Rekognition** (via Cloudinary)
   - Detects: Explicit nudity, violence, drugs, hate symbols, weapons
   - Provider: AWS Rekognition via Cloudinary add-on
   - Confidence: High (AWS ML models)

2. **Layer 2: Cloudinary AI Vision** (Custom checks)
   - Detects: Minors, gore, satanic imagery, custom violations
   - Provider: Cloudinary AI tagging and detection
   - Customizable: Add your own tag-based checks

3. **Layer 3: OpenAI Moderation API** (Text content)
   - Detects: Sexual content, hate speech, harassment, violence, self-harm
   - Provider: OpenAI Moderation API
   - Checks: Prompt titles, descriptions, and content text

## Architecture

```
User uploads prompt
       ↓
Prompt saved to DB (status: pending)
       ↓
ModerationOrchestrator runs all 3 layers
       ↓
ModerationLogs created for each service
       ↓
ContentFlags created for violations
       ↓
Prompt status updated (approved/rejected/flagged)
       ↓
User notified of result
```

## Database Schema

### Models Created

#### ModerationLog
- Tracks each moderation check
- Fields: service, status, confidence_score, flagged_categories, raw_response
- One log per service per prompt

#### ContentFlag
- Stores specific violations detected
- Fields: category, confidence, severity (low/medium/high/critical), details
- Multiple flags per moderation log

#### Prompt (Updated)
- New fields: moderation_status, requires_manual_review, reviewed_by, review_notes
- Tracks overall moderation state

## Configuration

### Required Environment Variables

Add to your Heroku config vars or `.env` file:

```bash
# OpenAI API Key (required for Layer 3)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Cloudinary (already configured, but verify)
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
```

### Cloudinary Add-ons Required

Enable these in Cloudinary Dashboard → Add-ons:

1. **AWS Rekognition Moderation**
   - Go to: https://cloudinary.com/console/addons
   - Enable: "AWS Rekognition Auto Moderation"
   - Note: May require Cloudinary Plus plan or higher

2. **AI Vision** (included in most plans)
   - Google Tagging
   - Face Detection
   - Object Detection

## Deployment Steps

### 1. Set Environment Variables

```bash
# Set OpenAI API key on Heroku
heroku config:set OPENAI_API_KEY=sk-your-key-here

# Verify Cloudinary is configured
heroku config:get CLOUDINARY_URL
```

### 2. Install Dependencies

```bash
# Install OpenAI Python SDK
pip install openai==1.12.0

# Update requirements.txt
pip freeze > requirements.txt
```

### 3. Deploy to Heroku

```bash
# Commit all changes
git add .
git commit -m "feat: implement 3-layer AI content moderation system"

# Push to Heroku
git push heroku main

# Migrations already applied ✓
```

### 4. Test Moderation

```bash
# Test with a single prompt (dry run)
heroku run python manage.py moderate_prompts --limit 1 --dry-run

# Moderate all pending prompts
heroku run python manage.py moderate_prompts

# Re-moderate all existing prompts
heroku run python manage.py moderate_prompts --all
```

## Usage

### Automatic Moderation

Moderation runs automatically when:
- User creates a new prompt → All 3 layers checked
- User edits an existing prompt → All 3 layers re-checked
- Admin bulk moderates → Via management command

### Manual Review Workflow

1. **Flagged Content** appears in Django Admin
2. Admin reviews the prompt and moderation logs
3. Admin can:
   - Approve (override AI decision)
   - Reject (confirm AI decision)
   - Add review notes
   - Assign to themselves (reviewed_by field)

### Django Admin Interface

Navigate to: https://mj-project-4.herokuapp.com/admin/

**Prompt List** shows:
- Moderation status badge (✓ Approved, ✗ Rejected, ⚠ Flagged, ⏳ Pending)
- Review flag (🔍) if requires manual review
- Filter by moderation status
- View moderation logs inline

**Moderation Logs** show:
- Which service flagged content
- Confidence scores
- Specific categories violated
- Full API responses for debugging

**Content Flags** show:
- Individual violations per check
- Severity levels (critical/high/medium/low)
- Confidence percentages

## Management Commands

### moderate_prompts

Run bulk moderation on prompts:

```bash
# Moderate all pending prompts
python manage.py moderate_prompts

# Re-moderate all prompts (force)
python manage.py moderate_prompts --all

# Moderate specific status
python manage.py moderate_prompts --status rejected

# Limit number of prompts
python manage.py moderate_prompts --limit 50

# Dry run (preview only)
python manage.py moderate_prompts --dry-run
```

## Customization

### Adjust Severity Thresholds

Edit `prompts/services/openai_moderation.py`:

```python
# Change which categories are critical
CRITICAL_CATEGORIES = [
    'sexual/minors',
    'violence/graphic',
    # Add your own...
]
```

Edit `prompts/services/cloudinary_moderation.py`:

```python
# Add custom checks
CUSTOM_CHECKS = {
    'your_category': {
        'severity': 'critical',
        'tags': ['tag1', 'tag2', 'tag3'],
    },
}
```

### Auto-Reject vs Manual Review

In `prompts/services/orchestrator.py`, adjust `_determine_overall_status()`:

```python
# Current: critical = rejected, high = flagged
# To auto-reject high severity too:
if 'rejected' in statuses or has_high_severity:
    overall_status = 'rejected'
```

## Monitoring

### Check Moderation Stats

```python
# In Django shell
from prompts.models import ModerationLog

# Count by status
ModerationLog.objects.filter(status='rejected').count()
ModerationLog.objects.filter(status='flagged').count()

# Recent violations
ModerationLog.objects.filter(
    status__in=['rejected', 'flagged']
).order_by('-moderated_at')[:10]
```

### Performance Monitoring

Each moderation check logs:
- Service name
- Response time
- Confidence scores
- Full API responses

Check Django logs for:
```
INFO: OpenAI moderation complete - Safe: False, Flags: 2, Max confidence: 0.95
INFO: Moderation complete for Prompt 123: rejected
```

## Troubleshooting

### OpenAI API Errors

**Error**: `OPENAI_API_KEY not found`
- Solution: Set environment variable on Heroku

**Error**: `Rate limit exceeded`
- Solution: Implement request throttling or upgrade OpenAI tier

### Cloudinary Errors

**Error**: `No Rekognition data found`
- Solution: Enable AWS Rekognition add-on in Cloudinary dashboard
- Note: May require paid plan

**Error**: `Resource not found`
- Solution: Ensure image/video was uploaded to Cloudinary successfully

### False Positives

If legitimate content is being flagged:

1. Review in Django Admin
2. Override by changing `moderation_status` to `approved`
3. Add notes explaining why it's safe
4. Consider adjusting severity thresholds

## Security & Privacy

- All moderation happens server-side
- API keys stored as environment variables
- Raw API responses stored for audit trail
- User data never sent to AI services (only uploaded media + text)
- GDPR compliant (data retention policies apply)

## Cost Estimates

### OpenAI Moderation API
- **Free tier**: 1M tokens/month
- **Cost**: $0.0005 per 1K tokens (extremely cheap)
- Average prompt: ~200 tokens = $0.0001 per check

### Cloudinary
- **Free tier**: 25K transformations/month
- **AWS Rekognition**: May require Plus plan (~$99/month)
- **AI Vision**: Included in most plans

### Estimated Monthly Cost
- For 1,000 prompts/month: ~$0.10 OpenAI + Cloudinary plan
- For 10,000 prompts/month: ~$1.00 OpenAI + Cloudinary plan

## Future Enhancements

- [ ] Webhook notifications for flagged content
- [ ] Email alerts to admins for critical violations
- [ ] User appeals system for rejected content
- [ ] ML model training on manual review decisions
- [ ] Real-time moderation status dashboard
- [ ] Automated content takedown for critical violations
- [ ] Integration with Perspective API (Google Jigsaw)
- [ ] Video frame-by-frame analysis

## Support

For issues or questions:
1. Check Django admin logs
2. Review ModerationLog raw_response field
3. Test individual services in Django shell
4. Check Cloudinary dashboard for add-on status

## License

This moderation system is part of PromptFinder and follows the same license.
