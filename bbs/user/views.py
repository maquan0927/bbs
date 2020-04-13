from rest_framework.response import Response
from rest_framework import status
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        # self.create(request, *args, **kwargs)