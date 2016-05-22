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
        vertex = Vertex('name', '/usr/test')
        self.assertIsInstance(vertex, Vertex)

    def test_save_vertex(self):
        vertex = Vertex('name', '/usr/test')
        vertex.save()
        self.assertTrue(self.graph.exists(vertex.node))

    def test_vertex_got_endpoint(self):
        vertex = Vertex('name', '/usr/test')
        vertex.save()
        self.assertEqual(
            vertex.node['endpoints'][0],
            '/usr/test'
        )

    def test_multiple_endpoints(self):
        vertex = Vertex('name', '/usr/test')
        vertex.save()
        vertex = Vertex('name', '/usr/test2')
        vertex.save()
        self.assertEqual(len(vertex.node['endpoints']), 2)

    def test_vertex_without_endpoint(self):
        vertex = Vertex('name')
        vertex.save()
        self.assertTrue(self.graph.exists(vertex.node))

    def test_vertex_without_name(self):
        with self.assertRaises(TypeError):
            Vertex()


class BaseEdgeTestCase(GraphTestCase):
    def setUp(self):
        super().setUp()
        self.origin = Vertex('origin')
        self.origin.save()
        self.target = Vertex('target', '/usr/test2')
        self.target.save()
        self.backend = settings.PERSISTENT_BACKEND

    def tearDown(self):
        self.backend.flush_db()


class EdgeTestCase(BaseEdgeTestCase):
    def test_create_edge(self):
        edge = Edge(self.origin, self.target, 'GET /test/')
        self.assertIsInstance(edge, Edge)

    def test_create_edge_twice(self):
        edge = Edge(self.origin, self.target, 'GET /test/')
        edge2 = Edge(self.origin, self.target, 'GET /test/')
        self.assertEqual(edge.name, edge2.name)

    def test_format_endpoint(self):
        endpoint = 'GET /test/3'
        edge = Edge(self.origin, self.target, endpoint)
        self.assertEqual('GET /test/{id}', edge.format_endpoint(endpoint))

    def test_format_endpoint_ending_in_slash(self):
        endpoint = 'GET /test/3/'
        edge = Edge(self.origin, self.target, endpoint)
        self.assertEqual('GET /test/{id}/', edge.format_endpoint(endpoint))

    def test_format_endpoint_with_action(self):
        endpoint = 'GET /test/3/action'
        edge = Edge(self.origin, self.target, endpoint)
        self.assertEqual('GET /test/{id}/action', edge.format_endpoint(endpoint))

    def test_format_endpoint_with_querystring(self):
        endpoint = 'GET /test/3?name=user'
        edge = Edge(self.origin, self.target, endpoint)
        self.assertEqual('GET /test/{id}', edge.format_endpoint(endpoint))

    def test_request_count(self):
        endpoint = 'GET /test/3'
        Edge(self.origin, self.target, endpoint)
        Edge(self.origin, self.target, endpoint)
        edge = Edge(self.origin, self.target, endpoint)
        endpoints = edge.load_endpoints()
        self.assertEqual(endpoints['GET /test/{id}'], 3)

    def test_request_count_with_multiple_endpoints(self):
        Edge(self.origin, self.target, 'GET /test/3/')
        Edge(self.origin, self.target, 'GET /test/3/')
        Edge(self.origin, self.target, 'GET /test/')
        Edge(self.origin, self.target, 'GET /test/')
        edge = Edge(self.origin, self.target, 'GET /test/3/')
        endpoints = edge.load_endpoints()
        self.assertEqual(endpoints['GET /test/{id}/'], 3)
        self.assertEqual(endpoints['GET /test/'], 2)


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


class RedisBackendTestCase(BaseEdgeTestCase):
    def test_load_endpoints(self):
        test_endpoint = 'GET /test/'
        self.edge = Edge(self.origin, self.target, test_endpoint)
        endpoints = self.edge.load_endpoints()
        self.assertIn(test_endpoint, endpoints)

    def test_load_multiple_endpoints(self):
        Edge(self.origin, self.target, 'GET /test/')
        self.edge = Edge(self.origin, self.target, 'GET /test/2')
        endpoints = self.edge.load_endpoints()
        self.assertEqual(len(endpoints), 2)
