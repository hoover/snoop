from django.conf import settings
from pathlib import Path
import subprocess
import hashlib
from .tikalib import tika_parse, extract_meta, tika_lang
from io import StringIO
from . import emails
from . import queues
from . import models

FILE_TYPES = {
    'application/x-directory': 'folder',
    'application/pdf': 'pdf',
    'text/plain': 'text',
    'text/html': 'html',
    'message/x-emlx': 'email',
    'message/rfc822': 'email',
    'application/vnd.ms-outlook': 'email',

    'application/msword': 'doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.template': 'doc',
    'application/vnd.ms-word.document.macroEnabled.12': 'doc',
    'application/vnd.ms-word.template.macroEnabled.12': 'doc',
    'application/vnd.oasis.opendocument.text': 'doc',
    'application/vnd.oasis.opendocument.text-template': 'doc',
    'application/rtf': 'doc',

    'application/vnd.ms-excel': 'xls',
    'application/vnd.openxlsformats-officedocument.spreadsheetml.sheet': 'xls',
    'application/vnd.openxlsformats-officedocument.spreadsheetml.template': 'xls',
    'application/vnd.ms-excel.sheet.macroEnabled.12': 'xls',
    'application/vnd.ms-excel.template.macroEnabled.12': 'xls',
    'application/vnd.ms-excel.addin.macroEnabled.12': 'xls',
    'application/vnd.ms-excel.sheet.binary.macroEnabled.12': 'xls',
    'application/vnd.oasis.opendocument.spreadsheet-template': 'xls',
    'application/vnd.oasis.opendocument.spreadsheet': 'xls',

    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'ppt',
    'application/vnd.openxmlformats-officedocument.presentationml.template': 'ppt',
    'application/vnd.openxmlformats-officedocument.presentationml.slideshow': 'ppt',
    'application/vnd.ms-powerpoint.addin.macroEnabled.12': 'ppt',
    'application/vnd.ms-powerpoint.presentation.macroEnabled.12': 'ppt',
    'application/vnd.ms-powerpoint.template.macroEnabled.12': 'ppt',
    'application/vnd.ms-powerpoint.slideshow.macroEnabled.12': 'ppt',
    'application/vnd.oasis.opendocument.presentation': 'ppt',
    'application/vnd.oasis.opendocument.presentation-template': 'ppt',
}

def pdftotext(input):
    return subprocess.check_output(['pdftotext', '-', '-'], stdin=input)

def doc_path(doc):
    return Path(settings.MALDINI_ROOT) / doc.path

def is_email(doc):
    return doc.content_type in ['message/x-emlx',
                                'message/rfc822',
                                'application/vnd.ms-outlook']

def open_email(doc):
    if doc.content_type == 'message/x-emlx':
        with open_document(doc) as f:
            assert doc.container_id is None, "can't parse emlx in container"
            return emails.EmlxParser(f, doc_path(doc))

    if doc.content_type == 'message/rfc822':
        with open_document(doc) as f:
            return emails.EmailParser(f)

    if doc.content_type == 'application/vnd.ms-outlook':
        with emails.open_msg(doc_path(doc)) as f:
            return emails.EmailParser(f)

    raise RuntimeError

def get_email_part(doc, part):
    return open_email(doc).open_part(part)

def parse_email(doc):
    email = open_email(doc)
    data = email.get_data()
    tree = email.get_tree()
    text = email.get_text()
    data['text'] = text
    return (tree, data)

def open_document(doc):
    if doc.content_type == 'application/x-directory':
        return StringIO()

    if doc.container is None:
        path = doc_path(doc)
        return path.open('rb')

    else:
        if is_email(doc.container):
            return get_email_part(doc.container, doc.path)

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
        'filename': doc.filename
    }

    if doc.container_id is None:
        data['path'] = doc.path

        if is_email(doc):
            (tree, email_data) = parse_email(doc)
            data.update(email_data)
            data['parts'] = tree
    else:
        data['message'] = doc.container_id

    filetype = guess_filetype(doc)
    data['type'] = filetype

    if filetype in settings.TIKA_FILE_TYPES and doc.disk_size <= settings.MAX_TIKA_FILE_SIZE:
        with open_document(doc) as f:
            parsed = tika_parse(doc.sha1, f.read())
        data['text'] = (parsed.get('content') or '').strip()
        data.update(extract_meta(parsed.get('metadata', {})))

    if settings.MALDINI_ANALYZE_LANG:
        if 'text' in data and len(data['text']) > 100:
            data['lang'] = tika_lang(data['text'])[:2]

    return data

def create_children(doc, data, verbose=True):
    for name, info in data.get('attachments', {}).items():
        child, created = models.Document.objects.update_or_create(
            container=doc,
            path=name,
            defaults={
                'disk_size': 0,
                'content_type': info['content_type'],
                'filename': info['filename'],
            },
        )

        if created:
            queues.put('digest', {'id': child.id}, verbose=verbose)
            if verbose: print('new child', child.id)
