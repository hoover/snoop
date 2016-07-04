import os
from pathlib import Path
import subprocess
import tempfile
from django.conf import settings
import shutil

CACHE_ROOT = Path(settings.ARCHIVE_CACHE_ROOT)

class MissingArchiveFile(Exception):
    pass

class EncryptedArchiveFile(Exception):
    pass

def extract_to_base(doc):
    if not settings.SEVENZIP_BINARY:
        raise RuntimeError

    base = CACHE_ROOT / doc.sha1
    if base.is_dir():
        return

    tmpdir = tempfile.mkdtemp(prefix=doc.sha1, dir=str(CACHE_ROOT))
    tmparchive = None
    if not doc.container:
        path = str(doc.absolute_path)
    else:
        tmparchive = tempfile.NamedTemporaryFile(suffix=doc.filename)
        with doc.open() as f:
            shutil.copyfileobj(f, tmparchive, length=4*1024*1024)
        path = tmparchive.name

    out = ""
    try:
        out = subprocess.check_output([
            settings.SEVENZIP_BINARY,
            '-y'
            '-pp',
            'e',
            path,
            '-o' + tmpdir,
        ], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        if "Wrong password" in out:
            raise EncryptedArchiveFile
        else:
            raise RuntimeError("7z failed")

    if tmparchive:
        tmparchive.close()

    shutil.move(tmpdir, str(base))



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
        raise MissingArchiveFile(str(path))
    return path.open('rb')

def is_archive(doc):
    return doc.content_type in [
        'application/zip',
        'application/x-zip',
        'application/x-gzip',
        'application/x-zip-compressed',
        'application/rar',
        'application/x-rar-compressed',
        'application/x-7z-compressed',
    ]
