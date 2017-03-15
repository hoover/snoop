import json
from pathlib import Path
from dateutil.parser import parse as dateutil_parse
from pprint import pformat
from django.http import HttpResponse, FileResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db.models.expressions import RawSQL
from . import models, html
from .digest import digest
from .walker import files_in
from .emails import open_msg

def json_response(request, data):
    json_dumps_params = {'separators': [',', ':']}
    if 'text/html' in request.META.get('HTTP_ACCEPT', ''):
        json_dumps_params = {
            'separators': [', ', ': '],
            'sort_keys': True,
            'indent': 2,
        }
    return JsonResponse(data, json_dumps_params=json_dumps_params)

def _format_size(num):
    for unit in ['', 'KB', 'MB', 'GB', 'TB']:
        if abs(num) < 1024.0:
            return "%3.1f %s" % (num, unit)
        num /= 1024.0
    return "%3.1f %s" % (num, 'PB')

def _format_date(date_value):
    return dateutil_parse(date_value).strftime("%d %B %Y")

def _find_doc(collection_slug, id):
    return get_object_or_404(
        models.Document,
        id=id,
        collection__slug=collection_slug,
    )

def document_raw(request, collection_slug, id):
    doc = _find_doc(collection_slug, id)
    if doc.content_type == 'text/html':
        return HttpResponse("This file has been stripped " +
                            "of links, images, forms and javascript.\n\n" +
                            html.get_safe_html(doc),
                            content_type='text/plain',
                            charset='UTF-8')
    with doc.open() as f:
        data = f.read()
        return HttpResponse(data, content_type=doc.content_type)

def document_ocr(request, collection_slug, id, tag):
    doc = _find_doc(collection_slug, id)
    ocr = get_object_or_404(
        models.Ocr,
        collection_id=doc.collection.id,
        tag=tag,
        md5=doc.md5
    )
    return FileResponse(
        ocr.absolute_path.open('rb'),
        content_type='application/pdf',
    )

def _as_eml(doc):
    if doc.content_type == 'application/vnd.ms-outlook':
        return str(Path(doc.filename).with_suffix('.eml'))

def document_as_eml(request, collection_slug, id):
    doc = _find_doc(collection_slug, id)
    if not _as_eml(doc):
        return HttpResponseNotFound()
    with open_msg(doc) as f:
        return HttpResponse(f.read(), content_type='message/rfc822')

def _process_document(collection_slug, id, data=None):
    parent_id = None
    children = []

    doc = _find_doc(collection_slug, id)

    try:
        if data is None:
            data = digest(doc)

    except Exception as e:
        error_message = doc.broken
        if not error_message:
            error_message = "{t.__name__} (not marked as broken)".format(t=type(e))
        data = {'type': 'ERROR: ' + error_message}

    else:
        data['size'] = doc.disk_size
        data['content-type'] = doc.content_type

        if data.get('type') in ['folder', 'archive', 'email-archive']:
            data['files'] = files_in(doc)
            for file in data['files']:
                file['size_pretty'] = _format_size(file['size'])

        if data.get('tree'):
            data['tree'] = pformat(data.get('tree'), indent=4, width=120)

        children = [{
            'id': str(child_doc.id),
            'filename': str(child_doc.filename),
            'content_type': child_doc.content_type,
        } for child_doc in doc.child_set.order_by('id')]

        parent_id = doc.parent_id

    as_eml = _as_eml(doc)

    data = _get_index_data_format(data)

    return {
        'id': str(id),
        'parent_id': parent_id,
        'content': data,
        'children': children,
        'as_eml': as_eml,
    }

def _get_index_data_format(digest_data):
    copy_keys = {
        'path',
        'text',
        'subject',
        'date',
        'to',
        'from',
        'sha1',
        'md5',
        'lang',
        'date-created',
        'message-id',
        'in-reply-to',
        'thread-index',
        'references',
        'message',
        'filename',
        'rev',
        'pgp',
        'word-count',
        'content-type',
        'size',
    }

    data = {key: digest_data.get(key) for key in copy_keys}
    data['filetype'] = digest_data.get('type')
    data['attachments'] = bool(digest_data.get('attachments'))
    data['people'] = ' '.join([digest_data.get('from', '')] + digest_data.get('to', []))
    data['ocr'] = bool(digest_data.get('ocr'))
    data['ocrtext'] = digest_data.get('ocr')

    return data

def document_json(request, collection_slug, id):
    return json_response(request, _process_document(collection_slug, id))

def feed(request, collection_slug):
    collection = get_object_or_404(models.Collection, slug=collection_slug)

    query = (
        collection.document_set
        .filter(digested_at__isnull=False)
        .order_by('-digested_at')
    )

    if 'lt' in request.GET:
        try:
            lt = dateutil_parse(request.GET['lt'])
        except ValueError:
            pass
        else:
            query = query.filter(digested_at__lt=lt)

    page_size = settings.SNOOP_FEED_PAGE_SIZE
    page = list(query[:page_size])

    def dump(digest, digested_at):
        digest_data = json.loads(digest.data)
        data = _process_document(collection_slug, digest.id, digest_data)
        version = digested_at.isoformat().replace('+00:00', 'Z')
        data['version'] = version
        return data

    digest_objects = models.Digest.objects.in_bulk([doc.id for doc in page])
    documents = [dump(digest_objects[doc.id], doc.digested_at) for doc in page]
    rv = {'documents': documents}
    if documents:
        last_document = documents[-1]
        rv['next'] = '?lt={}'.format(last_document['version'])
    return json_response(request, rv)

def collection(request, collection_slug):
    collection = get_object_or_404(models.Collection, slug=collection_slug)
    return json_response(request, {
        'name': collection.slug,
        'title': collection.title,
        'feed': 'feed',
        'description': collection.description,
        'data_urls': '{id}/json',
    })
