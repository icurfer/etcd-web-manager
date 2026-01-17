import tempfile
import os
import subprocess
import json
from typing import Optional, List, Dict, Any
from kubernetes import client, config
from apps.clusters.models import Cluster


class EtcdService:
    """K8s API를 통한 etcd 접근 서비스"""

    def __init__(self, cluster: Cluster):
        self.cluster = cluster
        self._setup_k8s_client()

    def _setup_k8s_client(self):
        """K8s 클라이언트 설정"""
        kubeconfig_content = self.cluster.get_kubeconfig()

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        ) as f:
            f.write(kubeconfig_content)
            self.kubeconfig_path = f.name

        config.load_kube_config(config_file=self.kubeconfig_path)
        self.core_api = client.CoreV1Api()

    def _cleanup(self):
        """임시 파일 정리"""
        if hasattr(self, 'kubeconfig_path') and os.path.exists(self.kubeconfig_path):
            os.unlink(self.kubeconfig_path)

    def _exec_etcdctl(
        self,
        command: List[str],
        namespace: str = 'kube-system',
        pod_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """etcd pod에서 etcdctl 명령 실행"""
        try:
            if not pod_name:
                pod_name = self._find_etcd_pod(namespace)

            etcdctl_cmd = [
                'etcdctl',
                '--endpoints=https://127.0.0.1:2379',
                '--cacert=/etc/kubernetes/pki/etcd/ca.crt',
                '--cert=/etc/kubernetes/pki/etcd/server.crt',
                '--key=/etc/kubernetes/pki/etcd/server.key',
            ] + command

            exec_command = [
                'kubectl',
                '--kubeconfig', self.kubeconfig_path,
                'exec', '-n', namespace, pod_name, '--',
            ] + etcdctl_cmd

            result = subprocess.run(
                exec_command,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return {
                    'success': False,
                    'error': result.stderr or 'Command failed'
                }

            return {
                'success': True,
                'data': result.stdout
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Command timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _find_etcd_pod(self, namespace: str = 'kube-system') -> str:
        """etcd pod 찾기"""
        pods = self.core_api.list_namespaced_pod(
            namespace=namespace,
            label_selector='component=etcd'
        )

        if not pods.items:
            pods = self.core_api.list_namespaced_pod(
                namespace=namespace,
                label_selector='tier=control-plane'
            )
            for pod in pods.items:
                if 'etcd' in pod.metadata.name:
                    return pod.metadata.name

            raise Exception('No etcd pod found')

        return pods.items[0].metadata.name

    def get_keys(
        self,
        prefix: str = '/',
        keys_only: bool = True,
        limit: int = 100
    ) -> Dict[str, Any]:
        """키 목록 조회"""
        cmd = ['get', prefix, '--prefix']

        if keys_only:
            cmd.append('--keys-only')

        cmd.extend(['--limit', str(limit)])

        result = self._exec_etcdctl(cmd)

        if result['success']:
            lines = result['data'].strip().split('\n')
            keys = [line for line in lines if line]
            result['keys'] = keys
            result['count'] = len(keys)

        return result

    def get_value(self, key: str) -> Dict[str, Any]:
        """특정 키의 값 조회"""
        cmd = ['get', key, '--print-value-only']
        result = self._exec_etcdctl(cmd)

        if result['success']:
            result['key'] = key
            result['value'] = result['data']

        return result

    def put_value(self, key: str, value: str) -> Dict[str, Any]:
        """키-값 저장"""
        cmd = ['put', key, value]
        return self._exec_etcdctl(cmd)

    def delete_key(self, key: str, prefix: bool = False) -> Dict[str, Any]:
        """키 삭제"""
        cmd = ['del', key]
        if prefix:
            cmd.append('--prefix')
        return self._exec_etcdctl(cmd)

    def get_cluster_health(self) -> Dict[str, Any]:
        """etcd 클러스터 상태 확인"""
        cmd = ['endpoint', 'health', '--write-out=json']
        result = self._exec_etcdctl(cmd)

        if result['success']:
            try:
                result['health'] = json.loads(result['data'])
            except json.JSONDecodeError:
                result['health'] = result['data']

        return result

    def get_cluster_status(self) -> Dict[str, Any]:
        """etcd 클러스터 상태 상세"""
        cmd = ['endpoint', 'status', '--write-out=json']
        result = self._exec_etcdctl(cmd)

        if result['success']:
            try:
                result['status'] = json.loads(result['data'])
            except json.JSONDecodeError:
                result['status'] = result['data']

        return result

    def get_members(self) -> Dict[str, Any]:
        """etcd 클러스터 멤버 조회"""
        cmd = ['member', 'list', '--write-out=json']
        result = self._exec_etcdctl(cmd)

        if result['success']:
            try:
                result['members'] = json.loads(result['data'])
            except json.JSONDecodeError:
                result['members'] = result['data']

        return result

    def __del__(self):
        self._cleanup()
