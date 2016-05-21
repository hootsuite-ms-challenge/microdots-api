from rest_framework import serializers

from django.conf import settings

from .models import Edge, Vertex


class EdgeSerializer(serializers.Serializer):
    node_from = serializers.CharField()
    node_to = serializers.CharField()

    def to_representation(self, obj):
        return {
            'from': obj.node_from,
            'to': obj.node_to
        }


class VertexSerializer(serializers.Serializer):
    name = serializers.CharField()
    endpoints = serializers.ListField(child=serializers.CharField())
    uuid = serializers.CharField()

    def to_representation(self, obj):
        return {
            'id': obj.uuid,
            'label': obj.name,
            'endpoints': obj.endpoints,
        }


class PortalSerializer(serializers.Serializer):
    nodes = serializers.ListField(child=VertexSerializer())
    edges = serializers.ListField(child=EdgeSerializer())
