from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import generic
from django.views.decorators.http import require_http_methods

from helpers import get_page_list, ajax_required
from .forms import CommentForm
from .models import Video, Classification


class IndexView(generic.ListView):  # ListView：显示对象列表
    '''
    展示对象列表（比如所有用户，所有文章）- ListView
    处理视频列表
    '''
    model = Video  # 作用于Video模型
    template_name = 'video/index.html'  # 告诉ListView要使用我们已经创建的模版文件
    context_object_name = 'video_list'  # 上下文变量名，告诉ListView，在前端模版文件中，可以使用该变量名来展现数据。
    paginate_by = 12  # 每页显示12条
    c = None

    #  主要功能就是传递额外的数据给模板
    def get_context_data(self, *, object_list=None, **kwargs):  # 重载get_context_data方法
        '''
        现在的分类id,视频分类并不属于Video模型.如果你想把分类id和视频分类传递给模板，你还可以通过重写get_context_data方法
        :param object_list:
        :param kwargs:
        :return:
        '''
        context = super(IndexView, self).get_context_data(**kwargs)
        paginator = context.get('paginator')  # context.get(‘paginator’)返回的是分页对象,分页器
        page = context.get('page_obj')  # context.get(‘page_obj’)返回的是当前页码
        page_list = get_page_list(paginator, page)  # 处理分页
        #  将分类数据通过Classification.objects.filter(status=True).values()从数据库里面过滤出来，
        classification_list = Classification.objects.filter(status=True).values()  # 获取分类列表
        context['c'] = self.c  # 为分类的id
        # 然后赋给classification_list,最后放到context字典里面.
        context['classification_list'] = classification_list
        context['page_list'] = page_list
        return context
    # 分页功能比较常用，所以需要把它单独拿出来封装到一个单独的文件中，我们新建templates/base/page_nav.html文件
    # 因为搜索框是很多页面都需要的，所以我们把代码写到templates/base/header.html文件里面。

    # get获取数据
    def get_queryset(self):
        '''
        该方法可以返回一个量身定制的对象列表。当我们使用Django自带的ListView展示所有对象列表时，
        ListView默认会返回Model.objects.all(),上面指定了
        model = Video
        :return:
        '''
        self.c = self.request.GET.get("c", None)
        if self.c:  # 如果有值,通过get_object_or_404(Classification, pk=self.c)先获取当前类，然后classification.video_set获取外键数据
            classification = get_object_or_404(Classification, pk=self.c)
            return classification.video_set.all().order_by('-create_time')
        else:  # 如果为None就响应全部
            return Video.objects.filter(status=0).order_by('-create_time')


class SearchListView(generic.ListView):
    '''
    处理搜索页面
    '''
    model = Video
    template_name = 'video/search.html'
    context_object_name = 'video_list'
    paginate_by = 8  # 每页显示8条
    q = ''

    def get_queryset(self):
        self.q = self.request.GET.get("q", "")
        # 利用filter将数据过滤出来。
        # 这里写了两层过滤，第一层过滤搜索关键词，
        # 第二层过滤status已发布的视频
        return Video.objects.filter(title__contains=self.q).filter(status=0)  # title__contains是包含的意思，表示查询title包含q的记录

    #  将获取到的classification_list追加到context字典中
    #  存放额外的数据，包括分页数据、q关键词
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(SearchListView, self).get_context_data(**kwargs)
        paginator = context.get('paginator')  # 返回的是分页对象
        page = context.get('page_obj')  # 返回当前页码
        page_list = get_page_list(paginator, page)
        context['page_list'] = page_list
        context['q'] = self.q  # 搜索的关键字
        return context


class VideoDetailView(generic.DetailView):
    '''
    展示某个对象的详细信息（比如用户资料，比如文章详情) - DetailView
    处理视频详情页
    '''
    model = Video
    template_name = 'video/detail.html'

    def get_object(self, queryset=None):
        '''
        可以通过更具体的get_object()方法来返回一个更具体的对象
        :param queryset:
        :return:
        '''
        obj = super().get_object()
        # 每次调用DetailView的时候，django都会回调get_object()这个函数。因此我们可以把increase_view_count()放到get_object()里面执行
        obj.increase_view_count()  # 添加一个次数自增函数
        return obj

    def get_context_data(self, **kwargs):
        '''
        重写get_context_data方法,实现视频推荐
        推荐逻辑：根据访问次数最高的n个视频来降序排序，然后推荐给用户的
        :param kwargs:
        :return:
        '''
        context = super(VideoDetailView, self).get_context_data(**kwargs)
        form = CommentForm()
        recommend_list = Video.objects.get_recommend_list()  # 通过order_by把view_count降序排序，并选取前4条数据
        context['form'] = form
        context['recommend_list'] = recommend_list
        return context
    # 当模板拿到数据后，即可渲染显示。这里我们将推荐侧栏的代码封装到templates/video/recommend.html里面. 后期改成基于物品的协同过滤算法推荐

@ajax_required  # 验证request必须是ajax请求
@require_http_methods(["POST"])  # 验证request必须是post请求
def like(request):
    #  喜欢功能
    if not request.user.is_authenticated:  # 判断用户是否已登录
        return JsonResponse({"code": 1, "msg": "请先登录"})
    video_id = request.POST['video_id']
    video = Video.objects.get(pk=video_id)
    user = request.user  # 获取已登录的用户
    video.switch_like(user)  # 调用switch_like(user)来实现喜欢或不喜欢功能
    return JsonResponse({"code": 0, "likes": video.count_likers(), "user_liked": video.user_liked(user)})


@ajax_required
@require_http_methods(["POST"])
def collect(request):
    '''
    实现收藏功能
    :param request:
    :return:
    '''
    if not request.user.is_authenticated:  # 判断用户是否已登录
        return JsonResponse({"code": 1, "msg": "请先登录"})
    video_id = request.POST['video_id']  # 前端获取视频id
    video = Video.objects.get(pk=video_id)  # 根据id从数据库获取对应的视频对象
    user = request.user  # 获取已登录的用户
    video.switch_collect(user)
    # video.count_collecters()返回收藏的人数,video.user_collected(user)返回当前登录用户是否收藏0代表收藏,1代表未收藏
    return JsonResponse({"code": 0, "collects": video.count_collecters(), "user_collected": video.user_collected(user)})



