from collections import Counter
import re

from py2neo import Node, Relationship

from django.conf import settings


class BaseGraph(object):
    backend = settings.PERSISTENT_BACKEND
    graph = settings.GRAPH

    def format_endpoint(self, endpoint):
        endpoint = re.sub(r'/\d+', '/{id}', endpoint)
        return re.sub(r'\?.*', '', endpoint)


class Vertex(BaseGraph):
    LABEL = 'Microdot'

    def __init__(self, name, endpoint=None):
        self.endpoints = None
        self.name = name
        self.dependents = None
        self.max_know_depedents = 0
        self.min_know_depedents = 0
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

    @property
    def dependents_number(self):
        self.update_dependents()
        if self.dependents:
            return len(self.dependents)
        return 0

    def update_dependents(self):
        self.dependents = [v for v in self.graph.match(
            rel_type=Edge.TYPE,
            end_node=self.node)
        ]
        return self.dependents

    def calc_vertex_size(self, minimum, maximum, nodes_number):
        min_settings, max_settings = settings.NODE_SIZE
        max_settings = min(max_settings, nodes_number)
        factor = (max_settings - min_settings) * (len(self.dependents) - minimum)
        self.vertex_size = (factor / max(1, (maximum - minimum))) + min_settings
        return self.vertex_size

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
        self.endpoint = endpoint
        self.relationship = self.instantiate_relationship(origin.node, target.node)

    def instantiate_relationship(self, origin_node, target_node):
        relationship = self.graph.match_one(start_node=origin_node,
                                            rel_type=self.TYPE,
                                            end_node=target_node)
        if relationship is None:
            name = origin_node['name'] + '-' + target_node['name']
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

    def delete(self):
        self.graph.separate(self.relationship)
