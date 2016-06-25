from pathlib import Path
from io import StringIO
import json
from django.db import models, transaction
from django.contrib.postgres.fields import JSONField
from django.conf import settings
from . import emails

def cache(model, keyfunc):

    def decorator(func):

        if not settings.MALDINI_CACHE:
            return func

        @transaction.atomic
        def wrapper(*args, **kwargs):
            key = keyfunc(*args, **kwargs)

            row, created = model.objects.get_or_create(pk=key)
            if not created:
                return json.loads(row.value)

            value = func(*args, **kwargs)

            row.value = json.dumps(value)
            row.save()

            return value

        return wrapper

    return decorator

class EmailCache(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.TextField()

class Document(models.Model):
    container = models.ForeignKey('Document', null=True)
    path = models.CharField(max_length=4000)
    content_type = models.CharField(max_length=100, blank=True)
    filename = models.CharField(max_length=1000)
    disk_size = models.BigIntegerField()

    md5 = models.CharField(max_length=40, blank=True, db_index=True)
    sha1 = models.CharField(max_length=50, blank=True, db_index=True)

    broken = models.CharField(max_length=100, blank=True)

    class Meta:
        # TODO: constraint does not apply to container=None rows
        unique_together = ('container', 'path')

    @property
    def absolute_path(self):
        return Path(settings.MALDINI_ROOT) / self.path

    def open(self):
        if self.content_type == 'application/x-directory':
            return StringIO()

        if self.container is None:
            return self.absolute_path.open('rb')

        else:
            if emails.is_email(self.container):
                return emails.get_email_part(self.container, self.path)

        raise RuntimeError

class Digest(models.Model):
    id = models.IntegerField(primary_key=True)
    data = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

class FolderMark(models.Model):
    path = models.CharField(max_length=4000, unique=True, db_index=True)

class Job(models.Model):
    queue = models.CharField(max_length=100)
    data = JSONField(null=True)
    started = models.BooleanField(default=False)

    class Meta:
        unique_together = ('queue', 'data')

class TikaCache(models.Model):
    sha1 = models.CharField(max_length=50, primary_key=True)
    value = models.TextField()

class TikaLangCache(models.Model):
    sha1 = models.CharField(max_length=50, primary_key=True)
    value = models.CharField(max_length=20)
