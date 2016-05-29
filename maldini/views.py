from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from .models import Document
from .digest import files_in, digest, open_document

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
        if request.GET.get('raw') == 'on':
            with open_document(doc) as f:
                data = f.read()
                return HttpResponse(data, content_type=doc.content_type)

        try:
            data = digest(doc)

        except:
            data = {'type': '-- ERROR --'}

        else:
            if data.get('type') == 'folder':
                data['files'] = files_in(doc.path + '/')

            attachments = [{
                'filename': a['filename'],
                'id': doc.document_set.get(path=n).id,
                'content_type': a['content_type'],
            } for n, a in data.get('attachments', {}).items()]

            if doc.container:
                up = doc.container.id
            elif '/' in doc.path:
                up_path = doc.path.rsplit('/', 1)[0]
                up = Document.objects.get(container=None, path=up_path).id
            else:
                up = 0

    return render(request, 'document.html', {
        'up': up,
        'data': data,
        'attachments': attachments,
    })
