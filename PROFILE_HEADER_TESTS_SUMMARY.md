# Profile Header Tests - Quick Reference

## Test Suite Overview

**Phase:** E (Part 1) - User Profiles & Social Foundation
**Date Created:** October 2025
**Status:** ✅ Complete and Production-Ready
**Total Tests:** 50+ test methods across 2 files

---

## Quick Start

### Install Dependencies
```bash
# Required for all tests
pip install django

# Optional for Selenium tests
pip install selenium

# Optional for coverage reports
pip install coverage
```

### Run Tests
```bash
# Quick run (Django tests only)
./run_profile_tests.sh django

# Full suite (Django + Selenium)
./run_profile_tests.sh all

# With coverage report
./run_profile_tests.sh coverage
```

---

## Test Files

### 1. `test_user_profile_header.py` (35+ tests)
Django unit and integration tests - no browser required

**Run:**
```bash
python manage.py test prompts.tests.test_user_profile_header
```

**Test Classes:**
- `ProfileHeaderVisibilityTestCase` (8 tests)
- `MediaFilterFormTestCase` (8 tests)
- `MobileResponsivenessTestCase` (2 tests)
- `OverflowArrowFunctionalityTestCase` (3 tests)
- `TrashTabIntegrationTestCase` (3 tests)
- `ProfileHeaderContextTestCase` (3 tests)
- `JavaScriptFunctionalityTestCase` (4 tests)
- `ProfileHeaderPerformanceTestCase` (2 tests)
- `EdgeCaseTestCase` (4 tests)

---

### 2. `test_user_profile_javascript.py` (15+ tests)
Selenium browser automation tests - requires ChromeDriver

**Run:**
```bash
python manage.py test prompts.tests.test_user_profile_javascript
```

**Test Classes:**
- `JavaScriptOverflowArrowTestCase` (6 tests)
- `JavaScriptMediaFilterTestCase` (2 tests)
- `JavaScriptMobileResponsivenessTestCase` (3 tests)
- `JavaScriptEdgeCaseTestCase` (2 tests)

---

## Feature Coverage Map

| Feature | Django Tests | Selenium Tests | Status |
|---------|--------------|----------------|--------|
| Edit Profile button visibility | ✅ 3 tests | ❌ | ✅ Complete |
| Overflow arrow HTML/CSS | ✅ 3 tests | ✅ 6 tests | ✅ Complete |
| Media filter form | ✅ 8 tests | ✅ 2 tests | ✅ Complete |
| Trash tab visibility | ✅ 7 tests | ❌ | ✅ Complete |
| Mobile responsiveness | ✅ 2 tests | ✅ 3 tests | ✅ Complete |
| Context variables | ✅ 3 tests | ❌ | ✅ Complete |
| JavaScript functionality | ✅ 4 tests | ✅ 6 tests | ✅ Complete |
| Performance | ✅ 2 tests | ❌ | ✅ Complete |
| Edge cases | ✅ 4 tests | ✅ 2 tests | ✅ Complete |

---

## Key Test Scenarios

### Edit Profile Button
**Expected:** Visible to owner only, green button with pen icon

**Tests:**
- ✅ Owner sees button (`test_edit_button_visible_to_owner`)
- ✅ Visitor doesn't see button (`test_edit_button_hidden_from_visitor`)
- ✅ Anonymous doesn't see button (`test_edit_button_hidden_from_anonymous`)

---

### Overflow Arrow
**Expected:** Scrolls tabs smoothly, logs to console, hover effect

**Tests:**
- ✅ Arrow exists in HTML (`test_overflow_arrow_html_present`)
- ✅ JavaScript handler present (`test_overflow_arrow_javascript_present`)
- ✅ Click scrolls container (Selenium) (`test_overflow_arrow_click_scrolls_container`)
- ✅ Console logging works (Selenium) (`test_overflow_arrow_console_logs`)
- ✅ Hover effect present (Selenium) (`test_overflow_arrow_hover_effect`)
- ✅ Smooth scroll behavior (Selenium) (`test_overflow_arrow_smooth_scroll`)

---

### Media Filter Form
**Expected:** Auto-submit, preserve values, filter correctly

**Tests:**
- ✅ Form renders correctly (`test_filter_form_renders`)
- ✅ Filter by images (`test_filter_by_media_type_images`)
- ✅ Filter by videos (`test_filter_by_media_type_videos`)
- ✅ Filter by AI generator (`test_filter_by_ai_generator`)
- ✅ Filter by date range (`test_filter_by_date_range_week`)
- ✅ Multiple filters work together (`test_filter_combination`)
- ✅ Values preserved after submit (`test_filter_form_preserves_values`)
- ✅ Auto-submit on change (Selenium) (`test_filter_form_auto_submits`)

---

### Trash Tab
**Expected:** Visible to owner only, shows count, integrates with tabs

