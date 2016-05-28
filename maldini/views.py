from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from .models import Document
from .digest import digest

def document(request, id):
    doc = get_object_or_404(Document, id=id)
    data = digest(doc)

    attachments = [{
        'filename': a['filename'],
        'id': doc.document_set.get(path=n).id,
        'content_type': a['content_type'],
    } for n, a in data.get('attachments', {}).items()]

    return render(request, 'document.html', {
        'data': data,
        'attachments': attachments,
    })
