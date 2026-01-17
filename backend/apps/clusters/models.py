from django.db import models
from django.contrib.auth.models import User
from cryptography.fernet import Fernet
from django.conf import settings
import base64
import os


class Cluster(models.Model):
    """Kubernetes 클러스터 정보"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    kubeconfig_encrypted = models.BinaryField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='clusters'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @staticmethod
    def get_encryption_key():
        key = settings.ENCRYPTION_KEY
        if not key:
            key = os.getenv('ENCRYPTION_KEY', Fernet.generate_key().decode())
        if isinstance(key, str):
            key = key.encode()
        if len(key) != 44:
            key = base64.urlsafe_b64encode(key.ljust(32)[:32])
        return key

    def set_kubeconfig(self, kubeconfig_content: str):
        """kubeconfig 내용을 암호화하여 저장"""
        fernet = Fernet(self.get_encryption_key())
        self.kubeconfig_encrypted = fernet.encrypt(kubeconfig_content.encode())

    def get_kubeconfig(self) -> str:
        """암호화된 kubeconfig를 복호화하여 반환"""
        fernet = Fernet(self.get_encryption_key())
        return fernet.decrypt(self.kubeconfig_encrypted).decode()


class ClusterConnection(models.Model):
    """클러스터 연결 로그"""
    cluster = models.ForeignKey(
        Cluster, on_delete=models.CASCADE, related_name='connections'
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )
    connected_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failed', 'Failed'),
    ])
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-connected_at']
