from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from .models import Document
from .prepare import extract

def document(request, id):
    doc = get_object_or_404(Document, id=id)
    data = extract(doc)
    return render(request, 'document.html', {
        'data': data,
    })
