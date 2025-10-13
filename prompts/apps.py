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
        """
        import prompts.signals  # noqa: F401
