from django.apps import AppConfig


class MlmtreeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mlmtree'


    def ready(self):
        import mlmtree.signals 
