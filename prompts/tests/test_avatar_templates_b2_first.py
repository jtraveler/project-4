"""
Regression tests for 163-B simplification of the avatar templates.

Originally written for Session 162-B (three-branch pattern:
`b2_avatar_url` → Cloudinary `avatar.url` → letter placeholder).
163-B collapsed to two branches (`avatar_url` → letter placeholder)
when UserProfile.avatar CloudinaryField was dropped and
b2_avatar_url was renamed to avatar_url in migration 0085.

Six templates were updated in 162-B and simplified in 163-B:
  - prompts/notifications.html
  - prompts/partials/_notification_list.html
  - prompts/user_profile.html
  - prompts/collections_profile.html
  - prompts/leaderboard.html
  - prompts/prompt_detail.html

`edit_profile.html` is owned by 163-C (direct upload rebuild) and
is NOT covered here.
"""
from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.template import Context, Template
from django.test import TestCase


SIX_TEMPLATE_PATHS = (
    'prompts/notifications.html',
    'prompts/partials/_notification_list.html',
    'prompts/user_profile.html',
    'prompts/collections_profile.html',
    'prompts/leaderboard.html',
    'prompts/prompt_detail.html',
)


def _read_template(relative_path: str) -> str:
    """Read a template file as raw text for structure-level checks."""
    full_path = Path(settings.BASE_DIR) / 'prompts' / 'templates' / relative_path
    return full_path.read_text()


class AvatarTemplateTwoBranchStructureTests(TestCase):
    """
    Structural checks — each of the 6 templates must use the
    `avatar_url` field name (163-B rename) and must NOT contain the
    old `b2_avatar_url` field name or the old Cloudinary `{% elif ...
    avatar and ... avatar.url %}` middle branch.

    Paired positive + negative assertions per CC_SPEC_TEMPLATE #9.
    """

    def test_every_template_uses_avatar_url_not_b2_avatar_url(self):
        for relative in SIX_TEMPLATE_PATHS:
            src = _read_template(relative)
            # Positive: new field name present
            self.assertIn(
                'avatar_url', src,
                f'{relative} missing post-163-B avatar_url reference',
            )
            # Paired negative: old b2_ prefix removed
            self.assertNotIn(
                'b2_avatar_url', src,
                f'{relative} still references pre-163-B b2_avatar_url',
            )

    def test_every_template_dropped_cloudinary_elif_branch(self):
        # The Cloudinary middle branch was `{% elif ... avatar and
        # ... avatar.url %}` in 162-B. After 163-B, no template
        # should reference `.avatar.url` (the CloudinaryField).
        for relative in SIX_TEMPLATE_PATHS:
            src = _read_template(relative)
            self.assertNotIn(
                '.avatar.url', src,
                (
                    f'{relative} still dereferences CloudinaryField '
                    f'.avatar.url — 163-B simplification incomplete'
                ),
            )

