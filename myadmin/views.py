import logging
import smtplib

import datetime
from chunked_upload.views import ChunkedUploadView, ChunkedUploadCompleteView
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.http import JsonResponse
from django.shortcuts import *
from django.template.loader import render_to_string
from django.views import generic
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from comment.models import Comment
from helpers import get_page_list, AdminUserRequiredMixin, ajax_required, SuperUserRequiredMixin, send_html_email
from users.models import User, Feedback
from video.models import Video, Classification
from .forms import UserLoginForm, VideoPublishForm, VideoEditForm, UserAddForm, UserEditForm, ClassificationAddForm, \
    ClassificationEditForm
from .models import MyChunkedUpload

logger = logging.getLogger('my_logger')

def login(request):
    '''
    后台管理登录模块
    :param request:
    :return:
    '''
    if request.method == 'POST':
        form = UserLoginForm(request=request, data=request.POST)
        if form.is_valid():  # 验证成功,获取用户名和密码
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            # user模型中的一个字段is_staff，用它来表示是否是管理员
            if user is not None and user.is_staff:  # 来判断管理员,如果是管理员，则auth_login登录并redirect跳转到主页。
                auth_login(request, user)  # 登录成功跳转到主页
                return redirect('myadmin:index')
            else:
                form.add_error('', '请输入管理员账号')
    else:
        form = UserLoginForm()
    return render(request, 'myadmin/login.html', {'form': form})


def logout(request):
    # 退出登录
    auth_logout(request)
    return redirect('myadmin:login')


class IndexView(AdminUserRequiredMixin, generic.View):
    """
    后台首页,总览数据
    """

    def get(self, request):
        video_count = Video.objects.get_count()  # 获取视频总数
        video_has_published_count = Video.objects.get_published_count()  # 获取发布数
        video_not_published_count = Video.objects.get_not_published_count()  # 获取未发布数
        user_count = User.objects.count()  # 获取用户总数
        # 通过exclude来过滤时间，使用了 lt 标签来过滤
        user_today_count = User.objects.exclude(date_joined__lt=datetime.date.today()).count()  # 获取当天用户数
        comment_count = Comment.objects.get_count()  # 获取评论内容总数
        comment_today_count = Comment.objects.get_today_count()  # 获取当天评论内容数
        data = {"video_count": video_count,
                "video_has_published_count": video_has_published_count,
                "video_not_published_count": video_not_published_count,
                "user_count": user_count,
                "user_today_count": user_today_count,
                "comment_count": comment_count,
                "comment_today_count": comment_today_count}
        return render(self.request, 'myadmin/index.html', data)  # 将数据整理成字典格式发给前端


class AddVideoView(SuperUserRequiredMixin, TemplateView):
    '''
    视频的上传采用的是分块上传的策略，并用了分块上传类库：django_chunked_upload
    上传的逻辑是这样的：前端先选择一个文件，通过jquery.fileupload.js中的$.fileupload()方法来上传文件，
    后端接收到后分批返回已上传块的进度，前端根据进度来更新界面。
    '''
    template_name = 'myadmin/video_add.html'


class MyChunkedUploadView(ChunkedUploadView):
    '''
    视频上传模块,上传成功后对调用'chunked_upload_complete/'路由执行MyChunkedUploadCompleteView类方法
    '''
    model = MyChunkedUpload
    field_name = 'the_file'


class MyChunkedUploadCompleteView(ChunkedUploadCompleteView):
    '''
    后端接收到后分批返回已上传块的进度，前端根据进度来更新界面,当全部接收完成后,前端调用chunked_upload_complete路由,
    通知后端,后端进行保存,并返回success
    上传完后,用户点击下一步，进入video_publish页面，开始发布前的资料填写
    '''
    model = MyChunkedUpload

    def on_completion(self, uploaded_file, request):
        print('uploaded--->', uploaded_file.name)
        pass

    def get_response_data(self, chunked_upload, request):
        video = Video.objects.create(file=chunked_upload.file)
        return {'code': 0, 'video_id': video.id, 'msg': 'success'}


