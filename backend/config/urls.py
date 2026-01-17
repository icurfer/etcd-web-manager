from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/clusters/', include('apps.clusters.urls')),
    path('api/etcd/', include('apps.etcd.urls')),
    path('api/auth/', include('apps.clusters.auth_urls')),
]
