from rest_framework.permissions import SAFE_METHODS, BasePermission

MUTATE_METHODS = ('PUT', 'PATCH')
MUTATE_DELETE_METHODS = (*MUTATE_METHODS, 'DELETE')
NO_DELETE_METHODS = (*MUTATE_METHODS, *SAFE_METHODS)

error_message = 'Недостаточно прав' + ' %(class)s.__doc__'


class SuperuserCUDAuthRetrieve(BasePermission):
    """
    Создать, изменить и удалить может только SU,
    просмотреть - любой авторизованный.
    """

    message = error_message

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated

        return request.user.is_authenticated and request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or request.user.is_superuser


class AdminManagerCUDAuthRetrieve(BasePermission):
    """
    Создать, изменить и удалить может только любой сотрудник,
    просмотреть - любой авторизованный.
    """

    message = error_message

    def has_permission(self, request, view):
        if request.method == 'POST':
            return not request.user.is_ordinary

        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return not request.user.is_ordinary


class OnlySuperuserDAdminManagerCUAuthRetrieve(BasePermission):
    """
    Удалить может только SU.

    Создать, изменить - сотрудник ТО или менеджер,
    просмотреть - любой авторизованный.
    """

    message = error_message

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated

        return not request.user.is_ordinary

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated

        if request.method == 'DELETE':
            return request.user.is_superuser

        return not request.user.is_ordinary


class OnlySuperuserDeleteAdminManagerCRU(BasePermission):
    """Удалить может только SU, всё остальное - только сотрудники."""

    message = error_message

    def has_permission(self, request, view):
        return request.user.is_authenticated and not request.user.is_ordinary

    def has_object_permission(self, request, view, obj):
        if request.method in NO_DELETE_METHODS:
            return not request.user.is_ordinary

        return request.user.is_superuser


class SuperuserDeleteAdminCRU(BasePermission):
    """
    Удалить может только SU.

    Изменить может только сотрудник ТО или SU,
    создать и просмотреть - любой авторизованный.
    """

    message = error_message

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if request.method in MUTATE_METHODS:
            return request.user.is_admin or request.user.is_superuser

        return request.user.is_superuser


class SuperuserDeleteOwnerCRU(BasePermission):
    """
    Удалить может только SU.

    Изменить может только владелец или SU,
    создать и просмотреть - любой авторизованный.
    """

    message = error_message

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS or (
            request.method in MUTATE_METHODS and (
                obj.owner == request.user or request.user.is_superuser
            )
        ):
            return True

        return request.user.is_superuser


class OwnerAndSuperuserCRUD(BasePermission):
    """
    Изменить или удалить может только владелец или SU,
    создать и просмотреть - любой авторизованный.
    """

    message = error_message

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return request.method in MUTATE_DELETE_METHODS and (
            obj.owner == request.user or request.user.is_superuser
        )


class AdminAndSuperuserCRUD(BasePermission):
    """
    Изменить или удалить может только сотрудник ТО или SU,
    создать и просмотреть - любой авторизованный.
    """

    message = error_message

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return request.method in MUTATE_DELETE_METHODS and (
            request.user.is_admin or request.user.is_superuser
        )


class OnlySuperuserUDAdminManagerCR(BasePermission):
    """
    Изменить или удалить может только SU,
    создать и просмотреть - только сотрудник.
    """

    message = error_message

    def has_permission(self, request, view):
        return request.user.is_authenticated and not request.user.is_ordinary

    def has_object_permission(self, request, view, obj):
        if request.method in MUTATE_DELETE_METHODS:
            return request.user.is_superuser

        return request.method in SAFE_METHODS and not request.user.is_ordinary


class OnlySuperuserUDAdminManagerCAuthR(BasePermission):
    """
    Изменить или удалить может только SU,
    создать - только сотрудник, а посмотреть любой авторизованный.
    """

    message = error_message

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated

        return request.user.is_authenticated and not request.user.is_ordinary

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if request.method in MUTATE_DELETE_METHODS:
            return request.user.is_superuser
