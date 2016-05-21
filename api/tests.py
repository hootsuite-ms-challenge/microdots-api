from unittest import TestCase

from django.conf import settings
from rest_framework.test import APIClient
from .models import Edge, Vertex


class GraphTestCase(TestCase):
    def setUp(self):
        self.graph = settings.GRAPH

    def tearDown(self):
        self.graph.delete_all()


class VertexTestCase(GraphTestCase):
    def test_create_vertex(self):
        vertex = Vertex('nome', '/usr/test')
        self.assertIsInstance(vertex, Vertex)

    def test_save_vertex(self):
        vertex = Vertex('nome', '/usr/test')
        vertex.save()
        self.assertTrue(self.graph.exists(vertex.node))

    def test_vertex_got_endpoint(self):
        vertex = Vertex('nome', '/usr/test')
        vertex.save()
        self.assertEqual(
            vertex.node['endpoints'][0],
            '/usr/test'
        )

    def test_multiple_endpoints(self):
        vertex = Vertex('nome', '/usr/test')
        vertex.save()
        vertex = Vertex('nome', '/usr/test2')
        vertex.save()
        self.assertEqual(len(vertex.node['endpoints']), 2)

    def test_vertex_without_endpoint(self):
        vertex = Vertex('nome')
        vertex.save()
        self.assertTrue(self.graph.exists(vertex.node))

    def test_vertex_without_name(self):
        with self.assertRaises(AttributeError):
            Vertex()


class EdgeTestCase(GraphTestCase):
    def setUp(self):
        super().setUp()

        self.origin = Vertex('origin')
        self.origin.save()
        self.target = Vertex('target', '/usr/test2')
        self.target.save()

    def test_create_edge(self):
        edge = Edge(self.origin, self.target, 'GET /test/')
        self.assertIsInstance(edge, Edge)


class ApiTestCase(GraphTestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.data = {
            'origin': 'origin-requester',
            'target': 'target-requester',
            'method': 'get',
            'endpoint': '/api/test/'
        }

    def test_post_microdot_response(self):
        request = self.client.post('/microdot/', self.data)
        self.assertEqual(201, request.status_code)
