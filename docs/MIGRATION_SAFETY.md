# Email Preferences Migration Safety Guidelines

**CRITICAL:** User email preferences are valuable data. Losing user preferences causes severe frustration and support burden.

---

## GOLDEN RULES

### ✅ Safe Operations
- Adding new fields with defaults
- Changing field types (with proper data conversion)
- Adding database indexes
- Renaming fields (using `migrations.RenameField`)
- Adding constraints that don't delete data

### ❌ UNSAFE Operations (NEVER DO THESE)
- `EmailPreferences.objects.all().delete()`
- Truncating tables
- Dropping and recreating tables with data
- Any operation that loses existing user preferences
- Resetting field values to defaults for existing users

---

## Before Running Migrations

### Step 1: Always Backup First
```bash
# Create timestamped backup
python manage.py backup_email_preferences

# Verify backup was created
ls -lh backups/email_preferences_backup_*.json
```

### Step 2: Review Migration File
```bash
# Look at the migration before running it
cat prompts/migrations/XXXX_migration_name.py

# Check for dangerous operations:
# - .delete()
# - .truncate()
# - RunPython with destructive code
```

### Step 3: Test on Staging First
```bash
# If you have a staging environment, test there first
heroku run python manage.py migrate --app your-staging-app

# Verify data is intact
heroku run python manage.py shell --app your-staging-app
>>> from prompts.models import EmailPreferences
>>> print(EmailPreferences.objects.count())
```

### Step 4: Run Migration
```bash
python manage.py migrate
```

### Step 5: Verify Data Integrity
```bash
python manage.py shell
>>> from prompts.models import EmailPreferences
>>> print(f"Total preferences: {EmailPreferences.objects.count()}")
>>> # Spot check a few random users
>>> prefs = EmailPreferences.objects.first()
>>> print(f"User: {prefs.user.username}")
>>> print(f"Preferences: comments={prefs.notify_comments}, likes={prefs.notify_likes}")
```

---

## Safe Migration Examples

### Example 1: Adding a New Field
```python
# SAFE: Adds new notification type with default value
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('prompts', '0031_create_email_preferences_for_existing_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailpreferences',
            name='notify_security_alerts',
            field=models.BooleanField(
                default=True,
                help_text='Receive notifications about security-related events'
            ),
        ),
    ]
```

### Example 2: Renaming a Field
```python
# SAFE: Renames field without losing data
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('prompts', '0032_add_security_alerts'),
    ]

    operations = [
        migrations.RenameField(
            model_name='emailpreferences',
            old_name='notify_comments',
            new_name='notify_comment_replies',
        ),
    ]
```

### Example 3: Adding an Index
```python
# SAFE: Improves performance without touching data
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('prompts', '0033_rename_notify_comments'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='emailpreferences',
            index=models.Index(
                fields=['user', 'updated_at'],
                name='email_prefs_user_updated_idx'
            ),
        ),
    ]
```

---

## UNSAFE Migration Examples (NEVER DO THESE)

### ❌ Example 1: Deleting All Data
```python
# ❌ DANGEROUS - NEVER DO THIS!
from django.db import migrations

def reset_all_preferences(apps, schema_editor):
    EmailPreferences = apps.get_model('prompts', 'EmailPreferences')
    EmailPreferences.objects.all().delete()  # ❌ LOSES ALL USER DATA!

class Migration(migrations.Migration):
    operations = [
        migrations.RunPython(reset_all_preferences),  # ❌ DESTRUCTIVE!
    ]
```

### ❌ Example 2: Resetting Field Values
```python
# ❌ DANGEROUS - OVERWRITES USER CHOICES!
from django.db import migrations

def reset_to_defaults(apps, schema_editor):
    EmailPreferences = apps.get_model('prompts', 'EmailPreferences')
    # ❌ This overwrites every user's carefully chosen preferences!
    EmailPreferences.objects.all().update(
        notify_comments=True,
        notify_likes=True,
        notify_marketing=False
    )

class Migration(migrations.Migration):
    operations = [
        migrations.RunPython(reset_to_defaults),  # ❌ OVERWRITES USER DATA!
    ]
```

### ❌ Example 3: Drop and Recreate Table
```python
# ❌ DANGEROUS - LOSES ALL DATA!
from django.db import migrations

class Migration(migrations.Migration):
    operations = [
        migrations.DeleteModel(name='EmailPreferences'),  # ❌ DELETES TABLE!
        migrations.CreateModel(name='EmailPreferences', ...),  # ❌ EMPTY TABLE!
    ]
```

