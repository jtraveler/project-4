# Phase E: User Profiles & Social Foundation

**Status:** Planning (October 2025)
**Estimated Duration:** 2-3 days (10-12 hours)
**Difficulty:** 🔥🔥 Medium
**Priority:** High - Foundation for community

## Overview
Build the social foundation by implementing user profiles, enhanced prompt details with reporting, and email preferences. This phase enables users to discover creators, follow interesting users, and control notifications.

## Why Phase E (Before Premium)?
1. **User Experience Gap:** No way to see a user's other prompts
2. **Foundation Needed:** Follow system requires profiles
3. **Notification Control:** Need preferences before increasing email volume
4. **Community First:** Build engagement before monetization
5. **Natural Progression:** From content management (D) to social features (E) to revenue (G)

## Goals:
- Users can view any creator's public profile
- Profiles display all prompts and statistics
- Users can report inappropriate content
- Users control their email preferences
- Foundation for follow system (Phase F)

## Part 1: Public User Profiles (Day 1 - 4-5 hours)

### Commit 9: User Profile Model & View

**Database Model:**
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    avatar = CloudinaryField('image', blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    twitter = models.CharField(max_length=50, blank=True)
    instagram = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
        ]
```

**Profile Page Features:**
- Username and display name
- Avatar (default if not set)
- Bio
- Member since date
- Statistics:
  - Total prompts (count)
  - Total likes received (aggregate)
  - Followers (placeholder for Phase F)
  - Following (placeholder for Phase F)
- Grid of user's public prompts (masonry layout)
- Social links (if provided)
- Follow button (placeholder for Phase F)

**URL Structure:**
- `/users/<username>/` - Public profile
- `/users/<username>/prompts/` - All prompts (paginated)
- `/users/<username>/liked/` - Liked prompts (Phase F)

### Commit 10: Profile Edit & Avatar Upload

**Features:**
- Profile settings page at `/settings/profile/`
- Edit form (bio, avatar, location, social links)
- Cloudinary avatar upload
- Form validation

**Form Fields:**
- Bio textarea (500 char limit with live counter)
- Avatar upload (Cloudinary widget)
- Location text input
- Website URL input
- Twitter handle input (@username)
- Instagram handle input (@username)
- Preview changes before saving
- Success/error messaging

## Part 2: Enhanced Prompt Detail (Day 2 - 2-3 hours)

### Commit 11: Report Feature

**Database Model:**
```python
class PromptReport(models.Model):
    REASON_CHOICES = [
        ('inappropriate', 'Inappropriate Content'),
        ('spam', 'Spam or Misleading'),
        ('copyright', 'Copyright Violation'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('dismissed', 'Dismissed'),
    ]

    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_reports')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    comment = models.TextField(blank=True, max_length=1000)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['prompt', 'reported_by']  # One report per user per prompt
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['prompt']),
        ]
```

**Report Flow:**
1. User clicks "Report" button
2. Modal appears with reason dropdown
3. Optional comment field (1000 char max)
4. Submit sends report
5. Email notification to admins
6. Thank you confirmation
7. Admin reviews in Django Admin

**Email to Admins:**
- Subject: "New Prompt Report - [Prompt Title]"
- Prompt URL
- Reported by user
- Reason and comment
- Direct link to admin review page

### Commit 12: Prompt Detail Enhancements

**Features:**
- "View Profile" link next to author name (with avatar)
- "More from this user" section (3-6 prompts by same author)
- Author info card:
  - Avatar (small)
  - Username
  - Follower count (placeholder)
  - Follow button (placeholder)
- Report button (discreet, bottom right or in dropdown menu)
- Improved layout and visual hierarchy

## Part 3: Email Preferences (Day 3 - 3-4 hours)

### Commit 13: Email Preferences Model & Settings Page

**Database Model:**
```python
class EmailPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_preferences')
    notify_comments = models.BooleanField(default=True, help_text='New comments on your prompts')
    notify_replies = models.BooleanField(default=True, help_text='Replies to your comments')
    notify_follows = models.BooleanField(default=True, help_text='New followers')
    notify_likes = models.BooleanField(default=True, help_text='Likes on your prompts')
    notify_mentions = models.BooleanField(default=True, help_text='Mentions (@username)')
    notify_weekly_digest = models.BooleanField(default=True, help_text='Weekly activity summary')
    notify_updates = models.BooleanField(default=True, help_text='Product updates and announcements')
    notify_marketing = models.BooleanField(default=False, help_text='Marketing emails and offers')
    unsubscribe_token = models.CharField(max_length=64, unique=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Generate unsubscribe token if not exists
        if not self.unsubscribe_token:
            import secrets
            self.unsubscribe_token = secrets.token_urlsafe(48)
        super().save(*args, **kwargs)
```

**Settings Page Features:**
- Clean, organized layout
- Toggle switches for each notification type
- Help text explaining each option
- "Unsubscribe from all" button (sets all to False except updates)
- Save button with success confirmation
- Mobile-responsive design
- Grouped by category:
  - Activity (comments, replies, likes)
  - Social (follows, mentions)
  - Digest (weekly summary)
  - Platform (updates, marketing)

### Commit 14: Update Notification Logic

**Implementation:**
- Helper function: `should_send_notification(user, notification_type)`
- Check preferences before sending any email
- Generate unique unsubscribe tokens
- Unsubscribe handler view (`/unsubscribe/<token>/`)
- Update email templates with footer links

**Email Template Footer:**
```html
<p style="font-size: 12px; color: #666;">
    You're receiving this because you're subscribed to [Notification Type] notifications.
    <a href="{{ unsubscribe_url }}">Unsubscribe</a> |
    <a href="{{ preferences_url }}">Manage Preferences</a>
</p>
```

## Success Criteria:
- [ ] Users can view any public profile
- [ ] Profiles show all prompts and stats
- [ ] Users can edit their own profile
- [ ] Avatar upload works (Cloudinary)
- [ ] Report button functional on prompt detail
- [ ] Admin receives report emails
- [ ] Email preferences page works
- [ ] All emails respect preferences
- [ ] Unsubscribe links work correctly
- [ ] No N+1 query issues
- [ ] Mobile-responsive
- [ ] All pages have proper error handling

## Files to Create:
- `prompts/models.py` - Add UserProfile, PromptReport, EmailPreferences
- `prompts/views.py` - Profile, settings, report views
- `prompts/forms.py` - Profile form, report form, settings form
- `prompts/urls.py` - New URL patterns
- `templates/users/profile.html`
- `templates/users/profile_edit.html`
- `templates/users/settings_notifications.html`
- `templates/prompts/report_modal.html`
- `templates/emails/` - Email templates with unsubscribe
- `prompts/admin.py` - Admin for new models
- Migration files

## Testing Checklist:
- [ ] View any user's profile
- [ ] Profile shows correct stats
- [ ] Edit own profile
- [ ] Upload avatar
- [ ] Report a prompt
- [ ] Receive report email (admin)
- [ ] Change email preferences
- [ ] Test each notification type respects preferences
- [ ] Click unsubscribe link
- [ ] Verify all forms validate correctly
- [ ] Test on mobile devices
- [ ] Check query performance (Django Debug Toolbar)

## Leads to Phase F:
- Follow button becomes functional
- Personalized feeds (need follow data)
- In-app notifications (use email preferences as model)
- User discovery features
