"""
Django test settings for running tests with SQLite
"""
from bbs.settings import *

# 使用 SQLite 内存数据库进行测试
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# 禁用 Redis 以简化测试
REDIS_URL = None

# 简化密码哈希以加速测试
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# 禁用日志输出到文件
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