class VideoPublishView(SuperUserRequiredMixin, generic.UpdateView):
    '''
    处理用户发布前视频资料编写功能（上传后,用户点击下一步,开始编写容视频标题、描述、分类、封面）
    '''
    model = Video
    form_class = VideoPublishForm
    template_name = 'myadmin/video_publish.html'

    def get_context_data(self, **kwargs):
        context = super(VideoPublishView, self).get_context_data(**kwargs)
        clf_list = Classification.objects.all().values()  # Classification视频分类表
        clf_data = {'clf_list':clf_list}
        context.update(clf_data)
        return context
    # 其中分类是通过get_context_data()带过来的，
    # 填写后，点击发布，django将通过UpdateView自动为你更新视频信息。并通过get_success_url跳转到成功页面
    def get_success_url(self):
        return reverse('myadmin:video_publish_success')  # video_publish_success发布成功路由


class VideoPublishSuccessView(generic.TemplateView):
    '''
    视频发布成功后跳转页面
    '''
    template_name = 'myadmin/video_publish_success.html'


class VideoEditView(SuperUserRequiredMixin, generic.UpdateView):
    '''
    处理视频管理编辑功能（编辑和添加视频详细信息功能差不多）
    '''
    model = Video
    form_class = VideoEditForm
    template_name = 'myadmin/video_edit.html'

    def get_context_data(self, **kwargs):
        context = super(VideoEditView, self).get_context_data(**kwargs)
        clf_list = Classification.objects.all().values()
        clf_data = {'clf_list':clf_list}
        context.update(clf_data)
        return context

    def get_success_url(self):
        messages.success(self.request, "保存成功")
        return reverse('myadmin:video_edit', kwargs={'pk': self.kwargs['pk']})


@ajax_required
@require_http_methods(["POST"])
def video_delete(request):
    '''
    处理删除视频功能
    :param request:
    :return:
    '''
    if not request.user.is_superuser:  # 必须要求是管理员
        return JsonResponse({"code": 1, "msg": "无删除权限"})
    video_id = request.POST['video_id']
    instance = Video.objects.get(id=video_id)
    instance.delete()
    return JsonResponse({"code": 0, "msg": "success"})


class VideoListView(AdminUserRequiredMixin, generic.ListView):
    '''
    处理视频列表功能
    '''
    model = Video
    template_name = 'myadmin/video_list.html'
    context_object_name = 'video_list'
    paginate_by = 10
    q = ''

    def get_context_data(self, *, object_list=None, **kwargs):
        '''
        重写get_context_data方法实现分页功能
        :param object_list:
        :param kwargs:
        :return:
        '''
        context = super(VideoListView, self).get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        page_list = get_page_list(paginator, page)
        context['page_list'] = page_list
        context['q'] = self.q
        return context

    def get_queryset(self):
        '''
        重写get_queryset方法实现搜索功能
        :return:
        '''
        self.q = self.request.GET.get("q", "")
        return Video.objects.get_search_list(self.q)  # get_search_list处理搜索结果


class ClassificationListView(AdminUserRequiredMixin, generic.ListView):
    '''
    分类管理列表
    '''
    model = Classification
    template_name = 'myadmin/classification_list.html'
    context_object_name = 'classification_list'
    paginate_by = 10
    q = ''

    def get_context_data(self, *, object_list=None, **kwargs):
        '''
        处理分页
        :param object_list:
        :param kwargs:
        :return:
        '''
        context = super(ClassificationListView, self).get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        page_list = get_page_list(paginator, page)
        context['page_list'] = page_list
        context['q'] = self.q
        return context

    def get_queryset(self):
        '''
        处理搜索功能
        :return:
        '''
        self.q = self.request.GET.get("q", "")
        return Classification.objects.filter(title__contains=self.q)


class ClassificationAddView(SuperUserRequiredMixin, generic.View):
    '''
    视频分类增加管理
    '''
    def get(self, request):
        '''
        负责展示界面
        :param request:
        :return:
        '''
        form = ClassificationAddForm()
        return render(self.request, 'myadmin/classification_add.html', {'form': form})

    def post(self, request):
        '''
        负责逻辑判断
        :param request:
        :return:
        '''
        form = ClassificationAddForm(data=request.POST)
        if form.is_valid():
            form.save(commit=True)
            return render(self.request, 'myadmin/classification_add_success.html')
        return render(self.request, 'myadmin/classification_add.html', {'form': form})


