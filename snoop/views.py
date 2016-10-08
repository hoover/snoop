import re
from pathlib import Path
from dateutil import parser
from pprint import pformat
from django.http import HttpResponse, FileResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render
from django.conf import settings
from django.utils.encoding import filepath_to_uri
from jinja2 import Environment
from . import models, html
from .digest import digest
from .walker import files_in
from .emails import open_msg
BOOTSTRP_CSS = ""

path = Path(settings.BASE_DIR) / 'assets' / 'bootstrap.min.css'
with path.open('r') as f:
    BOOTSTRP_CSS += f.read() + "\n"

def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'css': BOOTSTRP_CSS,
        'uriencode': filepath_to_uri,
    })
    return env

def _format_size(num):
    for unit in ['', 'KB', 'MB', 'GB', 'TB']:
        if abs(num) < 1024.0:
            return "%3.1f %s" % (num, unit)
        num /= 1024.0
    return "%3.1f %s" % (num, 'PB')

def _format_date(date_value):
    return parser.parse(date_value).strftime("%d %B %Y")

def document_raw(request, id):
    doc = get_object_or_404(models.Document, id=id)
    if doc.content_type == 'text/html':
        return HttpResponse("This file has been stripped " +
                            "of links, images, forms and javascript.\n\n" +
                            html.get_safe_html(doc),
                            content_type='text/plain',
                            charset='UTF-8')
    with doc.open() as f:
        data = f.read()
        return HttpResponse(data, content_type=doc.content_type)

def document_ocr(request, id, tag):
    doc = get_object_or_404(models.Document, id=id)
    ocr = get_object_or_404(models.Ocr, tag=tag, md5=doc.md5)
    return FileResponse(
        ocr.absolute_path.open('rb'),
        content_type='application/pdf',
    )

def _as_eml(doc):
    if doc.content_type == 'application/vnd.ms-outlook':
        return str(Path(doc.filename).with_suffix('.eml'))

def document_as_eml(request, id):
    doc = get_object_or_404(models.Document, id=id)
    if not _as_eml(doc):
        return HttpResponseNotFound()
    with open_msg(doc) as f:
        return HttpResponse(f.read(), content_type='message/rfc822')

def _process_document(id):
    parent_id = None
    attachments = []

    doc = get_object_or_404(models.Document, id=id)

    try:
        data = digest(doc)

    except Exception as e:
        error_message = doc.broken
        if not error_message:
            error_message = "{t.__name__} (not marked as broken)".format(t=type(e))
        data = {'type': 'ERROR: ' + error_message}

    else:
        if data.get('type') in ['folder', 'archive', 'email-archive']:
            data['files'] = files_in(doc)
            for file in data['files']:
                file['size'] = _format_size(file['size'])

        def attachment_id(n):
            try:
                a = doc.contained_set.get(path=n)
            except models.Document.DoesNotExist:
                return None
            else:
                return a.id

        if data.get('tree'):
            data['tree'] = pformat(data.get('tree'), indent=4, width=120)

        attachments = [{
            'filename': a['filename'],
            'id': attachment_id(n),
            'content_type': a['content_type'],
        } for n, a in data.get('attachments', {}).items()]

        parent_id = doc.parent_id

    as_eml = _as_eml(doc)

    for field in ['date', 'date-created']:
        if data.get(field):
            data[field] = _format_date(data[field])

    return {
        'id': id,
        'parent_id': parent_id,
        'data': data,
        'attachments': attachments,
        'as_eml': as_eml,
    }

def document(request, id):
    embed = request.GET.get('embed') == 'on'
    data = _process_document(id)
    data['embed'] = embed
    return render(request, 'document.html', data)
