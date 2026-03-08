from django.apps import AppConfig


class OrchestratorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.orchestrator"
    verbose_name = "Orchestrator"

    def ready(self):
        # Ensure all signals and beat schedules are loaded
        pass
