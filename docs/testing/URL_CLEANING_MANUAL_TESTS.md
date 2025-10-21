# Manual Testing Checklist for Social Media URL Cleaning

This checklist can be used for manual testing before or alongside automated tests.

## How to Use This Checklist

1. **Access the form:** Navigate to the user profile edit page
2. **Test each input:** Enter the value in the appropriate field
3. **Record result:** Mark ✅ if behaves as expected, ❌ if not
4. **Note errors:** Record any unexpected behavior or error messages

---

## Section 1: Twitter Field - Valid Inputs

**Expected Behavior:** All should convert to `https://twitter.com/[username]` format

| # | Input Value | Expected Output | Status | Notes |
|---|-------------|-----------------|--------|-------|
| 1 | `elonmusk` | `https://twitter.com/elonmusk` | ⬜ |  |
| 2 | `@elonmusk` | `https://twitter.com/elonmusk` | ⬜ |  |
| 3 | `https://twitter.com/elonmusk` | `https://twitter.com/elonmusk` | ⬜ |  |
| 4 | `https://x.com/elonmusk` | `https://twitter.com/elonmusk` | ⬜ |  |
| 5 | `http://twitter.com/elonmusk` | `https://twitter.com/elonmusk` | ⬜ | HTTP → HTTPS |
| 6 | `elon_musk` | `https://twitter.com/elon_musk` | ⬜ | Underscore allowed |
| 7 | `user123` | `https://twitter.com/user123` | ⬜ | Numbers allowed |
| 8 | `aaaaaaaaaaaaaaa` (15 chars) | `https://twitter.com/aaaaaaaaaaaaaaa` | ⬜ | Max length |
| 9 | `a` | `https://twitter.com/a` | ⬜ | Min length |
| 10 | `ElonMusk` | `https://twitter.com/ElonMusk` | ⬜ | Case preserved |
| 11 | `https://twitter.com/elonmusk/` | `https://twitter.com/elonmusk` | ⬜ | Trailing slash removed |
| 12 | `https://www.twitter.com/elonmusk` | `https://twitter.com/elonmusk` | ⬜ | www normalized |
| 13 | `  elonmusk  ` | `https://twitter.com/elonmusk` | ⬜ | Whitespace trimmed |
| 14 | *(empty field)* | *(empty - saved as blank)* | ⬜ | Optional field |

**Total Valid Tests:** 14
**Passed:** ___ / 14

---

## Section 2: Twitter Field - Invalid Inputs

**Expected Behavior:** All should show validation error and prevent save

| # | Input Value | Expected Error Message | Status | Notes |
|---|-------------|------------------------|--------|-------|
| 15 | `aaaaaaaaaaaaaaaa` (16 chars) | "Enter a valid Twitter username (1-15 characters)" | ⬜ | Too long |
| 16 | `elon musk` | "Enter a valid Twitter username (alphanumeric and underscore only)" | ⬜ | Space not allowed |
| 17 | `elon!musk` | "Enter a valid Twitter username" | ⬜ | ! not allowed |
| 18 | `elon-musk` | "Enter a valid Twitter username" | ⬜ | Hyphen not allowed |
| 19 | `elon/musk` | "Enter a valid Twitter username" | ⬜ | Slash not allowed |
| 20 | `@@elonmusk` | "Enter a valid Twitter username" | ⬜ | Multiple @ symbols |
| 21 | `https://facebook.com/elonmusk` | "Enter a valid Twitter URL or username" | ⬜ | Wrong platform |
| 22 | `https://twiter.com/elonmusk` | "Enter a valid Twitter URL or username" | ⬜ | Domain typo |

**Total Invalid Tests:** 8
**Passed:** ___ / 8

---

## Section 3: Twitter Field - Security Tests

**Expected Behavior:** All should be rejected with validation error

