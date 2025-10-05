# Cloudinary Webhook Setup for AWS Rekognition Moderation

This document explains how to configure the Cloudinary webhook to receive AWS Rekognition moderation results.

## Overview

The moderation flow works as follows:

1. **Upload**: User submits content → CloudinaryField uploads with `moderation='aws_rek'`
2. **Async Processing**: AWS Rekognition analyzes the content (takes a few seconds)
3. **Webhook Callback**: Cloudinary sends moderation results to our webhook endpoint
4. **Auto-Publish/Flag**: Webhook updates Prompt status based on results:
   - **Approved** → Set status=1 (Published)
   - **Rejected** → Keep status=0 (Draft), create ContentFlag

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

## Code References

- **Webhook Handler**: `prompts/views.py:cloudinary_moderation_webhook()`
- **URL Config**: `prompts/urls.py` (line 27)
- **Custom CloudinaryField**: `prompts/models.py` (lines 8-17)
- **Orchestrator Logic**: `prompts/services/orchestrator.py` (lines 105-124)

## Next Steps

- [ ] Add webhook signature validation
- [ ] Configure Cloudinary dashboard webhook
- [ ] Test with SFW and NSFW images
- [ ] Monitor webhook success rate
- [ ] Set up alerting for failed webhooks
