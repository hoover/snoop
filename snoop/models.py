from pathlib import Path
from io import BytesIO
import json
from contextlib import contextmanager
import tempfile
import shutil
from django.db import models, transaction
from django.contrib.postgres.fields import JSONField
from django.conf import settings

def cache(model, keyfunc):

    def decorator(func):

        if not settings.SNOOP_CACHE:
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

        wrapper.no_cache = func
        return wrapper

    return decorator

class EmailCache(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.TextField()
    time = models.DateTimeField(auto_now=True)

class ArchiveListCache(models.Model):
    sha1 = models.CharField(max_length=50, primary_key=True)
    value = models.TextField()
    time = models.DateTimeField(auto_now=True)

class Document(models.Model):
    container = models.ForeignKey('Document',
                                  related_name='snoop_document_container',
                                  null=True)
    parent = models.ForeignKey('Document',
                               related_name='snoop_document_parent',
                               null=True)
    path = models.CharField(max_length=4000)
    content_type = models.CharField(max_length=100, blank=True)
    filename = models.CharField(max_length=1000)
    disk_size = models.BigIntegerField()
    md5 = models.CharField(max_length=40, blank=True, db_index=True)
    sha1 = models.CharField(max_length=50, blank=True, db_index=True)
    broken = models.CharField(max_length=100, blank=True)
    rev = models.IntegerField(null=True)
    flags = JSONField(default=dict, blank=True)

    class Meta:
        # TODO: constraint does not apply to container=None rows
        unique_together = ('container', 'path')

    @property
    def absolute_path(self):
        assert self.container is None
        return Path(settings.SNOOP_ROOT) / self.path

    def _open_file(self):
        if self.content_type == 'application/x-directory':
            return BytesIO()

        if self.container is None:
            return self.absolute_path.open('rb')

        else:
            from . import emails, archives, pst

            if emails.is_email(self.container):
                return emails.get_email_part(self.container, self.path)

            if archives.is_archive(self.container):
                return archives.open_file(self.container, self.path)

            if pst.is_pst_file(self.container):
                return pst.open_file(self.container, self.path)

        raise RuntimeError

    @contextmanager
    def open(self, filesystem=False):
        """ Open the document as a file. If the document is inside an email or
        archive, it will be copied to a temporary file:

            with doc.open() as f:
                f.read()

        If ``filesystem`` is True, ``f`` will have a ``path`` attribute, which
        is the absolute path of the file on disk.
        """

        with self._open_file() as f:
            if filesystem:
                if self.container:
                    MB = 1024*1024
                    suffix = Path(self.filename).suffix
                    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
                        shutil.copyfileobj(f, tmp, length=4*MB)
                        tmp.flush()
                        tmp.path = Path(tmp.name)
                        yield tmp

                else:
                    f.path = self.absolute_path
                    yield f

            else:
                yield f

class Ocr(models.Model):
    tag = models.CharField(max_length=100)
    md5 = models.CharField(max_length=40, db_index=True)
    path = models.CharField(max_length=4000)
    text = models.TextField(blank=True)

    class Meta:
        unique_together = ('tag', 'md5')

    @property
    def absolute_path(self):
        return Path(settings.SNOOP_OCR_ROOT) / self.tag / self.path

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
        index_together = ('queue', 'started')

class TikaCache(models.Model):
    sha1 = models.CharField(max_length=50, primary_key=True)
    value = models.TextField()
    time = models.DateTimeField(auto_now=True)

class TikaLangCache(models.Model):
    sha1 = models.CharField(max_length=50, primary_key=True)
    value = models.CharField(max_length=20)
    time = models.DateTimeField(auto_now=True)

class HtmlTextCache(models.Model):
    sha1 = models.CharField(max_length=50, primary_key=True)
    value = models.TextField()
    time = models.DateTimeField(auto_now=True)
