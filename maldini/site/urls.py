from django.conf.urls import url
from django.contrib import admin
from .. import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^doc/(?P<id>\d+)$', views.document),
    url(r'^doc/(?P<id>\d+)/raw/.*$', views.document_raw),
    url(r'^doc/(?P<id>\d+)/ocr/(?P<tag>[^/]+)/.*$', views.document_ocr),
]
