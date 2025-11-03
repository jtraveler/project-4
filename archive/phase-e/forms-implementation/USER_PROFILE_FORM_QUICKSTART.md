# UserProfileForm - Quick Start

**5-Minute Implementation Guide**

---

## Files Created

1. **Form:** `prompts/forms.py` → Added `UserProfileForm` class
2. **Documentation:** `docs/forms/USER_PROFILE_FORM_GUIDE.md` (complete guide)

---

## 1. Create View (2 minutes)

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

    return render(request, 'prompts/edit_profile.html', {
        'form': form,
        'profile': profile,
    })
```

---

## 2. Add URL (30 seconds)

```python
# prompts/urls.py

urlpatterns = [
    # ... existing URLs ...
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]
```

---

## 3. Create Template (2 minutes)

```django
<!-- prompts/templates/prompts/edit_profile.html -->

{% extends "base.html" %}

{% block content %}
<div class="container my-5">
    <h1>Edit Profile</h1>

    {% if messages %}
        {% for message in messages %}
            <div class="alert alert-{{ message.tags }}">{{ message }}</div>
        {% endfor %}
    {% endif %}

    <form method="post" enctype="multipart/form-data">
        {% csrf_token %}

        <!-- Avatar -->
        <div class="mb-3">
            <label>{{ form.avatar.label }}</label>
            {% if profile.avatar %}
                <div><img src="{{ profile.avatar.url }}" width="100" class="rounded-circle"></div>
            {% endif %}
            {{ form.avatar }}
            {% if form.avatar.errors %}<div class="text-danger">{{ form.avatar.errors }}</div>{% endif %}
        </div>

        <!-- Bio -->
        <div class="mb-3">
            <label for="{{ form.bio.id_for_label }}">{{ form.bio.label }}</label>
            {{ form.bio }}
            <div id="bio-counter" class="form-text"></div>
            {% if form.bio.errors %}<div class="text-danger">{{ form.bio.errors }}</div>{% endif %}
        </div>

        <!-- Twitter -->
        <div class="mb-3">
            <label for="{{ form.twitter_url.id_for_label }}">{{ form.twitter_url.label }}</label>
            {{ form.twitter_url }}
            {% if form.twitter_url.errors %}<div class="text-danger">{{ form.twitter_url.errors }}</div>{% endif %}
        </div>

        <!-- Instagram -->
        <div class="mb-3">
            <label for="{{ form.instagram_url.id_for_label }}">{{ form.instagram_url.label }}</label>
            {{ form.instagram_url }}
            {% if form.instagram_url.errors %}<div class="text-danger">{{ form.instagram_url.errors }}</div>{% endif %}
        </div>

        <!-- Website -->
        <div class="mb-3">
            <label for="{{ form.website_url.id_for_label }}">{{ form.website_url.label }}</label>
            {{ form.website_url }}
            {% if form.website_url.errors %}<div class="text-danger">{{ form.website_url.errors }}</div>{% endif %}
        </div>

        <button type="submit" class="btn btn-primary">Save Changes</button>
        <a href="{% url 'user_profile' username=request.user.username %}" class="btn btn-secondary">Cancel</a>
    </form>
</div>

<script>
// Character counter for bio
document.addEventListener('DOMContentLoaded', function() {
    const bio = document.getElementById('id_bio');
    const counter = document.getElementById('bio-counter');

    function updateCounter() {
        const current = bio.value.length;
        counter.textContent = `${current} / 500 characters`;
        counter.className = current > 450 ? 'form-text text-warning' : 'form-text text-muted';
    }

    bio.addEventListener('input', updateCounter);
    updateCounter();
});
</script>
{% endblock %}
```

---

## 4. Optional: Avatar Cleanup Signal (1 minute)

Add to bottom of `prompts/models.py`:

```python
from django.db.models.signals import pre_save
from django.dispatch import receiver
import cloudinary.uploader

@receiver(pre_save, sender=UserProfile)
def delete_old_avatar(sender, instance, **kwargs):
    """Delete old avatar from Cloudinary when replaced"""
    if not instance.pk:
        return
    try:
        old = UserProfile.objects.get(pk=instance.pk)
        if old.avatar and old.avatar != instance.avatar:
            cloudinary.uploader.destroy(old.avatar.public_id)
    except UserProfile.DoesNotExist:
        pass
```

---

## 5. Test It!

1. **Navigate:** Go to `/profile/edit/`
2. **Upload avatar:** Choose JPG/PNG/WebP under 5MB
3. **Fill bio:** Type up to 500 characters (watch counter)
4. **Add social URLs:** Twitter, Instagram, Website
5. **Save:** Form validates and uploads to Cloudinary automatically

---

## What the Form Does

✅ **Bio:** 500 char limit with live counter
✅ **Avatar:** Upload to Cloudinary (5MB max, 100x100 min)
✅ **Twitter/X:** Validates twitter.com or x.com URLs
✅ **Instagram:** Validates instagram.com URLs
✅ **Website:** Accepts any valid URL
✅ **Auto-correction:** Adds https:// if missing
✅ **User-friendly errors:** Clear messages with format examples

---

## Cloudinary Integration

**No manual Cloudinary code needed!** The form uses Django's built-in file upload:

1. User selects avatar file
2. Form validates (size, type, dimensions)
3. `form.save()` triggers CloudinaryField upload
4. Cloudinary applies transformations (300x300, face crop)
5. Model stores public_id and URL

**Transformations applied automatically:**
- 300x300 crop
- Face detection gravity
- Auto quality
- Auto format (WebP for modern browsers)

---

## Next Steps

- Read full guide: `docs/forms/USER_PROFILE_FORM_GUIDE.md`
- Add avatar cleanup signal (recommended)
- Enhance with JavaScript preview (optional)
- Add profanity check to bio (optional)
- Style with Bootstrap/custom CSS

---

## Quick Answers

**Q: How to delete avatars from Cloudinary?**
A: Add the signal in step 4 above.

**Q: How to customize validations?**
A: Edit `clean_*()` methods in `UserProfileForm` class.

**Q: How to change URL patterns?**
A: Edit `_validate_social_url()` regex patterns.

**Q: How to add more fields?**
A: Add to `Meta.fields` and create `clean_<field>()` method.

---

**Total Implementation Time:** ~10 minutes
**Complexity:** Low (leverages Django + Cloudinary built-ins)
**Maintenance:** Minimal (signals handle cleanup)
