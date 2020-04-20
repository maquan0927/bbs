from rest_framework import serializers
from module.models import Module

class ModuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Module
        fields = '__all__'
