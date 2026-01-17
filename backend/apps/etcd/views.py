from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from apps.clusters.models import Cluster
from .services import EtcdService
from .serializers import (
    KeyListRequestSerializer,
    KeyValueSerializer,
    KeyDeleteSerializer
)


class BaseEtcdView(APIView):
    permission_classes = [IsAuthenticated]

    def get_etcd_service(self, cluster_id: int) -> EtcdService:
        cluster = get_object_or_404(Cluster, pk=cluster_id, is_active=True)
        return EtcdService(cluster)


class KeyListView(BaseEtcdView):
    """키 목록 조회"""

    def get(self, request, cluster_id):
        serializer = KeyListRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            service = self.get_etcd_service(cluster_id)
            result = service.get_keys(**serializer.validated_data)
            return Response(result)
        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KeyTreeView(BaseEtcdView):
    """트리 구조로 키 조회"""

    def get(self, request, cluster_id):
        prefix = request.query_params.get('prefix', '/')
        limit = int(request.query_params.get('limit', 500))

        try:
            service = self.get_etcd_service(cluster_id)
            result = service.get_keys(prefix=prefix, keys_only=True, limit=limit)

            if not result['success']:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

            tree = self._build_tree(result.get('keys', []))
            return Response({
                'success': True,
                'tree': tree,
                'count': result.get('count', 0)
            })
        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _build_tree(self, keys: list) -> list:
        """키 목록을 트리 구조로 변환"""
        root = {'children': {}}

        for key in keys:
            parts = key.strip('/').split('/')
            current = root

            for i, part in enumerate(parts):
                if not part:
                    continue

                if part not in current['children']:
                    current['children'][part] = {
                        'name': part,
                        'key': '/' + '/'.join(parts[:i+1]),
                        'is_dir': i < len(parts) - 1,
                        'children': {}
                    }
                current = current['children'][part]

        return self._dict_to_list(root['children'])

    def _dict_to_list(self, node: dict) -> list:
        """딕셔너리 트리를 리스트 형태로 변환"""
        result = []
        for key, value in sorted(node.items()):
            item = {
                'name': value['name'],
                'key': value['key'],
                'is_dir': bool(value['children'])
            }
            if value['children']:
                item['children'] = self._dict_to_list(value['children'])
            result.append(item)
        return result


class KeyValueView(BaseEtcdView):
    """키-값 조회/저장"""

    def get(self, request, cluster_id):
        key = request.query_params.get('key')
        if not key:
            return Response(
                {'success': False, 'error': 'Key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = self.get_etcd_service(cluster_id)
            result = service.get_value(key)
            return Response(result)
        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, cluster_id):
        serializer = KeyValueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            service = self.get_etcd_service(cluster_id)
            result = service.put_value(
                serializer.validated_data['key'],
                serializer.validated_data.get('value', '')
            )
            return Response(result)
        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, cluster_id):
        serializer = KeyDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            service = self.get_etcd_service(cluster_id)
            result = service.delete_key(
                serializer.validated_data['key'],
                prefix=serializer.validated_data.get('prefix', False)
            )
            return Response(result)
        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClusterHealthView(BaseEtcdView):
    """etcd 클러스터 상태"""

    def get(self, request, cluster_id):
        try:
            service = self.get_etcd_service(cluster_id)
            health = service.get_cluster_health()
            cluster_status = service.get_cluster_status()
            members = service.get_members()

            return Response({
                'success': True,
                'health': health.get('health'),
                'status': cluster_status.get('status'),
                'members': members.get('members')
            })
        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
