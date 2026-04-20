"""
Social-login signal handlers — 163-D.

Two receivers from django-allauth:

1. `user_signed_up` fires AFTER any signup completes. For social
   signups, `sociallogin` is present in kwargs. For password signups
   it's absent — we skip.

2. `social_account_added` fires when an EXISTING User links a new
   SocialAccount (e.g. a password user connects Google for the
   first time).

Both call `capture_social_avatar(user, sociallogin, force=False)` —
`force=False` preserves any direct-uploaded avatar the user has
(their explicit choice wins over auto-capture).

Registered at app startup via `prompts/apps.py` `ready()`.

163-A R5 (corrected by @architect-review): BOTH signals must be
hooked. `user_signed_up` alone misses the existing-user-links-provider
case.
"""
import logging

from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import social_account_added

from prompts.services.social_avatar_capture import capture_social_avatar

logger = logging.getLogger(__name__)


@receiver(user_signed_up)
def handle_social_signup(sender, request, user, **kwargs):
    """
    First-time signup — social or password.

    For password signup, `sociallogin` is absent in kwargs → no-op.
    For social signup, fetch the provider photo and upload to B2.

    `force=False` — a new user with a new profile has avatar_source
    'default', so the force flag doesn't matter here, but we pass
    False explicitly for clarity and consistency with the
    social_account_added handler.
    """
    sociallogin = kwargs.get('sociallogin')
    if not sociallogin:
        # Password signup — not our concern.
        return

    result = capture_social_avatar(user, sociallogin, force=False)

    if result.get('skipped'):
        logger.info(
            'Social signup avatar skipped for user_id=%s reason=%s',
            user.id, result.get('reason'),
        )
    elif result.get('success'):
        logger.info(
            'Social signup avatar captured for user_id=%s provider=%s',
            user.id, sociallogin.account.provider,
        )
    else:
        logger.warning(
            'Social signup avatar FAILED for user_id=%s reason=%s',
            user.id, result.get('reason'),
        )


@receiver(social_account_added)
def handle_social_account_linked(sender, request, sociallogin, **kwargs):
    """
    Existing user links a new social account.

    Example: a user who signed up with email+password later connects
    their Google account so they can sign in with either. This fires
    then.

    `force=False` means if they already have a direct-uploaded
    avatar (`avatar_source='direct'`), we don't overwrite. Their
    local upload wins. 163-E's sync button passes force=True when
    the user explicitly wants to swap.
    """
    user = sociallogin.user

    result = capture_social_avatar(user, sociallogin, force=False)

    if result.get('skipped'):
        logger.info(
            'Social account linked, avatar skipped '
            'user_id=%s reason=%s',
            user.id, result.get('reason'),
        )
    elif result.get('success'):
        logger.info(
            'Social account linked, avatar captured '
            'user_id=%s provider=%s',
            user.id, sociallogin.account.provider,
        )
    else:
        logger.warning(
            'Social account linked, avatar FAILED '
            'user_id=%s reason=%s',
            user.id, result.get('reason'),
        )
