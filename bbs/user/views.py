from rest_framework.response import Response
from rest_framework import mixins, generics
from user.models import User
from user.serializers import UserSerializer
from common.decorator import user_passes_test
from django.utils.decorators import method_decorator
from rest_framework.views import APIView, status
from django.core.mail import send_mail
from django.conf import settings
from common.redis_api import set_to_redis, get_from_redis, delete_to_redis
import random

class UserEmail(APIView):

    def post(self, request, *args, **kwargs):
        if User.objects.filter(email=request.data['email']).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZ0123456789'
        base_len = len(base_str)
        random_str = ''
        for i in range(6):
            random_str += base_str[random.randint(0, base_len)]
        send_mail('校园论坛邮箱验证', '邮箱验证码为：%s' % random_str,
                  settings.EMAIL_HOST_FROM, [request.data['email']] ,
                  auth_user=settings.EMAIL_HOST_USER, auth_password=settings.EMAIL_HOST_PASSWORD)
        set_to_redis(request.data['email'], random_str, 180)
        return Response(status=status.HTTP_200_OK)


class UserList(generics.GenericAPIView,
               mixins.CreateModelMixin,
               mixins.ListModelMixin):

    serializer_class = UserSerializer
    queryset = User.objects.all().order_by('id')

    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if User.objects.filter(username=request.data['username']).exists() or User.objects.filter(email=request.data['email']).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        code = get_from_redis(request.data['email'])
        if code:
            if code != request.data['code']:
                return Response(status=status.HTTP_302_FOUND)
        else:
            return Response(status=status.HTTP_302_FOUND)
        delete_to_redis(request.data['email'])
        return self.create(request, *args, **kwargs)


class UserDetail(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