---

## Data Conversion Migrations (Advanced)

If you need to change field types or convert data formats, use this pattern:

### Safe Data Conversion Example
```python
# SAFE: Converts data without losing it
from django.db import migrations, models

def convert_old_to_new_format(apps, schema_editor):
    EmailPreferences = apps.get_model('prompts', 'EmailPreferences')
    for prefs in EmailPreferences.objects.all():
        # Convert data from old format to new format
        # Example: combining two fields into one
        if prefs.old_field_1 or prefs.old_field_2:
            prefs.new_combined_field = True
        else:
            prefs.new_combined_field = False
        prefs.save()

class Migration(migrations.Migration):
    dependencies = [
        ('prompts', '0034_add_new_combined_field'),
    ]

    operations = [
        # Step 1: Add new field (previous migration)
        # Step 2: Convert data (this migration)
        migrations.RunPython(
            convert_old_to_new_format,
            reverse_code=migrations.RunPython.noop  # No reverse needed
        ),
        # Step 3: Remove old fields (future migration, after verifying new field works)
    ]
```

---

## Recovery Procedures

### If Migration Goes Wrong

1. **Immediately stop the migration if still running:**
   ```bash
   # Ctrl+C to stop
   ```

2. **Check what data still exists:**
   ```bash
   python manage.py shell
   >>> from prompts.models import EmailPreferences
   >>> print(EmailPreferences.objects.count())
   ```

3. **Restore from backup:**
   ```bash
   # Find your most recent backup
   ls -lht backups/email_preferences_backup_*.json | head -1

   # Restore it
   python manage.py restore_email_preferences backups/email_preferences_backup_YYYYMMDD_HHMMSS.json
   ```

4. **Rollback the migration:**
   ```bash
   # Find the migration number before the bad one
   python manage.py showmigrations prompts

   # Rollback to previous migration
   python manage.py migrate prompts 0031  # Replace with actual previous migration number
   ```

5. **Fix the migration code** before trying again

---

## Testing Migrations Locally

Before deploying a migration:

```bash
# 1. Backup production database (if possible)
python manage.py backup_email_preferences

# 2. Create a local copy of production data (if possible)
# Download backup and restore locally

# 3. Run migration locally
python manage.py migrate

# 4. Verify data integrity
python manage.py shell
>>> from prompts.models import EmailPreferences
>>> # Check count didn't change unexpectedly
>>> # Spot check some random users
>>> # Verify new fields have expected values

# 5. Test rollback works
python manage.py migrate prompts 0031  # Previous migration
python manage.py migrate prompts 0032  # Forward again

# 6. If all tests pass, deploy to staging, then production
```

---

## Automated Safety Checks

The project includes automated tests that verify:
- Data persists across saves
- Signal auto-creates preferences
- User deletion cascades properly
- No accidental data loss

Run these before deploying migrations:
```bash
python manage.py test prompts.tests.test_email_preferences_safety
```

---

## Questions Before Modifying EmailPreferences

Ask yourself these questions before creating a migration:

1. **Does this delete any existing data?** ❌ If yes, redesign the migration
2. **Does this overwrite user choices?** ❌ If yes, redesign the migration
3. **Did I back up first?** ✅ Required before ANY migration
4. **Did I test locally first?** ✅ Required before production deploy
5. **Can I roll back if something goes wrong?** ✅ Verify rollback works
6. **Do I have a backup less than 24 hours old?** ✅ Fresh backups critical

---

## Emergency Contacts

If you accidentally lose user data:

1. **Don't panic** - backups exist
2. **Don't run more migrations** - stop and assess
3. **Check backups immediately:** `ls -lht backups/`
4. **Restore from most recent backup**
5. **Document what happened** for post-mortem

---

## Summary Checklist

Before running ANY migration touching EmailPreferences:

- [ ] Backup created: `python manage.py backup_email_preferences`
- [ ] Migration reviewed for dangerous operations
- [ ] Tested locally with production-like data
- [ ] Tested on staging environment (if available)
- [ ] Rollback plan documented
- [ ] Backup less than 24 hours old
- [ ] Team notified if this is a risky migration
- [ ] Emergency restore command ready: `python manage.py restore_email_preferences backups/...`

**Only proceed when ALL boxes are checked.**

---

**Remember:** It's much easier to prevent data loss than to explain to users why their carefully configured preferences disappeared.
