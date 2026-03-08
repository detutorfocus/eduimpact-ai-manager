from django.apps import AppConfig


class BrandsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.brands"
    verbose_name = "Brands"

    def ready(self):
        pass  # Signal registration can go here in future
