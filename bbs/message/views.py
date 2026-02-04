from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from common.permissions import IsLogin
from common.response import api_response, ErrorCode
from message.models import Message
from message.serializers import MessageSerializer


class MessageList(ListAPIView):
    """消息列表"""

    serializer_class = MessageSerializer
    permission_classes = (IsLogin,)

    def get_queryset(self):
        queryset = Message.objects.filter(user=self.request.user)

        # 按消息类型筛选
        message_type = self.request.query_params.get('type')
        if message_type is not None:
            queryset = queryset.filter(type=message_type)

        # 按已读状态筛选
        read = self.request.query_params.get('read')
        if read is not None:
            queryset = queryset.filter(read=read)

        return queryset


class MessageDetail(APIView):
    """消息详情"""

    permission_classes = (IsLogin,)

    def get(self, request, message_id):
        """获取消息详情并标记为已读"""
        try:
            message = Message.objects.get(id=message_id, user=request.user)
        except Message.DoesNotExist:
            return api_response(code=ErrorCode.NOT_FOUND, message='消息不存在')

        # 标记为已读
        if message.read == 0:
            message.read = 1
            message.save()

        serializer = MessageSerializer(message)
        return api_response(data=serializer.data)

    def delete(self, request, message_id):
        """删除消息"""
        try:
            message = Message.objects.get(id=message_id, user=request.user)
        except Message.DoesNotExist:
            return api_response(code=ErrorCode.NOT_FOUND, message='消息不存在')

        message.delete()
        return api_response(message='删除成功')


class MessageReadAll(APIView):
    """标记所有消息为已读"""

    permission_classes = (IsLogin,)

    def post(self, request):
        Message.objects.filter(user=request.user, read=0).update(read=1)
        return api_response(message='全部标记为已读')


class MessageUnreadCount(APIView):
    """获取未读消息数量"""

    permission_classes = (IsLogin,)

    def get(self, request):
        count = Message.objects.filter(user=request.user, read=0).count()
        return api_response(data={'unread_count': count})
