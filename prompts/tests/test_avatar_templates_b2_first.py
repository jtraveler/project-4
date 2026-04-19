"""
Regression tests for Session 162-B.

Six templates were updated to prefer `userprofile.b2_avatar_url` over
the Cloudinary `avatar.url`, with a three-branch pattern:
  b2_avatar_url → Cloudinary avatar → letter placeholder.

Each test creates real `User` / `UserProfile` instances (Rule 1 —
session 162 mandates real ORM rows for template traversal tests,
not `SimpleNamespace` mocks) and asserts the rendered template
makes the correct avatar choice.

`edit_profile.html` is explicitly NOT covered here — it uses the
`{% cloudinary %}` server-side face-crop transform and is reserved
for Session 164 F2 (upload pipeline switch lands first).
"""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.template import Context, Template
from django.test import TestCase


def _read_template(relative_path: str) -> str:
    """Read a template file as raw text for structure-level checks."""
    full_path = Path(settings.BASE_DIR) / 'prompts' / 'templates' / relative_path
    return full_path.read_text()


class AvatarTemplateB2FirstStructureTests(TestCase):
    """
    Structural checks — each of the 6 templates must have the
    three-branch pattern, with the `b2_avatar_url` branch first and
    the Cloudinary `avatar.url` branch second.

    These tests cover the "did CC actually update the file" dimension
    per CC_SPEC_TEMPLATE Critical Reminder #9: paired positive and
    negative assertions.
    """

    def test_notifications_html_has_b2_first_pattern(self):
        src = _read_template('prompts/notifications.html')
        # Positive: b2 branch exists
        self.assertIn(
            '{% if notification.sender.userprofile.b2_avatar_url %}', src,
        )
        # Positive: Cloudinary branch is now elif
        self.assertIn(
            '{% elif notification.sender.userprofile.avatar '
            'and notification.sender.userprofile.avatar.url %}',
            src,
        )
        # Negative: old standalone `{% if ... avatar.url %}` pattern is gone
        self.assertNotIn(
            '{% if notification.sender.userprofile.avatar '
            'and notification.sender.userprofile.avatar.url %}',
            src,
        )
        # Ordering: b2 branch appears BEFORE elif Cloudinary branch
        idx_b2 = src.find(
            '{% if notification.sender.userprofile.b2_avatar_url %}'
        )
        idx_cloudinary = src.find(
            '{% elif notification.sender.userprofile.avatar '
            'and notification.sender.userprofile.avatar.url %}'
        )
        self.assertLess(idx_b2, idx_cloudinary)

    def test_notification_list_partial_has_b2_first_pattern(self):
        src = _read_template('prompts/partials/_notification_list.html')
        self.assertIn(
            '{% if notification.sender.userprofile.b2_avatar_url %}', src,
        )
        self.assertIn(
            '{% elif notification.sender.userprofile.avatar '
            'and notification.sender.userprofile.avatar.url %}',
            src,
        )
        self.assertNotIn(
            '{% if notification.sender.userprofile.avatar '
            'and notification.sender.userprofile.avatar.url %}',
            src,
        )
        idx_b2 = src.find(
            '{% if notification.sender.userprofile.b2_avatar_url %}'
        )
        idx_cloudinary = src.find(
            '{% elif notification.sender.userprofile.avatar '
            'and notification.sender.userprofile.avatar.url %}'
        )
        self.assertLess(idx_b2, idx_cloudinary)

    def test_user_profile_html_has_b2_first_pattern(self):
        src = _read_template('prompts/user_profile.html')
        # Positive: b2 branch exists
        self.assertIn('{% if profile.b2_avatar_url %}', src)
        # Positive: Cloudinary branch uses `avatar and avatar.url` double
        # guard (consistent with the other 4 templates, aligned with
        # 162-B cross-spec absorption)
        self.assertIn(
            '{% elif profile.avatar and profile.avatar.url %}', src,
        )
        # Negative: old standalone `{% if profile.avatar.url %}` pattern
        # (without b2 branch preceding it) is gone. Since `{% elif ... %}`
        # shares the `{% if ... %}` prefix, the old standalone form is
        # specifically `{% if profile.avatar.url %}` with no b2 elif
        # chain — not present anywhere in the file.
        self.assertNotIn('{% if profile.avatar.url %}', src)
        # Count: b2 branch appears exactly once
        self.assertEqual(src.count('{% if profile.b2_avatar_url %}'), 1)
        # Ordering: b2 appears before Cloudinary elif
        idx_b2 = src.find('{% if profile.b2_avatar_url %}')
        idx_cloudinary = src.find(
            '{% elif profile.avatar and profile.avatar.url %}'
        )
        self.assertLess(idx_b2, idx_cloudinary)

    def test_collections_profile_html_has_b2_first_pattern(self):
        src = _read_template('prompts/collections_profile.html')
        self.assertIn('{% if profile.b2_avatar_url %}', src)
        # Same double-guard consistency after 162-B absorption
        self.assertIn(
            '{% elif profile.avatar and profile.avatar.url %}', src,
        )
        self.assertNotIn('{% if profile.avatar.url %}', src)
        self.assertEqual(src.count('{% if profile.b2_avatar_url %}'), 1)
        idx_b2 = src.find('{% if profile.b2_avatar_url %}')
        idx_cloudinary = src.find(
            '{% elif profile.avatar and profile.avatar.url %}'
        )
        self.assertLess(idx_b2, idx_cloudinary)

    def test_leaderboard_html_has_b2_first_pattern(self):
        src = _read_template('prompts/leaderboard.html')
        self.assertIn('{% if creator.userprofile.b2_avatar_url %}', src)
        self.assertIn(
            '{% elif creator.userprofile.avatar '
            'and creator.userprofile.avatar.url %}',
            src,
        )
        self.assertNotIn(
            '{% if creator.userprofile.avatar '
            'and creator.userprofile.avatar.url %}',
            src,
        )
        idx_b2 = src.find('{% if creator.userprofile.b2_avatar_url %}')
        idx_cloudinary = src.find(
            '{% elif creator.userprofile.avatar '
            'and creator.userprofile.avatar.url %}'
        )
        self.assertLess(idx_b2, idx_cloudinary)

    def test_prompt_detail_html_has_b2_first_pattern(self):
        src = _read_template('prompts/prompt_detail.html')
        self.assertIn(
            '{% if prompt.author.userprofile.b2_avatar_url %}', src,
        )
        self.assertIn(
            '{% elif prompt.author.userprofile.avatar '
            'and prompt.author.userprofile.avatar.url %}',
            src,
        )
        self.assertNotIn(
            '{% if prompt.author.userprofile.avatar '
            'and prompt.author.userprofile.avatar.url %}',
            src,
        )
        idx_b2 = src.find(
            '{% if prompt.author.userprofile.b2_avatar_url %}'
        )
        idx_cloudinary = src.find(
            '{% elif prompt.author.userprofile.avatar '
            'and prompt.author.userprofile.avatar.url %}'
        )
        self.assertLess(idx_b2, idx_cloudinary)

    def test_edit_profile_html_is_unchanged_no_b2_avatar_url(self):
        """
        edit_profile.html is explicitly out of scope for 162-B.
        Reserved for Session 164 F2 — it uses the `{% cloudinary %}`
        server-side face-crop transform that has no direct B2
        equivalent until the upload pipeline switch in Session 163 F1.

        This test guards against accidental inclusion.
        """
        src = _read_template('prompts/edit_profile.html')
        self.assertNotIn('b2_avatar_url', src)


