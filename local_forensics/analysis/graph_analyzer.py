class GraphAnalyzer:

    def analyze(self, graph, root_tx=None):
        transactions = []
        addresses = []

        for node, data in graph.nodes(data=True):
            if data.get("node_type") == "transaction":
                transactions.append(node)

            elif data.get("node_type") == "address":
                addresses.append(node)

        return {
            "transaction_count": len(transactions),
            "address_count": len(addresses),
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
        }