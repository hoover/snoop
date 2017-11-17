from pathlib import Path
from django.db import models
from django.contrib.postgres.fields import JSONField


class Collection(models.Model):
    path = models.CharField(max_length=4000)
    name = models.CharField(max_length=100, unique=True)
    ocr = JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name

    def get_root(self):
        try:
            return self.document_set.filter(parent__isnull=True).get()
        except Document.DoesNotExist:
            return self.document_set.create()


class Blob(models.Model):
    md5 = models.CharField(max_length=32, db_index=True)
    sha1 = models.CharField(max_length=40, db_index=True)
    sha3_256 = models.CharField(max_length=64, unique=True)
    size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100, blank=True)
    mime_encoding = models.CharField(max_length=100, blank=True)


class Document(models.Model):
    blob = models.ForeignKey('Blob', null=True, blank=True)
    collection = models.ForeignKey('Collection')
    parent = models.ForeignKey('Document',
                               related_name='child_set',
                               null=True)
    filename_bytes = models.BinaryField(max_length=1000)

    @property
    def filename(self):
        return bytes(self.filename_bytes).decode('utf8')

    @property
    def path(self):
        doc = self
        names = []
        while doc:
            names.append(doc.filename)
            doc = doc.parent
        names.reverse()
        return '/'.join(names)

    def __str__(self):
        return f"{self.collection}:{self.path}"

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
