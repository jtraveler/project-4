# UserProfileForm - Usage Examples

**Real-world validation scenarios and error handling**

---

## Example 1: Basic Usage (Happy Path)

**User Input:**
- Bio: "AI artist creating prompts for Midjourney and DALL-E"
- Avatar: `portrait.jpg` (2MB, 1200x1200px)
- Twitter: `twitter.com/username`
- Instagram: `instagram.com/artist.studio`
- Website: `myportfolio.com`

**What Happens:**

```python
# View processing
form = UserProfileForm(request.POST, request.FILES, instance=profile)

# Form validation
form.is_valid()  # True

# Field cleaning
bio → "AI artist creating prompts for Midjourney and DALL-E" (trimmed)
avatar → File object (valid)
twitter_url → "https://twitter.com/username" (auto-corrected)
instagram_url → "https://instagram.com/artist.studio" (auto-corrected)
website_url → "https://myportfolio.com" (auto-corrected)

# Save
profile = form.save()
# Avatar automatically uploaded to Cloudinary
# Transformation applied: 300x300 crop, face gravity
# profile.avatar.url → "https://res.cloudinary.com/...transformations.../portrait.jpg"
```

**Result:** ✅ Profile saved successfully

---

## Example 2: Avatar Too Large

**User Input:**
- Avatar: `huge_photo.jpg` (8MB, 6000x4000px)

**What Happens:**

```python
form.is_valid()  # False

# clean_avatar() raises error
ValidationError('Avatar file size must be under 5MB.')

# Form errors
form.errors['avatar'] = ['Avatar file size must be under 5MB.']
```

**Template Display:**

```html
<div class="invalid-feedback d-block">
    Avatar file size must be under 5MB.
</div>
```

**Result:** ❌ Form rejected with clear error message

---

## Example 3: Invalid Twitter URL

**User Input:**
- Twitter: `facebook.com/page`

**What Happens:**

```python
# clean_twitter_url() validates
url = "https://facebook.com/page"  # Auto-corrected to https://
pattern = r'https?://(www\.)?(twitter\.com|x\.com)/[\w]+/?'
re.match(pattern, url)  # False

# Raises error
ValidationError('Please enter a valid Twitter/X URL (e.g., https://twitter.com/username)')
```

**Result:** ❌ `"Twitter/X URL: Please enter a valid Twitter/X URL..."`

---

## Example 4: Avatar Too Small

**User Input:**
- Avatar: `tiny.jpg` (50KB, 50x50px)

**What Happens:**

```python
# clean_avatar() checks dimensions with Pillow
from PIL import Image
image = Image.open(avatar)
width, height = image.size  # (50, 50)

if width < 100 or height < 100:
    raise ValidationError('Avatar must be at least 100x100 pixels.')
```

**Result:** ❌ `"Avatar: Avatar must be at least 100x100 pixels."`

---

## Example 5: Multiple Errors

**User Input:**
- Bio: (501 characters - too long)
- Avatar: `document.pdf` (wrong file type)
- Twitter: `not-a-url`
- Instagram: (empty)
- Website: `https://` + "x" * 195  # 203 chars total

**What Happens:**

```python
form.is_valid()  # False

# Multiple validation errors
form.errors = {
    'bio': ['Bio cannot exceed 500 characters.'],
    'avatar': ['Invalid file format. Please upload JPG, PNG, or WebP.'],
    'twitter_url': ['Please enter a valid Twitter/X URL (e.g., https://twitter.com/username)'],
    'website_url': ['URL cannot exceed 200 characters.']
}
```

**Template Display:**

```html
<div class="alert alert-danger">
    <h4>Please correct the following errors:</h4>
    <ul>
        <li>Bio: Bio cannot exceed 500 characters.</li>
        <li>Avatar: Invalid file format. Please upload JPG, PNG, or WebP.</li>
        <li>Twitter/X URL: Please enter a valid Twitter/X URL...</li>
        <li>Website URL: URL cannot exceed 200 characters.</li>
    </ul>
</div>
```

**Result:** ❌ Multiple errors displayed, form preserved

---

## Example 6: Clearing Avatar

**User Input:**
- Checks "Clear" checkbox for avatar
- Keeps other fields unchanged

**What Happens:**

