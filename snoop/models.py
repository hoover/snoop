from pathlib import Path
from io import BytesIO
import json
from contextlib import contextmanager
import tempfile
import shutil
from django.db import models, transaction
from django.contrib.postgres.fields import JSONField
from django.conf import settings


class Collection(models.Model):
    root = models.CharField(max_length=4000)
    name = models.CharField(max_length=100, unique=True)
    ocr = JSONField(default=dict, blank=True)

    filesystem_path = ceva(null=True)

    def __str__(self):
        return self.slug

class Blob(models.Model):
    md5 = models.BytesField(max_length=16, db_index=True)
    sha1 = models.BytesField(max_length=20, db_index=True)
    sha3_256 = models.BytesField(max_length=32, unique=True)
    size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100, blank=True)
    mime_encoding = models.CharField(max_length=100, blank=True)


class Document(models.Model):
    blob = models.ForeignKey('Blob', null=True, blank=True)
    collection = models.ForeignKey('Collection')
    parent = models.ForeignKey('Document',
                               related_name='child_set',
                               null=True)
    filename_bytes = models.BytesField(max_length=1000)

    class Meta:
        unique_together = ('parent', 'filename_bytes')

class Ocr(models.Model):
    collection = models.ForeignKey(
        'Collection',
        related_name='ocr_documents',
    )
    tag = models.CharField(max_length=100)
    md5 = models.CharField(max_length=40, db_index=True)
    path = models.CharField(max_length=4000)
    text = models.TextField(blank=True)

    class Meta:
        unique_together = ('collection', 'tag', 'md5')

    @property
    def absolute_path(self):
        return Path(self.collection.ocr[self.tag]) / self.path
