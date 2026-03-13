# REPORT_NOTIF_URL_REVERSE.md
# Session 126 — March 13, 2026

## Summary

Both notification helpers in `prompts/tasks.py` (`_fire_bulk_gen_job_notification` and
`_fire_bulk_gen_publish_notification`) were using hardcoded URL strings instead of
Django's `reverse()`. This is a fragility issue — if URL patterns change in `urls.py`,
the notification links would silently break. Both helpers were updated to use
`reverse()` with the correct namespaced URL names. A latent bug was also fixed in the
process: the old hardcoded profile URL was `/profile/{username}/` but the actual URL
pattern is `users/<str:username>/`, so the notification link had been pointing to a
non-existent path. The `reverse()` call now correctly produces `/users/{username}/`.

## Code Changes (Before / After)

### _fire_bulk_gen_job_notification
```python
# Before
job_url = f'/tools/bulk-ai-generator/job/{job.id}/'
# After
job_url = reverse('prompts:bulk_generator_job', args=[str(job.id)])
```

### _fire_bulk_gen_publish_notification
```python
# Before
profile_url = f'/profile/{job.created_by.username}/'
# After
profile_url = reverse('prompts:user_profile', args=[job.created_by.username])
```

## reverse() Import

`reverse` was **not** previously imported in `tasks.py`. Added at module level (line 30),
alphabetically positioned within the existing `from django.*` import block:

```python
from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import F
from django.urls import reverse          ← added here
from django.utils.text import slugify
```

No duplicate import introduced. `reverse` appears exactly once in the file's imports.

## Bonus Bug Fixed

The old hardcoded profile URL `/profile/{username}/` does not match any URL pattern in
`prompts/urls.py`. The actual pattern is `path('users/<str:username>/', ..., name='user_profile')`.
The `reverse()` call correctly resolves to `/users/{username}/`. All published notification
links to user profiles were previously broken (404). This is now corrected.

## Agent Ratings

| Agent | Score | Notes |
|-------|-------|-------|
| @django-pro | 9.5/10 | All 5 evaluation dimensions passed; flagged hidden /profile/ → /users/ bug fix as bonus positive |
| @code-reviewer | 9.0/10 | Verified minimal blast radius, consistent pattern, existing try/except guards cover any reverse() failure |
| Average | 9.25/10 | Pass (threshold: 8.0) |

## Agent-Flagged Items (Non-blocking)

- Both agents independently noted the silent bug fix: the old hardcoded `/profile/` path
  was already broken (pointing to a non-existent URL). The `reverse()` change fixes it.
  Both recommended documenting this in the commit message — noted in this report.

## Test Results

| Metric | Value |
|--------|-------|
| Tests | 1155 |
| Failures | 0 |
| Skipped | 12 |

## Follow-up Items

- The 6 existing notification tests mock `create_notification` and do not exercise the
  URL construction. If notification helper tests are added in a future spec, they should
  use a real job object and assert the `link` field resolves to the expected path.
