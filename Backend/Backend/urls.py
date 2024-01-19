from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from api import urls as api_urls
from chat import urls as chat_urls


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_urls)),
    path('chat/', include(chat_urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
