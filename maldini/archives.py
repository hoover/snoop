import os
from pathlib import Path
import subprocess
import tempfile
from django.conf import settings
import shutil
from maldini import models
from maldini.content_types import guess_filetype

CACHE_ROOT = Path(settings.ARCHIVE_CACHE_ROOT)

class MissingArchiveFile(Exception):
    pass

class EncryptedArchiveFile(Exception):
    pass

def other_temps(sha1, current_dir):
    current = Path(current_dir).name
    for dir in CACHE_ROOT.iterdir():
        if dir.name == current:
            continue
        hash = dir.name[:len(sha1)]
        if sha1 == hash:
            return True
    return False

def mark_broken(tmpdir, archive_path):
    tmppath = Path(tmpdir)
    newpath = tmppath.with_name('broken_' + tmppath.name)
    shutil.move(tmpdir, str(newpath))
    shutil.copy(archive_path, str(newpath))

def call_7z(archive_path, output_dir):
    try:
        subprocess.check_output([
            settings.SEVENZIP_BINARY,
            '-y',
            '-pp',
            'x',
            archive_path,
            '-o' + output_dir,
        ], stderr=subprocess.STDOUT)

    except subprocess.CalledProcessError as e:
        if "Wrong password" in e.output.decode():
            raise EncryptedArchiveFile
        else:
            raise RuntimeError("7z failed: " + e.output.decode())

def extract_to_base(doc):
    if not settings.SEVENZIP_BINARY:
        raise RuntimeError

    base = CACHE_ROOT / doc.sha1
    if base.is_dir():
        return

    tmpdir = tempfile.mkdtemp(
        prefix=doc.sha1,
        dir=str(CACHE_ROOT),
        suffix='_tmp')

    if other_temps(doc.sha1, tmpdir):
        shutil.rmtree(tmpdir)
        raise RuntimeError("Another worker has taken this one")

    if not doc.container:
        temp = False
        path = str(doc.absolute_path)
    else:
        temp = True
        path = tempfile.mktemp(suffix=doc.filename)
        with doc.open() as f, open(path, 'wb') as g:
            shutil.copyfileobj(f, g, length=4*1024*1024)

    try:
        call_7z(path, tmpdir)

    except Exception:
        mark_broken(tmpdir, path)
        if temp:
            os.remove(path)
        raise
    else:
        shutil.move(tmpdir, str(base))
        if temp:
            os.remove(path)


@models.cache(models.ArchiveListCache, lambda doc: doc.sha1)
def list_files(doc):
    base = CACHE_ROOT / doc.sha1
    if not base.is_dir():
        extract_to_base(doc)

    filelist = []

    for root, dirs, files in os.walk(str(base.resolve())):
        for file in files:
            abs = Path(root) / file
            rel = abs.relative_to(base)
            filelist.append(str(rel))

    return filelist

def open_file(doc, name):
    path = CACHE_ROOT / doc.sha1 / name
    if not path.exists():
        extract_to_base(doc)
        if not path.exists():
            raise MissingArchiveFile(str(path))
    return path.open('rb')

def is_archive(doc):
    return guess_filetype(doc) == 'archive' and \
           doc.content_type not in [
            'application/x-tar',
            'application/x-bzip2',
    ]