| # | Input Value | Attack Type | Status | Notes |
|---|-------------|-------------|--------|-------|
| 23 | `../../../etc/passwd` | Path Traversal | ⬜ | Should reject |
| 24 | `<script>alert(1)</script>` | XSS Script Tag | ⬜ | Should reject |
| 25 | `user" onload="alert(1)` | XSS Event Handler | ⬜ | Should reject |
| 26 | `javascript:alert(1)` | JavaScript Protocol | ⬜ | Should reject |
| 27 | `data:text/html,<script>` | Data URI | ⬜ | Should reject |
| 28 | `@twitter.com@evil.com` | Open Redirect | ⬜ | Should reject |
| 29 | `user?admin=true` | Query Injection | ⬜ | Should reject |
| 30 | `user#admin` | Fragment Injection | ⬜ | Should reject |

**Total Security Tests:** 8
**Passed:** ___ / 8

---

## Section 4: Instagram Field - Valid Inputs

**Expected Behavior:** All should convert to `https://instagram.com/[username]` format

| # | Input Value | Expected Output | Status | Notes |
|---|-------------|-----------------|--------|-------|
| 31 | `instagram` | `https://instagram.com/instagram` | ⬜ |  |
| 32 | `@instagram` | `https://instagram.com/instagram` | ⬜ |  |
| 33 | `https://instagram.com/instagram` | `https://instagram.com/instagram` | ⬜ |  |
| 34 | `http://instagram.com/instagram` | `https://instagram.com/instagram` | ⬜ | HTTP → HTTPS |
| 35 | `user.name` | `https://instagram.com/user.name` | ⬜ | Dot allowed |
| 36 | `user_name` | `https://instagram.com/user_name` | ⬜ | Underscore allowed |
| 37 | `user123` | `https://instagram.com/user123` | ⬜ | Numbers allowed |
| 38 | `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` (30 chars) | `https://instagram.com/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` | ⬜ | Max length |
| 39 | `a` | `https://instagram.com/a` | ⬜ | Min length |
| 40 | `user.name_123` | `https://instagram.com/user.name_123` | ⬜ | Complex username |
| 41 | `https://www.instagram.com/user` | `https://instagram.com/user` | ⬜ | www normalized |
| 42 | `  instagram  ` | `https://instagram.com/instagram` | ⬜ | Whitespace trimmed |
| 43 | *(empty field)* | *(empty - saved as blank)* | ⬜ | Optional field |

**Total Valid Tests:** 13
**Passed:** ___ / 13

---

## Section 5: Instagram Field - Invalid Inputs

**Expected Behavior:** All should show validation error

| # | Input Value | Expected Error Message | Status | Notes |
|---|-------------|------------------------|--------|-------|
| 44 | `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` (31 chars) | "Enter a valid Instagram username (1-30 characters)" | ⬜ | Too long |
| 45 | `user name` | "Enter a valid Instagram username" | ⬜ | Space not allowed |
| 46 | `user!name` | "Enter a valid Instagram username" | ⬜ | ! not allowed |
| 47 | `user-name` | "Enter a valid Instagram username" | ⬜ | Hyphen not allowed |
| 48 | `user/name` | "Enter a valid Instagram username" | ⬜ | Slash not allowed |
| 49 | `.username` | "Enter a valid Instagram username" | ⬜ | Can't start with dot |
| 50 | `username.` | "Enter a valid Instagram username" | ⬜ | Can't end with dot |
| 51 | `user..name` | "Enter a valid Instagram username" | ⬜ | Consecutive dots |
| 52 | `https://twitter.com/username` | "Enter a valid Instagram URL or username" | ⬜ | Wrong platform |

**Total Invalid Tests:** 9
**Passed:** ___ / 9

---

## Section 6: Instagram Field - Security Tests

**Expected Behavior:** All should be rejected

