import hashlib
from pathlib import Path
import pytest
from django.conf import settings
from snoop import models
from snoop.utils import chunks
from snoop.magic import Magic

pytestmark = pytest.mark.django_db

WORDS_MD5 = 'cbbcded3dc3b61ad50c4e36f79c37084'
WORDS_SHA1 = '33a07ef770a51b476e5a480b2dc3628c3b939395'
WORDS_SHA3_256 = ('5490ccb75c33798427f7e746150e74f1'
                  '816da0449dd9c40a7f741f039d16d6cc')


def resolve(doc):
    name = doc.filename
    parent = resolve(doc.parent) if doc.parent else Path(doc.collection.root)
    return parent / name


def walk(doc):
    path = resolve(doc)

    if path.is_file():
        if doc.blob is None:
            hashes = {
                'md5': hashlib.md5(),
                'sha1': hashlib.sha1(),
                'sha3_256': hashlib.sha3_256(),
            }
            magic = Magic()

            with path.open('rb') as f:
                size = 0
                for block in chunks(f):
                    size += len(block)
                    for h in hashes.values():
                        h.update(block)
                    magic.update(block)

            fields = {name: hash.hexdigest() for name, hash in hashes.items()}
            fields['size'] = size
            (fields['mime_type'], fields['mime_encoding']) = magic.get_result()

            blob, _ = models.Blob.objects.get_or_create(
                sha3_256=fields['sha3_256'],
                defaults=fields,
            )
            doc.blob = blob
            doc.save()

    elif path.is_dir():
        children = {c.filename_bytes: c for c in doc.child_set.all()}

        for item in path.iterdir():
            filename_bytes = item.name.encode('utf8')
            child = children.get(filename_bytes)
            if child is None:
                child = doc.child_set.create(
                    collection=doc.collection,
                    filename_bytes=filename_bytes,
                )
            walk(child)


def lookup(col, path):
    doc = None

    for name in path.split('/'):
        for child in col.document_set.filter(parent=doc):
            if child.filename == name:
                break
        else:
            raise RuntimeError(f'not found: {name} in {doc}')
        doc = child

    return doc


def test_walk_testdata():
    col = models.Collection.objects.create(root=settings.SNOOP_ROOT)
    walk(col.get_root())

    words = lookup(col, '/words/usr-share-dict-words.txt')
    assert words.filename == 'usr-share-dict-words.txt'
    assert words.blob.md5 == WORDS_MD5
    assert words.blob.sha1 == WORDS_SHA1
    assert words.blob.sha3_256 == WORDS_SHA3_256
    assert words.blob.mime_type == 'text/plain'
    assert words.blob.mime_encoding == 'utf-8'
