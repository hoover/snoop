import os
from pathlib import Path
import subprocess
import tempfile
from django.conf import settings
import shutil
from maldini import models

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

def mark_broken(tmpdir):
    tmppath = Path(tmpdir)
    newpath = tmppath.with_name('broken_' + tmppath.name)
    shutil.move(tmpdir, str(newpath))

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

    with tempfile.NamedTemporaryFile(suffix=doc.filename) as tmparchive:
        if not doc.container:
            path = str(doc.absolute_path)
        else:
            with doc.open() as f:
                shutil.copyfileobj(f, tmparchive, length=4*1024*1024)
            path = tmparchive.name

        try:
            print('starting')
            subprocess.check_output([
                settings.SEVENZIP_BINARY,
                '-y',
                '-pp',
                'x',
                path,
                '-o' + tmpdir,
            ], stderr=subprocess.STDOUT)

        except subprocess.CalledProcessError as e:
            mark_broken(tmpdir)

            if "Wrong password" in e.output.decode():
                raise EncryptedArchiveFile
            else:
                shutil.copy(path, '/tmp/file.zip')
                raise RuntimeError("7z failed: " + e.output.decode())
        except Exception:
            mark_broken(tmpdir)
            raise
        else:
            shutil.move(tmpdir, str(base))


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
    return doc.content_type in [
        'application/zip',
        'application/x-zip',
        'application/x-gzip',
        'application/x-zip-compressed',
        'application/rar',
        'application/x-rar-compressed',
        'application/x-7z-compressed',
    ]
