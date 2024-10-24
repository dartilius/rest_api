from rest_framework.permissions import SAFE_METHODS, BasePermission

MUTATE_METHODS = ['PUT', 'PATCH']
UNSAFE_METHODS = [*MUTATE_METHODS, 'DELETE']
CREATE_RETRIEVE_METHODS = [*SAFE_METHODS, 'POST']

error_message = 'Недостаточно прав.'


class OnlySuperuserCUDAuthRetrieve(BasePermission):
    """
    Создать, изменить и удалить может только SU,
    просмотреть - любой авторизованный.
    """

    message = error_message

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or request.user.is_superuser


class OnlySuperuserDeleteAdminCRU(BasePermission):
    """
    Удалить может только SU.

    Изменить может только сотрудник ТО или SU,
    просмотреть - любой авторизованный.
    """

    message = error_message

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method == 'DELETE':
            return request.user.is_superuser

        if request.method == 'GET':
            return True

        return request.method in CREATE_RETRIEVE_METHODS or (
            request.method in MUTATE_METHODS and (
                request.user.is_admin or request.user.is_superuser
            )
        )


class OnlySuperuserDeleteOwnerCRU(BasePermission):
    """
    Удалить может только SU.

    Изменить может только владелец или SU,
    просмотреть - любой авторизованный.
    """

    message = error_message

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method == 'DELETE':
            return request.user.is_superuser

        return request.method in CREATE_RETRIEVE_METHODS or (
            request.method in MUTATE_METHODS and (
                obj.owner == request.user or request.user.is_superuser
            )
        )


class OwnerAndSuperuserCRUD(BasePermission):
    """
    Изменить или удалить может только владелец или SU,
    просмотреть - любой авторизованный.
    """

    message = error_message

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.method in CREATE_RETRIEVE_METHODS or (
            request.method in UNSAFE_METHODS and (
                obj.owner == request.user or request.user.is_superuser
            )
        )


class AdminAndSuperuserCRUD(BasePermission):
    """
    Изменить или удалить может только сотрудник ТО или SU,
    просмотреть - любой авторизованный.
    """

    message = error_message

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.method in CREATE_RETRIEVE_METHODS or (
            request.method in UNSAFE_METHODS and (
                request.user.is_admin or request.user.is_superuser
            )
        )
