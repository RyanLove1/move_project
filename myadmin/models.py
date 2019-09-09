from chunked_upload.models import ChunkedUpload
from django.db import models

# Create your models here.
class MyChunkedUpload(ChunkedUpload):
    pass
# Override the default ChunkedUpload to make the `user` field nullable
# 重写默认的ChunkedUpload以使“user”字段为空
MyChunkedUpload._meta.get_field('user').null = True

