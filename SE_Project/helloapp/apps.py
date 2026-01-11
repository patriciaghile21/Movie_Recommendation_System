from django.apps import AppConfig


class HelloappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'helloapp'

    def ready(self):
        import importlib
        importlib.import_module('.signals', package=self.name)