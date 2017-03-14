import os
from pathlib import Path
import subprocess
import tempfile
from django.conf import settings
import shutil
from . import models
from . import exceptions
from .walker import Walker

KNOWN_TYPES = {
    'application/zip',
    'application/rar',
    'application/x-7z-compressed',
    'application/x-zip',
    'application/x-gzip',
    'application/x-zip-compressed',
    'application/x-rar-compressed',
}

if settings.SNOOP_ARCHIVE_CACHE_ROOT:
    CACHE_ROOT = Path(settings.SNOOP_ARCHIVE_CACHE_ROOT)
else:
    CACHE_ROOT = None

class MissingArchiveFile(exceptions.BrokenDocument):
    flag = 'archive_missing_file'

class EncryptedArchiveFile(exceptions.BrokenDocument):
    flag = 'archive_encrypted'

class ExtractingFailed(exceptions.BrokenDocument):
    flag = 'archive_extraction_failed'

def _other_temps(sha1, current):
    for dir in CACHE_ROOT.iterdir():
        if dir.name == current:
            continue
        hash = dir.name[:len(sha1)]
        if sha1 == hash:
            return True
    return False

def call_7z(archive_path, output_dir):
    try:
        subprocess.check_output([
            settings.SNOOP_SEVENZIP_BINARY,
            '-y',
            '-pp',
            'x',
            str(archive_path),
            '-o' + str(output_dir),
        ], stderr=subprocess.STDOUT)

    except subprocess.CalledProcessError as e:
        sevenzip_output = e.output.decode()
        if "Wrong password" in sevenzip_output:
            raise EncryptedArchiveFile
        else:
            raise ExtractingFailed(sevenzip_output)

def extract_to_base(doc):
    if not settings.SNOOP_SEVENZIP_BINARY:
        raise RuntimeError

    base = CACHE_ROOT / doc.sha1
    if base.is_dir():
        return

    tmp = Path(tempfile.mkdtemp(
        prefix=doc.sha1,
        dir=str(CACHE_ROOT),
        suffix='_tmp',
    ))

    if _other_temps(doc.sha1, tmp.name):
        shutil.rmtree(str(tmp))
        raise RuntimeError("Another worker has taken this one")

    with doc.open(filesystem=True) as archive:
        try:
            call_7z(archive.path, tmp)

        except Exception:
            tmp.rename(tmp.with_name('broken_' + tmp.name))
            raise

        else:
            tmp.rename(base)

def list_children(doc):
    base = CACHE_ROOT / doc.sha1
    if not base.is_dir():
        extract_to_base(doc)
    child_list = Walker.walk(
        root=base,
        prefix=None,
        container_doc=doc,
        collection=doc.collection
    )
    return [(doc.id, created) for doc, created in child_list]

def open_file(doc, name):
    path = CACHE_ROOT / doc.sha1 / name
    if not path.exists():
        extract_to_base(doc)
        if not path.exists():
            raise MissingArchiveFile(str(path))
    return path.open('rb')

def is_archive(doc):
    return doc.content_type in KNOWN_TYPES
