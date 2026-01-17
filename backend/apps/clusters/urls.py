from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClusterViewSet, ClusterConnectionViewSet

router = DefaultRouter()
router.register(r'', ClusterViewSet, basename='cluster')
router.register(r'connections', ClusterConnectionViewSet, basename='connection')

urlpatterns = [
    path('', include(router.urls)),
]
