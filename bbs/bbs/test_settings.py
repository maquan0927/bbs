"""
测试专用配置文件，使用SQLite作为数据库
"""
from bbs.settings import *

# 使用SQLite进行测试
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

# 禁用password验证器以加快测试
AUTH_PASSWORD_VALIDATORS = []

# 使用简单的日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'bbs': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}
