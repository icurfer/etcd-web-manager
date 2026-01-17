from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from kubernetes import client, config
import tempfile
import os
import yaml

from .models import Cluster, ClusterConnection
from .serializers import (
    ClusterSerializer,
    ClusterCreateSerializer,
    ClusterConnectionSerializer,
    ClusterStatusSerializer
)


class ClusterViewSet(viewsets.ModelViewSet):
    queryset = Cluster.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ClusterCreateSerializer
        return ClusterSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """클러스터 연결 상태 확인"""
        cluster = self.get_object()
        result = {
            'cluster_id': cluster.id,
            'cluster_name': cluster.name,
            'is_connected': False,
            'version': None,
            'nodes_count': None,
            'error': None
        }

        try:
            k8s_client = self._get_k8s_client(cluster)
            version_api = client.VersionApi(k8s_client)
            version = version_api.get_code()
            result['version'] = version.git_version

            core_api = client.CoreV1Api(k8s_client)
            nodes = core_api.list_node()
            result['nodes_count'] = len(nodes.items)
            result['is_connected'] = True

            ClusterConnection.objects.create(
                cluster=cluster,
                user=request.user,
                status='success'
            )
        except Exception as e:
            result['error'] = str(e)
            ClusterConnection.objects.create(
                cluster=cluster,
                user=request.user,
                status='failed',
                error_message=str(e)
            )

        serializer = ClusterStatusSerializer(result)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """연결 테스트"""
        cluster = self.get_object()
        try:
            k8s_client = self._get_k8s_client(cluster)
            version_api = client.VersionApi(k8s_client)
            version = version_api.get_code()
            return Response({
                'success': True,
                'message': f'Connected successfully. K8s version: {version.git_version}'
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def validate_kubeconfig(self, request):
        """kubeconfig 유효성 검사"""
        kubeconfig_content = request.data.get('kubeconfig', '')
        try:
            yaml.safe_load(kubeconfig_content)
            return Response({'valid': True, 'message': 'Valid kubeconfig format'})
        except yaml.YAMLError as e:
            return Response({
                'valid': False,
                'message': f'Invalid YAML format: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    def _get_k8s_client(self, cluster: Cluster):
        """클러스터의 kubeconfig로 K8s 클라이언트 생성"""
        kubeconfig_content = cluster.get_kubeconfig()

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        ) as f:
            f.write(kubeconfig_content)
            temp_path = f.name

        try:
            config.load_kube_config(config_file=temp_path)
            return client.ApiClient()
        finally:
            os.unlink(temp_path)


class ClusterConnectionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ClusterConnectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ClusterConnection.objects.all()
        cluster_id = self.request.query_params.get('cluster_id')
        if cluster_id:
            queryset = queryset.filter(cluster_id=cluster_id)
        return queryset[:100]