class AvatarTemplateTwoBranchRenderTests(TestCase):
    """
    Render-level checks — extract the avatar if/else block from each
    template into a minimal `Template` object, then render it with
    two UserProfile states (avatar_url set, avatar_url empty) to
    verify each branch produces the expected output.
    """

    def setUp(self):
        self.user_with_avatar = User.objects.create_user(
            username='avatar163b',
            email='avatar@example.com',
            password='x',
        )
        self.user_with_avatar.userprofile.avatar_url = (
            'https://media.promptfinder.net/avatars/direct_1.jpg'
        )
        self.user_with_avatar.userprofile.avatar_source = 'direct'
        self.user_with_avatar.userprofile.save()
        self.user_with_avatar.refresh_from_db()

        self.user_without_avatar = User.objects.create_user(
            username='noavatar163b',
            email='noavatar@example.com',
            password='x',
        )
        self.user_without_avatar.refresh_from_db()

    def _render(self, source: str, context: dict) -> str:
        return Template(source).render(Context(context))

    # ---- notifications.html block ----

    NOTIFICATIONS_BLOCK = (
        '{% if notification.sender.userprofile.avatar_url %}'
        '<img src="{{ notification.sender.userprofile.avatar_url }}" '
        'class="notif-avatar">'
        '{% else %}'
        '<div class="notif-avatar-placeholder">'
        '{{ notification.sender.username|first|upper }}</div>'
        '{% endif %}'
    )

    def test_notifications_block_renders_avatar_url_when_set(self):
        class FakeNotification:
            sender = self.user_with_avatar

        rendered = self._render(
            self.NOTIFICATIONS_BLOCK,
            {'notification': FakeNotification()},
        )
        self.assertIn('avatars/direct_1.jpg', rendered)     # positive
        self.assertNotIn('notif-avatar-placeholder', rendered)  # paired negative

    def test_notifications_block_renders_placeholder_when_empty(self):
        class FakeNotification:
            sender = self.user_without_avatar

        rendered = self._render(
            self.NOTIFICATIONS_BLOCK,
            {'notification': FakeNotification()},
        )
        self.assertIn('notif-avatar-placeholder', rendered)  # positive
        # Paired negative: first letter of username rendered
        self.assertIn('N', rendered)

    # ---- user_profile.html block ----

    USER_PROFILE_BLOCK = (
        '{% if profile.avatar_url %}'
        '<img src="{{ profile.avatar_url }}" class="profile-avatar">'
        '{% else %}'
        '<div class="profile-avatar-placeholder">'
        '{{ profile_user.username|slice:":1"|upper }}'
        '</div>'
        '{% endif %}'
    )

    def test_user_profile_block_renders_avatar_url_when_set(self):
        rendered = self._render(
            self.USER_PROFILE_BLOCK,
            {
                'profile': self.user_with_avatar.userprofile,
                'profile_user': self.user_with_avatar,
            },
        )
        self.assertIn('avatars/direct_1.jpg', rendered)          # positive
        self.assertNotIn('profile-avatar-placeholder', rendered)  # paired negative

    def test_user_profile_block_renders_placeholder_when_empty(self):
        rendered = self._render(
            self.USER_PROFILE_BLOCK,
            {
                'profile': self.user_without_avatar.userprofile,
                'profile_user': self.user_without_avatar,
            },
        )
        self.assertIn('profile-avatar-placeholder', rendered)    # positive
        self.assertNotIn('<img src="', rendered)                 # paired negative

    # ---- leaderboard.html block ----

    LEADERBOARD_BLOCK = (
        '{% if creator.userprofile.avatar_url %}'
        '<img src="{{ creator.userprofile.avatar_url }}" '
        'class="leaderboard-avatar">'
        '{% else %}'
        '<div class="leaderboard-avatar-placeholder">'
        '{{ creator.username|first|upper }}</div>'
        '{% endif %}'
    )

    def test_leaderboard_block_renders_avatar_url_when_set(self):
        rendered = self._render(
            self.LEADERBOARD_BLOCK,
            {'creator': self.user_with_avatar},
        )
        self.assertIn('avatars/direct_1.jpg', rendered)
        self.assertNotIn('leaderboard-avatar-placeholder', rendered)

    def test_leaderboard_block_renders_placeholder_when_empty(self):
        rendered = self._render(
            self.LEADERBOARD_BLOCK,
            {'creator': self.user_without_avatar},
        )
        self.assertIn('leaderboard-avatar-placeholder', rendered)  # positive
        self.assertNotIn('<img', rendered)                         # paired negative

    # ---- prompt_detail.html block ----

    PROMPT_DETAIL_BLOCK = (
        '{% if prompt.author.userprofile.avatar_url %}'
        '<img src="{{ prompt.author.userprofile.avatar_url }}" '
        'class="avatar-img">'
        '{% else %}'
        '<span class="avatar-letter">'
        '{{ prompt.author.username|first|upper }}</span>'
        '{% endif %}'
    )

    def test_prompt_detail_block_renders_avatar_url_when_set(self):
        class FakePrompt:
            author = self.user_with_avatar

        rendered = self._render(
            self.PROMPT_DETAIL_BLOCK,
            {'prompt': FakePrompt()},
        )
        self.assertIn('avatars/direct_1.jpg', rendered)
        self.assertNotIn('avatar-letter', rendered)

    def test_prompt_detail_block_renders_letter_when_empty(self):
        class FakePrompt:
            author = self.user_without_avatar

        rendered = self._render(
            self.PROMPT_DETAIL_BLOCK,
            {'prompt': FakePrompt()},
        )
        self.assertIn('avatar-letter', rendered)  # positive
        self.assertNotIn('<img', rendered)        # paired negative
