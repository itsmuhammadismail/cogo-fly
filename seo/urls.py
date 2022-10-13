from .views import interface


from django.urls import path


urlpatterns = [
    path("", interface, name="interface"),
]
