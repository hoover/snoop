from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Document
from .prepare import extract

def text(request, id):
    doc = get_object_or_404(Document, id=id)
    data = extract(doc)
    return HttpResponse(
        data.get('text', '-- no text --'),
        content_type='text/plain',
    )
