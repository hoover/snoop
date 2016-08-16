import os
from pathlib import Path
import subprocess
import tempfile
from django.conf import settings
import shutil
from . import models
from .content_types import guess_filetype

KNOWN_TYPES = {
    'application/zip',
    'application/rar',
    'application/x-7z-compressed',
    'application/x-zip',
    'application/x-gzip',
    'application/x-zip-compressed',
    'application/x-rar-compressed',
}

if settings.ARCHIVE_CACHE_ROOT:
    CACHE_ROOT = Path(settings.ARCHIVE_CACHE_ROOT)
else:
    CACHE_ROOT = None

class MissingArchiveFile(Exception):
    pass

class EncryptedArchiveFile(Exception):
    pass

class ExtractingFailed(Exception):
    pass

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
            settings.SEVENZIP_BINARY,
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
    if not settings.SEVENZIP_BINARY:
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


@models.cache(models.ArchiveListCache, lambda doc: doc.sha1)
def list_files(doc):
    base = CACHE_ROOT / doc.sha1
    if not base.is_dir():
        extract_to_base(doc)

    file_list = []
    folder_list = []

    for root, dirs, files in os.walk(str(base)):
        for file in files:
            abs = Path(root) / file
            rel = abs.relative_to(base)
            file_list.append(str(rel))
        for folder in dirs:
            abs = Path(root) / folder
            rel = abs.relative_to(base)
            folder_list.append(str(rel))

    return {
        'file_list': file_list,
        'folder_list': folder_list,
    }

def open_file(doc, name):
    path = CACHE_ROOT / doc.sha1 / name
    if not path.exists():
        extract_to_base(doc)
        if not path.exists():
            raise MissingArchiveFile(str(path))
    return path.open('rb')

def is_archive(doc):
    return doc.content_type in KNOWN_TYPES
