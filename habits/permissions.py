from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение на редактирование только владельцу.
    Для публичных привычек - только чтение.
    """

    def has_object_permission(self, request, view, obj):
        # Разрешаем безопасные методы всем (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Для остальных методов проверяем, является ли пользователь владельцем
        return obj.user == request.user


class IsOwner(permissions.BasePermission):
    """
    Разрешение только для владельца (полный доступ)
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
