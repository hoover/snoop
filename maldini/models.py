from __future__ import unicode_literals
from django.db import models
from django.contrib.postgres.fields import JSONField

class Document(models.Model):
    path = models.CharField(max_length=4000, unique=True, db_index=True)
    disk_size = models.BigIntegerField()
    push = models.BooleanField(default=False)
    status = JSONField(default=dict)

class Failure(models.Model):
    document = models.OneToOneField(Document, db_index=True,
        on_delete=models.CASCADE)

class Generation(models.Model):
    document = models.OneToOneField(Document, db_index=True,
        on_delete=models.CASCADE)
    n = models.IntegerField()

class Cache(models.Model):
    document = models.OneToOneField(Document, db_index=True,
        on_delete=models.CASCADE)
    data = models.TextField()

class Digest(models.Model):
    id = models.IntegerField(primary_key=True)
    data = models.TextField()

class FolderMark(models.Model):
    path = models.CharField(max_length=4000, unique=True, db_index=True)
