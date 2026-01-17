from django.urls import path
from .views import (
    KeyListView,
    KeyTreeView,
    KeyValueView,
    ClusterHealthView
)

urlpatterns = [
    path('<int:cluster_id>/keys/', KeyListView.as_view(), name='etcd-keys'),
    path('<int:cluster_id>/tree/', KeyTreeView.as_view(), name='etcd-tree'),
    path('<int:cluster_id>/kv/', KeyValueView.as_view(), name='etcd-kv'),
    path('<int:cluster_id>/health/', ClusterHealthView.as_view(), name='etcd-health'),
]