| # | Input Value | Attack Type | Status | Notes |
|---|-------------|-------------|--------|-------|
| 53 | `../../admin` | Path Traversal | ⬜ | Should reject |
| 54 | `<script>alert(1)</script>` | XSS Script Tag | ⬜ | Should reject |
| 55 | `javascript:alert(1)` | JavaScript Protocol | ⬜ | Should reject |
| 56 | `username?redirect=evil.com` | Query Injection | ⬜ | Should reject |

**Total Security Tests:** 4
**Passed:** ___ / 4

---

## Section 7: Website Field - Valid Inputs

**Expected Behavior:** All should be formatted as `https://[domain][path]`

| # | Input Value | Expected Output | Status | Notes |
|---|-------------|-----------------|--------|-------|
| 57 | `example.com` | `https://example.com` | ⬜ | Add HTTPS |
| 58 | `www.example.com` | `https://www.example.com` | ⬜ | Preserve www |
| 59 | `https://example.com` | `https://example.com` | ⬜ | Already formatted |
| 60 | `http://example.com` | `https://example.com` | ⬜ | HTTP → HTTPS |
| 61 | `blog.example.com` | `https://blog.example.com` | ⬜ | Subdomain |
| 62 | `example.com/about` | `https://example.com/about` | ⬜ | With path |
| 63 | `example.com?ref=twitter` | `https://example.com?ref=twitter` | ⬜ | With query |
| 64 | `example.com#section` | `https://example.com#section` | ⬜ | With anchor |
| 65 | `blog.example.com/page?id=123#top` | `https://blog.example.com/page?id=123#top` | ⬜ | Complex URL |
| 66 | `my-site.com` | `https://my-site.com` | ⬜ | Hyphenated domain |
| 67 | `api.dev.example.com` | `https://api.dev.example.com` | ⬜ | Multiple subdomains |
| 68 | `  example.com  ` | `https://example.com` | ⬜ | Whitespace trimmed |
| 69 | `EXAMPLE.COM` | `https://example.com` | ⬜ | Lowercase domain |
| 70 | *(empty field)* | *(empty - saved as blank)* | ⬜ | Optional field |

**Total Valid Tests:** 14
**Passed:** ___ / 14

---

## Section 8: Website Field - Invalid Inputs

**Expected Behavior:** All should show validation error

| # | Input Value | Expected Error Message | Status | Notes |
|---|-------------|------------------------|--------|-------|
| 71 | `example.123` | "Enter a valid URL" | ⬜ | Invalid TLD |
| 72 | `example` | "Enter a valid URL" | ⬜ | No TLD |
| 73 | `my site.com` | "Enter a valid URL" | ⬜ | Space in domain |
| 74 | `my@site.com` | "Enter a valid URL" | ⬜ | @ in domain |
| 75 | `example.com//page` | "Enter a valid URL" | ⬜ | Double slash |
| 76 | `ftp://example.com` | "Enter a valid URL" | ⬜ | FTP protocol |

**Total Invalid Tests:** 6
**Passed:** ___ / 6

---

## Section 9: Website Field - Security Tests

**Expected Behavior:** All should be rejected

| # | Input Value | Attack Type | Status | Notes |
|---|-------------|-------------|--------|-------|
| 77 | `example.com/../../etc/passwd` | Path Traversal | ⬜ | Should reject |
| 78 | `example.com/..%2F..%2Fadmin` | Encoded Path Traversal | ⬜ | Should reject |
| 79 | `<script>alert(1)</script>` | XSS Script Tag | ⬜ | Should reject |
| 80 | `javascript:alert(document.cookie)` | JavaScript Protocol | ⬜ | Should reject |
| 81 | `file:///etc/passwd` | File Protocol | ⬜ | Should reject |
| 82 | `data:text/html,<h1>Phish</h1>` | Data Protocol | ⬜ | Should reject |

**Total Security Tests:** 6
**Passed:** ___ / 6

---

## Section 10: Cross-Field Integration Tests

**Expected Behavior:** Form handles multiple fields correctly

