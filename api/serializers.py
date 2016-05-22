from rest_framework import serializers

from .models import Edge, Vertex


class EdgeSerializer(serializers.Serializer):
    node_from = serializers.CharField()
    node_to = serializers.CharField()

    def to_representation(self, obj):
        return {
            'from': obj.node_from,
            'to': obj.node_to,
            'usage': self.get_endpoint_usage(obj),
            'id': obj.name,
            'endpoints': self.get_endpoints(obj),
        }

    def get_endpoint_usage(self, obj):
        total = set(obj.target.node['endpoints'])
        partial = set(obj.load_endpoints().keys())
        intersection = total.intersection(partial)
        usage = len(intersection) * 100 / len(total)
        return '{:.1f}%'.format(usage)

    def get_endpoints(self, obj):
        endpoints = obj.load_endpoints()
        return [{'endpoint': e, 'access': endpoints[e]} for e in endpoints]


class VertexSerializer(serializers.Serializer):
    name = serializers.CharField()
    endpoints = serializers.ListField(child=serializers.CharField())

    def to_representation(self, obj):
        return {
            'id': obj.name,
            'label': obj.name,
            'endpoints': obj.endpoints,
            'value': obj.vertex_size,
        }


class PortalSerializer(serializers.Serializer):
    nodes = serializers.ListField(child=VertexSerializer())
    edges = serializers.ListField(child=EdgeSerializer())


class MicrodotSerializer(serializers.Serializer):
    origin = serializers.CharField()
    target = serializers.CharField()
    method = serializers.CharField()
    endpoint = serializers.CharField()

    def save(self):
        endpoint = '{method} {uri}'.format(method=self.validated_data['method'],
                                           uri=self.validated_data['endpoint'])
        origin = Vertex(self.validated_data['origin'])
        origin.save()
        target = Vertex(self.validated_data['target'], endpoint)
        target.save()
        Edge(origin, target, endpoint).save()
