from functools import wraps
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponse, HttpResponseForbidden

def user_passes_test(test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    注解用于重写django自带的user_passes_test，当test_func返回为false后，返回状态码从302修改为403拒绝访问
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            if request.user.is_authenticated:
                return HttpResponseForbidden()
            return HttpResponse(status=401)
        return _wrapped_view
    return decorator