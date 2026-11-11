from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "BeyondConnect Chatbot Admin"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("chat.urls")),
]
