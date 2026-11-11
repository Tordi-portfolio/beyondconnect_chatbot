from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.index, name="index"),
    path("healthz", views.health, name="health"),
    path("api/chat/", views.api_chat, name="api_chat"),
    path("api/chat/<uuid:cid>/", views.api_history, name="api_history"),
]