| # | Test Scenario | Expected Result | Status | Notes |
|---|---------------|-----------------|--------|-------|
| 83 | All fields empty | Form saves successfully | ⬜ | Optional fields |
| 84 | All fields valid | All URLs cleaned and saved correctly | ⬜ |  |
| 85 | Twitter valid, Instagram empty, Website valid | Valid fields saved, empty field blank | ⬜ |  |
| 86 | Twitter invalid (too long), others valid | Error on Twitter only, form doesn't save | ⬜ |  |
| 87 | All fields have whitespace only | All treated as empty, form saves | ⬜ |  |
| 88 | Mix of valid usernames and full URLs | All normalized to full URLs | ⬜ |  |

**Total Integration Tests:** 6
**Passed:** ___ / 6

---

## Section 11: Edge Case Tests

**Expected Behavior:** System handles unusual but valid inputs

| # | Input Field | Input Value | Expected Behavior | Status | Notes |
|---|-------------|-------------|-------------------|--------|-------|
| 89 | Twitter | `https://mobile.twitter.com/user` | Normalize to `https://twitter.com/user` | ⬜ | Mobile URL |
| 90 | Instagram | `https://m.instagram.com/user` | Normalize to `https://instagram.com/user` | ⬜ | Mobile URL |
| 91 | Website | `example.com///` | Clean to `https://example.com` | ⬜ | Multiple slashes |
| 92 | All fields | *(extremely long input - 500+ chars)* | Reject with clear error | ⬜ | DOS prevention |
| 93 | Twitter | `ELONMUSK` | Preserve case: `https://twitter.com/ELONMUSK` | ⬜ | Case handling |
| 94 | Website | `ExAmPlE.CoM` | Lowercase domain: `https://example.com` | ⬜ | Domain normalization |

**Total Edge Case Tests:** 6
**Passed:** ___ / 6

---

## Testing Summary

**Total Test Cases:** 94

### By Category:
- ✅ Twitter Valid: ___ / 14
- ❌ Twitter Invalid: ___ / 8
- 🛡️ Twitter Security: ___ / 8
- ✅ Instagram Valid: ___ / 13
- ❌ Instagram Invalid: ___ / 9
- 🛡️ Instagram Security: ___ / 4
- ✅ Website Valid: ___ / 14
- ❌ Website Invalid: ___ / 6
- 🛡️ Website Security: ___ / 6
- 🔗 Integration: ___ / 6
- 🎯 Edge Cases: ___ / 6

### Overall Pass Rate: ___ / 94 (___%)

---

## Critical Failures

**If any of these fail, DO NOT deploy to production:**

- [ ] **Path Traversal** (Tests 23, 53, 77, 78) - Must reject
- [ ] **XSS Injection** (Tests 24, 25, 54, 79) - Must reject
- [ ] **Open Redirect** (Test 28) - Must reject
- [ ] **Protocol Injection** (Tests 26, 27, 55, 76, 80, 81, 82) - Must reject
- [ ] **Invalid Characters** (All "Invalid Input" sections) - Must show errors
- [ ] **Empty Fields** (Tests 14, 43, 70, 87) - Must accept as optional

---

## Notes and Observations

*(Use this space to record any unexpected behavior, edge cases discovered during testing, or areas needing improvement)*

---

## Test Environment

- **Date Tested:** __________
- **Tester Name:** __________
- **Browser:** __________
- **OS:** __________
- **Form URL:** __________
- **Django Version:** __________

---

## Next Steps After Testing

1. **If all tests pass:**
   - ✅ Document test results
   - ✅ Commit automated test file
   - ✅ Deploy to staging
   - ✅ Retest on staging
   - ✅ Deploy to production

2. **If tests fail:**
   - ❌ Document failures in detail
   - ❌ Create bug tickets
   - ❌ Fix issues
   - ❌ Retest
   - ❌ Repeat until all pass

3. **Continuous Improvement:**
   - Add new edge cases discovered during manual testing to automated suite
   - Monitor production logs for unexpected input patterns
   - Update tests as requirements change
