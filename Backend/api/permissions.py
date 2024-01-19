from rest_framework.permissions import BasePermission, IsAuthenticated


class IsAdmin(BasePermission):
    """Права только для админа"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 3 and (request.user.blocked is False)


class IsPartnerOrAdmin(BasePermission):
    """Админ либо партнер владелец объекта"""
    def has_object_permission(self, request, view, obj):
        return (request.user.role == 2 and
                obj.owner == request.user) or request.user.role == 3

    def has_permission(self, request, view):
        return IsAuthenticated().has_permission(request, view) and request.user.is_authenticated and (request.user.blocked is False)


class IsPartnerOrAdminCreate(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == 2 or request.user.role == 3) and (request.user.blocked is False)
    

class IsUser(BasePermission):
    """Пользователь аутентицифирован, является либо админом, либо обычным пользователем и не заблокирован"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == 1 or request.user.role == 3) and (request.user.blocked is False)


class IsPartnerOrAdminForApplicationsOnExcursions(BasePermission):
    """На заявку на экскурсию может ответить либо администратор либо владелец экскурсии"""
    def has_object_permission(self, request, view, obj):
        return (request.user.role == 2 and
                obj.excursion.owner == request.user) or request.user.role == 3

    def has_permission(self, request, view):
        return IsAuthenticated().has_permission(request, view) and request.user.is_authenticated and (request.user.blocked is False)