```python
# ClearableFileInput sets avatar to False (Django convention)
form.cleaned_data['avatar'] = False

# Form saves
profile = form.save()
profile.avatar  # None (cleared in database)

# Signal handler deletes old avatar from Cloudinary
@receiver(pre_save, sender=UserProfile)
def delete_old_avatar(sender, instance, **kwargs):
    # Detects avatar changed from [public_id] to None
    cloudinary.uploader.destroy(old_avatar.public_id)
```

**Result:** ✅ Avatar removed from profile and Cloudinary

---

## Example 7: No Changes Submitted

**User Input:**
- Clicks "Save Changes" without editing anything

**What Happens:**

```python
# Form bound with POST data
form = UserProfileForm(request.POST, request.FILES, instance=profile)

# All fields match existing values
form.is_valid()  # True
form.has_changed()  # False

# Save anyway (Django creates UPDATE query, no DB changes)
profile = form.save()

# Success message
messages.success(request, 'Profile updated successfully!')
```

**Result:** ✅ Success message shown, no actual database changes

**Optimization (optional):**

```python
if form.is_valid():
    if form.has_changed():
        form.save()
        messages.success(request, 'Profile updated successfully!')
    else:
        messages.info(request, 'No changes detected.')
```

---

## Example 8: URL Auto-Correction

**User Input:**
- Twitter: `x.com/elonmusk`
- Instagram: `www.instagram.com/artist`
- Website: `example.com/portfolio`

**What Happens:**

```python
# clean_twitter_url()
url = "x.com/elonmusk"
if not url.startswith(('http://', 'https://')):
    url = f'https://{url}'  # "https://x.com/elonmusk"
# Validates against pattern → True
return url  # "https://x.com/elonmusk"

# clean_instagram_url()
url = "www.instagram.com/artist"
url = f'https://{url}'  # "https://www.instagram.com/artist"
return url

# clean_website_url()
url = "example.com/portfolio"
url = f'https://{url}'  # "https://example.com/portfolio"
return url
```

**Result:** ✅ All URLs auto-corrected to full HTTPS URLs

---

## Example 9: Edge Case - GIF Upload Attempt

**User Input:**
- Avatar: `animated.gif` (3MB, 500x500px)

**What Happens:**

```python
# clean_avatar() checks file extension
filename = "animated.gif".lower()
valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']

if not any(filename.endswith(ext) for ext in valid_extensions):
    raise ValidationError('Invalid file format. Please upload JPG, PNG, or WebP.')
```

**Result:** ❌ `"Avatar: Invalid file format. Please upload JPG, PNG, or WebP."`

**Note:** GIFs are explicitly blocked (not in `valid_extensions` list)

---

## Example 10: Pillow Not Installed (Graceful Degradation)

**User Input:**
- Avatar: `photo.jpg` (4MB, 200x200px)

**What Happens:**

```python
# clean_avatar() tries to import Pillow
try:
    from PIL import Image
    # ... dimension validation ...
except ImportError:
    # Pillow not installed, skip dimension validation
    pass  # File still validates (size, type checks passed)

# Form saves successfully
profile = form.save()
```

**Result:** ✅ Profile saved (dimension checks skipped gracefully)

**Recommendation:** Install Pillow in production for full validation:
```bash
pip install Pillow
```

---

## Example 11: Cloudinary Upload Error

**User Input:**
- Avatar: `valid_photo.jpg` (2MB, 1000x1000px)
- (Cloudinary API key invalid or network error)

**What Happens:**

```python
# Form validation passes
form.is_valid()  # True

# Attempt save
try:
    profile = form.save()
except Exception as e:
    # Cloudinary raises CloudinaryException
    logger.error(f"Cloudinary error: {e}")
    messages.error(request, f'Error uploading avatar: {str(e)}')
    # Render form again with error message
```

**Result:** ❌ Error message displayed, form preserved

**Best Practice View Code:**

```python
if form.is_valid():
    try:
        form.save()
        messages.success(request, 'Profile updated!')
        return redirect('user_profile', username=request.user.username)
    except Exception as e:
        logger.error(f"Profile save error: {e}", exc_info=True)
        messages.error(request, 'An error occurred. Please try again.')
        # Falls through to render form with error
```

---

## Example 12: Profanity in Bio (Optional Feature)

**User Input:**
- Bio: "Check out my awesome [profane word] prompts!"

**What Happens (if profanity check enabled):**

