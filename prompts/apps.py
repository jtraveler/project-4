from django.apps import AppConfig


class PromptsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'prompts'

    def ready(self):
        """
        Import signal handlers when Django starts.

        This method is called once Django has finished loading the app.
        It ensures our signal handlers (like UserProfile auto-creation)
        are registered and active.

        163-D: social_signals hooks allauth's user_signed_up +
        social_account_added. Inert until the developer configures
        Google OAuth credentials.
        """
        import prompts.signals  # noqa: F401
        import prompts.notification_signals  # noqa: F401
        import prompts.social_signals  # noqa: F401 — 163-D
        prompts.notification_signals.connect_m2m_signals()
