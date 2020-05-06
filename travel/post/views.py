from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from common.permissions import IsLogin
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

class PostDetail(RetrieveUpdateDestroyAPIView):

    serializer_class = PostSerializer
    permission_classes = (IsLogin, )

    def get_object(self):
        try:
            return Post.objects.get(id=self.kwargs['id'])
        except:
            raise Http404
