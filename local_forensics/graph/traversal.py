import networkx as nx
class GraphTraversal:
    def __init__(self, graph): self.graph = graph
    def neighbors(self, node_id): return list(self.graph.neighbors(node_id)) if node_id in self.graph else []
    def incoming(self, node_id): return list(self.graph.predecessors(node_id)) if node_id in self.graph else []
    def outgoing(self, node_id): return list(self.graph.successors(node_id)) if node_id in self.graph else []
    def shortest_path(self, source, target):
        try: return nx.shortest_path(self.graph, source=source, target=target)
        except nx.NetworkXNoPath: return []
    def get_subgraph(self, root_node, depth=2):
        if root_node not in self.graph: return nx.MultiDiGraph()
        nodes = nx.single_source_shortest_path_length(self.graph, root_node, cutoff=depth)
        return self.graph.subgraph(nodes.keys()).copy()
