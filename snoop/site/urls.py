from django.conf.urls import url
from django.contrib import admin
from .. import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^doc/(?P<id>\d+)$', views.document),
    url(r'^doc/(?P<id>\d+).json$', views.document_json),
    url(r'^(?s)doc/(?P<id>\d+)/raw/.*$', views.document_raw),
    url(r'^doc/(?P<id>\d+)/ocr/(?P<tag>[^/]+)/.*$', views.document_ocr),
    url(r'^(?s)doc/(?P<id>\d+)/eml/.*$', views.document_as_eml),
]
