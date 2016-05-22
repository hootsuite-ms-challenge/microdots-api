from collections import Counter
import re

from py2neo import Node, Relationship

from django.conf import settings


class BaseGraph(object):
    backend = settings.PERSISTENT_BACKEND
    graph = settings.GRAPH

    def format_endpoint(self, endpoint):
        endpoint = re.sub(r'/\d', '/{id}', endpoint)
        return re.sub(r'\?.*', '', endpoint)


class Vertex(BaseGraph):
    LABEL = 'Microdot'

    def __init__(self, name, endpoint=None):
        self.endpoints = None
        self.name = name
        self.node = self.instantiate_node(name)
        if endpoint:
            self.endpoints.add(self.format_endpoint(endpoint))

    def instantiate_node(self, name):
        node = self.graph.find_one(self.LABEL, property_key='name', property_value=name)
        if not node:
            node = Node(self.LABEL, name=name)
        self.name = node['name']

        self.endpoints = node['endpoints']
        if self.endpoints:
            self.endpoints = set(self.endpoints)
        else:
            self.endpoints = set()

        return node

    def save(self):
        self.node['endpoints'] = list(self.endpoints)
        if self.graph.exists(self.node):
            self.graph.push(self.node)
        else:
            self.graph.create(self.node)


class Edge(BaseGraph):
    TYPE = 'Depends'

    def __init__(self, origin, target, endpoint=None):
        self.origin = origin
        self.target = target
        self.relationship = self.instantiate_relationship(origin.node, target.node)
        if endpoint:
            self.endpoint = endpoint

    def instantiate_relationship(self, origin_node, target_node):
        relationship = self.graph.match_one(start_node=origin_node, rel_type=self.TYPE, end_node=target_node)
        if relationship is None:
            name = origin_node['name'] + '-' +  target_node['name']
            relationship = Relationship(origin_node, self.TYPE, target_node, name=name)
        return relationship

    def load_endpoints(self):
        endpoints = self.backend.load_endpoints(self.name)
        return Counter(endpoints)

    @property
    def name(self):
        return self.relationship.__name__

    @property
    def node_from(self):
        return self.origin.name

    @property
    def node_to(self):
        return self.target.name

    def save_endpoint(self, endpoint):
        endpoint = self.format_endpoint(endpoint)
        self.backend.save_endpoint(self.name, endpoint)

    def save(self):
        if self.graph.exists(self.relationship):
            self.graph.push(self.relationship)
        else:
            self.graph.create(self.relationship)

        if self.endpoint:
            self.save_endpoint(self.endpoint)
