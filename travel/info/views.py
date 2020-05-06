from rest_framework.generics import ListAPIView, CreateAPIView
from info.serializers import IndexImgSerializer, RecommendSerializer, TourguideSerializer, MessageSerializer
from info.models import IndexImg, Recommend, Tourguide, Message
from rest_framework.permissions import IsAuthenticated

class IndexImgList(ListAPIView):

    serializer_class = IndexImgSerializer
    queryset = IndexImg.objects.all().order_by('id')
    pagination_class = None

class RecomendList(ListAPIView):

    serializer_class = RecommendSerializer
    queryset = Recommend.objects.all().order_by('id')
    pagination_class = None

class TourguideList(ListAPIView):

    serializer_class = TourguideSerializer
    queryset = Tourguide.objects.all().order_by('id')
    pagination_class = None

class MessageList(CreateAPIView):

    serializer_class = MessageSerializer
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return self.create(request, *args, **kwargs)
