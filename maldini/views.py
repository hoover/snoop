from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from .models import Document
from .digest import digest
from .walker import files_in
from dateutil import parser
from pprint import pformat

def _format_date(date_value):
    return parser.parse(date_value).strftime("%Y-%m-%d")

def document_raw(request, id):
    doc = get_object_or_404(Document, id=id)
    with doc.open() as f:
        data = f.read()
        return HttpResponse(data, content_type=doc.content_type)

def document(request, id):
    up = None
    attachments = []

    if id == '0':
        data = {
            'type': 'folder',
            'files': files_in(''),
        }

    else:
        doc = get_object_or_404(Document, id=id)

        try:
            data = digest(doc)

        except:
            data = {'type': '-- ERROR --'}

        else:
            if data.get('type') == 'folder':
                data['files'] = files_in(doc.path + '/')

            def attachment_id(n):
                try:
                    a = doc.document_set.get(path=n)
                except Document.DoesNotExist:
                    return None
                else:
                    return a.id

            if data.get('parts'):
                data['parts'] = pformat(data.get('parts'), indent=4, width=120)

            attachments = [{
                'filename': a['filename'],
                'id': attachment_id(n),
                'content_type': a['content_type'],
            } for n, a in data.get('attachments', {}).items()]

            if doc.container:
                up = doc.container.id
            elif '/' in doc.path:
                up_path = doc.path.rsplit('/', 1)[0]
                up = Document.objects.get(container=None, path=up_path).id
            else:
                up = 0

    for field in ['date', 'date_created']:
        if data.get(field):
            data[field] = _format_date(data[field])

    return render(request, 'document.html', {
        'id': id,
        'up': up,
        'data': data,
        'attachments': attachments,
    })
