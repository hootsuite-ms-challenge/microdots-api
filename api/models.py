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

    def __init__(self, origin, target):
        self.origin = origin
        self.target = target
        self.relationship = Relationship(origin, self.TYPE, target)

    @property
    def node_from(self):
        return self.origin.__name__

    @property
    def node_to(self):
        return self.target.__name__

    def save(self):
        self.graph.create(self.relationship)
