from rest_framework.response import Response
from rest_framework import mixins, generics, status
from rest_framework.views import APIView
from user.models import User
from user.serializers import UserSerializer
from common.decorator import user_passes_test
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.conf import settings
from common.redis_api import set_to_redis, get_from_redis, delete_to_redis
from django.contrib.auth.hashers import make_password
from common.permissions import IsLogin
from common.response import api_response, ErrorCode
import random
import re


class UserEmail(APIView):
    """邮箱验证码发送"""

    def post(self, request, *args, **kwargs):
        email = request.data.get('email', '')

        # 验证邮箱格式
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            return api_response(code=ErrorCode.PARAM_ERROR, message='邮箱格式不正确')

        if User.objects.filter(email=email).exists():
            return api_response(code=ErrorCode.EMAIL_EXISTS, message='该邮箱已被注册')

        # 检查是否在冷却时间内
        existing_code = get_from_redis(f'email_cooldown_{email}')
        if existing_code:
            return api_response(code=ErrorCode.TOO_FREQUENT, message='请求过于频繁，请稍后再试')

        # 生成6位验证码
        base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZ0123456789'
        random_str = ''.join(random.choice(base_str) for _ in range(6))

        try:
            send_mail(
                '校园论坛邮箱验证',
                f'您的邮箱验证码为：{random_str}，有效期3分钟，请勿泄露给他人。',
                settings.EMAIL_HOST_FROM,
                [email],
                auth_user=settings.EMAIL_HOST_USER,
                auth_password=settings.EMAIL_HOST_PASSWORD
            )
        except Exception as e:
            return api_response(code=ErrorCode.EMAIL_SEND_FAILED, message='邮件发送失败')

        # 存储验证码，有效期3分钟
        set_to_redis(email, random_str, 180)
        # 设置冷却时间60秒
        set_to_redis(f'email_cooldown_{email}', '1', 60)

        return api_response(message='验证码发送成功')


class UserList(generics.GenericAPIView,
               mixins.CreateModelMixin,
               mixins.ListModelMixin):
    """用户列表和注册"""

    serializer_class = UserSerializer
    queryset = User.objects.all().order_by('-date_joined')
    pagination_class = None

    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def get(self, request, *args, **kwargs):
        """获取用户列表（仅管理员）"""
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """用户注册"""
        username = request.data.get('username', '')
        email = request.data.get('email', '')
        code = request.data.get('code', '')

        # 参数验证
        if not all([username, email, code]):
            return api_response(code=ErrorCode.PARAM_ERROR, message='参数不完整')

        # 用户名长度验证
        if len(username) < 2 or len(username) > 20:
            return api_response(code=ErrorCode.PARAM_ERROR, message='用户名长度应在2-20个字符之间')

        # 检查用户名和邮箱是否已存在
        if User.objects.filter(username=username).exists():
            return api_response(code=ErrorCode.USERNAME_EXISTS, message='用户名已被使用')

        if User.objects.filter(email=email).exists():
            return api_response(code=ErrorCode.EMAIL_EXISTS, message='邮箱已被注册')

        # 验证码校验
        stored_code = get_from_redis(email)
        if not stored_code or stored_code != code:
            return api_response(code=ErrorCode.CODE_ERROR, message='验证码错误或已过期')

        # 删除已使用的验证码
        delete_to_redis(email)

        return self.create(request, *args, **kwargs)


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    """用户详情"""

    serializer_class = UserSerializer
    permission_classes = (IsLogin,)

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        """获取当前用户信息"""
        return api_response(data=self.get_serializer(self.get_object()).data)

    def patch(self, request, *args, **kwargs):
        """更新用户信息"""
        if request.data.get('password', None):
            request.data['password'] = make_password(request.data['password'])
        elif 'password' in request.data:
            request.data.pop('password')
        return self.partial_update(request, *args, **kwargs)


class UserPublicProfile(generics.RetrieveAPIView):
    """用户公开信息（无需登录）"""

    serializer_class = UserSerializer

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        if not user:
            return api_response(code=ErrorCode.NOT_FOUND, message='用户不存在')

        # 只返回公开信息
        data = {
            'id': user.id,
            'username': user.username,
            'avatar': user.avatar.url if user.avatar else None,
            'bio': user.bio,
            'date_joined': user.date_joined,
            'post_count': user.posts.count() if hasattr(user, 'posts') else 0
        }
        return api_response(data=data)
