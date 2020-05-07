from rest_framework import serializers
from info.models import *
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_staff = True
        user.save()
        return user

    class Meta:
        model = User
        fields = ('id', 'username', 'password')
        extra_kwargs = {'password': {'write_only': True}}


class IndexImgSerializer(serializers.ModelSerializer):

    class Meta:
        model = IndexImg
        fields = '__all__'


class RecommendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommend
        fields = '__all__'

class TourguideSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tourguide
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
