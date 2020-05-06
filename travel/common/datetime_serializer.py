from rest_framework import serializers
import pytz


class DateTimeFieldWihTZ(serializers.DateTimeField):
    """
    序列化datetime列修改时区为shanghai
    """
    def to_representation(self, value):
        value = value.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Asia/Shanghai'))
        return super(DateTimeFieldWihTZ, self).to_representation(value)
