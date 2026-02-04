"""
Django test settings - 使用 SQLite 进行单元测试
"""

from bbs.settings import *

# 使用 SQLite 内存数据库进行测试
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# 禁用日志文件输出
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'bbs': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}

# 简化密码验证器
AUTH_PASSWORD_VALIDATORS = []

# 禁用自定义异常处理器，避免循环导入
REST_FRAMEWORK['EXCEPTION_HANDLER'] = 'rest_framework.views.exception_handler'

# 设置 AUTO FIELD
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
