# 404 Diagnostic Tools

Quick tools to identify the exact source of Cloudinary 404 errors.

---

## 🎯 Quick Start

### Option 1: Python Diagnostic (Backend)

```bash
# Run locally
python scripts/diagnose_404.py

# Or in production
heroku run python scripts/diagnose_404.py --app mj-project-4
```

**What it does:**
- Checks admin user's avatar field
- Checks admin's prompt images
- Identifies malformed URLs in database
- Provides recommendations

### Option 2: Browser Diagnostic (Frontend)

```bash
# Open in browser
open scripts/browser_diagnostic.html

# Or manually
# 1. Open scripts/browser_diagnostic.html in browser
# 2. Navigate to http://127.0.0.1:8000/users/admin/
# 3. Open DevTools (F12)
# 4. Click diagnostic buttons
```

**What it does:**
- Finds all images on page
- Identifies broken images
- Tests Cloudinary URLs
- Checks for malformed URLs

---

## 📋 Step-by-Step Process

### Step 1: Run Python Diagnostic

```bash
python scripts/diagnose_404.py
```

**Look for:**
```
⚠️  WARNING: URL is missing domain!
⚠️  This is likely the 404 source!
```

### Step 2: Run Management Command

```bash
# Investigate
python manage.py fix_admin_avatar --investigate

# Fix if needed
python manage.py fix_admin_avatar --fix
```

### Step 3: Browser Check

1. Open `scripts/browser_diagnostic.html`
2. Navigate to profile page with 404
3. Click "Find Broken Images"
4. Note the exact URL

### Step 4: Verify Fix

1. Refresh browser page
2. Check DevTools Console
3. Should see NO 404 errors

---

## 🔍 What to Report

When asking for help, provide:

1. **Python diagnostic output:**
   ```
   [Paste output from diagnose_404.py]
   ```

2. **Exact 404 URL from browser:**
   ```
   [Paste URL from browser console or diagnostic tool]
   ```

3. **Where it appears:**
   - Avatar?
   - Prompt image?
   - Other?

---

## 🚀 Quick Fixes

### Fix 1: Clear Admin Avatar

```bash
python manage.py fix_admin_avatar --fix
```

### Fix 2: Hard Refresh Browser

```
Windows/Linux: Ctrl + Shift + R
Mac: Cmd + Shift + R
```

### Fix 3: Clear Browser Cache

```
DevTools → Network tab → Disable cache checkbox
```

---

## 📊 Expected Output

### Python Diagnostic (Healthy)

```
====================================
404 DIAGNOSTIC REPORT - Admin User
====================================

✓ Found admin user: admin

====================================
1. AVATAR CHECK
====================================
Profile exists: Yes
Has avatar: False
  ✓ No avatar set (using default letter avatar)

====================================
2. PROMPT IMAGES CHECK
====================================
Admin has 3 prompts

Checking first 5 prompts:
  Prompt #1: Test Prompt
    Has image: Yes
    URL: https://res.cloudinary.com/...
    ✓ URL looks good

====================================
3. SUMMARY & RECOMMENDATIONS
====================================

✓ No obvious issues found in database
```

### Python Diagnostic (Problem Found)

```
====================================
1. AVATAR CHECK
====================================
Profile exists: Yes
Has avatar: True

Avatar Details:
  Raw value: 8ee87aee-3c11-4f23-9749-c737914598dd_lk4gpu
  Type: <class 'str'>
  ⚠️  WARNING: URL is missing domain!
  ⚠️  This is likely the 404 source!

====================================
3. SUMMARY & RECOMMENDATIONS
====================================

⚠️  FOUND 1 ISSUE(S):

  1. Avatar URL malformed: 8ee87aee-3c11-4f23-9749-c737914598dd_lk4gpu

📋 RECOMMENDED ACTION:
  1. Run: python manage.py fix_admin_avatar --fix
  2. Refresh browser page
  3. Check console for 404 errors
```

---

## 🛠️ Advanced Diagnostics

### Check All Users

```python
# Django shell
from django.contrib.auth.models import User
from prompts.models import UserProfile

for user in User.objects.all():
    profile = UserProfile.objects.get(user=user)
    if profile.avatar:
        avatar_str = str(profile.avatar)
        if not avatar_str.startswith('http'):
            print(f"⚠️  {user.username}: {avatar_str}")
```

### Check All Prompts

```python
from prompts.models import Prompt

for prompt in Prompt.objects.all():
    if prompt.featured_image:
        img_str = str(prompt.featured_image)
        if not img_str.startswith('http'):
            print(f"⚠️  {prompt.title}: {img_str}")
```

### Test URL in Browser Console

```javascript
// Replace with actual URL
const testUrl = "https://res.cloudinary.com/...";

fetch(testUrl)
    .then(r => {
        console.log('Status:', r.status);
        console.log('x-cld-error:', r.headers.get('x-cld-error'));
    })
    .catch(e => console.error('Error:', e));
```

---

## 🎯 Common Issues

### Issue 1: Avatar Field Corrupted

**Symptom:** `Raw value: 8ee87aee-3c11...` (no http://)

**Fix:**
```bash
python manage.py fix_admin_avatar --fix
```

### Issue 2: Prompt Image Corrupted

**Symptom:** Prompt featured_image is malformed

**Fix:** Need to create similar command for prompts:
```bash
python manage.py fix_prompt_images --prompt-id=123 --fix
```

### Issue 3: CDN Cache

**Symptom:** URL looks correct but still 404

**Fix:** Wait 24 hours or contact Cloudinary support

### Issue 4: Image Doesn't Exist

**Symptom:** x-cld-error: "Resource not found"

**Fix:** Check Cloudinary Media Library, may need to re-upload

---

## 📝 Files Created

- `scripts/diagnose_404.py` - Python backend diagnostic
- `scripts/browser_diagnostic.html` - Browser frontend diagnostic
- `scripts/README_404_diagnostic.md` - This file

---

**Created:** Phase F Day 1 (October 27, 2025)
**Purpose:** Identify exact source of Cloudinary 404 errors
**Related:** fix_admin_avatar management command
