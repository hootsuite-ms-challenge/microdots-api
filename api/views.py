from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Edge, Vertex
from .serializers import MicrodotSerializer, PortalSerializer


class MicrodotView(APIView):
    def post(self, request):
        serializer = MicrodotSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response('ok', status=status.HTTP_201_CREATED)


class GraphView(APIView):
    graph = settings.GRAPH

    def get(self, request):
        serializer = PortalSerializer({'nodes': self.get_vertexes(),
                                       'edges': self.get_edges()})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_edges(self):
        edges = []
        for e in self.graph.match(rel_type=Edge.TYPE):
            edge = Edge(origin=Vertex(e.start_node()['name']),
                        target=Vertex(e.end_node()['name']))
            if len(edge.load_endpoints().keys()):
                edges.append(edge)
        return edges

    def get_vertexes(self):
        vertexes = []
        for v in self.graph.find(label=Vertex.LABEL):
            vertex = Vertex(name=v['name'])
            vertexes.append(vertex)

        return vertexes
