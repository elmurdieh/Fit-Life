from django.apps import AppConfig

class PrimerAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'primerApp'

    def ready(self):
        import primerApp.signals # Importa el archivo donde está definido el signal
