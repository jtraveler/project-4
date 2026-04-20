"""
Custom allauth adapters.

ClosedAccountAdapter: blocks email/password signup (CAPTCHA + email
verification come in a later session).

OpenSocialAccountAdapter (163-D): permits social signup so the
Google OAuth flow can create new users when the developer enables
OAuth credentials. Kept separate from ClosedAccountAdapter so the
password-signup freeze is preserved (163-A Gotcha 1).
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class ClosedAccountAdapter(DefaultAccountAdapter):
    """Disables email/password signup. Wired via ACCOUNT_ADAPTER."""

    def is_open_for_signup(self, request):
        """Return False to close registration."""
        return False


class OpenSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Permits social-login signup. Allauth uses this adapter for the
    social-only signup path (163-D). Separate from
    ClosedAccountAdapter so the password-signup freeze is preserved.

    Wired via SOCIALACCOUNT_ADAPTER in settings.py.
    """

    def is_open_for_signup(self, request, sociallogin):
        return True
