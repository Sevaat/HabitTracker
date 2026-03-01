from django.urls import path
from . import views

urlpatterns = [
    # Список привычек и создание
    path('', views.HabitListCreateView.as_view(), name='habit-list'),

    # Детальная информация, редактирование, удаление
    path('<int:pk>/', views.HabitRetrieveUpdateDestroyView.as_view(), name='habit-detail'),

    # Публичные привычки
    path('public/', views.PublicHabitListView.as_view(), name='public-habits'),

    # Переключение публичности
    path('<int:pk>/toggle-public/', views.HabitTogglePublicView.as_view(), name='toggle-public'),
]