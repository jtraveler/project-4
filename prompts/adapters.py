"""
Custom allauth account adapter.

Temporarily closes registration while keeping login active.
To re-enable registration, remove ACCOUNT_ADAPTER from settings.py.
"""
from allauth.account.adapter import DefaultAccountAdapter


class ClosedAccountAdapter(DefaultAccountAdapter):
    """Adapter that disables new user registration."""

    def is_open_for_signup(self, request):
        """Return False to close registration."""
        return False
