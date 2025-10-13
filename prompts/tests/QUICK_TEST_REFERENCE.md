# Quick Test Reference - User Profiles

## Most Important Tests to Run First

### 1. Signal Handler Tests (Critical - Bug Fix Verification)
```bash
python manage.py test prompts.tests.test_user_profiles.UserProfileSignalTests
```

**What it tests:**
- ✅ Profile auto-created on user registration
- ✅ No infinite loop bug
- ✅ No duplicate profiles created

**Why it's critical:** This was the main bug you fixed. These tests verify your fix works.

---

### 2. Model Method Tests (Performance Critical)
```bash
python manage.py test prompts.tests.test_user_profiles.UserProfileMethodTests
```

**What it tests:**
- ✅ `get_avatar_color_index()` returns consistent 1-8 color
- ✅ `get_total_likes()` uses efficient aggregate query (1 query, not N)

**Why it's critical:** Verifies N+1 query prevention and consistent user experience.

---

### 3. View Tests (User Experience)
```bash
python manage.py test prompts.tests.test_user_profiles.UserProfileViewTests
```

**What it tests:**
- ✅ Profile page loads (200 OK)
- ✅ 404 for invalid users
- ✅ Media filtering works (all/photos/videos)
- ✅ is_owner flag set correctly
- ✅ Published prompts only (no drafts/deleted)

**Why it's critical:** Core user-facing functionality.

---

## Quick Smoke Test (5 Most Important)

Run these 5 tests to verify core functionality:

```bash
# Test 1: Signal creates profiles
python manage.py test prompts.tests.test_user_profiles.UserProfileSignalTests.test_profile_created_on_user_creation

# Test 2: No infinite loop
python manage.py test prompts.tests.test_user_profiles.UserProfileSignalTests.test_no_infinite_loop_on_profile_save

# Test 3: View loads
python manage.py test prompts.tests.test_user_profiles.UserProfileViewTests.test_profile_view_returns_200

# Test 4: Media filtering
python manage.py test prompts.tests.test_user_profiles.UserProfileViewTests.test_media_filter_all_shows_all_prompts

# Test 5: Efficient likes query
python manage.py test prompts.tests.test_user_profiles.UserProfileMethodTests.test_get_total_likes_uses_single_query
```

---

## Common Test Failures and Fixes

### ❌ Test: `test_profile_created_on_user_creation` FAILS

**Error:** `AttributeError: 'User' object has no attribute 'userprofile'`

**Fix:**
1. Check `prompts/apps.py`:
   ```python
   def ready(self):
       import prompts.signals  # Import signals
   ```

