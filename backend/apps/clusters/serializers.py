from rest_framework import serializers
from .models import Cluster, ClusterConnection


class ClusterSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source='created_by.username', read_only=True
    )

    class Meta:
        model = Cluster
        fields = [
            'id', 'name', 'description', 'is_active',
            'created_at', 'updated_at', 'created_by_username'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by_username']


class ClusterCreateSerializer(serializers.ModelSerializer):
    kubeconfig = serializers.CharField(write_only=True)

    class Meta:
        model = Cluster
        fields = ['id', 'name', 'description', 'kubeconfig', 'is_active']

    def create(self, validated_data):
        kubeconfig = validated_data.pop('kubeconfig')
        cluster = Cluster(**validated_data)
        cluster.set_kubeconfig(kubeconfig)
        cluster.save()
        return cluster

    def update(self, instance, validated_data):
        kubeconfig = validated_data.pop('kubeconfig', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if kubeconfig:
            instance.set_kubeconfig(kubeconfig)
        instance.save()
        return instance


class ClusterConnectionSerializer(serializers.ModelSerializer):
    cluster_name = serializers.CharField(source='cluster.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ClusterConnection
        fields = [
            'id', 'cluster', 'cluster_name', 'user', 'username',
            'connected_at', 'status', 'error_message'
        ]


class ClusterStatusSerializer(serializers.Serializer):
    cluster_id = serializers.IntegerField()
    cluster_name = serializers.CharField()
    is_connected = serializers.BooleanField()
    version = serializers.CharField(allow_null=True)
    nodes_count = serializers.IntegerField(allow_null=True)
    error = serializers.CharField(allow_null=True)
