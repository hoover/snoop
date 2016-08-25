import os
from pathlib import Path
import subprocess
import tempfile
from django.conf import settings
import shutil

KNOWN_TYPES = {
    'application/x-hoover-pst',
}

if settings.SNOOP_PST_CACHE_ROOT:
    CACHE_ROOT = Path(settings.SNOOP_PST_CACHE_ROOT)
else:
    CACHE_ROOT = None

class PSTExtractionFailed(Exception):
    pass

class MissingPSTFile(Exception):
    pass

def _other_temps(sha1, current):
    for dir in CACHE_ROOT.iterdir():
        if dir.name == current:
            continue
        hash = dir.name[:len(sha1)]
        if sha1 == hash:
            return True
    return False

def call_readpst(pst_path, output_dir):
    try:
        subprocess.check_output([
            settings.SNOOP_READPST_BINARY,
            '-D',
            '-M',
            '-e',
            '-o',
            str(output_dir),
            '-teajc',
            str(pst_path),
        ], stderr=subprocess.STDOUT)

    except subprocess.CalledProcessError as e:
        raise PSTExtractionFailed('readpst failed: ' + e.output.decode())

def extract_to_base(doc):
    if not settings.SNOOP_READPST_BINARY:
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

    with doc.open(filesystem=True) as pst_file:
        try:
            call_readpst(pst_file.path, tmp)

        except Exception:
            tmp.rename(tmp.with_name('broken_' + tmp.name))
            raise

        else:
            tmp.rename(base)


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
            raise MissingPSTFile(str(path))
    return path.open('rb')

def is_pst_file(doc):
    return doc.content_type in KNOWN_TYPES
