from django.apps import AppConfig

class CoreAppConfig(AppConfig):
    name = 'core'

    def ready(self):
        # Use signals (staff permissions, etc.)
        import core.signals
