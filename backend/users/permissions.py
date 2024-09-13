from rest_framework import permissions


class OnlySuperUserDelete(permissions.BasePermission):
    """Удалить может только SU."""

    message = 'Недостаточно прав для удаления.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser


class OnlyOwnerAndSuperUserDelete(permissions.BasePermission):
    """Удалить может только владелец или SU."""

    message = 'Недостаточно прав для удаления.'

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user.is_superuser


class OnlyOwnerAndSuperUserUpdate(permissions.BasePermission):
    """Изменить может только владелец или SU."""

    message = 'Недостаточно прав для изменения.'

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user.is_superuser
