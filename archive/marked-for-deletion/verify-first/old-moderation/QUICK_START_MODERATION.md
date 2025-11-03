# Content Moderation System - Quick Start Guide

## 🚀 Deploy in 5 Minutes

### Step 1: Get OpenAI API Key (2 min)
```bash
# 1. Go to https://platform.openai.com/api-keys
# 2. Click "Create new secret key"
# 3. Copy the key (starts with sk-...)
# 4. Set on Heroku:
heroku config:set OPENAI_API_KEY=sk-your-actual-key-here
```

### Step 2: Enable Cloudinary Add-on (2 min)
```bash
# 1. Go to https://cloudinary.com/console/addons
# 2. Find "AWS Rekognition Auto Moderation"
# 3. Click "Enable" or "Subscribe"
# Note: May require paid plan upgrade
```

### Step 3: Deploy (1 min)
```bash
git add .
git commit -m "feat: add AI content moderation system"
git push heroku main
```

### Step 4: Test (30 sec)
```bash
# Test moderation on 1 prompt
heroku run python manage.py moderate_prompts --limit 1
```

**Done! ✅** Your moderation system is live.

---

## 🔍 Quick Check

### Is it working?
```bash
# Upload a test prompt at your site
# Then check:
heroku run python manage.py shell

>>> from prompts.models import ModerationLog
>>> ModerationLog.objects.latest('moderated_at')
# Should show recent log entry
```

### View in Admin
```
https://mj-project-4.herokuapp.com/admin/prompts/moderationlog/
```

---

## 📊 Common Commands

### Moderate all pending prompts
```bash
heroku run python manage.py moderate_prompts
```

### Re-moderate everything (force)
```bash
heroku run python manage.py moderate_prompts --all
```

### Test without changes (dry run)
```bash
heroku run python manage.py moderate_prompts --dry-run
```

### Moderate specific number
```bash
heroku run python manage.py moderate_prompts --limit 50
```

---

## 🎯 What Gets Checked?

### Images/Videos (AWS Rekognition)
- ❌ Explicit nudity
- ❌ Violence/gore
- ❌ Drugs, alcohol, tobacco
- ❌ Hate symbols
- ❌ Weapons

### Images/Videos (Cloudinary AI)
- ❌ Minors (children, teenagers)
- ❌ Gore (blood, injuries)
- ❌ Satanic imagery (demons, occult)
- ❌ Custom violations (extensible)

### Text (OpenAI)
- ❌ Sexual content
- ❌ Hate speech
- ❌ Harassment
- ❌ Violence
- ❌ Self-harm

---

## 📈 Monitoring

### Check logs
```bash
heroku logs --tail | grep -i moderation
```

### Check OpenAI usage
```
https://platform.openai.com/usage
```

### Check Cloudinary usage
```
https://cloudinary.com/console/usage
```

---

## 🛠 Troubleshooting

### OpenAI errors?
```bash
# Check if key is set
heroku config:get OPENAI_API_KEY

# Should return: sk-...
# If empty, set it again
```

### Cloudinary errors?
```bash
# Check if add-on is enabled
# Go to: https://cloudinary.com/console/addons
# Verify AWS Rekognition is active
```

### Prompts stuck in pending?
```bash
# Run moderation manually
heroku run python manage.py moderate_prompts --status pending
```

---

## 🎨 Customization

### Want to change sensitivity?

Edit `prompts/services/openai_moderation.py`:
```python
# Line 28: Adjust critical categories
CRITICAL_CATEGORIES = [
    'sexual/minors',
    # Add or remove categories
]
```

### Want custom checks?

Edit `prompts/services/cloudinary_moderation.py`:
```python
# Line 44: Add custom violation detection
CUSTOM_CHECKS = {
    'your_category': {
        'severity': 'critical',
        'tags': ['tag1', 'tag2', 'tag3'],
    },
}
```

Then deploy:
```bash
git add .
git commit -m "adjust moderation thresholds"
git push heroku main
```

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Deploy | `git push heroku main` |
| Moderate pending | `heroku run python manage.py moderate_prompts` |
| Re-moderate all | `heroku run python manage.py moderate_prompts --all` |
| Test without changes | `heroku run python manage.py moderate_prompts --dry-run` |
| Check logs | `heroku logs --tail` |
| Django admin | `https://mj-project-4.herokuapp.com/admin/` |

---

## ✅ Success Checklist

After deployment, verify:
- [ ] OPENAI_API_KEY is set (`heroku config:get OPENAI_API_KEY`)
- [ ] Cloudinary Rekognition is enabled
- [ ] New prompts trigger moderation
- [ ] Moderation logs appear in admin
- [ ] User sees feedback messages
- [ ] No 500 errors on upload

---

## 🚨 Emergency: Disable Moderation

If something goes wrong:

```bash
# Option 1: Approve all prompts
heroku run python manage.py shell
>>> from prompts.models import Prompt
>>> Prompt.objects.all().update(moderation_status='approved')

# Option 2: Comment out moderation in code
# Edit prompts/views.py and comment out orchestrator calls
# Then: git commit + git push heroku main
```

---

## 📚 Full Documentation

- **Complete guide**: `MODERATION_SYSTEM.md`
- **Deployment steps**: `DEPLOYMENT_CHECKLIST.md`
- **Implementation details**: `MODERATION_IMPLEMENTATION_SUMMARY.md`

---

**Need help?** Check the full documentation or Django admin logs for detailed error messages.

**Status**: ✅ Ready to Deploy
