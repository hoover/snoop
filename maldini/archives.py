import os
from pathlib import Path
import subprocess
import tempfile
from django.conf import settings
import shutil
from contextlib import contextmanager
from maldini import models
from maldini.content_types import guess_filetype

if settings.ARCHIVE_CACHE_ROOT:
    CACHE_ROOT = Path(settings.ARCHIVE_CACHE_ROOT)
else:
    CACHE_ROOT = None

class MissingArchiveFile(Exception):
    pass

class EncryptedArchiveFile(Exception):
    pass

def _other_temps(sha1, current):
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

@contextmanager
def _file_on_disk(doc):
    if doc.container:
        MB = 1024*1024
        suffix = Path(doc.filename).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
            with doc.open() as f:
                shutil.copyfileobj(f, tmp, length=4*MB)
                tmp.flush()
            yield Path(tmp.name)

    else:
        yield doc.absolute_path

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

    if _other_temps(doc.sha1, Path(tmpdir).name):
        shutil.rmtree(tmpdir)
        raise RuntimeError("Another worker has taken this one")

    with _file_on_disk(doc) as archive:
        try:
            call_7z(str(archive), tmpdir)

        except Exception:
            mark_broken(tmpdir, str(archive))
            raise

        else:
            shutil.move(tmpdir, str(base))


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
    return guess_filetype(doc) == 'archive' and \
           doc.content_type not in [
            'application/x-tar',
            'application/x-bzip2',
    ]
