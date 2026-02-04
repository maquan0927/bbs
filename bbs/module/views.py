from rest_framework import mixins
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from common.decorator import user_passes_test
from common.permissions import IsAdmin
from common.response import api_response, ErrorCode
from django.utils.decorators import method_decorator
from module.models import Module
from module.serializers import ModuleSerializer
from django.http import Http404


class ModuleList(ListAPIView, mixins.CreateModelMixin):
    """板块列表"""

    serializer_class = ModuleSerializer
    pagination_class = None

    def get_queryset(self):
        return Module.objects.filter(is_active=True)

    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def post(self, request, *args, **kwargs):
        """创建板块（仅管理员）"""
        return self.create(request, *args, **kwargs)


class ModuleDetail(RetrieveUpdateDestroyAPIView):
    """板块详情"""

    serializer_class = ModuleSerializer
    permission_classes = (IsAdmin,)

    def get_object(self):
        try:
            return Module.objects.get(id=self.kwargs['id'])
        except Module.DoesNotExist:
            raise Http404

    def get(self, request, *args, **kwargs):
        """获取板块详情"""
        module = self.get_object()
        serializer = self.get_serializer(module)
        return api_response(data=serializer.data)

    def delete(self, request, *args, **kwargs):
        """软删除板块"""
        module = self.get_object()
        module.is_active = False
        module.save()
        return api_response(message='删除成功')
