from django.urls import path
from . import views

urlpatterns = [
    path('', views.show_message, name = 'show_message'),
]