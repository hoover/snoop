from django.conf import settings
from pathlib import Path
import subprocess
import hashlib
from .tikalib import tika_parse, extract_meta
from io import StringIO
from . import emails

FILE_TYPES = {
    'application/x-directory': 'folder',
    'application/vnd.oasis.opendocument.text': 'doc',
    'application/pdf': 'pdf',
    'application/msword': 'doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'doc',
    'application/vnd.ms-excel': 'xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xls',
    'text/plain': 'text',
    'text/html': 'html',
    'message/x-emlx': 'email',
    'message/rfc822': 'email'
}

def pdftotext(input):
    return subprocess.check_output(['pdftotext', '-', '-'], stdin=input)

def doc_path(doc):
    return Path(settings.MALDINI_ROOT) / doc.path

def is_email(doc):
    return doc.content_type in ['message/x-emlx', 'message/rfc822']

def open_email(doc):
    if doc.content_type == 'message/x-emlx':
        with open_document(doc) as f:
            assert doc.container_id is None, "can't parse emlx in container"
            return emails.EmlxParser(f, doc_path(doc))

    if doc.content_type == 'message/rfc822':
        with open_document(doc) as f:
            return emails.EmailParser(f)

    raise RuntimeError

def open_document(doc):
    if doc.content_type == 'application/x-directory':
        return StringIO()

    if doc.container is None:
        path = doc_path(doc)
        return path.open('rb')

    else:
        if is_email(doc.container):
            return open_email(doc.container).open_part(doc.path)

    raise RuntimeError

def _path_bits(doc):
    if doc.container:
        yield from _path_bits(doc.container)
    yield doc.path

def _calculate_hashes(opened_file):
    BUF_SIZE = 65536

    md5 = hashlib.md5()
    sha1 = hashlib.sha1()

    while True:
        data = opened_file.read(BUF_SIZE)
        if not data:
            break
        md5.update(data)
        sha1.update(data)

    fsize = opened_file.tell()

    return (md5.hexdigest(), sha1.hexdigest(), fsize)

def guess_filetype(doc):

    content_type = doc.content_type.split(';')[0]  # for: text/plain; charset=ISO-1234

    return FILE_TYPES.get(content_type)

def digest(doc):
    if not doc.sha1:
        with open_document(doc) as f:
            md5, sha1, fsize = _calculate_hashes(f)
        if not doc.disk_size:
            doc.disk_size = fsize
        doc.sha1 = sha1
        doc.md5 = md5
        doc.save()

    data = {
        'title': '|'.join(_path_bits(doc)),
        'lang': None,
        'sha1': doc.sha1,
        'md5': doc.md5,
    }

    if doc.container_id is None:
        data['path'] = doc.path

        if is_email(doc):
            email = open_email(doc)
            data.update(email.get_data())
            data['parts'] = email.get_tree()

    filetype = guess_filetype(doc)
    data['type'] = filetype

    if filetype in settings.TIKA_FILE_TYPES and doc.disk_size <= settings.MAX_TIKA_FILE_SIZE:
        with open_document(doc) as f:
            parsed = tika_parse(doc.sha1, f.read())
        data['text'] = (parsed.get('content') or '').strip()
        data.update(extract_meta(parsed['metadata']))

    return data
