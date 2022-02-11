# -*- coding: utf-8 -*-
"""Category Tree
"""
class CategoryNode(object):
    """category node"""
    def __init__(self, doc_title):
        self.doc_title = doc_title
        self.parents = set()
        self.children = set()


class CategoryNetwork(object):
    """category network
    in most case, the doc-catetories will generate a tree, here we view it as Network for general.
    """
    def __init__(self):
        self._roots = []
        self._leaves = []
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
            pnode.direct_children.add(node)
    