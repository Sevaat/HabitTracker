from django.urls import path

from . import views

urlpatterns = [
    path("link/", views.TelegramLinkView.as_view(), name="telegram-link"),
    path("status/", views.TelegramStatusView.as_view(), name="telegram-status"),
    path("unlink/", views.TelegramUnlinkView.as_view(), name="telegram-unlink"),
]
