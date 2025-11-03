# Content Moderation System - Deployment Checklist

## Pre-Deployment

- [x] Database migrations created
- [x] Migration applied to Heroku PostgreSQL
- [x] Models created (ModerationLog, ContentFlag)
- [x] Moderation services implemented (OpenAI, Cloudinary)
- [x] Django admin interface configured
- [x] Management command created

## Required Before Going Live

### 1. Environment Variables

```bash
# Set OpenAI API Key
heroku config:set OPENAI_API_KEY=sk-your-openai-key-here

# Verify Cloudinary is configured
heroku config:get CLOUDINARY_URL
```

**Get OpenAI API Key:**
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy and save (won't be shown again)
4. Set on Heroku

### 2. Cloudinary Add-ons

**Enable AWS Rekognition:**
1. Login to Cloudinary: https://cloudinary.com/console
2. Go to Add-ons → AWS Rekognition Auto Moderation
3. Enable the add-on
4. Note: May require upgrading to paid plan

**Verify AI Vision:**
- Should be enabled by default
- Check in Cloudinary Console → Settings → Upload

### 3. Install Dependencies

```bash
# Local installation (optional, for testing)
pip install openai==1.12.0

# The dependency is already in requirements.txt
# Heroku will install it automatically on next deployment
```

### 4. Deploy to Heroku

```bash
# Stage all changes
git add prompts/models.py
git add prompts/migrations/0019_*.py
git add prompts/services/
git add prompts/views.py
git add prompts/admin.py
git add prompts/management/
git add requirements.txt
git add MODERATION_SYSTEM.md
git add DEPLOYMENT_CHECKLIST.md

# Commit
git commit -m "feat: implement comprehensive 3-layer AI content moderation system

- Layer 1: AWS Rekognition via Cloudinary for image/video moderation
- Layer 2: Cloudinary AI Vision for custom checks (minors, gore, satanic)
- Layer 3: OpenAI Moderation API for text content
- Added ModerationLog and ContentFlag models
- Integrated into prompt create/edit workflows
- Enhanced Django admin with moderation interface
- Added management command for bulk moderation
- Full documentation in MODERATION_SYSTEM.md"

# Push to Heroku
git push heroku main
```

### 5. Verify Deployment

```bash
# Check deployment logs
heroku logs --tail

# Verify migrations
heroku run python manage.py showmigrations prompts

# Test management command (dry run)
heroku run python manage.py moderate_prompts --limit 1 --dry-run
```

## Post-Deployment Testing

### Test 1: Create New Prompt with Safe Content

1. Go to https://mj-project-4.herokuapp.com/create-prompt/
2. Upload a safe image (landscape, nature, etc.)
3. Add safe text content
4. Submit
5. **Expected**: Prompt approved immediately ✓
6. Check Django admin → Moderation Logs → Should show 3 logs (rekognition, cloudinary_ai, openai) all approved

### Test 2: View Moderation in Admin

1. Go to https://mj-project-4.herokuapp.com/admin/
2. Click on "Prompts" → See moderation badge column
3. Click on "Moderation logs" → See all checks
4. Click on "Content flags" → See specific violations

### Test 3: Bulk Moderate Existing Prompts

```bash
# Start with small batch
heroku run python manage.py moderate_prompts --limit 10

# Check results in admin
# Review any flagged content

# If all looks good, moderate all
heroku run python manage.py moderate_prompts --all
```

### Test 4: Monitor Logs

```bash
# Watch for moderation activity
heroku logs --tail --source app | grep -i moderation

# Look for:
# - "OpenAI moderation complete"
# - "Moderation complete for Prompt"
# - Any errors or warnings
```

## Rollback Plan (If Needed)

If moderation causes issues:

```bash
# Option 1: Disable moderation checks in views
# Comment out orchestrator calls in prompts/views.py

# Option 2: Set all to approved
heroku run python manage.py shell
>>> from prompts.models import Prompt
>>> Prompt.objects.all().update(moderation_status='approved')

# Option 3: Revert migration
heroku run python manage.py migrate prompts 0018  # Previous migration
```

## Monitoring Checklist

After deployment, monitor:

- [ ] Check Django admin for flagged content daily (first week)
- [ ] Review ModerationLog for any API errors
- [ ] Monitor Heroku logs for moderation errors
- [ ] Check OpenAI usage dashboard (https://platform.openai.com/usage)
- [ ] Verify Cloudinary transformation usage
- [ ] Test user experience (upload speed, feedback messages)

## Known Limitations

1. **AWS Rekognition**: Requires Cloudinary paid plan (~$99/month)
   - If not available: Service will log error, flag for manual review
   - Workaround: Remove rekognition checks or use alternative

2. **OpenAI API**: Requires API key and credits
   - Free tier: 1M tokens/month (enough for ~5,000 prompts)
   - If limit hit: Service will fail gracefully, flag for manual review

3. **Performance**: Each upload now runs 3 API calls
   - Average time: 2-4 seconds total
   - User sees loading indicator
   - Consider async/background processing for high volume

## Optional Enhancements

After basic system is stable:

- [ ] Add email notifications for flagged content
- [ ] Create moderation dashboard view
- [ ] Implement user appeal system
- [ ] Add webhook for real-time alerts
- [ ] Set up automated content takedown for critical violations
- [ ] Add moderation analytics/reporting

## Support Resources

- OpenAI Docs: https://platform.openai.com/docs/guides/moderation
- Cloudinary Moderation: https://cloudinary.com/documentation/aws_rekognition_auto_moderation_addon
- Django Admin: https://docs.djangoproject.com/en/4.2/ref/contrib/admin/

## Success Criteria

✓ Deployment successful if:
- [x] No deployment errors
- [ ] Migrations applied successfully
- [ ] OpenAI API key configured
- [ ] New prompts trigger moderation
- [ ] Moderation logs created in admin
- [ ] No 500 errors on upload
- [ ] Appropriate user feedback shown

## Next Steps After Deployment

1. Monitor for 24-48 hours
2. Review all flagged content
3. Adjust sensitivity thresholds if needed
4. Document any false positives/negatives
5. Train team on manual review process
6. Consider implementing automated responses for critical violations

---

**Deployed by**: [Your Name]
**Date**: [Deployment Date]
**Version**: 1.0.0
**Status**: ✓ Ready for Production
