from django.conf import settings
import hashlib
import json
from pathlib import Path
from .tikalib import tika_parse, extract_meta, tika_lang
from . import emails
from . import text
from . import queues
from . import models
from . import archives
from . import pst
from . import exceptions
from . import pgp
from . import html
from .content_types import guess_content_type, guess_filetype
from .utils import chunks, word_count, log_result, extract_exif

INHERITABLE_DOCUMENT_FLAGS = [
    'pgp',
]

def _path_bits(doc):
    if doc.container:
        yield from _path_bits(doc.container)
        if emails.is_email(doc.container):
            yield doc.filename
        else:
            yield doc.path
    else:
        yield doc.path

def _calculate_hashes(opened_file):

    md5 = hashlib.md5()
    sha1 = hashlib.sha1()

    for data in chunks(opened_file):
        md5.update(data)
        sha1.update(data)

    fsize = opened_file.tell()

    return (md5.hexdigest(), sha1.hexdigest(), fsize)

def digest(doc):
    if not doc.sha1:
        with doc.open() as f:
            md5, sha1, fsize = _calculate_hashes(f)
        if not doc.disk_size:
            doc.disk_size = fsize
        doc.sha1 = sha1
        doc.md5 = md5
        doc.save()

    data = {
        'path': '//'.join(_path_bits(doc)),
        'lang': None,
        'sha1': doc.sha1,
        'md5': doc.md5,
        'filename': doc.filename,
        'rev': doc.rev,
    }

    if emails.is_email(doc):
        data.update(emails.parse_email(doc))

    if 'pgp' in doc.flags:
        data['pgp'] = doc.flags['pgp']

    if doc.container_id:
        data['message'] = doc.container_id

    filetype = guess_filetype(doc)
    data['type'] = filetype

    if filetype in ['text', 'html']:
        data['text'] = text.get_text(doc)

    if filetype == 'html':
        data['safe_html'] = html.get_safe_html(doc)

    if filetype == 'image':
        data.update(extract_exif(doc))

    if filetype in settings.SNOOP_TIKA_FILE_TYPES and \
            doc.disk_size <= settings.SNOOP_TIKA_MAX_FILE_SIZE:
        parsed = tika_parse(doc.sha1, doc.open)
        data['text'] = (parsed.get('content') or '').strip()
        data.update(extract_meta(parsed.get('metadata', {})))

    if settings.SNOOP_ANALYZE_LANG:
        if 'text' in data and len(data['text']) > 100:
            data['lang'] = tika_lang(data['text'])[:2]

    if 'text' in data:
        data['word-count'] = word_count(data['text'])

    ocr_items = list(models.Ocr.objects.filter(md5=doc.md5))
    if ocr_items:
        data['ocr'] = {ocr.tag: ocr.text for ocr in ocr_items}

    if archives.is_archive(doc):
        data.update(archives.list_files(doc))
    elif pst.is_pst_file(doc):
        data.update(pst.list_files(doc))

    return data

def create_children(doc, data, verbose=True):
    children_info = []
    if emails.is_email(doc):
        for name, info in data.get('attachments', {}).items():
            children_info.append({
                'path': name,
                'content_type': info['content_type'],
                'filename': info['filename'],
                'size': info.get('size', 0),
            })
    elif archives.is_archive(doc) or pst.is_pst_file(doc):
        for path in data['file_list']:
            children_info.append({
                'path': path,
                'content_type': guess_content_type(path),
                'filename': Path(path).name,
                'size': 0,
            })
        for path in data['folder_list']:
            children_info.append({
                'path': path,
                'content_type': 'application/x-directory',
                'filename': Path(path).name,
                'size': 0,
            })

    inherited_flags = {
        key: doc.flags[key]
        for key in doc.flags
        if key in INHERITABLE_DOCUMENT_FLAGS
    }

    new_children = 0
    for info in children_info:
        child, created = models.Document.objects.update_or_create(
            container=doc,
            path=info['path'],
            defaults={
                'disk_size': info['size'],
                'content_type': info['content_type'],
                'filename': info['filename'],
                'flags': inherited_flags,
            },
        )

        if created:
            queues.put('digest', {'id': child.id}, verbose=verbose)
            if verbose: print('new child', child.id)
            new_children += 1

    return new_children

@log_result({"type": "worker", "queue": "digest"})
def worker(id, verbose):
    status = {
        'document': id,
    }
    try:
        document = models.Document.objects.get(id=id)
    except models.Document.DoesNotExist:
        if verbose: print('MISSING')
        status['error'] = 'document_missing'
        return status

    try:
        data = digest(document)

    except exceptions.BrokenDocument as e:
        assert e.flag is not None
        document.broken = e.flag
        document.save()
        if verbose: print(e.flag)
        status['error'] = 'broken'
        status['broken'] = document.broken
        return status

    else:
        if document.broken:
            if verbose: print('removing broken flag', document.broken)
            document.broken = ''
            document.save()

    new_children = create_children(document, data, verbose)
    if new_children > 0:
        status['new_children'] = new_children

    models.Digest.objects.update_or_create(
        id=document.id,
        defaults={'data': json.dumps(data)},
    )

    if verbose: print('type:', data.get('type'))

    queues.put('index', {'id': document.id}, verbose=verbose)

    return status

