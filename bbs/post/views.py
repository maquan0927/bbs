from rest_framework.response import Response
from rest_framework import mixins, generics
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from common.decorator import user_passes_test
from common.permissions import IsAdmin, IsLogin
from django.utils.decorators import method_decorator
from post.serializers import PostSerializer
from post.models import Post
from django.http import Http404

class PostList(ListCreateAPIView):

    serializer_class = PostSerializer
    permission_classes = (IsLogin,)

    def get_queryset(self):
        try:
            queryset = Post.objects.all().order_by('-create_time')
            if self.request.query_params.get('module'):
                queryset = queryset.filter(module_id=self.request.query_params.get('module'))
            return queryset
        except:
            raise Http404
