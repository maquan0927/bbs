from rest_framework.response import Response
from rest_framework import mixins, generics
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from common.decorator import user_passes_test
from common.permissions import IsAdmin, IsLogin
from django.utils.decorators import method_decorator
from module.models import Module
from module.serializers import ModuleSerializer
from django.http import Http404

class ModuleList(ListAPIView,
                 mixins.CreateModelMixin):

    serializer_class = ModuleSerializer
    queryset = Module.objects.all().order_by('id')
    pagination_class = None

    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ModuleDetail(RetrieveUpdateDestroyAPIView):

    serializer_class = ModuleSerializer
    permission_classes = (IsAdmin,)

    def get_object(self):
        try:
            return Module.objects.get(id=self.kwargs['id'])
        except:
            raise Http404
