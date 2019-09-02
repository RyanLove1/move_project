from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import generic
from django.views.decorators.http import require_http_methods

from helpers import get_page_list, ajax_required
from .forms import CommentForm
from .models import Video, Classification


class IndexView(generic.ListView):
    model = Video  # 作用于Video模型
    template_name = 'video/index.html'  # 告诉ListView要使用我们已经创建的模版文件
    context_object_name = 'video_list'  # 上下文变量名，告诉ListView，在前端模版文件中，可以使用该变量名来展现数据。
    paginate_by = 12  # 每页显示12条
    c = None
    #  将分类数据通过Classification.objects.filter(status=True).values()从数据库里面过滤出来，然后赋给classification_list，最后放到context字典里面。
    #  主要功能就是传递额外的数据给模板
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        page_list = get_page_list(paginator, page)
        classification_list = Classification.objects.filter(status=True).values()
        context['c'] = self.c
        context['classification_list'] = classification_list
        context['page_list'] = page_list
        return context

    # get获取数据
    def get_queryset(self):
        self.c = self.request.GET.get("c", None)
        if self.c:  # 如果有值,通过get_object_or_404(Classification, pk=self.c)先获取当前类，然后classification.video_set获取外键数据
            classification = get_object_or_404(Classification, pk=self.c)
            return classification.video_set.all().order_by('-create_time')
        else:  # 如果为None就响应全部
            return Video.objects.filter(status=0).order_by('-create_time')


class SearchListView(generic.ListView):
    model = Video
    template_name = 'video/search.html'
    context_object_name = 'video_list'
    paginate_by = 8
    q = ''

    def get_queryset(self):
        self.q = self.request.GET.get("q", "")
        #  title__contains是包含的意思，表示查询title包含q的记录。
        # 利用filter将数据过滤出来。这里写了两层过滤，第一层过滤搜索关键词，
        # 第二层过滤status已发布的视频
        return Video.objects.filter(title__contains=self.q).filter(status=0)

    #  将获取到的classification_list追加到context字典中
    #  存放额外的数据，包括分页数据、q关键词
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(SearchListView, self).get_context_data(**kwargs)
        paginator = context.get('paginator')  # 返回的是分页对象
        page = context.get('page_obj')  # 返回当前页码
        page_list = get_page_list(paginator, page)
        context['page_list'] = page_list
        context['q'] = self.q
        return context


class VideoDetailView(generic.DetailView):
    model = Video
    template_name = 'video/detail.html'

    def get_object(self, queryset=None):
        obj = super().get_object()
        obj.increase_view_count()
        return obj

    def get_context_data(self, **kwargs):
        context = super(VideoDetailView, self).get_context_data(**kwargs)
        form = CommentForm()
        recommend_list = Video.objects.get_recommend_list()
        context['form'] = form
        context['recommend_list'] = recommend_list
        return context

@ajax_required
@require_http_methods(["POST"])
def like(request):
    #  喜欢功能
    if not request.user.is_authenticated:
        return JsonResponse({"code": 1, "msg": "请先登录"})
    video_id = request.POST['video_id']
    video = Video.objects.get(pk=video_id)
    user = request.user
    video.switch_like(user)
    return JsonResponse({"code": 0, "likes": video.count_likers(), "user_liked": video.user_liked(user)})


@ajax_required
@require_http_methods(["POST"])
def collect(request):
    if not request.user.is_authenticated:
        return JsonResponse({"code": 1, "msg": "请先登录"})
    video_id = request.POST['video_id']
    video = Video.objects.get(pk=video_id)
    user = request.user
    video.switch_collect(user)
    return JsonResponse({"code": 0, "collects": video.count_collecters(), "user_collected": video.user_collected(user)})



