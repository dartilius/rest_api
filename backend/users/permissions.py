from rest_framework import permissions


class IsSuperUserOrAuthReadOnly(permissions.BasePermission):
    """Читает аутентифицированный, удаляет, обновляет и удаляет SU."""

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated and
            request.user.is_superuser
        )


class AuthAndOnlySuperUserDelete(permissions.BasePermission):
    """Удалить может только SU."""

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS and
            request.user.is_authenticated or
            request.user.is_authenticated and (
                request.user.is_manager or
                request.user.is_superuser or
                request.user.is_admin
            )
        )

    def has_object_permission(self, request, view, obj):
        # return (
        #     (
        #         request.method == 'DELETE' and
        #         request.user.is_authenticated and
        #         request.user.is_superuser
        #     ) or (
        #         request.method != 'DELETE' and
        #         request.user.is_authenticated and
        #         request.user.is_admin or
        #         request.user.is_manager or
        #         request.user.is_superuser
        #     )
        # )
        return request.user.is_authenticated and request.user.is_superuser
