# Views Split - Testing Checklist

**Date**: December 13, 2025
**Task**: Verify views.py split into modular package

## Pre-Testing Verification

- [x] All 11 module files created
- [x] Python syntax valid (all files compile)
- [x] Backup created (views.py.backup)
- [x] __init__.py exports all 47 views
- [x] Documentation created (README.md, STRUCTURE.txt)

## 1. Automated Testing

### Run Full Test Suite

```bash
cd /Users/matthew/Documents/vscode-projects/project-4/live-working-project
python manage.py test prompts
```

- [ ] All tests pass
- [ ] No import errors
- [ ] No deprecation warnings
- [ ] Test count matches expected (~70+ tests)

**If tests fail**: Check error messages, verify imports, consider rollback

## 2. Server Startup

### Start Development Server

```bash
python manage.py runserver
```

- [ ] Server starts without errors
- [ ] No import errors in console
- [ ] No "Module not found" errors
- [ ] Django loads successfully

**If errors occur**: Note the specific import error and fix in affected module

## 3. Critical Path Testing

### Homepage (PromptList)
- [ ] Navigate to http://localhost:8000/
- [ ] Homepage loads successfully
- [ ] Prompts display in grid
- [ ] No 500 errors
- [ ] Load More button works
- [ ] Tabs work (Home/All/Photos/Videos)

### Prompt Detail (prompt_detail)
- [ ] Click on any prompt
- [ ] Detail page loads
- [ ] Image displays
- [ ] Comments section visible
- [ ] Like button present

### Upload Flow (upload_views)
- [ ] Navigate to /upload/
- [ ] Step 1 drag-and-drop works
- [ ] Step 2 form loads
- [ ] Can submit upload
- [ ] No errors during upload

### User Profile (user_views)
- [ ] Navigate to /users/[username]/
- [ ] Profile page loads
- [ ] User's prompts display
- [ ] Edit profile link works
- [ ] Email preferences accessible

### Social Features (social_views)
- [ ] Follow button works
- [ ] Unfollow button works
- [ ] Follow status updates correctly
- [ ] No AJAX errors in console

### API Endpoints (api_views)
- [ ] Like button works (AJAX)
- [ ] Prompt reordering works (admin)
- [ ] No 403/404 errors
- [ ] JSON responses valid

### Admin Tools (admin_views)
- [ ] Navigate to admin dashboard
- [ ] Media issues page loads
- [ ] Bulk actions work
- [ ] No permission errors

### Leaderboard (leaderboard_views)
- [ ] Navigate to /leaderboard/
- [ ] Page loads successfully
- [ ] Rankings display
- [ ] Filters work

### AI Generator Pages (generator_views)
- [ ] Navigate to /ai/midjourney/
- [ ] Category page loads
- [ ] Prompts filter correctly
- [ ] Pagination works

## 4. Import Verification

### Python Shell Test

```bash
python manage.py shell
```

```python
# Test imports
from prompts.views import PromptList
from prompts.views import prompt_detail, prompt_edit
from prompts.views import upload_step1, upload_step2
from prompts.views import user_profile, follow_user
from prompts.views import leaderboard
from prompts.views import ai_generator_category

# Check all 47 views are accessible
from prompts import views
print(f"Total exports: {len([x for x in dir(views) if not x.startswith('_')])}")
# Should print ~47-50 (47 views + a few Django internals)
```

- [ ] All imports successful
- [ ] No ImportError exceptions
- [ ] View functions/classes accessible
- [ ] Export count matches expected

## 5. URL Routing Check

### Verify All URLs Resolve

```bash
python manage.py show_urls | grep prompts
```

- [ ] All URL patterns still resolve
- [ ] No broken references
- [ ] View names match

Or manually test these URLs:
- [ ] / (homepage)
- [ ] /prompt/[slug]/ (detail)
- [ ] /upload/ (upload)
- [ ] /users/[username]/ (profile)
- [ ] /leaderboard/
- [ ] /ai/midjourney/
- [ ] Admin URLs still work

## 6. Error Log Check

### Monitor for Warnings

While testing, watch for:
- [ ] No import warnings in logs
- [ ] No "module not found" errors
- [ ] No circular import issues
- [ ] No deprecation warnings

## 7. Browser Console Check

### Check for JavaScript Errors

Open browser DevTools and verify:
- [ ] No 404 errors for static files
- [ ] No AJAX endpoint failures
- [ ] No CORS issues
- [ ] API responses valid JSON

## 8. Performance Check

### Compare Before/After

- [ ] Page load times similar
- [ ] No significant performance degradation
- [ ] Memory usage normal
- [ ] No circular import warnings

## 9. Documentation Review

### Verify Documentation

- [ ] README.md is complete
- [ ] STRUCTURE.txt is accurate
- [ ] VIEWS_SPLIT_SUMMARY.md is clear
- [ ] Inline docstrings preserved

## 10. Final Verification

### All Systems Go

- [ ] All automated tests pass
- [ ] All manual tests pass
- [ ] No import errors
- [ ] No URL routing errors
- [ ] Documentation complete
- [ ] Backup still available

## Post-Testing Actions

### If All Tests Pass ✅

```bash
# Delete backup
rm prompts/views.py.backup

# Commit to git
git add prompts/views/
git add VIEWS_SPLIT_SUMMARY.md
git add TESTING_CHECKLIST.md
git commit -m "refactor(views): Split monolithic views.py into modular package

- Split 3,929-line views.py into 11 focused modules
- Maintained 100% backward compatibility
- All 70+ tests passing
- Comprehensive documentation added

Modules: redirect, prompt, upload, user, social, api, admin, generator, leaderboard, utility
"

# Push to remote
git push origin main
```

### If Tests Fail ❌

```bash
# Rollback to original
mv prompts/views.py.backup prompts/views.py
rm -rf prompts/views/

# Investigate errors
# Fix issues in modules
# Re-run tests
```

## Common Issues & Solutions

### Issue: "Module not found"
**Solution**: Check import paths in affected module, verify __init__.py exports

### Issue: "Cannot import name 'X'"
**Solution**: Verify function is in correct module and listed in __all__

### Issue: Circular import
**Solution**: Move shared utilities to separate module or use lazy imports

### Issue: Tests fail but views work
**Solution**: Check test imports, may need to update test file imports

## Notes

- Keep `views.py.backup` until all tests pass
- Test on both local development and staging if available
- Consider testing with different Python versions
- Verify all decorators preserved correctly
- Check that all permissions checks still work

## Sign-Off

- [ ] All automated tests passing
- [ ] All manual tests passing
- [ ] No errors in logs
- [ ] Documentation reviewed
- [ ] Code committed to git
- [ ] Backup removed

**Tester**: _____________________
**Date**: _____________________
**Status**: ✅ APPROVED / ❌ NEEDS WORK