```python
def clean_bio(self):
    bio = self.cleaned_data.get('bio', '').strip()

    # Profanity check (commented out by default)
    if bio:
        profanity_service = ProfanityFilterService()
        is_clean, found_words, max_severity = profanity_service.check_text(bio)
        if not is_clean and max_severity in ['high', 'critical']:
            raise ValidationError('Bio contains inappropriate content.')

    return bio
```

**Result:** ❌ `"Bio: Bio contains inappropriate content."`

**Note:** Profanity check is **commented out by default** in the form. Uncomment lines 305-310 to enable.

---

## Example 13: Special Characters in URLs

**User Input:**
- Instagram: `instagram.com/user.name_123`
- Twitter: `twitter.com/user_name`

**What Happens:**

```python
# Instagram regex allows dots and underscores
pattern = r'https?://(www\.)?instagram\.com/[\w.]+/?'
# [\w.] matches word chars and dots
re.match(pattern, "https://instagram.com/user.name_123")  # True

# Twitter regex allows underscores
pattern = r'https?://(www\.)?(twitter\.com|x\.com)/[\w]+/?'
# [\w] matches word chars and underscores
re.match(pattern, "https://twitter.com/user_name")  # True
```

**Result:** ✅ Both URLs validated successfully

---

## Example 14: Empty Form Submission

**User Input:**
- (All fields left empty)

**What Happens:**

```python
# All fields are optional
for field in self.fields:
    self.fields[field].required = False

# Validation passes
form.is_valid()  # True

# Save (no changes to database if instance exists)
profile = form.save()
```

**Result:** ✅ Profile saved (no errors, no changes)

**Optional: Require at least one field**

Uncomment lines 442-452 in form to enforce:

```python
def clean(self):
    cleaned_data = super().clean()

    has_content = any([
        cleaned_data.get('bio'),
        cleaned_data.get('avatar'),
        cleaned_data.get('twitter_url'),
        cleaned_data.get('instagram_url'),
        cleaned_data.get('website_url'),
    ])
    if not has_content:
        raise ValidationError('Please fill in at least one field.')

    return cleaned_data
```

---

## Example 15: International Characters in Bio

**User Input:**
- Bio: "日本のAIアーティスト 🎨 Creating amazing art!"

**What Happens:**

```python
# Django handles Unicode correctly
bio = "日本のAIアーティスト 🎨 Creating amazing art!"
len(bio)  # Character count, not byte count

# Validation
if len(bio) > 500:  # Character-based limit
    raise ValidationError('Bio cannot exceed 500 characters.')
```

**Result:** ✅ Unicode and emojis handled correctly

---

## Testing Checklist

Use these examples to test your implementation:

- [ ] Valid avatar upload (JPG, PNG, WebP under 5MB)
- [ ] Avatar too large (>5MB)
- [ ] Avatar wrong format (PDF, GIF, etc.)
- [ ] Avatar too small (<100x100)
- [ ] Avatar too large (>4000x4000)
- [ ] Bio at character limit (exactly 500)
- [ ] Bio over character limit (501+)
- [ ] Twitter URL auto-correction (no https://)
- [ ] Instagram URL auto-correction
- [ ] Website URL auto-correction
- [ ] Invalid Twitter URL (wrong domain)
- [ ] Invalid Instagram URL (wrong domain)
- [ ] Clear avatar checkbox
- [ ] Empty form submission
- [ ] No changes (submit without editing)
- [ ] Multiple errors at once
- [ ] Unicode characters in bio
- [ ] Emojis in bio
- [ ] Special characters in usernames (dots, underscores)
- [ ] Network error during save

---

## Summary

**The form handles:**
✅ File uploads (automatic Cloudinary integration)
✅ Size validation (5MB avatar limit)
✅ Type validation (JPG, PNG, WebP only)
✅ Dimension validation (100x100 min, 4000x4000 max)
✅ URL validation (pattern matching)
✅ URL auto-correction (adds https://)
✅ Character limits (500 chars for bio)
✅ Multiple errors (all displayed together)
✅ Graceful degradation (Pillow optional)
✅ Unicode support (international characters)
✅ User-friendly error messages
✅ Avatar deletion (clear checkbox + signal)

**What you need to implement:**
- View function
- URL pattern
- Template
- Optional: Avatar cleanup signal
- Optional: Character counter JavaScript
- Optional: Profanity filter in bio

See `USER_PROFILE_FORM_QUICKSTART.md` for implementation steps.
