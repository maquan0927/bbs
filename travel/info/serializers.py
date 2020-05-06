from rest_framework import serializers
from info.models import *

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
