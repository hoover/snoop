from django.conf.urls import url
from django.contrib import admin
from .. import views

urlpatterns = [
    url(r'^(?P<collection_slug>[\w-]+)/json$', views.collection),
    url(r'^(?P<collection_slug>[\w-]+)/feed$', views.feed),
    url(r'^(?P<collection_slug>[\w-]+)/(?P<id>\d+)$', views.document),
    url(r'^(?P<collection_slug>[\w-]+)/(?P<id>\d+)/json$', views.document_json),
    url(r'^(?s)(?P<collection_slug>[\w-]+)/(?P<id>\d+)/raw/.*$', views.document_raw),
    url(r'^(?P<collection_slug>[\w-]+)/(?P<id>\d+)/ocr/(?P<tag>[^/]+)/.*$', views.document_ocr),
    url(r'^(?s)(?P<collection_slug>[\w-]+)/(?P<id>\d+)/eml/.*$', views.document_as_eml),
]
