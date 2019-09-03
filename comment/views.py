'''
评论功能是一个独立的模块，该功能通用性较高，在其他很多网站中都有评论功能,
为了避免以后开发其他网站时重复造轮子，我们建立一个新的应用，命名为comment
'''
from datetime import datetime

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import *
from django.template.loader import render_to_string
from ratelimit.decorators import ratelimit  # 该模块用户限时用户发送速率

from video.forms import CommentForm
from video.models import Video


@ratelimit(key='ip', rate='2/m')
def submit_comment(request,pk):
    """
    处理用户提交评论
    每分钟限制发2条
    """
    was_limited = getattr(request, 'limited', False)
    if was_limited:
        return JsonResponse({"code": 1, 'msg': '评论太频繁了，请1分钟后再试'})
        pass
    video = get_object_or_404(Video, pk = pk)
    form = CommentForm(data=request.POST)  # 需要一个form，我们把form放到video/forms.py


    if form.is_valid():  # 表单验证
        new_comment = form.save(commit=False)
        new_comment.user = request.user
        new_comment.nickname = request.user.nickname
        new_comment.avatar = request.user.avatar
        new_comment.video = video
        new_comment.save()

        data = dict()
        data['nickname'] = request.user.nickname
        data['avatar'] = request.user.avatar
        data['timestamp'] = datetime.fromtimestamp(datetime.now().timestamp())
        data['content'] = new_comment.content

        comments = list()
        comments.append(data)  # 将所有信息封装成列表套字典格式

        html = render_to_string(
            "comment/comment_single.html", {"comments": comments})

        return JsonResponse({"code":0,"html": html})
    return JsonResponse({"code":1,'msg':'评论失败!'})


def get_comments(request):
    '''
    获取评论数据
    :param request:
    :return:
    '''
    if not request.is_ajax():  # 判断是不是ajax请求
        return HttpResponseBadRequest()
    page = request.GET.get('page')
    page_size = request.GET.get('page_size')
    video_id = request.GET.get('video_id')
    # get_object_or_404方法第一个参数是模型Models或数据集queryset的名字,
    # 第二个参数是需要满足的条件（比如pk = id, title = 'python')。当需要获取的对象不存在时，给方法会自动返回Http 404错误。
    video = get_object_or_404(Video, pk=video_id)  # 根据video_id获取视频对象,如果获取不到自动返回404
    comments = video.comment_set.order_by('-timestamp').all()
    comment_count = len(comments)

    paginator = Paginator(comments, page_size)  # paginator对象来实现分页
    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = []

    if len(rows) > 0:
        code = 0
        html = render_to_string(
            "comment/comment_single.html", {"comments": rows})
    else:
        code = 1
        html = ""

    return JsonResponse({
        "code":code,
        "html": html,
        "comment_count": comment_count
    })
