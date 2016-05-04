from __future__ import unicode_literals
from django.db import models


class Document(models.Model):
    path = models.CharField(max_length=4000, unique=True, db_index=True)
    disk_size = models.BigIntegerField()
    push = models.BooleanField(default=False)

class FolderMark(models.Model):
    path = models.CharField(max_length=4000, unique=True, db_index=True)
