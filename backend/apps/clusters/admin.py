from django.contrib import admin
from .models import Cluster, ClusterConnection


@admin.register(Cluster)
class ClusterAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at', 'created_by']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']


@admin.register(ClusterConnection)
class ClusterConnectionAdmin(admin.ModelAdmin):
    list_display = ['cluster', 'user', 'status', 'connected_at']
    list_filter = ['status', 'connected_at']
