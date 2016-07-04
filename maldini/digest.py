from django.conf import settings
import hashlib
import json
from .tikalib import tika_parse, extract_meta, tika_lang
from . import emails
from . import text
from . import queues
from . import models
from . import archives
from .walker import mime_type
from .utils import chunks

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

    'application/zip': 'archive',
    'application/rar': 'archive',
    'application/x-7z-compressed': 'archive',
    'application/x-tar': 'archive',
    'application/x-bzip2': 'archive',
}

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
    BUF_SIZE = 65536

    md5 = hashlib.md5()
    sha1 = hashlib.sha1()

    for data in chunks(opened_file):
        md5.update(data)
        sha1.update(data)

    fsize = opened_file.tell()

    return (md5.hexdigest(), sha1.hexdigest(), fsize)

def guess_filetype(doc):

    content_type = doc.content_type.split(';')[0]  # for: text/plain; charset=ISO-1234

    return FILE_TYPES.get(content_type)

def docs_under_archive(doc):
    children = models.Document.objects.filter(container=doc)
    return [{
        'id': child.id,
        'filename': child.filename
    } for child in children]

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

    if doc.container_id is None:
        if emails.is_email(doc):
            data.update(emails.parse_email(doc))
    else:
        data['message'] = doc.container_id

    filetype = guess_filetype(doc)
    data['type'] = filetype

    if filetype in ['text', 'html']:
        data['text'] = text.get_text(doc)

    if filetype in settings.TIKA_FILE_TYPES and doc.disk_size <= settings.MAX_TIKA_FILE_SIZE:
        parsed = tika_parse(doc.sha1, doc.open)
        data['text'] = (parsed.get('content') or '').strip()
        data.update(extract_meta(parsed.get('metadata', {})))

    if settings.MALDINI_ANALYZE_LANG:
        if 'text' in data and len(data['text']) > 100:
            data['lang'] = tika_lang(data['text'])[:2]

    ocr_items = list(models.Ocr.objects.filter(md5=doc.md5))
    if ocr_items:
        data['ocr'] = {ocr.tag: ocr.text for ocr in ocr_items}

    ## TODO: if is_archive, extract it here.
    # get_archive_contents: extract or find on disk,
    # walk it, return relative filenames
    # Cache this return value as json right here, with:
    # Filename, filesize
    if archives.is_archive(doc):
        data['files'] = docs_under_archive(doc)

    return data

def create_children(doc, data, verbose=True):
    children_info = []
    if emails.is_email(doc):
        for name, info in data.get('attachments', {}).items():
            children_info.append({
                'path': name,
                'content_type': info['content_type'],
                'filename': info['filename'],
            })
    elif archives.is_archive(doc):
        for name in archives.list_files(doc):
            children_info.append({
                'path': name,
                'content_type': mime_type(name),
                'filename': name,
            })

    for info in children_info:
        child, created = models.Document.objects.update_or_create(
            container=doc,
            path=info['path'],
            defaults={
                'disk_size': 0,
                'content_type': info['content_type'],
                'filename': info['filename'],
            },
        )

        if created:
            queues.put('digest', {'id': child.id}, verbose=verbose)
            if verbose: print('new child', child.id)

def worker(id, verbose):
    try:
        document = models.Document.objects.get(id=id)
    except models.Document.DoesNotExist:
        if verbose: print('MISSING')
        return

    try:
        data = digest(document)

    except emails.MissingEmlxPart:
        document.broken = 'missing_emlx_part'
        document.save()
        if verbose: print('missing_emlx_part')
        return

    except emails.PayloadError:
        document.broken = 'payload_error'
        document.save()
        if verbose: print('payload_error')
        return

    except emails.CorruptedFile:
        document.broken = 'corrupted_file'
        document.save()
        if verbose: print('corrupted_file')
        return

    except archives.EncryptedArchiveFile:
        document.broken = 'encrypted archive'
        document.save()
        if verbose: print('encrypted archive')
        return

    except archives.MissingArchiveFile:
        document.broken = 'missing archive file'
        document.save()
        if verbose: print('missing archive file')
        return

    else:
        if document.broken:
            if verbose: print('removing broken flag', document.broken)
            document.broken = ''
            document.save()

    create_children(document, data, verbose)

    models.Digest.objects.update_or_create(
        id=document.id,
        defaults={'data': json.dumps(data)},
    )

    if verbose: print('type:', data.get('type'))

    queues.put('index', {'id': document.id}, verbose=verbose)
