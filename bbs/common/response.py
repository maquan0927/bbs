from rest_framework.response import Response
from rest_framework import status


class ErrorCode:
    """错误码定义"""
    SUCCESS = 0
    PARAM_ERROR = 1001
    NOT_FOUND = 1002
    PERMISSION_DENIED = 1003
    USERNAME_EXISTS = 2001
    EMAIL_EXISTS = 2002
    CODE_ERROR = 2003
    EMAIL_SEND_FAILED = 2004
    TOO_FREQUENT = 2005
    POST_NOT_FOUND = 3001
    ALREADY_LIKED = 3002
    NOT_LIKED = 3003
    ALREADY_FAVORITED = 3004
    NOT_FAVORITED = 3005
    SELF_ACTION_NOT_ALLOWED = 4001


ERROR_MESSAGES = {
    ErrorCode.SUCCESS: '成功',
    ErrorCode.PARAM_ERROR: '参数错误',
    ErrorCode.NOT_FOUND: '资源不存在',
    ErrorCode.PERMISSION_DENIED: '权限不足',
    ErrorCode.USERNAME_EXISTS: '用户名已存在',
    ErrorCode.EMAIL_EXISTS: '邮箱已被注册',
    ErrorCode.CODE_ERROR: '验证码错误',
    ErrorCode.EMAIL_SEND_FAILED: '邮件发送失败',
    ErrorCode.TOO_FREQUENT: '请求过于频繁',
    ErrorCode.POST_NOT_FOUND: '帖子不存在',
    ErrorCode.ALREADY_LIKED: '已经点过赞了',
    ErrorCode.NOT_LIKED: '还没有点赞',
    ErrorCode.ALREADY_FAVORITED: '已经收藏过了',
    ErrorCode.NOT_FAVORITED: '还没有收藏',
    ErrorCode.SELF_ACTION_NOT_ALLOWED: '不能对自己进行此操作',
}


def api_response(code=ErrorCode.SUCCESS, message=None, data=None, http_status=status.HTTP_200_OK):
    """
    统一的API响应格式
    :param code: 业务错误码
    :param message: 错误信息
    :param data: 返回数据
    :param http_status: HTTP状态码
    :return: Response对象
    """
    if message is None:
        message = ERROR_MESSAGES.get(code, '未知错误')

    response_data = {
        'code': code,
        'message': message,
        'data': data
    }

    return Response(response_data, status=http_status)
