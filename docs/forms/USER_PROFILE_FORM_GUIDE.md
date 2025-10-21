# UserProfileForm Implementation Guide

**Created:** October 20, 2025
**Purpose:** Complete guide for using and customizing the UserProfile ModelForm

---

## Table of Contents

1. [Overview](#overview)
2. [Form Features](#form-features)
3. [Usage in Views](#usage-in-views)
4. [Cloudinary Integration](#cloudinary-integration)
5. [Field-by-Field Details](#field-by-field-details)
6. [Validation Strategy](#validation-strategy)
7. [Template Implementation](#template-implementation)
8. [JavaScript Enhancement](#javascript-enhancement)
9. [Error Handling](#error-handling)
10. [Best Practices](#best-practices)

---

## Overview

The `UserProfileForm` is a Django ModelForm for editing user profile information with:
- Bio text area (500 character limit)
- Avatar upload (Cloudinary-backed)
- Social media URLs (Twitter/X, Instagram)
- Personal website URL
- Comprehensive validation
- User-friendly error messages

**Location:** `prompts/forms.py`
**Model:** `UserProfile` (one-to-one with Django User)

---

## Form Features

### 1. Bio Field
- **Type:** Textarea
- **Max Length:** 500 characters
- **Features:**
  - Character counter (via data attributes)
  - HTML maxlength attribute (client-side enforcement)
  - Server-side validation (defense in depth)
  - Optional profanity filtering (commented out by default)

### 2. Avatar Field
- **Type:** ImageField with ClearableFileInput
- **Max Size:** 5MB
- **Allowed Formats:** JPG, PNG, WebP
- **Validation:**
  - File size check
  - File type validation
  - Dimension validation (100x100 min, 4000x4000 max)
  - Pillow-based image verification
- **Cloudinary Integration:**
  - Automatic upload via model's CloudinaryField
  - Transformations applied (300x300 crop, face detection)
  - Auto-format and quality optimization

### 3. Social Media URLs
- **Twitter/X:** Validates twitter.com or x.com domains
- **Instagram:** Validates instagram.com domain
- **Pattern Matching:** Regex validation for proper URL structure
- **Auto-Correction:** Adds https:// if missing
- **User-Friendly Errors:** Suggests correct format

### 4. Website URL
- **Flexible Validation:** Accepts any valid URL
- **Auto-Correction:** Adds https:// if missing
- **Max Length:** 200 characters

---

## Usage in Views

### Basic Edit Profile View

```python
# prompts/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserProfileForm

@login_required
def edit_profile(request):
    """Edit user profile"""
    profile = request.user.userprofile

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('user_profile', username=request.user.username)
    else:
        form = UserProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'prompts/edit_profile.html', context)
```

### Advanced View with Error Handling

```python
@login_required
def edit_profile(request):
    """Edit user profile with comprehensive error handling"""
    profile = request.user.userprofile

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            try:
                # Save form (Cloudinary upload happens automatically)
                updated_profile = form.save()

                # Success message
                messages.success(
                    request,
                    'Your profile has been updated successfully!'
                )

                # Redirect to profile page
                return redirect('user_profile', username=request.user.username)

            except Exception as e:
                # Handle Cloudinary upload errors or other issues
                messages.error(
                    request,
                    f'Error saving profile: {str(e)}. Please try again.'
                )
                # Form stays populated, user can retry
        else:
            # Form validation errors (handled by template)
            messages.error(
                request,
                'Please correct the errors below.'
            )
    else:
        form = UserProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile,
        'current_avatar_url': profile.avatar.url if profile.avatar else None,
    }
    return render(request, 'prompts/edit_profile.html', context)
```

### URL Configuration

```python
# prompts/urls.py

urlpatterns = [
    # ... other URLs ...
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]
```

---

## Cloudinary Integration

### How It Works

**Django ModelForm + CloudinaryField = Automatic Upload**

1. **User submits form** with new avatar image
2. **Form validates** file size, type, dimensions (in `clean_avatar()`)
3. **Form saves** instance via `form.save()`
4. **CloudinaryField automatically uploads** to Cloudinary
5. **Model stores** Cloudinary public_id and URL

**No manual Cloudinary API calls needed!** The CloudinaryField handles everything.

### Avatar Transformations

Defined in the model:

```python
# prompts/models.py (already in your code)

avatar = CloudinaryField(
    'avatar',
    blank=True,
    null=True,
    transformation={
        'width': 300,
        'height': 300,
        'crop': 'fill',
        'gravity': 'face',  # Smart cropping focuses on faces
        'quality': 'auto',
        'fetch_format': 'auto'  # WebP for modern browsers
    },
)
```

### Handling Avatar Deletion

**Built-in with ClearableFileInput:**

When user checks "Clear" checkbox and saves:
1. Form sets `avatar` to `None`
2. Django/Cloudinary **does NOT** auto-delete old image
3. **Manual cleanup recommended** (see below)

**Option 1: Django Signal (Recommended)**

```python
# prompts/models.py

from django.db.models.signals import pre_save
from django.dispatch import receiver
import cloudinary.uploader

@receiver(pre_save, sender=UserProfile)
def delete_old_avatar(sender, instance, **kwargs):
    """Delete old avatar from Cloudinary when replaced"""
    if not instance.pk:
        return  # New instance, no old avatar

    try:
        old_profile = UserProfile.objects.get(pk=instance.pk)
        old_avatar = old_profile.avatar
        new_avatar = instance.avatar

        # If avatar changed or cleared
        if old_avatar and old_avatar != new_avatar:
            # Delete from Cloudinary
            cloudinary.uploader.destroy(old_avatar.public_id)
    except UserProfile.DoesNotExist:
        pass  # Should never happen, but safe
```

**Option 2: Manual Cleanup in View**

```python
@login_required
def edit_profile(request):
    profile = request.user.userprofile
    old_avatar_public_id = profile.avatar.public_id if profile.avatar else None

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            updated_profile = form.save()

            # Clean up old avatar if changed
            new_avatar_public_id = (
                updated_profile.avatar.public_id if updated_profile.avatar else None
            )
            if old_avatar_public_id and old_avatar_public_id != new_avatar_public_id:
                try:
                    cloudinary.uploader.destroy(old_avatar_public_id)
                except Exception as e:
                    # Log but don't fail the update
                    logger.warning(f"Failed to delete old avatar: {e}")

            messages.success(request, 'Profile updated!')
            return redirect('user_profile', username=request.user.username)
```

### Cloudinary URL Building

```python
# In template or view context
if profile.avatar:
    # Default transformation (from model)
    avatar_url = profile.avatar.url

    # Custom transformation (override defaults)
    from django.conf import settings
    custom_avatar = profile.avatar.build_url(
        cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
        width=150,
        height=150,
        crop='thumb',
        gravity='face',
        quality='auto'
    )
```

---

## Field-by-Field Details

### Bio Field

**Validation Rules:**
- Max 500 characters (enforced client + server)
- Trimmed whitespace
- Optional profanity check (commented out)

**Character Counter JavaScript:**

```javascript
// Add to edit_profile.html
document.addEventListener('DOMContentLoaded', function() {
    const bioField = document.getElementById('id_bio');
    const counter = document.createElement('div');
    counter.id = 'bio-counter';
    counter.className = 'form-text text-muted';
    bioField.parentNode.appendChild(counter);

    function updateCounter() {
        const current = bioField.value.length;
        const max = 500;
        counter.textContent = `${current} / ${max} characters`;

        // Change color near limit
        if (current > 450) {
            counter.classList.add('text-warning');
        } else {
            counter.classList.remove('text-warning');
        }

        if (current >= max) {
            counter.classList.add('text-danger');
        } else {
            counter.classList.remove('text-danger');
        }
    }

    bioField.addEventListener('input', updateCounter);
    updateCounter();  // Initial count
});
```

### Avatar Field

**Validation Levels:**

1. **Client-side (HTML):**
   - `accept="image/jpeg,image/png,image/webp"` (browser file picker filter)

2. **Form Validation (`clean_avatar()`):**
   - File size check (5MB max)
   - Extension validation
   - Pillow dimension check (100x100 min, 4000x4000 max)

3. **Cloudinary (automatic):**
   - Virus scanning (if enabled in Cloudinary)
   - Format verification
   - Upload success/failure

**Error Messages:**

- `"Avatar file size must be under 5MB."`
- `"Invalid file format. Please upload JPG, PNG, or WebP."`
- `"Avatar must be at least 100x100 pixels."`
- `"Avatar dimensions cannot exceed 4000x4000 pixels."`
- `"Invalid image file: [Pillow error]"`

### Twitter/X URL Field

**Valid Formats:**
- `https://twitter.com/username`
- `https://x.com/username`
- `twitter.com/username` → auto-corrected to `https://twitter.com/username`

**Regex Pattern:**
```python
r'https?://(www\.)?(twitter\.com|x\.com)/[\w]+/?'
```

**Example Validation:**

```python
# VALID
"https://twitter.com/elonmusk"
"https://x.com/OpenAI"
"twitter.com/username"  # Auto-corrects to https://

# INVALID
"https://facebook.com/page"  # Wrong domain
"https://twitter.com/"  # Missing username
"not-a-url"  # Not a URL
```

### Instagram URL Field

**Valid Formats:**
- `https://instagram.com/username`
- `https://www.instagram.com/username.studio`

**Regex Pattern:**
```python
r'https?://(www\.)?instagram\.com/[\w.]+/?'
```

**Note:** Allows dots in username (e.g., `user.name`)

### Website URL Field

**Flexible Validation:**
- Accepts **any valid URL** (not restricted to specific domains)
- Auto-adds `https://` if missing
- Max 200 characters

**Examples:**

```python
# VALID
"https://myportfolio.com"
"myportfolio.com"  # Auto-corrects
"http://localhost:8000"  # Even local URLs
"https://subdomain.example.co.uk/path"

# INVALID
"not a url"
"<200 char limit exceeded>"
```

---

## Validation Strategy

### Three-Level Validation

**1. Client-Side (HTML attributes)**
- `maxlength="500"` on bio
- `accept="image/*"` on avatar
- `type="url"` on URL fields
- **Pros:** Instant feedback, no server round-trip
- **Cons:** Easily bypassed, not trustworthy

**2. Form-Level (Django Form)**
- `clean_<field>()` methods
- File size, type, dimension checks
- URL pattern matching
- **Pros:** Secure, customizable, good error messages
- **Cons:** Requires server round-trip

**3. Model-Level (Database constraints)**
- `max_length=500` on bio field
- `URLField` validation
- **Pros:** Last line of defense, prevents data corruption
- **Cons:** Generic error messages

### Field-Level vs Form-Level Validation

**Field-Level (`clean_<field>()`):**
- Use for validating **individual fields in isolation**
- Bio length, avatar size, URL format
- Return cleaned value or raise `ValidationError`

**Form-Level (`clean()`):**
- Use for validating **relationships between fields**
- Example: "At least one social link required"
- Access all cleaned data via `self.cleaned_data`
- Return entire `cleaned_data` dict

**Example:**

```python
def clean_bio(self):
    """Validate bio (field-level)"""
    bio = self.cleaned_data.get('bio', '').strip()
    if len(bio) > 500:
        raise ValidationError('Bio too long.')
    return bio

def clean(self):
    """Validate form as a whole (form-level)"""
    cleaned_data = super().clean()

    # Example: Require at least one contact method
    has_social = any([
        cleaned_data.get('twitter_url'),
        cleaned_data.get('instagram_url'),
        cleaned_data.get('website_url'),
    ])
    if not has_social:
        raise ValidationError('Please provide at least one social link.')

    return cleaned_data
```

---

## Template Implementation

### Basic Template

```django
<!-- prompts/templates/prompts/edit_profile.html -->

{% extends "base.html" %}
{% load static %}

{% block content %}
<div class="container my-5">
    <div class="row justify-content-center">
        <div class="col-lg-8">
            <h1 class="mb-4">Edit Profile</h1>

            {% if messages %}
                {% for message in messages %}
                    <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}

            <form method="post" enctype="multipart/form-data" novalidate>
                {% csrf_token %}

                <!-- Avatar Section -->
                <div class="mb-4">
                    <label class="form-label">{{ form.avatar.label }}</label>

                    <!-- Current avatar preview -->
                    {% if profile.avatar %}
                        <div class="mb-2">
                            <img src="{{ profile.avatar.url }}"
                                 alt="Current avatar"
                                 class="rounded-circle"
                                 width="100"
                                 height="100">
                        </div>
                    {% endif %}

                    {{ form.avatar }}

                    {% if form.avatar.help_text %}
                        <div class="form-text">{{ form.avatar.help_text }}</div>
                    {% endif %}

                    {% if form.avatar.errors %}
                        <div class="invalid-feedback d-block">
                            {{ form.avatar.errors }}
                        </div>
                    {% endif %}
                </div>

                <!-- Bio Section -->
                <div class="mb-4">
                    <label for="{{ form.bio.id_for_label }}" class="form-label">
                        {{ form.bio.label }}
                    </label>
                    {{ form.bio }}
                    <div id="bio-counter" class="form-text"></div>

                    {% if form.bio.errors %}
                        <div class="invalid-feedback d-block">
                            {{ form.bio.errors }}
                        </div>
                    {% endif %}
                </div>

                <!-- Social Media URLs -->
                <div class="row">
                    <div class="col-md-6 mb-4">
                        <label for="{{ form.twitter_url.id_for_label }}" class="form-label">
                            {{ form.twitter_url.label }}
                        </label>
                        {{ form.twitter_url }}
                        {% if form.twitter_url.help_text %}
                            <div class="form-text">{{ form.twitter_url.help_text }}</div>
                        {% endif %}
                        {% if form.twitter_url.errors %}
                            <div class="invalid-feedback d-block">
                                {{ form.twitter_url.errors }}
                            </div>
                        {% endif %}
                    </div>

                    <div class="col-md-6 mb-4">
                        <label for="{{ form.instagram_url.id_for_label }}" class="form-label">
                            {{ form.instagram_url.label }}
                        </label>
                        {{ form.instagram_url }}
                        {% if form.instagram_url.help_text %}
                            <div class="form-text">{{ form.instagram_url.help_text }}</div>
                        {% endif %}
                        {% if form.instagram_url.errors %}
                            <div class="invalid-feedback d-block">
                                {{ form.instagram_url.errors }}
                            </div>
                        {% endif %}
                    </div>
                </div>

                <!-- Website URL -->
                <div class="mb-4">
                    <label for="{{ form.website_url.id_for_label }}" class="form-label">
                        {{ form.website_url.label }}
                    </label>
                    {{ form.website_url }}
                    {% if form.website_url.help_text %}
                        <div class="form-text">{{ form.website_url.help_text }}</div>
                    {% endif %}
                    {% if form.website_url.errors %}
                        <div class="invalid-feedback d-block">
                            {{ form.invalid_feedback.errors }}
                        </div>
                    {% endif %}
                </div>

                <!-- Non-field errors (form-level) -->
                {% if form.non_field_errors %}
                    <div class="alert alert-danger">
                        {{ form.non_field_errors }}
                    </div>
                {% endif %}

                <!-- Action Buttons -->
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-primary">
                        Save Changes
                    </button>
                    <a href="{% url 'user_profile' username=request.user.username %}"
                       class="btn btn-secondary">
                        Cancel
                    </a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/profile_form.js' %}"></script>
{% endblock %}
```

### Crispy Forms Alternative (Recommended)

```django
{% load crispy_forms_tags %}

<form method="post" enctype="multipart/form-data">
    {% csrf_token %}
    {{ form|crispy }}

    <button type="submit" class="btn btn-primary">Save Changes</button>
    <a href="{% url 'user_profile' username=request.user.username %}" class="btn btn-secondary">Cancel</a>
</form>
```

---

## JavaScript Enhancement

### Character Counter for Bio

```javascript
// static/js/profile_form.js

document.addEventListener('DOMContentLoaded', function() {
    const bioField = document.getElementById('id_bio');
    if (!bioField) return;

    // Create counter element
    const counter = document.createElement('div');
    counter.id = 'bio-counter';
    counter.className = 'form-text text-muted mt-1';

    // Insert after textarea
    bioField.parentNode.appendChild(counter);

    // Update counter function
    function updateCounter() {
        const current = bioField.value.length;
        const max = 500;
        const remaining = max - current;

        counter.textContent = `${current} / ${max} characters`;

        // Color coding
        counter.classList.remove('text-muted', 'text-warning', 'text-danger');
        if (remaining <= 0) {
            counter.classList.add('text-danger');
        } else if (remaining < 50) {
            counter.classList.add('text-warning');
        } else {
            counter.classList.add('text-muted');
        }
    }

    // Event listeners
    bioField.addEventListener('input', updateCounter);
    bioField.addEventListener('change', updateCounter);

    // Initial update
    updateCounter();
});
```

### Avatar Preview Before Upload

```javascript
// static/js/profile_form.js

document.addEventListener('DOMContentLoaded', function() {
    const avatarInput = document.getElementById('id_avatar');
    if (!avatarInput) return;

    avatarInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;

        // Validate file size (5MB)
        if (file.size > 5 * 1024 * 1024) {
            alert('File size must be under 5MB.');
            avatarInput.value = '';
            return;
        }

        // Show preview
        const reader = new FileReader();
        reader.onload = function(e) {
            // Find or create preview image
            let preview = document.getElementById('avatar-preview');
            if (!preview) {
                preview = document.createElement('img');
                preview.id = 'avatar-preview';
                preview.className = 'rounded-circle mt-2';
                preview.width = 100;
                preview.height = 100;
                avatarInput.parentNode.appendChild(preview);
            }
            preview.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });
});
```

### URL Validation Hints

```javascript
// static/js/profile_form.js

document.addEventListener('DOMContentLoaded', function() {
    // Twitter URL helper
    const twitterInput = document.getElementById('id_twitter_url');
    if (twitterInput) {
        twitterInput.addEventListener('blur', function() {
            let url = twitterInput.value.trim();
            if (url && !url.startsWith('http')) {
                twitterInput.value = 'https://' + url;
            }
        });
    }

    // Instagram URL helper
    const instagramInput = document.getElementById('id_instagram_url');
    if (instagramInput) {
        instagramInput.addEventListener('blur', function() {
            let url = instagramInput.value.trim();
            if (url && !url.startsWith('http')) {
                instagramInput.value = 'https://' + url;
            }
        });
    }

    // Website URL helper
    const websiteInput = document.getElementById('id_website_url');
    if (websiteInput) {
        websiteInput.addEventListener('blur', function() {
            let url = websiteInput.value.trim();
            if (url && !url.startsWith('http')) {
                websiteInput.value = 'https://' + url;
            }
        });
    }
});
```

---

## Error Handling

### Displaying Form Errors

**Per-Field Errors:**

```django
{% if form.bio.errors %}
    <div class="invalid-feedback d-block">
        {{ form.bio.errors }}
    </div>
{% endif %}
```

**Non-Field Errors (form-level):**

```django
{% if form.non_field_errors %}
    <div class="alert alert-danger">
        {{ form.non_field_errors }}
    </div>
{% endif %}
```

**All Errors at Top:**

```django
{% if form.errors %}
    <div class="alert alert-danger">
        <h4>Please correct the following errors:</h4>
        <ul>
            {% for field, errors in form.errors.items %}
                {% for error in errors %}
                    <li>{{ field }}: {{ error }}</li>
                {% endfor %}
            {% endfor %}
        </ul>
    </div>
{% endif %}
```

### Common Error Scenarios

**1. Avatar File Too Large**

```python
# Form returns:
ValidationError('Avatar file size must be under 5MB.')

# User sees:
"Avatar: Avatar file size must be under 5MB."
```

**2. Invalid Social URL**

```python
# Form returns:
ValidationError('Please enter a valid Twitter/X URL (e.g., https://twitter.com/username)')

# User sees:
"Twitter/X URL: Please enter a valid Twitter/X URL (e.g., https://twitter.com/username)"
```

**3. Bio Too Long**

```python
# Form returns:
ValidationError('Bio cannot exceed 500 characters.')

# User sees:
"Bio: Bio cannot exceed 500 characters."
# (Should rarely happen with maxlength attribute)
```

**4. Cloudinary Upload Failure**

```python
# View catches exception:
except Exception as e:
    messages.error(request, f'Error uploading avatar: {str(e)}')

# User sees:
Alert: "Error uploading avatar: [Cloudinary error message]"
```

### Logging Errors

```python
import logging
logger = logging.getLogger(__name__)

@login_required
def edit_profile(request):
    # ... form validation ...

    if form.is_valid():
        try:
            form.save()
        except Exception as e:
            logger.error(
                f"Profile save error for user {request.user.username}: {str(e)}",
                exc_info=True  # Includes full traceback
            )
            messages.error(request, 'An error occurred. Please try again.')
```

---

## Best Practices

### 1. Cloudinary Best Practices

**Use CloudinaryField, Not Manual Uploads:**
```python
# GOOD (automatic)
class UserProfile(models.Model):
    avatar = CloudinaryField('avatar', ...)

# BAD (manual, unnecessary)
def save_avatar(request):
    result = cloudinary.uploader.upload(request.FILES['avatar'])
    profile.avatar_url = result['secure_url']
```

**Define Transformations in Model:**
```python
# Transformations apply automatically
avatar = CloudinaryField(
    'avatar',
    transformation={
        'width': 300,
        'height': 300,
        'crop': 'fill',
        'gravity': 'face',
    }
)
```

**Clean Up Old Avatars:**
- Use Django signals (see Cloudinary Integration section)
- Or manual cleanup in view
- Prevents orphaned files

### 2. Form Validation Best Practices

**Always Validate Server-Side:**
- Client-side validation is UX, not security
- Attackers can bypass HTML attributes
- Always validate in `clean_*()` methods

**Provide Helpful Error Messages:**
```python
# GOOD
raise ValidationError(
    'Please enter a valid Twitter/X URL (e.g., https://twitter.com/username)'
)

# BAD
raise ValidationError('Invalid URL')
```

**Trim Whitespace:**
```python
bio = self.cleaned_data.get('bio', '').strip()
```

**Use `mark_safe()` for HTML in Errors:**
```python
from django.utils.safestring import mark_safe

error_message = mark_safe(
    'Bio contains inappropriate content. '
    '<a href="/guidelines/">Learn more</a>'
)
```

### 3. Security Best Practices

**File Upload Security:**
- Validate file size (DoS prevention)
- Validate file type (code execution prevention)
- Use Pillow to verify images (header spoofing prevention)
- Let Cloudinary handle virus scanning

**URL Validation:**
- Use domain whitelisting for social URLs
- Auto-add https:// (prevent mixed content)
- Validate against patterns (prevent XSS)

**Profanity Filtering (Optional):**
```python
def clean_bio(self):
    bio = self.cleaned_data.get('bio', '').strip()

    # Check for profanity
    profanity_service = ProfanityFilterService()
    is_clean, found_words, max_severity = profanity_service.check_text(bio)

    if not is_clean and max_severity in ['high', 'critical']:
        raise ValidationError('Bio contains inappropriate content.')

    return bio
```

### 4. Performance Best Practices

**Lazy Load Pillow:**
```python
try:
    from PIL import Image
    # Use Image
except ImportError:
    # Skip dimension validation
    pass
```

**Optimize Database Queries:**
```python
# In view, select related user
profile = request.user.userprofile  # Uses cached relation
```

**Cache Avatar URLs:**
```python
# In template
{% load cache %}
{% cache 3600 user_avatar user.id %}
    <img src="{{ user.userprofile.avatar.url }}" alt="Avatar">
{% endcache %}
```

### 5. UX Best Practices

**Show Current Values:**
- Display current avatar before upload
- Pre-fill form with existing data
- Show "Currently: [value]" for file fields

**Provide Examples:**
- Placeholder text with format examples
- Help text with acceptable formats
- Error messages with correct format examples

**Character Counters:**
- Real-time feedback for bio
- Color coding (green → yellow → red)
- Show remaining characters

**Preview Uploads:**
- JavaScript preview for avatar before submit
- Instant feedback on file selection

---

## Answers to Your Questions

### 1. Best way to handle Cloudinary file upload in Django form?

**Answer:** Use Django's built-in form handling with CloudinaryField. No manual API calls needed.

```python
# In form
avatar = forms.ImageField(required=False, ...)

# In view
if form.is_valid():
    form.save()  # CloudinaryField handles upload automatically
```

The CloudinaryField in your model does all the heavy lifting:
- Uploads file to Cloudinary
- Applies transformations
- Stores public_id and URL
- Handles errors

### 2. Should I use ClearableFileInput for avatar or Cloudinary widget?

**Answer:** Use **ClearableFileInput** (Django's built-in widget).

**Reasons:**
- Standard Django behavior (familiar to developers)
- Built-in "Clear" checkbox for deletion
- No custom JavaScript needed
- Works with CloudinaryField automatically
- Better browser compatibility

**Cloudinary widget** (from `cloudinary.forms`) is overkill for simple uploads and adds unnecessary complexity.

### 3. URL validation - accept any URL or validate specific social media patterns?

**Answer:** **Both** - depends on the field.

**For Twitter/Instagram:** Validate specific patterns
```python
# Ensures users enter actual profile URLs, not random links
pattern = r'https?://(www\.)?(twitter\.com|x\.com)/[\w]+/?'
```

**For Website:** Accept any valid URL
```python
# Flexible - portfolio, blog, company site, etc.
url = self.cleaned_data.get('website_url', '').strip()
if url and not url.startswith(('http://', 'https://')):
    url = f'https://{url}'
```

**Benefits:**
- Twitter/Instagram: Prevents user errors, ensures clickable links
- Website: Maximum flexibility, no false rejections

### 4. How to handle avatar deletion (clear existing)?

**Answer:** Two-part solution:

**Part 1: ClearableFileInput handles UI**
- User checks "Clear" checkbox
- Form sets `avatar` to `None`
- Old image reference removed from database

**Part 2: Delete from Cloudinary (manual)**

**Option A: Django Signal (Recommended)**
```python
from django.db.models.signals import pre_save

@receiver(pre_save, sender=UserProfile)
def delete_old_avatar(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old_profile = UserProfile.objects.get(pk=instance.pk)
        if old_profile.avatar and old_profile.avatar != instance.avatar:
            cloudinary.uploader.destroy(old_profile.avatar.public_id)
    except UserProfile.DoesNotExist:
        pass
```

**Option B: View Logic**
```python
old_avatar_id = profile.avatar.public_id if profile.avatar else None
# ... save form ...
if old_avatar_id and old_avatar_id != profile.avatar.public_id:
    cloudinary.uploader.destroy(old_avatar_id)
```

**Recommendation:** Use Signal for cleaner separation of concerns.

### 5. Form-level vs field-level validation for URLs?

**Answer:** **Field-level** (individual `clean_<field>()` methods).

**Reasons:**
- Each URL is independent (no cross-field validation needed)
- Clearer error messages ("Twitter URL: Invalid format")
- Easier to reuse validation logic
- Better separation of concerns

**When to use form-level (`clean()`):**
- Validating relationships: "At least one social link required"
- Complex logic: "If Twitter provided, Instagram optional"
- Cross-field validation: "Bio required if no social links"

**Example of form-level validation you might add:**

```python
def clean(self):
    cleaned_data = super().clean()

    # Ensure at least one contact method if bio is empty
    has_bio = bool(cleaned_data.get('bio', '').strip())
    has_social = any([
        cleaned_data.get('twitter_url'),
        cleaned_data.get('instagram_url'),
        cleaned_data.get('website_url'),
    ])

    if not has_bio and not has_social:
        raise ValidationError(
            'Please provide either a bio or at least one social link.'
        )

    return cleaned_data
```

---

## Summary

**What You Have:**
- Complete, production-ready `UserProfileForm`
- Cloudinary integration (automatic, no manual code)
- Comprehensive validation (file size, type, dimensions, URLs)
- User-friendly error messages
- Character counter support
- Avatar deletion handling
- Social media URL validation

**How to Use:**
1. Import form: `from .forms import UserProfileForm`
2. Create view: `form = UserProfileForm(request.POST, request.FILES, instance=profile)`
3. Save on valid: `form.save()` (Cloudinary upload happens automatically)
4. Add JavaScript for character counter (optional but recommended)
5. Implement signal for avatar cleanup (optional but recommended)

**Next Steps:**
1. Create `edit_profile` view
2. Add URL to `urls.py`
3. Create template `edit_profile.html`
4. Add JavaScript for character counter and preview
5. Test all validation scenarios
6. Deploy!

---

**End of Guide**