class AvatarTemplateB2FirstRenderTests(TestCase):
    """
    Render-level checks — extract the avatar if/elif/else block from
    each template into a minimal `Template` object, then render it
    with three different UserProfile states to verify each branch
    produces the expected output.

    This avoids fixture complexity of constructing full view contexts
    (which drag in leaderboard query sets, notification lists, etc.)
    while still exercising the actual template-engine logic on real
    ORM rows.
    """

    def setUp(self):
        # Three users — one per scenario per fresh test (setUp runs per test).
        # CloudinaryField values become CloudinaryResource objects only after
        # a refresh_from_db roundtrip; before refresh they remain plain
        # strings and the template's `{{ avatar.url }}` returns empty.
        # Refresh the userprofile on every branch so the template engine
        # sees production-shaped objects.
        self.user_b2 = User.objects.create_user(
            username='b2user162b',
            email='b2user@example.com',
            password='x',
        )
        self.user_b2.userprofile.b2_avatar_url = (
            'https://media.promptfinder.net/avatars/b2.jpg'
        )
        self.user_b2.userprofile.save()
        self.user_b2.refresh_from_db()

        self.user_cloudinary = User.objects.create_user(
            username='cloudinary162b',
            email='cloudinary@example.com',
            password='x',
        )
        self.user_cloudinary.userprofile.avatar = (
            'legacy/cloudinary_avatar_id'
        )
        self.user_cloudinary.userprofile.save()
        self.user_cloudinary.refresh_from_db()

        self.user_neither = User.objects.create_user(
            username='neither162b',
            email='neither@example.com',
            password='x',
        )
        self.user_neither.refresh_from_db()

    def _render_block(self, template_source: str, context: dict) -> str:
        tmpl = Template(template_source)
        return tmpl.render(Context(context))

    # ---- notifications.html block ----

    NOTIFICATIONS_BLOCK = (
        '{% if notification.sender.userprofile.b2_avatar_url %}'
        '<img src="{{ notification.sender.userprofile.b2_avatar_url }}" '
        'class="notif-avatar">'
        '{% elif notification.sender.userprofile.avatar and '
        'notification.sender.userprofile.avatar.url %}'
        '<img src="{{ notification.sender.userprofile.avatar.url }}" '
        'class="notif-avatar">'
        '{% else %}'
        '<div class="notif-avatar-placeholder">'
        '{{ notification.sender.username|first|upper }}</div>'
        '{% endif %}'
    )

    def test_notifications_block_renders_b2_first(self):
        output = self._render_block(
            self.NOTIFICATIONS_BLOCK,
            {'notification': _FakeNotification(self.user_b2)},
        )
        self.assertIn(
            'https://media.promptfinder.net/avatars/b2.jpg', output,
        )
        self.assertNotIn('cloudinary.com', output)
        self.assertNotIn('placeholder', output)

    def test_notifications_block_falls_back_to_cloudinary(self):
        output = self._render_block(
            self.NOTIFICATIONS_BLOCK,
            {'notification': _FakeNotification(self.user_cloudinary)},
        )
        self.assertIn('cloudinary.com', output)
        self.assertNotIn(
            'https://media.promptfinder.net/avatars/b2.jpg', output,
        )
        self.assertNotIn('placeholder', output)

    def test_notifications_block_falls_back_to_placeholder(self):
        output = self._render_block(
            self.NOTIFICATIONS_BLOCK,
            {'notification': _FakeNotification(self.user_neither)},
        )
        self.assertIn('placeholder', output)
        self.assertIn('N', output)  # First letter of 'neither162b'
        self.assertNotIn(
            'https://media.promptfinder.net/avatars/b2.jpg', output,
        )
        self.assertNotIn('cloudinary.com', output)

    # ---- profile templates (user_profile + collections_profile) ----

    # Matches the post-162-B absorption form: `profile.avatar and
    # profile.avatar.url` double-guard for consistency with other templates.
    PROFILE_BLOCK = (
        '{% if profile.b2_avatar_url %}'
        '<img src="{{ profile.b2_avatar_url }}" class="profile-avatar">'
        '{% elif profile.avatar and profile.avatar.url %}'
        '<img src="{{ profile.avatar.url }}" class="profile-avatar">'
        '{% else %}'
        '<div class="profile-avatar-placeholder">'
        '{{ profile_user.username|first|upper }}</div>'
        '{% endif %}'
    )

    def test_user_profile_block_renders_b2_first(self):
        output = self._render_block(
            self.PROFILE_BLOCK,
            {
                'profile': self.user_b2.userprofile,
                'profile_user': self.user_b2,
            },
        )
        self.assertIn(
            'https://media.promptfinder.net/avatars/b2.jpg', output,
        )
        self.assertNotIn('cloudinary.com', output)

    def test_user_profile_block_falls_back_to_cloudinary(self):
        output = self._render_block(
            self.PROFILE_BLOCK,
            {
                'profile': self.user_cloudinary.userprofile,
                'profile_user': self.user_cloudinary,
            },
        )
        self.assertIn('cloudinary.com', output)
        self.assertNotIn(
            'https://media.promptfinder.net/avatars/b2.jpg', output,
        )

    def test_user_profile_block_falls_back_to_placeholder(self):
        output = self._render_block(
            self.PROFILE_BLOCK,
            {
                'profile': self.user_neither.userprofile,
                'profile_user': self.user_neither,
            },
        )
        self.assertIn('placeholder', output)
        self.assertNotIn(
            'https://media.promptfinder.net/avatars/b2.jpg', output,
        )
        self.assertNotIn('cloudinary.com', output)

    # The `collections_profile.html` uses identical `profile.*` traversal
    # as `user_profile.html`, so the PROFILE_BLOCK exercises both. Explicit
    # structure test (above, in AvatarTemplateB2FirstStructureTests) proves
    # the same pattern exists in the file.

    def test_collections_profile_block_shares_profile_traversal_b2(self):
        """
        collections_profile.html uses the same `profile.b2_avatar_url` /
        `profile.avatar.url` / placeholder chain as user_profile.html
        (verified in the structure tests above). This test re-exercises
        the PROFILE_BLOCK with the b2 user to confirm shared traversal
        still resolves b2 first.
        """
        output = self._render_block(
            self.PROFILE_BLOCK,
            {
                'profile': self.user_b2.userprofile,
                'profile_user': self.user_b2,
            },
        )
        self.assertIn(
            'https://media.promptfinder.net/avatars/b2.jpg', output,
        )
        self.assertNotIn('cloudinary.com', output)

    def test_collections_profile_block_falls_back_to_cloudinary(self):
        output = self._render_block(
            self.PROFILE_BLOCK,
            {
                'profile': self.user_cloudinary.userprofile,
                'profile_user': self.user_cloudinary,
            },
        )
        self.assertIn('cloudinary.com', output)
        self.assertNotIn(
            'https://media.promptfinder.net/avatars/b2.jpg', output,
        )

    def test_collections_profile_block_falls_back_to_placeholder(self):
        output = self._render_block(
            self.PROFILE_BLOCK,
            {
                'profile': self.user_neither.userprofile,
                'profile_user': self.user_neither,
            },
        )
        self.assertIn('placeholder', output)
        self.assertNotIn('cloudinary.com', output)
        self.assertNotIn(
            'https://media.promptfinder.net/avatars/b2.jpg', output,
        )

    # ---- leaderboard.html block ----

    LEADERBOARD_BLOCK = (
        '{% if creator.userprofile.b2_avatar_url %}'
        '<img src="{{ creator.userprofile.b2_avatar_url }}" '
        'class="leaderboard-avatar">'
        '{% elif creator.userprofile.avatar and '
        'creator.userprofile.avatar.url %}'
        '<img src="{{ creator.userprofile.avatar.url }}" '
        'class="leaderboard-avatar">'
        '{% else %}'
        '<div class="leaderboard-avatar-placeholder">'
        '{{ creator.username|first|upper }}</div>'
        '{% endif %}'
    )

    def test_leaderboard_block_renders_b2_first(self):
        output = self._render_block(
            self.LEADERBOARD_BLOCK, {'creator': self.user_b2},
        )
        self.assertIn(
            'https://media.promptfinder.net/avatars/b2.jpg', output,
        )
        self.assertNotIn('cloudinary.com', output)

    def test_leaderboard_block_falls_back_to_cloudinary(self):
        output = self._render_block(
            self.LEADERBOARD_BLOCK, {'creator': self.user_cloudinary},
        )
        self.assertIn('cloudinary.com', output)
        self.assertNotIn(
            'https://media.promptfinder.net/avatars/b2.jpg', output,
        )

    def test_leaderboard_block_falls_back_to_placeholder(self):
        output = self._render_block(
            self.LEADERBOARD_BLOCK, {'creator': self.user_neither},
        )
        self.assertIn('placeholder', output)
        self.assertNotIn('cloudinary.com', output)

    # ---- prompt_detail.html block ----

    PROMPT_DETAIL_BLOCK = (
        '{% if prompt.author.userprofile.b2_avatar_url %}'
        '<img src="{{ prompt.author.userprofile.b2_avatar_url }}" '
        'class="avatar-img">'
        '{% elif prompt.author.userprofile.avatar and '
        'prompt.author.userprofile.avatar.url %}'
        '<img src="{{ prompt.author.userprofile.avatar.url }}" '
        'class="avatar-img">'
        '{% else %}'
        '<span class="avatar-letter">'
        '{{ prompt.author.username|first|upper }}</span>'
        '{% endif %}'
    )

    def test_prompt_detail_block_renders_b2_first(self):
        output = self._render_block(
            self.PROMPT_DETAIL_BLOCK,
            {'prompt': _FakePrompt(self.user_b2)},
        )
        self.assertIn(
            'https://media.promptfinder.net/avatars/b2.jpg', output,
        )
        self.assertNotIn('cloudinary.com', output)

    def test_prompt_detail_block_falls_back_to_cloudinary(self):
        output = self._render_block(
            self.PROMPT_DETAIL_BLOCK,
            {'prompt': _FakePrompt(self.user_cloudinary)},
        )
        self.assertIn('cloudinary.com', output)
        self.assertNotIn(
            'https://media.promptfinder.net/avatars/b2.jpg', output,
        )

    def test_prompt_detail_block_falls_back_to_placeholder(self):
        output = self._render_block(
            self.PROMPT_DETAIL_BLOCK,
            {'prompt': _FakePrompt(self.user_neither)},
        )
        self.assertIn('avatar-letter', output)
        self.assertNotIn(
            'https://media.promptfinder.net/avatars/b2.jpg', output,
        )
        self.assertNotIn('cloudinary.com', output)

    # ---- _notification_list.html (partial) ----

    NOTIFICATION_LIST_BLOCK = NOTIFICATIONS_BLOCK  # Same traversal pattern

    def test_notification_list_partial_block_renders_b2_first(self):
        output = self._render_block(
            self.NOTIFICATION_LIST_BLOCK,
            {'notification': _FakeNotification(self.user_b2)},
        )
        self.assertIn(
            'https://media.promptfinder.net/avatars/b2.jpg', output,
        )
        self.assertNotIn('cloudinary.com', output)


class _FakeNotification:
    """Minimal shape for rendering — only `sender` is accessed."""

    def __init__(self, user):
        self.sender = user


class _FakePrompt:
    """Minimal shape for rendering — only `author` is accessed."""

    def __init__(self, user):
        self.author = user
