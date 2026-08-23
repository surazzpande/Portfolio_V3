from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from portfolio import views

urlpatterns = [
    path("", views.home, name="home"),
    path("contact/", views.contact, name="contact"),
    path("writing/", views.post_list, name="post_list"),
    path("writing/<slug:slug>/", views.post_detail, name="post_detail"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
