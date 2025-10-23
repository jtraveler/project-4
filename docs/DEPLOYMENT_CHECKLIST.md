# Deployment Checklist for Email Preferences System

**Before deploying ANY changes to the EmailPreferences system, complete this checklist.**

---

## Pre-Deployment (REQUIRED)

### 1. Data Backup ✅ CRITICAL
- [ ] Run backup command:
  ```bash
  python manage.py backup_email_preferences
  ```
- [ ] Verify backup file created:
  ```bash
  ls -lht backups/email_preferences_backup_*.json | head -1
  ```
- [ ] Check backup file size is reasonable (not 0 bytes)
- [ ] Store backup in safe location (commit to git, upload to cloud storage, etc.)
- [ ] Record backup filename for rollback: `________________`

### 2. Test Database Verification ✅ CRITICAL
- [ ] Confirm tests use test database (not production):
  ```bash
  python manage.py test prompts.tests.test_email_preferences_safety -v 2
  ```
- [ ] Verify test output shows "Creating test database..."
- [ ] Check production data unchanged after tests:
  ```bash
  python manage.py shell
  >>> from prompts.models import EmailPreferences
  >>> print(f"Count: {EmailPreferences.objects.count()}")
  >>> # Record count: ________________
  >>> exit()
  ```

### 3. Code Review
- [ ] No `.delete()` calls on EmailPreferences QuerySets
- [ ] No `.truncate()` operations
- [ ] No data-destructive migrations
- [ ] Signal handlers don't delete data
- [ ] Admin actions have confirmation dialogs
- [ ] Tests don't mock out safety checks

### 4. Migration Safety Review (if migrations exist)
- [ ] Review all new migration files:
  ```bash
  ls -lt prompts/migrations/*.py | head -5
  ```
- [ ] Check for dangerous operations:
  - [ ] No `.delete()` operations
  - [ ] No `.update()` that overwrites user choices
  - [ ] No `DROP TABLE` statements
  - [ ] No data loss in `RunPython` functions
- [ ] Review migration code in `docs/MIGRATION_SAFETY.md`
- [ ] Test migration locally first:
  ```bash
  python manage.py migrate
  # Verify data intact
  python manage.py shell
  >>> from prompts.models import EmailPreferences
  >>> EmailPreferences.objects.count()  # Should match recorded count
  ```

### 5. Staging Environment Testing (if available)
- [ ] Deploy to staging environment
- [ ] Run migrations on staging:
  ```bash
  heroku run python manage.py migrate --app your-staging-app
  ```
- [ ] Verify staging data intact:
  ```bash
  heroku run python manage.py shell --app your-staging-app
  >>> from prompts.models import EmailPreferences
  >>> print(EmailPreferences.objects.count())
  ```
- [ ] Test user workflows manually on staging
- [ ] Check for errors in staging logs

### 6. Rollback Plan
- [ ] Document current migration state:
  ```bash
  python manage.py showmigrations prompts | tail -5
  # Current migration: ________________
  ```
- [ ] Test rollback locally:
  ```bash
  python manage.py migrate prompts <previous_migration>
  python manage.py migrate prompts <current_migration>
  ```
- [ ] Document rollback commands:
  ```bash
  # If deployment fails, run:
  python manage.py migrate prompts ________________
  python manage.py restore_email_preferences backups/________________
  ```

---

## Deployment

### 7. Pre-Deployment Snapshot
- [ ] Record current state:
  ```bash
  python manage.py shell
  >>> from prompts.models import EmailPreferences
  >>> count = EmailPreferences.objects.count()
  >>> print(f"Total preferences: {count}")
  >>> # Record: ________________
  >>>
  >>> # Spot check first user
  >>> first = EmailPreferences.objects.first()
  >>> print(f"First user: {first.user.username}")
  >>> print(f"Comments: {first.notify_comments}")
  >>> # Record: ________________
  >>> exit()
  ```

### 8. Deploy Code
- [ ] Push code to production:
  ```bash
  git push heroku main
  # OR
  git push origin main  # If using CI/CD
  ```
- [ ] Monitor deployment logs for errors
- [ ] Wait for deployment to complete

### 9. Run Migrations (if needed)
- [ ] Run migrations:
  ```bash
  heroku run python manage.py migrate --app your-app
  # OR
  python manage.py migrate  # If SSH'd into server
  ```
- [ ] Monitor migration output for errors
- [ ] Check migration completed successfully

---

## Post-Deployment Verification

### 10. Data Integrity Check ✅ CRITICAL
- [ ] Verify preference count unchanged:
  ```bash
  python manage.py shell
  >>> from prompts.models import EmailPreferences
  >>> new_count = EmailPreferences.objects.count()
  >>> print(f"New count: {new_count}")
  >>> # Should match pre-deployment count: ________________
  >>>
  >>> # Verify first user's data still correct
  >>> first = EmailPreferences.objects.first()
  >>> print(f"User: {first.user.username}")
  >>> print(f"Comments: {first.notify_comments}")
  >>> # Should match pre-deployment data: ________________
  >>> exit()
  ```

