from django.contrib import admin
from django.urls import path, include
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('parser/', include('subject_parser.urls')),
]

