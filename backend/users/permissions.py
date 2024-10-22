from rest_framework.permissions import SAFE_METHODS, BasePermission

MUTATE_METHODS = ['PUT', 'PATCH']
UNSAFE_METHODS = MUTATE_METHODS + ['DELETE']
CREATE_RETRIEVE_METHODS = SAFE_METHODS + ('POST',)


class OnlySuperuserDelete(BasePermission):
    """Удалить может только SU."""

    message = 'Недостаточно прав для удаления.'

    def has_permission(self, request, view):
        if request.method == 'DELETE':
            return request.user.is_authenticated and request.user.is_superuser
        else:
            return True


class OnlyOwnerAndSuperuserUpdate(BasePermission):
    """
    Изменить может только владелец или SU,
    просмотреть - авторизованный.
    """

    message = 'Недостаточно прав для изменения.'

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method == 'DELETE':
            return OnlySuperuserDelete()
        else:
            return request.method in CREATE_RETRIEVE_METHODS or (
                request.method in MUTATE_METHODS and (
                    obj.owner == request.user or request.user.is_superuser
                )
            )


class OnlyOwnerAndSuperuserUpdateOrDelete(BasePermission):
    """
    Изменить или удалить может только владелец или SU,
    просмотреть - авторизованный.
    """

    message = 'Недостаточно прав для изменения.'

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.method in CREATE_RETRIEVE_METHODS or (
            request.method in UNSAFE_METHODS and (
                obj.owner == request.user or request.user.is_superuser
            )
        )


class OnlyAdminAndSuperuserUpdate(BasePermission):
    """
    Изменить может только сотрудник ТО или SU,
    просмотреть - авторизованный.
    """

    message = 'Недостаточно прав для изменения.'

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method == 'DELETE':
            return OnlySuperuserDelete()
        else:
            return request.method in CREATE_RETRIEVE_METHODS or (
                request.method in MUTATE_METHODS and (
                    request.user.is_admin or request.user.is_superuser
                )
            )


class OnlyAdminAndSuperuserUpdateOrDelete(BasePermission):
    """
    Изменить или удалить может только сотрудник ТО или SU,
    просмотреть - авторизованный.
    """

    message = 'Недостаточно прав для изменения.'

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.method in CREATE_RETRIEVE_METHODS or (
            request.method in UNSAFE_METHODS and (
                request.user.is_admin or request.user.is_superuser
            )
        )
