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
        serializer = PortalSerializer({'nodes': self.get_vertices(),
                                       'edges': self.get_edges()})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_edges(self):
        edges = []
        for e in self.graph.match(rel_type=Edge.TYPE):
            edge = Edge(origin=Vertex(e.start_node()['name']),
                        target=Vertex(e.end_node()['name']))
            if len(edge.load_endpoints()):
                edges.append(edge)
            else:
                edge.delete()
        return edges

    def get_vertices(self):
        vertices = []
        max_depends = 0
        min_depends = 0
        for v in self.graph.find(label=Vertex.LABEL):
            vertex = Vertex(name=v['name'])
            dependents = vertex.dependents_number
            max_depends = max(max_depends, dependents)
            min_depends = min(min_depends, dependents)
            vertices.append(vertex)

        for v in vertices:
            v.calc_vertex_size(min_depends, max_depends, len(vertices))

        return vertices