### 11. Spot Check Random Users
- [ ] Check 5 random users:
  ```bash
  python manage.py shell
  >>> from prompts.models import EmailPreferences
  >>> import random
  >>>
  >>> # Get 5 random users
  >>> all_prefs = list(EmailPreferences.objects.all())
  >>> sample = random.sample(all_prefs, min(5, len(all_prefs)))
  >>>
  >>> for prefs in sample:
  ...     print(f"\nUser: {prefs.user.username}")
  ...     print(f"  Comments: {prefs.notify_comments}")
  ...     print(f"  Likes: {prefs.notify_likes}")
  ...     print(f"  Marketing: {prefs.notify_marketing}")
  ...     print(f"  Token exists: {bool(prefs.unsubscribe_token)}")
  >>> exit()
  ```

### 12. Functional Testing
- [ ] Navigate to `/settings/notifications/` while logged in
- [ ] Toggle a switch and save
- [ ] Verify success message appears (only once)
- [ ] Refresh page and verify change persisted
- [ ] Check browser console for JavaScript errors
- [ ] Test on mobile device (responsive design)

### 13. Log Monitoring
- [ ] Check application logs for errors:
  ```bash
  heroku logs --tail --app your-app
  # OR
  tail -f /var/log/your-app/production.log
  ```
- [ ] Look for:
  - Database errors
  - 500 errors
  - EmailPreferences exceptions
  - Signal handler failures

### 14. Performance Check
- [ ] Verify page load times acceptable:
  ```bash
  curl -o /dev/null -s -w "Time: %{time_total}s\n" https://your-domain.com/settings/notifications/
  ```
- [ ] Check database query count (Django Debug Toolbar if enabled)
- [ ] Verify no N+1 query issues

---

## Rollback Procedure (If Issues Found)

### If Data Loss Detected:

1. **IMMEDIATELY stop all operations**
2. **Do NOT run more migrations**
3. **Restore from backup:**
   ```bash
   python manage.py restore_email_preferences backups/email_preferences_backup_YYYYMMDD_HHMMSS.json
   ```
4. **Verify restoration:**
   ```bash
   python manage.py shell
   >>> from prompts.models import EmailPreferences
   >>> EmailPreferences.objects.count()  # Should match original count
   ```
5. **Rollback migrations if needed:**
   ```bash
   python manage.py migrate prompts <previous_migration_number>
   ```
6. **Document what happened** for post-mortem

### If Functional Issues Found:

1. **Check logs first** - often configuration issue
2. **If code issue, rollback deployment:**
   ```bash
   heroku rollback --app your-app
   # OR
   git revert <commit_hash>
   git push heroku main
   ```
3. **Verify site working after rollback**
4. **Fix issue locally, re-test, re-deploy**

---

## Post-Deployment Documentation

### 15. Update Documentation
- [ ] Update `CLAUDE.md` with deployment date
- [ ] Document any issues encountered
- [ ] Update `PHASE_E_SPEC.md` status if applicable
- [ ] Add notes to git commit:
  ```bash
  git commit --allow-empty -m "docs: Phase E Task 4 deployed successfully

  - EmailPreferences system deployed
  - All data integrity checks passed
  - Backup created: backups/email_preferences_backup_YYYYMMDD_HHMMSS.json
  - Pre-deployment count: X users
  - Post-deployment count: X users (matched)
  "
  ```

### 16. Team Notification
- [ ] Notify team of successful deployment
- [ ] Share any lessons learned
- [ ] Update issue tracker / project management tool

---

## Quick Reference Commands

### Essential Commands
```bash
# Backup
python manage.py backup_email_preferences

# Restore
python manage.py restore_email_preferences backups/email_preferences_backup_YYYYMMDD_HHMMSS.json

# Check count
python manage.py shell -c "from prompts.models import EmailPreferences; print(EmailPreferences.objects.count())"

# Run migrations
python manage.py migrate

# Rollback migration
python manage.py migrate prompts <previous_migration_number>

# Run safety tests
python manage.py test prompts.tests.test_email_preferences_safety
```

---

## Deployment Status

**Deployment Date:** ________________
**Deployed By:** ________________
**Backup File:** ________________
**Pre-deployment Count:** ________________
**Post-deployment Count:** ________________
**Issues Found:** ________________
**Rollback Required:** Yes / No

**Sign-off:** All checks completed successfully ☐

---

## Summary

✅ **Before Deployment:**
- Backup created
- Tests passed
- Migrations reviewed
- Rollback plan ready

✅ **During Deployment:**
- Code deployed
- Migrations run
- Logs monitored

✅ **After Deployment:**
- Data verified intact
- Spot checks passed
- Functional tests passed
- Documentation updated

**Only mark complete when ALL checks pass.**

---

**Remember:** User preferences are critical data. 10 minutes of careful checking prevents hours of recovery work and user frustration.
