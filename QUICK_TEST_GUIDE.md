# Quick Testing Guide - Rate Limiting Security Fixes
**Date:** October 25, 2025

## ✅ What Was Fixed

1. **IP Spoofing Vulnerability** - Now validates X-Forwarded-For headers
2. **Weak Hashing** - Replaced MD5 with SHA-256
3. **Cache Error Handling** - Added try/except with logging
4. **Information Disclosure** - Removed tokens from logs
5. **Hardcoded Values** - Moved to configurable settings

---

## 🚀 Quick Manual Tests (5 minutes)

### Test 1: Basic Rate Limiting Works
```bash
# 1. Start Django dev server
python3 manage.py runserver

# 2. Get a valid unsubscribe URL (create test user with EmailPreferences first)
python3 manage.py shell
>>> from prompts.models import EmailPreferences
>>> prefs = EmailPreferences.objects.first()
>>> print(f"http://127.0.0.1:8000/unsubscribe/{prefs.unsubscribe_token}/")

# 3. Open URL in browser
# 4. Refresh 5 times rapidly (Cmd+R or Ctrl+R)
# 5. On 6th refresh, should see "Too Many Requests" error with clock icon
```

**Expected Result:** ✅ Rate limit triggered on 6th request

---

### Test 2: IP Validation Function
```bash
python3 manage.py shell

from django.test import RequestFactory
from prompts.views import get_client_ip

factory = RequestFactory()

# Test direct connection
request = factory.get('/')
request.META['REMOTE_ADDR'] = '203.0.113.45'
ip = get_client_ip(request)
print(f"Direct IP: {ip}")
# Expected: 203.0.113.45 ✅

# Test behind proxy
request = factory.get('/')
request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.45, 10.0.0.5'
request.META['REMOTE_ADDR'] = '10.0.0.5'
ip = get_client_ip(request)
print(f"Proxied IP: {ip}")
# Expected: 203.0.113.45 (client IP, not proxy) ✅
```

**Expected Results:**
- Direct connection returns REMOTE_ADDR ✅
- Proxied connection extracts client IP from X-Forwarded-For ✅

---

### Test 3: Cache Error Handling
```bash
# Test that unsubscribe still works if cache fails

python3 manage.py shell

# Temporarily break cache
from django.core.cache import cache
from django.db import connection

# Option 1: Clear cache
cache.clear()

# Option 2: Drop cache table (more dramatic test)
cursor = connection.cursor()
cursor.execute("DROP TABLE IF EXISTS cache_table")

# Exit shell and test in browser
# Navigate to unsubscribe URL
# Expected: Request succeeds (fails open), logs cache error

# Recreate cache table
python3 manage.py createcachetable
```

**Expected Result:** ✅ Unsubscribe works even when cache fails, error logged

---

## ⚠️ Before Production Deployment

### CRITICAL: Update TRUSTED_PROXIES

Edit `prompts_manager/settings.py` (around line 308):

```python
# Update with your actual production proxy IP ranges
TRUSTED_PROXIES = [
    '10.0.0.0/8',      # Private network - UPDATE
    '172.16.0.0/12',   # Private network - UPDATE
    '192.168.0.0/16',  # Private network - UPDATE
    # Add Heroku router ranges (if using Heroku)
    # Add AWS ELB ranges (if using AWS)
    # Add Cloudflare ranges (if using Cloudflare)
]
```

**Heroku Example:**
```python
if 'DYNO' in os.environ:
    TRUSTED_PROXIES = [
        '10.0.0.0/8',
        '172.16.0.0/12',
        '192.168.0.0/16',
    ]
```

---

## 📊 Check Implementation

### Files Changed:
```bash
# Check settings.py has new config
grep -A 10 "UNSUBSCRIBE_RATE_LIMIT" prompts_manager/settings.py

# Check views.py has new function
grep -A 5 "def get_client_ip" prompts/views.py

# Check SHA-256 is used (not MD5)
grep "sha256" prompts/views.py
```

**Expected:**
- ✅ UNSUBSCRIBE_RATE_LIMIT = 5
- ✅ UNSUBSCRIBE_RATE_LIMIT_TTL = 3600
- ✅ TRUSTED_PROXIES list exists
- ✅ get_client_ip() function exists
- ✅ SHA-256 hashing used

---

## 🔍 Monitor in Production

### Key Logs to Watch:
```bash
# Rate limit violations (should be rare)
grep "Rate limit exceeded" logs/

# Cache errors (should be ZERO)
grep "Cache backend error" logs/

# Invalid token attempts (watch for spikes)
grep "Invalid unsubscribe token attempt" logs/
```

### Alert If:
- ❌ More than 10 cache errors per hour
- ⚠️ More than 50 rate limit hits per hour
- ℹ️ More than 10 invalid tokens from single IP

---

## 📝 Quick Verification Checklist

Before marking as complete:

- [ ] Rate limiting triggers on 6th request (Test 1)
- [ ] get_client_ip() validates proxy headers (Test 2)
- [ ] Cache errors handled gracefully (Test 3)
- [ ] SHA-256 used instead of MD5 (grep check)
- [ ] No token info in logs (grep check)
- [ ] TRUSTED_PROXIES configured for production
- [ ] Settings have rate limit configuration
- [ ] Security report reviewed (SECURITY_FIXES_REPORT.md)

---

## 🎯 Production Deployment

```bash
# 1. Review all changes
git diff prompts_manager/settings.py prompts/views.py

# 2. Update TRUSTED_PROXIES for production
# Edit settings.py with actual proxy IPs

# 3. Run checks
python3 manage.py check
python3 manage.py check --deploy

# 4. Test in staging (if available)
# Run all 3 manual tests above

# 5. Deploy to production
git add prompts_manager/settings.py prompts/views.py SECURITY_FIXES_REPORT.md
git commit -m "fix(security): Apply critical rate limiting security fixes

- Fix IP spoofing vulnerability with trusted proxy validation
- Replace MD5 with SHA-256 for IP hashing
- Add cache error handling (fail-open policy)
- Remove token information from logs
- Make rate limit configurable via settings

Security rating improved from 6/10 to 9/10.
Production-ready after TRUSTED_PROXIES configuration."

git push heroku main

# 6. Monitor logs for first 24 hours
heroku logs --tail | grep -E "Rate limit|Cache backend|Invalid unsubscribe"
```

---

## 📞 Support

**Issues?** Check SECURITY_FIXES_REPORT.md for detailed documentation
**Questions?** Review CLAUDE.md Phase E completion notes
**Security concerns?** Report immediately

**Date:** October 25, 2025
**Status:** ✅ FIXES APPLIED - Ready for production after TRUSTED_PROXIES update
