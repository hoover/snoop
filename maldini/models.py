from django.db import models
from django.contrib.postgres.fields import JSONField

class Document(models.Model):
    container = models.ForeignKey('Document', null=True)
    path = models.CharField(max_length=4000)
    content_type = models.CharField(max_length=100, blank=True)
    disk_size = models.BigIntegerField()

    md5 = models.CharField(max_length=40, null=True, db_index=True)
    sha1 = models.CharField(max_length=50, null=True, db_index=True)

    class Meta:
        # TODO: constraint does not apply to container=None rows
        unique_together = ('container', 'path')

class Digest(models.Model):
    id = models.IntegerField(primary_key=True)
    data = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

class FolderMark(models.Model):
    path = models.CharField(max_length=4000, unique=True, db_index=True)

class Error(models.Model):
    document_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

class Job(models.Model):
    queue = models.CharField(max_length=100)
    data = JSONField(null=True)
    started = models.BooleanField(default=False)

    class Meta:
        unique_together = ('queue', 'data')

class TikaCache(models.Model):
    sha1 = models.CharField(max_length=50, primary_key=True)
    data = models.TextField()
