import networkx as nx
class BitcoinGraphBuilder:
    def __init__(self): self.graph = nx.MultiDiGraph()
    def build(self, crawl_result: dict):
        self.graph.clear()
        transactions = crawl_result.get("transactions", {})
        for tx_hash, tx in transactions.items():
            self.graph.add_node(f"tx:{tx_hash}", node_type="transaction", tx_hash=tx_hash, network="bitcoin")
            for item in tx.get("inputs", []):
                address = item.get("address")
                if address:
                    self.graph.add_node(f"address:{address}", node_type="address", address=address, network="bitcoin")
                    self.graph.add_edge(f"address:{address}", f"tx:{tx_hash}", edge_type="input", value=item.get("value", 0))
            for item in tx.get("outputs", []):
                address = item.get("address")
                if address:
                    self.graph.add_node(f"address:{address}", node_type="address", address=address, network="bitcoin")
                    self.graph.add_edge(f"tx:{tx_hash}", f"address:{address}", edge_type="output", value=item.get("value", 0))
        return self.graph
    def summary(self):
        transaction_count = sum(1 for _, d in self.graph.nodes(data=True) if d.get("node_type") == "transaction")
        address_count = sum(1 for _, d in self.graph.nodes(data=True) if d.get("node_type") == "address")
        return {"nodes": self.graph.number_of_nodes(), "edges": self.graph.number_of_edges(), "transactions": transaction_count, "addresses": address_count}
