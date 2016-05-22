import json
from unittest import TestCase

from django.conf import settings
from rest_framework.test import APIClient
from .models import Edge, Vertex


class GraphTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.graph = settings.GRAPH
        self.backend = settings.PERSISTENT_BACKEND

    def tearDown(self):
        super().tearDown()
        self.graph.delete_all()
        self.backend.flush_db()


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

    def test_get_number_of_dependents(self):
        origin_one = Vertex('foo')
        origin_one.save()
        origin_two = Vertex('bar')
        origin_two.save()
        target = Vertex('foobar')
        target.save()
        Edge(origin_one, target, 'GET /test/').save()
        Edge(origin_two, target, 'GET /test/2').save()
        self.assertEqual(2, target.dependents_number)

    def test_get_number_of_zero_dependents(self):
        target = Vertex('foobar')
        target.save()
        self.assertEqual(0, target.dependents_number)

    def test_get_vertex_maximum_size(self):
        vertex = Vertex('name')
        vertex.save()
        vertex.dependents = range(16)
        self.assertEqual(settings.NODE_SIZE[1], vertex.calc_vertex_size(4, 16, 400))

    def test_get_vertex_minimum_size(self):
        vertex = Vertex('name')
        vertex.save()
        vertex.dependents = [1]
        self.assertEqual(settings.NODE_SIZE[0], vertex.calc_vertex_size(1, 15, 400))


class BaseEdgeTestCase(GraphTestCase):
    def setUp(self):
        super().setUp()
        self.origin = Vertex('origin')
        self.origin.save()
        self.target = Vertex('target', '/usr/test2')
        self.target.save()


class EdgeTestCase(BaseEdgeTestCase):
    def test_create_edge(self):
        edge = Edge(self.origin, self.target, 'GET /test/')
        self.assertIsInstance(edge, Edge)

    def test_create_edge_twice(self):
        edge = Edge(self.origin, self.target, 'GET /test/')
        edge.save()
        edge2 = Edge(self.origin, self.target, 'GET /test/')
        edge2.save()
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
        Edge(self.origin, self.target, endpoint).save()
        Edge(self.origin, self.target, endpoint).save()
        edge = Edge(self.origin, self.target, endpoint)
        edge.save()
        endpoints = edge.load_endpoints()
        self.assertEqual(endpoints['GET /test/{id}'], 3)

    def test_request_count_with_multiple_endpoints(self):
        Edge(self.origin, self.target, 'GET /test/3/').save()
        Edge(self.origin, self.target, 'GET /test/').save()
        Edge(self.origin, self.target, 'GET /test/3/').save()
        Edge(self.origin, self.target, 'GET /test/').save()
        edge = Edge(self.origin, self.target, 'GET /test/3/')
        edge.save()
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

    def test_get_graph_json(self):
        origin = Vertex('origin')
        origin.save()
        target = Vertex('target', 'GET /test/3/')
        target.save()
        edge = Edge(origin, target, 'GET /test/3/')
        edge.save()
        request = self.client.get('/graph/')
        self.assertEqual(200, request.status_code)

    def test_get_graph_json_partial_usage(self):
        origin = Vertex('origin')
        origin.save()
        target = Vertex('target', 'GET /test/3/')
        target.save()
        Vertex('target', 'GET /foo/bar/').save()
        edge = Edge(origin, target, 'GET /test/3/')
        edge.save()
        request = self.client.get('/graph/')
        content = json.loads(request.content.decode('utf-8'))
        self.assertEqual('50.0%', content['edges'][0]['label'])

    def test_get_graph_json_without_redis_endpoint(self):
        origin = Vertex('origin')
        origin.save()
        target = Vertex('target', 'GET /test/3/')
        target.save()
        edge = Edge(origin, target, 'GET /test/3/')
        edge.save()
        backend = settings.PERSISTENT_BACKEND
        backend.flush_db()

        request = self.client.get('/graph/')
        content = json.loads(request.content.decode('utf-8'))
        self.assertFalse(content['edges'])


class RedisBackendTestCase(BaseEdgeTestCase):
    def test_load_endpoints(self):
        test_endpoint = 'GET /test/'
        self.edge = Edge(self.origin, self.target, test_endpoint)
        self.edge.save()
        endpoints = self.edge.load_endpoints()
        self.assertIn(test_endpoint, endpoints)

    def test_load_multiple_endpoints(self):
        Edge(self.origin, self.target, 'GET /test/').save()
        self.edge = Edge(self.origin, self.target, 'GET /test/2')
        self.edge.save()
        endpoints = self.edge.load_endpoints()
        self.assertEqual(len(endpoints), 2)