@ajax_required  # 装饰器
@require_http_methods(["POST"])
def classification_delete(request):
    '''
    处理分类管理删除
    :param request:
    :return:
    '''
    if not request.user.is_superuser:
        return JsonResponse({"code": 1, "msg": "无删除权限"})
    classification_id = request.POST['classification_id']
    instance = Classification.objects.get(id=classification_id)
    instance.delete()
    return JsonResponse({"code": 0, "msg": "success"})


class ClassificationEditView(SuperUserRequiredMixin, generic.UpdateView):
    '''
    处理视频分类管理修改
    '''
    model = Classification
    form_class = ClassificationEditForm
    template_name = 'myadmin/classification_edit.html'

    def get_success_url(self):
        messages.success(self.request, "保存成功")
        return reverse('myadmin:classification_edit', kwargs={'pk': self.kwargs['pk']})


class CommentListView(AdminUserRequiredMixin, generic.ListView):
    '''
    处理评论模块功能
    '''
    model = Comment
    template_name = 'myadmin/comment_list.html'
    context_object_name = 'comment_list'
    paginate_by = 10
    q = ''

    def get_context_data(self, *, object_list=None, **kwargs):
        '''
        实现分页功能
        :param object_list:
        :param kwargs:
        :return:
        '''
        context = super(CommentListView, self).get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        page_list = get_page_list(paginator, page)
        context['page_list'] = page_list
        context['q'] = self.q
        return context

    def get_queryset(self):
        '''
        实现搜索功能
        :return:
        '''
        self.q = self.request.GET.get("q", "")
        # 评论内容根据时间排序
        return Comment.objects.filter(content__contains=self.q).order_by('-timestamp')

@ajax_required  # 必须是ajax请求
@require_http_methods(["POST"])
def comment_delete(request):
    '''
    处理删除评论
    通过ajax将video_id传给删除接口，ajax的代码位于static/js/myadmin/comment_list.js，
    删除评论的接口是api_comment_delete
    :param request:
    :return:
    '''
    if not request.user.is_superuser:
        return JsonResponse({"code": 1, "msg": "无删除权限"})
    comment_id = request.POST['comment_id']
    instance = Comment.objects.get(id=comment_id)
    instance.delete()
    return JsonResponse({"code": 0, "msg": "success"})


class UserListView(AdminUserRequiredMixin, generic.ListView):
    '''
    处理用户管理列表模块
    '''
    model = User
    template_name = 'myadmin/user_list.html'
    context_object_name = 'user_list'
    paginate_by = 10
    q = ''

    def get_context_data(self, *, object_list=None, **kwargs):
        '''
        处理分页
        :param object_list:
        :param kwargs:
        :return:
        '''
        context = super(UserListView, self).get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        page_list = get_page_list(paginator, page)
        context['page_list'] = page_list
        context['q'] = self.q
        return context

    def get_queryset(self):
        '''
        处理搜索
        :return:
        '''
        self.q = self.request.GET.get("q", "")
        return User.objects.filter(username__contains=self.q).order_by('-date_joined')


class UserAddView(SuperUserRequiredMixin, generic.View):
    '''
    处理用户管理的添加用户
    '''
    def get(self, request):
        form = UserAddForm()
        return render(self.request, 'myadmin/user_add.html', {'form': form})

    def post(self, request):
        form = UserAddForm(data=request.POST)
        if form.is_valid():
            '''
            模型里null=False字段添加一些非表单的数据，该方法会非常有用。如果你指定commit=False，
            那么save方法不会理解将表单数据存储到数据库，而是给你返回一个当前对象。这时你可以添加表单以外的额外数据，再一起存储'''
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')  # 获取前端输入的密码
            user.set_password(password)  # 设置密码
            user.save()  # 保存
            return render(self.request, 'myadmin/user_add_success.html')
        return render(self.request, 'myadmin/user_add.html', {'form': form})


