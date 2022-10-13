from django.apps import AppConfig

class Notifications(AppConfig):
    name = 'cogofly'
    
    def ready(self):
        from . import signals