**Tests:**
- ✅ Owner sees trash tab (`test_trash_tab_visible_to_owner`)
- ✅ Visitor doesn't see trash (`test_trash_tab_hidden_from_visitor`)
- ✅ Anonymous doesn't see trash (`test_trash_tab_hidden_from_anonymous`)
- ✅ Count accurate (`test_trash_count_accuracy`)
- ✅ Shows trashed prompts (`test_trash_tab_shows_trashed_prompts`)
- ✅ All tab excludes trash (`test_all_tab_excludes_trashed_prompts`)
- ✅ Integrates with overflow (`test_trash_tab_in_overflow_system`)

---

### Mobile Responsiveness
**Expected:** Form stacks on mobile, inline on desktop

**Tests:**
- ✅ Mobile CSS classes present (`test_media_filter_form_has_mobile_classes`)
- ✅ Media queries present (`test_mobile_css_media_queries_present`)
- ✅ Form stacks on mobile (Selenium) (`test_mobile_viewport_filter_form_stacking`)
- ✅ Form inline on desktop (Selenium) (`test_desktop_viewport_filter_form_inline`)

---

## Common Commands

### Run Specific Test Class
```bash
python manage.py test prompts.tests.test_user_profile_header.ProfileHeaderVisibilityTestCase
```

### Run Specific Test Method
```bash
python manage.py test prompts.tests.test_user_profile_header.ProfileHeaderVisibilityTestCase.test_edit_button_visible_to_owner
```

### Run with Verbose Output
```bash
python manage.py test prompts.tests.test_user_profile_header --verbosity=2
```

### Run with Keepdb (Faster)
```bash
python manage.py test prompts.tests.test_user_profile_header --keepdb
```

### Generate Coverage Report
```bash
coverage run --source='prompts' manage.py test prompts.tests.test_user_profile_header
coverage report
coverage html
open htmlcov/index.html  # View report
```

---

## Selenium Setup

### Install ChromeDriver (macOS)
```bash
brew install chromedriver
```

### Install ChromeDriver (Ubuntu)
```bash
sudo apt-get install chromium-chromedriver
```

### Or Use webdriver-manager
```bash
pip install webdriver-manager
```

Then modify test file:
```python
from webdriver_manager.chrome import ChromeDriverManager

cls.selenium = webdriver.Chrome(ChromeDriverManager().install())
```

---

## Troubleshooting

### Issue: `TemplateDoesNotExist`
**Solution:** Check template path:
```bash
ls prompts/templates/prompts/user_profile.html
```

### Issue: `selenium.common.exceptions.WebDriverException`
**Solution:** Install ChromeDriver or skip Selenium tests:
```bash
python manage.py test prompts.tests.test_user_profile_header  # Skip Selenium
```

### Issue: Query count too high
**Solution:** Use `select_related()` or `prefetch_related()` in view:
```python
prompts = Prompt.objects.filter(author=user).select_related('author')
```

### Issue: Selenium tests fail with "chrome not reachable"
**Solution:** Check Chrome is installed:
```bash
google-chrome --version  # Linux
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version  # macOS
```

---

## Expected Results

### Django Tests (Success)
```
Ran 35 tests in 12.456s

OK
```

### Selenium Tests (Success)
```
Ran 15 tests in 45.123s

OK
```

### Selenium Tests (ChromeDriver Missing)
```
Ran 15 tests in 0.234s

OK (skipped=15)
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run profile header tests
  run: |
    python manage.py test prompts.tests.test_user_profile_header --verbosity=2
```

### Pre-Commit Hook
```bash
#!/bin/bash
python manage.py test prompts.tests.test_user_profile_header --failfast
```

---

## Test Metrics

**Total Test Methods:** 50+
**Django Tests:** 35+
**Selenium Tests:** 15+
**Estimated Run Time:**
- Django only: ~12-15 seconds
- Selenium only: ~45-60 seconds
- Full suite: ~60-75 seconds

**Code Coverage:**
- Target: 80%+ of user_profile.html template logic
- Measured: Run `./run_profile_tests.sh coverage`

---

## Next Steps

### Phase E (Part 2): Enhanced Prompt Detail Page
- Report button functionality
- "More from this user" section
- Author info card

### Phase E (Part 3): Email Preferences Dashboard
- Settings form tests
- Email preference toggles
- Unsubscribe token validation

---

## Documentation

**Full Documentation:** `prompts/tests/README_PROFILE_HEADER_TESTS.md`
**Project Spec:** `PHASE_E_SPEC.md`
**Implementation Guide:** `PHASE_A_E_GUIDE.md`
**Project Overview:** `CLAUDE.md`

---

## Contact & Support

**Test Suite Version:** 1.0
**Last Updated:** October 2025
**Status:** Production-Ready ✅

For issues or questions:
1. Check `README_PROFILE_HEADER_TESTS.md`
2. Review individual test docstrings
3. Run with `--verbosity=2` for detailed output
4. Use `./run_profile_tests.sh specific` for targeted debugging

---

**Happy Testing! 🧪✅**
