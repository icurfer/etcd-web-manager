from rest_framework import serializers


class KeyListRequestSerializer(serializers.Serializer):
    prefix = serializers.CharField(default='/', required=False)
    keys_only = serializers.BooleanField(default=True, required=False)
    limit = serializers.IntegerField(default=100, min_value=1, max_value=1000, required=False)


class KeyValueSerializer(serializers.Serializer):
    key = serializers.CharField()
    value = serializers.CharField(required=False, allow_blank=True)


class KeyDeleteSerializer(serializers.Serializer):
    key = serializers.CharField()
    prefix = serializers.BooleanField(default=False, required=False)


class EtcdResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    data = serializers.CharField(required=False, allow_null=True)
    error = serializers.CharField(required=False, allow_null=True)
    keys = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    count = serializers.IntegerField(required=False)


class TreeNodeSerializer(serializers.Serializer):
    key = serializers.CharField()
    name = serializers.CharField()
    is_dir = serializers.BooleanField()
    children = serializers.ListField(required=False)
