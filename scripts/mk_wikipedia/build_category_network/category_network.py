# -*- coding: utf-8 -*-
"""Category Tree
"""
import json


class CategoryNode(object):
    """category node"""
    def __init__(self, doc_title):
        self.doc_title = doc_title
        self.parents = set()
        self.children = set()

    def __eq__(self, other):
        if not isinstance(other, CategoryNode):
            return False
        if other.doc_title != self.doc_title:
            return False

        def _nodes_cmp(ns1, ns2):
            if len(ns1) != len(ns2):
                return False
            ns1_titles = set([n.doc_title for n in ns1])
            ns2_titles = set([n.doc_title for n in ns2])
            return ns1_titles == ns2_titles

        return _nodes_cmp(self.parents, other.parents) and _nodes_cmp(self.children, other.children)

    def __hash__(self):
        return hash(self.doc_title)


class CategoryNetwork(object):
    """category network
    in most case, the doc-catetories will generate a tree, here we view it as Network for general.
    """
    def __init__(self):
        self._title2node = {}
    
    def add_node_and_link(self, doc_title, categories):
        """Add node to network and link it.
        doc_title will be the base node and categories is parent node.
        a category may still be a `doc_title` so that it could make the network.
        """
        if doc_title not in self._title2node:
            node = CategoryNode(doc_title)
            self._title2node[doc_title] = node
        else:
            node = self._title2node[doc_title]
        # link the network
        parent_titles = categories
        for pt in parent_titles:
            if pt not in self._title2node:
                pnode = CategoryNode(pt)
                self._title2node[pt] = pnode
            else:
                pnode = self._title2node[pt]
            node.parents.add(pnode)
            pnode.children.add(node)
    
    def serialize(self):
        """pickle will raise 
        RecursionError: maximum recursion depth exceeded while pickling an object
        should serialize by ourself.
        """
        # ATTENTION: use `str`, because json serialize/deserialize big int will error 
        #            => not equal... 
        #            This cost me a lot of time to debug this...
        node_sign = lambda n: str(id(n))
        sign2data = {}
        for node in self._title2node.values():
            sign = node_sign(node)
            data = {
                "t": node.doc_title,
                # only need save 1 direction.
                "c": [node_sign(n) for n in node.children]
            }
            sign2data[sign] = data
        return json.dumps(sign2data, ensure_ascii=False)

    @classmethod
    def deserialize(cls, data: str):
        """desrialize from a json str"""
        # we first create all node without link, then link again.
        # 1. init all data
        data = json.loads(data)
        sign2node = {}        
        for sign, node_data in data.items():
            assert sign not in sign2node
            node = CategoryNode(node_data["t"])
            sign2node[sign] = node
        
        # 2. link all node
        for sign, node_data in data.items():
            node = sign2node[sign]
            children_signs = node_data["c"]
            for cs in children_signs:
                cnode = sign2node[cs]
                node.children.add(cnode)
                cnode.parents.add(node)
        # 3. create the network
        title2node = {}
        for node in sign2node.values():
            t = node.doc_title
            title2node[t] = node
        network = cls()
        network._title2node = title2node
        return network

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        for t, node in self._title2node.items():
            if t not in other._title2node:
                return False
            cnode = other._title2node[t]
            if node != cnode:
                return False
        return True
