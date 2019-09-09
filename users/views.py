from helpers import AuthorRequiredMixin, get_page_list
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import *
from django.views import generic
from ratelimit.decorators import ratelimit

from .models import Feedback

from .forms import ProfileForm, SignUpForm, UserLoginForm, ChangePwdForm, SubscribeForm, FeedbackForm

User = get_user_model()

def login(request):
    '''
    处理用户登录
    :param request:
    :return:
    '''
    if request.method == 'POST':
        next = request.POST.get('next', '/')
        form = UserLoginForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)  # 相当于用户登录信息验证
            if user is not None:
                auth_login(request, user)  # 登录
                # return redirect('home')
                return redirect(next)  # 跳转到指定的页面
        else:
            print(form.errors)
    else:
        next = request.GET.get('next', '/')  # next对应的是登录后要跳转的url
        form = UserLoginForm()
    print(next)
    return render(request, 'registration/login.html', {'form': form, 'next':next})

def signup(request):
    '''
    处理用户注册
    :param request:
    :return:
    '''
    if request.method == 'POST':
        form = SignUpForm(request.POST)  # 初始化一个表单
        if form.is_valid():  # 表示验证成功
            form.save()
            username = form.cleaned_data.get('username')  # 读取表单返回的值，返回类型为字典dict型
            raw_password1 = form.cleaned_data.get('password1')
            #  使用 authenticate() 函数.它接受两个参数，用户名 username 和 密码 password ,
            # 并在密码对给出的用户名合法的情况下返回一个 User 对象.如果密码不合法,authenticate()返回None
            user = authenticate(username=username, password=raw_password1)
            # login接受两个参数，第一个是request对象，第二个是user对象。login方法使用SessionMiddleware将userID存入session当中.
            # 注意，在用户还未登录的时候，也存在着匿名用户的Session，在其登陆之后，之前在匿名Session中保留的信息，都会保留下来.
            # 这两个方法要结合使用，而且必须要先调用authenticate()，因为该方法会User的一个属性上纪录该用户已经通过校验了,
            # 这个属性会被随后的login过程所使用
            auth_login(request, user)  # login(request,user)
            return redirect('home')  # 跳转到首页
        else:
            print(form.errors)
    else:  # get请求返回注册页
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


def logout(request):
    # 这个方法，会将存储在用户session的数据全部清空，这样避免有人用当前用户的浏览器登陆然后就可以查看当前用户的数据了，
    # 回想一下login会保留anonymous用户的session数据。
    # 如果需要将一些东西加入到登出之后的用户session，那么需要在logout方法调用之后再进行。
    auth_logout(request)
    return redirect('home')


def change_password(request):
    '''
    处理修改密码
    通过验证form合法性，然后调用user.save()来保存修改。
    然后通过update_session_auth_hash来更新session。
    :param request:
    :return:
    '''
    if request.method == 'POST':
        form = ChangePwdForm(request.user, request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if not user.is_staff and not user.is_superuser:
                user.save()
                update_session_auth_hash(request, user)  # 更新session 非常重要！
                messages.success(request, '修改成功')
                return redirect('users:change_password')
            else:
                messages.warning(request, '无权修改管理员密码')
                return redirect('users:change_password')
        else:
            print(form.errors)
    else:
        form = ChangePwdForm(request.user)
    return render(request, 'registration/change_password.html', {
        'form': form
    })


class ProfileView(LoginRequiredMixin,AuthorRequiredMixin, generic.UpdateView):
    """
    处理修改个人信息模块
    继承了LoginRequiredMixin和AuthorRequiredMixin两个类，这两个类属于公共类，
    其中LoginRequiredMixin的用途是：只允许登录的用户访问该视图类，
    AuthorRequiredMixin的用途是：只允许用户自己查看自己的个人资料，别人是无法查看的
    """
    model = User
    form_class = ProfileForm
    template_name = 'users/profile.html'

    def get_success_url(self):
        '''
        当更新成功后，django会回调get_success_url来将结果告诉模板
        :return:
        '''
        messages.success(self.request, "保存成功")
        return reverse('users:profile', kwargs={'pk': self.request.user.pk})


class SubscribeView(LoginRequiredMixin,AuthorRequiredMixin, generic.UpdateView):
    '''
    处理订阅功能
    订阅的功能和修改个人资料功能类似，也是属于更新操作，所以同样是使用UpdateView来更新
    '''
    model = User
    form_class = SubscribeForm
    template_name = 'users/subscribe.html'

    def get_success_url(self):
        messages.success(self.request, "保存成功")
        return reverse('users:subscribe', kwargs={'pk': self.request.user.pk})

class FeedbackView(LoginRequiredMixin, generic.CreateView):
    '''
    处理用户反馈模块
    限流量的技术：ratelimit。这是一个第三方类库，通过使用他，
    可以防止恶意提交数据。它使用超级简单，只需要配置好key和rate即可，
    key代表业务，rate代表速率，这里我们设置key为ip，即限制ip地址，
    rate为’2/m’，表示每分钟限制请求2次。超过2次就提示用户操作频繁。
    '''
    model = Feedback
    form_class = FeedbackForm
    template_name = 'users/feedback.html'

    @ratelimit(key='ip', rate='2/m')  # ip请求频率设置,每分钟只能请求两次
    def post(self, request, *args, **kwargs):
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            messages.warning(self.request, "操作太频繁了，请1分钟后再试")
            return render(request, 'users/feedback.html', {'form': FeedbackForm()})
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "提交成功")
        return reverse('users:feedback')

class CollectListView(generic.ListView):
    '''
    处理收藏功能模块
    '''
    model = User
    # template_name = 'users/collect_videos.html'和context_object_name = 'video_list'
    # 表示这个实例要作为名为video_list的参数传入users/collect_videos.html中。
    template_name = 'users/collect_videos.html'
    context_object_name = 'video_list'
    # video_list对象会作为参数传入users/collect_videos.html，
    # 之后你就可以在users/collect_videos.html中通过类似{{ video_list.title }}或{{ video_list.author }}的标签来生成特定的页面了。
    paginate_by = 10

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(CollectListView, self).get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        page_list = get_page_list(paginator, page)  # 获取分页器对象列表
        context['page_list'] = page_list
        return context
    def get_queryset(self):
        user = get_object_or_404(User, pk=self.kwargs.get('pk'))
        videos = user.collected_videos.all()  # collected_videos就是models收藏字段中定义的别名
        return videos


class LikeListView(generic.ListView):
    '''
    处理喜欢功能模块,和处理收藏功能模块差不多
    '''
    model = User
    template_name = 'users/like_videos.html'
    context_object_name = 'video_list'
    paginate_by = 10

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(LikeListView, self).get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        page_list = get_page_list(paginator, page)
        context['page_list'] = page_list
        return context

    def get_queryset(self):
        user = get_object_or_404(User, pk=self.kwargs.get('pk'))
        videos = user.liked_videos.all()
        return videos