class UserEditView(SuperUserRequiredMixin, generic.UpdateView):
    '''
    用户管理修改用户功能
    '''
    model = User
    form_class = UserEditForm
    template_name = 'myadmin/user_edit.html'

    def get_success_url(self):
        messages.success(self.request, "保存成功")
        return reverse('myadmin:user_edit', kwargs={'pk': self.kwargs['pk']})


@ajax_required
@require_http_methods(["POST"])
def user_delete(request):
    '''
    处理后台管理用户删除功能模块
    :param request:
    :return:
    '''
    if not request.user.is_superuser:
        return JsonResponse({"code": 1, "msg": "无删除权限"})
    user_id = request.POST['user_id']
    instance = User.objects.get(id=user_id)
    if instance.is_superuser:
        return JsonResponse({"code": 1, "msg": "不能删除管理员"})
    instance.delete()
    return JsonResponse({"code": 0, "msg": "success"})


class SubscribeView(SuperUserRequiredMixin, generic.View):
    '''
    处理订阅功能邮件发送
    SuperUserRequiredMixin超级用户拦截器
    '''
    def get(self, request):
        '''
        发送订阅通知页面
        :param request:
        :return:
        '''
        video_list = Video.objects.get_published_list()  # 获取视频对象列表
        return render(request, "myadmin/subscribe.html" ,{'video_list':video_list})

    def post(self, request):
        '''
        点击通知订阅用户，即可触发ajax发送代码,调用post请求
        :param request:
        :return:
        '''
        if not request.user.is_superuser:
            return JsonResponse({"code": 1, "msg": "无权限"})
        video_id = request.POST['video_id']  # 从前端获取视频id
        video = Video.objects.get(id=video_id)  # 数据库中获取视频对象
        subject = video.title  # 发送视频的标题
        context = {'video': video,'site_url':settings.SITE_URL}  # 包含video对象和设置里面设置好的网址
        html_message = render_to_string('myadmin/mail_template.html', context)  # 跳转到mail_template.html页面,并且把发送邮件的内容传递过去
        email_list = User.objects.filter(subscribe=True).values_list('email',flat=True)  # 订阅视频用户的email列表,加个参数flat=True可以获取email的值列表
        # 分组
        email_list = [email_list[i:i + 2] for i in range(0, len(email_list), 2)]  # 列表套列表
        print(email_list)
        if email_list:
            for to_list in email_list:
                print('to_list',to_list)
                try:
                    send_html_email(subject, html_message, to_list)  # 调用send_html_email发送邮件
                except smtplib.SMTPException as e:
                    logger.error(e)  # 错误信息写入日志
                    return JsonResponse({"code": 1, "msg": "发送失败"})
            return JsonResponse({"code": 0, "msg": "success"})
        else:
            return JsonResponse({"code": 1, "msg": "邮件列表为空"})


class FeedbackListView(AdminUserRequiredMixin, generic.ListView):
    '''
    处理用户反馈功能模块
    AdminUserRequiredMixin管理员拦截器
    '''
    model = Feedback
    template_name = 'myadmin/feedback_list.html'
    context_object_name = 'feedback_list'
    paginate_by = 10
    q = ''

    def get_context_data(self, *, object_list=None, **kwargs):
        '''
        传递了分页数据
        :param object_list:
        :param kwargs:
        :return:
        '''
        context = super(FeedbackListView, self).get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        page_list = get_page_list(paginator, page)  # 分页器
        context['page_list'] = page_list
        context['q'] = self.q
        return context

    def get_queryset(self):
        '''
        传递了搜索数据
        :return:
        '''
        self.q = self.request.GET.get("q", "")
        return Feedback.objects.filter(content__contains=self.q).order_by('-timestamp')


@ajax_required  # 必须是ajax请求装饰器
@require_http_methods(["POST"])  # 必须是post请求
def feedback_delete(request):
    if not request.user.is_superuser:
        return JsonResponse({"code": 1, "msg": "无删除权限"})
    feedback_id = request.POST['feedback_id']  # 获取前端反馈信息id
    instance = Feedback.objects.get(id=feedback_id)  # 数据库中获取对应的反馈信息
    instance.delete()  # 删除反馈
    return JsonResponse({"code": 0, "msg": "success"})

