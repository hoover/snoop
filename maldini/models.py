from __future__ import unicode_literals
from django.db import models
from django.contrib.postgres.fields import JSONField

class Document(models.Model):
    path = models.CharField(max_length=4000, unique=True, db_index=True)
    disk_size = models.BigIntegerField()
    push = models.BooleanField(default=False)
    status = JSONField(default=dict)

class Prop(models.Model):
    document = models.ForeignKey(Document, db_index=True)
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=1000)

    class Meta:
        index_together = [
            ('key', 'value'),
        ]

class FolderMark(models.Model):
    path = models.CharField(max_length=4000, unique=True, db_index=True)
