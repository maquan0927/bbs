from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """管理员权限"""
    message = '需要管理员权限'

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class IsLogin(BasePermission):
    """登录权限"""
    message = '请先登录'

    def has_permission(self, request, view):
        # GET请求允许匿名访问
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        # 其他请求需要登录
        return request.user and request.user.is_authenticated


class IsOwnerOrReadOnly(BasePermission):
    """只有拥有者可以修改"""
    message = '只有拥有者才能进行此操作'

    def has_object_permission(self, request, view, obj):
        # 读取请求允许所有人
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        # 管理员可以操作任何对象
        if request.user and request.user.is_superuser:
            return True
        # 检查是否是拥有者
        return obj.user == request.user


class IsModuleAdmin(BasePermission):
    """板块管理员权限"""
    message = '需要板块管理员权限'

    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        if request.user and request.user.is_superuser:
            return True
        # 检查是否是板块管理员
        if hasattr(obj, 'module') and obj.module:
            return request.user in obj.module.admin.all()
        return False