2. Check `prompts/__init__.py`:
   ```python
   default_app_config = 'prompts.apps.PromptsConfig'
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

---

### ❌ Test: `test_no_infinite_loop_on_profile_save` FAILS

**Error:** `RecursionError: maximum recursion depth exceeded`

**Fix:** Signal handler should NOT call `profile.save()`:

```python
@receiver(post_save, sender=User)
def ensure_user_profile_exists(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
        # DO NOT call profile.save() here!
```

---

### ❌ Test: `test_get_total_likes_uses_single_query` FAILS

**Error:** `AssertionError: Expected 1 query, got 5`

**Fix:** Use aggregate, not loop:

```python
def get_total_likes(self):
    from django.db.models import Count
    result = self.user.prompts.filter(
        status=1,
        deleted_at__isnull=True
    ).aggregate(total_likes=Count('likes'))
    return result['total_likes'] or 0
```

---

### ❌ Test: `test_profile_view_returns_200` FAILS

**Error:** `AssertionError: 404 != 200`

**Fix:** Check URL pattern in `prompts/urls.py`:

```python
path('users/<str:username>/', views.user_profile, name='user_profile'),
```

---

### ❌ Test: `test_media_filter_photos_shows_only_images` FAILS

**Error:** Videos appearing in photos filter

**Fix:** Check view filtering logic:

```python
if media_filter == 'photos':
    prompts = prompts.filter(featured_image__isnull=False)
elif media_filter == 'videos':
    prompts = prompts.filter(featured_video__isnull=False)
```

---

## Test-Driven Development Workflow

### Adding a New Feature to User Profiles

**Example:** Add "follower_count" field to UserProfile

**Step 1: Write the test FIRST**
```python
def test_follower_count_defaults_to_zero(self):
    """Test follower_count field defaults to 0."""
    profile = self.user.userprofile
    self.assertEqual(profile.follower_count, 0)
```

**Step 2: Run test (should FAIL)**
```bash
python manage.py test prompts.tests.test_user_profiles.UserProfileModelTests.test_follower_count_defaults_to_zero
```

**Step 3: Add the field**
```python
class UserProfile(models.Model):
    # ... existing fields ...
    follower_count = models.IntegerField(default=0)
```

**Step 4: Run test (should PASS)**
```bash
python manage.py test prompts.tests.test_user_profiles.UserProfileModelTests.test_follower_count_defaults_to_zero
```

---

## Performance Testing

### Test Query Efficiency

**Run with query logging:**
```python
from django.test.utils import CaptureQueriesContext
from django.db import connection

with CaptureQueriesContext(connection) as context:
    profile.get_total_likes()
    print(f"Queries: {len(context.queries)}")
    for query in context.queries:
        print(query['sql'])
```

**Expected:** 1 query (aggregate)
**Bad:** 5+ queries (N+1 problem)

---

## Integration Testing Checklist

After tests pass, manually verify:

- [ ] Visit `/users/<username>/` - Page loads
- [ ] Click "Photos" filter - Only images shown
- [ ] Click "Videos" filter - Only videos shown
- [ ] Click "All" filter - Both shown
- [ ] Check avatar color - Consistent across refreshes
- [ ] Check total likes stat - Matches actual likes
- [ ] Create new user - Profile exists immediately
- [ ] Upload prompt - Appears in profile
- [ ] Delete prompt - Disappears from profile
- [ ] View own profile - "Edit Profile" button visible
- [ ] View other profile - No edit button

---

## Debugging Failed Tests

### Enable verbose output
```bash
python manage.py test prompts.tests.test_user_profiles -v 2
```

### Run single failing test
```bash
python manage.py test prompts.tests.test_user_profiles.UserProfileViewTests.test_profile_view_returns_200 -v 2
```

### Add debug prints in test
```python
def test_profile_view_returns_200(self):
    url = reverse('prompts:user_profile', args=['profileview'])
    print(f"DEBUG: URL = {url}")

    response = self.client.get(url)
    print(f"DEBUG: Status = {response.status_code}")
    print(f"DEBUG: Context = {response.context.keys() if response.context else 'None'}")

    self.assertEqual(response.status_code, 200)
```

### Check database state
```python
def test_something(self):
    # Print all users
    print(User.objects.all().values_list('username', flat=True))

    # Print all profiles
    print(UserProfile.objects.all().count())
```

---

## Test Coverage Report

### Install coverage
```bash
pip install coverage
```

### Run with coverage
```bash
coverage run --source='.' manage.py test prompts.tests.test_user_profiles
coverage report
coverage html  # Creates htmlcov/index.html
```

### View HTML report
```bash
open htmlcov/index.html
```

**Target Coverage:**
- Models: 100%
- Views: 95%+
- Signal Handlers: 100%

---

## Continuous Integration Setup

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python manage.py test prompts.tests.test_user_profiles
```

---

## Best Practices

### ✅ DO:
- Run tests before committing
- Write test first, then implementation (TDD)
- Use descriptive test names
- Test edge cases (empty, null, deleted)
- Mock external services (Cloudinary)
- Use setUpTestData for performance

### ❌ DON'T:
- Skip tests because "it works locally"
- Test implementation details (only test behavior)
- Use sleep() or delays in tests
- Commit failing tests
- Forget to test error cases

---

## Quick Commands Cheat Sheet

```bash
# Run all user profile tests
python manage.py test prompts.tests.test_user_profiles

# Run specific class
python manage.py test prompts.tests.test_user_profiles.UserProfileModelTests

# Run specific test
python manage.py test prompts.tests.test_user_profiles.UserProfileModelTests.test_profile_str_representation

# Verbose output
python manage.py test prompts.tests.test_user_profiles -v 2

# Keep test database for inspection
python manage.py test prompts.tests.test_user_profiles --keepdb

# Fast fail (stop on first failure)
python manage.py test prompts.tests.test_user_profiles --failfast

# Parallel execution (faster)
python manage.py test prompts.tests.test_user_profiles --parallel

# With coverage
coverage run --source='.' manage.py test prompts.tests.test_user_profiles
coverage report -m  # Show missing lines
```

---

**Last Updated:** January 2025
**Status:** ✅ Ready for Use
