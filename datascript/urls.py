from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.Home.as_view(), name='home'),
    path('paul-chopra-upload/', views.paul_chopra_upload, name='paul chopra upload'),
    path('steve-ginsberg-upload/', views.steve_ginsberg_upload, name= 'steve ginsberg upload'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)