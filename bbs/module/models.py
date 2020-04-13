from django.db import models
from user.models import User

class Module(models.Model):
    name = models.CharField('板块', max_length=32)
    admin = models.ManyToManyField(User, db_constraint=False, related_name="modulesadmin")