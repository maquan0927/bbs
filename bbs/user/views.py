from django.http.response import Http404
from rest_framework import mixins, generics
from user.models import User
from user.serializers import UserSerializer
from rest_framework.permissions import AllowAny
from common.decorator import user_passes_test
from django.utils.decorators import method_decorator

class UserList(generics.GenericAPIView,
               mixins.CreateModelMixin,
               mixins.ListModelMixin):

    serializer_class = UserSerializer
    queryset = User.objects.all().order_by('id')
    permission_classes = (AllowAny, )

    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.create(request, *args, **kwargs)


class UserDetail(generics.GenericAPIView,
                 mixins.RetrieveModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.DestroyModelMixin):

    serializer_class = UserSerializer

    def get_object(self):
        try:
            return User.objects.get(id=self.kwargs['id'])
        except:
            raise Http404

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)