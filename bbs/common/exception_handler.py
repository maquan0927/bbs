from rest_framework.views import exception_handler
from rest_framework import status
from common.response import api_response, ErrorCode
import logging

logger = logging.getLogger('bbs')


def custom_exception_handler(exc, context):
    """
    自定义异常处理器
    """
    response = exception_handler(exc, context)

    if response is not None:
        # 记录异常日志
        logger.warning(f'API Exception: {exc}, View: {context.get("view")}')

        # 统一返回格式
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            return api_response(
                code=ErrorCode.PERMISSION_DENIED,
                message='认证失败，请先登录',
                http_status=response.status_code
            )
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            return api_response(
                code=ErrorCode.PERMISSION_DENIED,
                message='权限不足',
                http_status=response.status_code
            )
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            return api_response(
                code=ErrorCode.NOT_FOUND,
                message='资源不存在',
                http_status=response.status_code
            )
        elif response.status_code == status.HTTP_400_BAD_REQUEST:
            return api_response(
                code=ErrorCode.PARAM_ERROR,
                message='请求参数错误',
                data=response.data,
                http_status=response.status_code
            )

    return response
