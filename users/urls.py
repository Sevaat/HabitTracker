from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

urlpatterns = [
    # Аутентификация (если нужны дополнительные эндпоинты)
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Регистрация пользователя
    path("register/", views.UserRegistrationView.as_view(), name="user_register"),
]
