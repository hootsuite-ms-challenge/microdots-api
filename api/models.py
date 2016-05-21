import re

from py2neo import Node, Relationship

from django.conf import settings


class BaseGraph(object):
    graph = settings.GRAPH


class Vertex(BaseGraph):
    LABEL = 'Microdot'

    def __init__(self, name=None, endpoint=None):
        self.endpoints = None
        self.uuid = None
        self.name = name
        self.node = self.instantiate_node(name)
        if endpoint:
            self.endpoints.add(endpoint)

    def instantiate_node(self, name):
        node = self.graph.find_one(self.LABEL, property_key='name', property_value=name)
        if not node:
            node = Node(self.LABEL, name=name)
        self.uuid = node.__name__

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

    def __init__(self, origin, target, endpoint):
        self.origin = origin
        self.target = target
        self.relationship = self.instantiate_relationship(origin, target)
        self.add_endpoint(endpoint)

    def instantiate_relationship(self, origin, target):
        relationship = self.graph.match(start_node=origin, rel_type=self.TYPE, end_node=target.node)
        if not relationship:
            relationship = Relationship(origin.node, self.TYPE, target.node)
        self.uuid = relationship.__name__
        return relationship

    def format_endpoint(self, endpoint):
        endpoint = re.sub(r'/\d', '/{id}', endpoint)
        return re.sub(r'\?.*', '', endpoint)

    @property
    def node_from(self):
        return self.origin.node.__name__

    @property
    def node_to(self):
        return self.target.node.__name__

    def add_endpoint(self, endpoint):
        # TODO adds on Redis the endpoint
        pass

    def save(self):
        self.graph.create(self.relationship)
