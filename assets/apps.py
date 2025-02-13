from django.apps import AppConfig


class AssetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'assets'

    def ready(self):
        import assets.signals
        from actstream import registry

        
        from .models import Asset
        registry.register(Asset)