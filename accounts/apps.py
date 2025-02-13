from django.apps import AppConfig




class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    
    def ready(self):
        import accounts.signals
        from actstream import registry

        
        from .models import CustomUser
        registry.register(CustomUser)
        
        
        

