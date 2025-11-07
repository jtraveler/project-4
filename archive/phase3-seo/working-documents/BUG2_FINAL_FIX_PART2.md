# Bug 2: Final Fix - Part 2

**Issue Found:** Getting 404 instead of redirect to trash

**Root Cause:**
`prompt_queryset` was using `Prompt.objects` which uses the custom `PromptManager` that **excludes deleted prompts**. So `get_object_or_404()` was throwing 404 before the `deleted_at` check could run.

**Solution:**
Changed `Prompt.objects` to `Prompt.all_objects` on line 172.

**Change Made:**

```python
# Before (line 171):
prompt_queryset = Prompt.objects.select_related('author').prefetch_related(...)

# After (line 172):
prompt_queryset = Prompt.all_objects.select_related('author').prefetch_related(...)
```

**Why This Works:**
- `Prompt.all_objects` includes deleted prompts
- Authenticated user: Prompt fetched → `deleted_at` check runs → Redirect to trash ✅
- Anonymous user: Still protected by `deleted_at__isnull=True` filter (line 216) → 404 ✅

**Testing Required:**
Same as before - delete a prompt, go to homepage, click back button. Should now see redirect to trash with message instead of 404.
