from investigation.engine import InvestigationEngine
from blockchain.bitcoin import BitcoinProvider
from graph.traversal import GraphTraversal

TX_HASH = "bf8e31192dbe4588e2f527c297aabf1d932b887fc8d917e1fa14fe533b2ddacb"
SRC = "bc1q3gqwp4mnvlpdj9gplk7h6zt42vnpjc89u3hvkf"
OUT1 = "bc1q0k3mt3envsynl89tlqrdr9xgrljlh9ux4rhu2h"
OUT2 = "bc1qglfqjnmvws70g2erjjahkzsxryyjadkufpkn99"

ROOT = {
    "network": "bitcoin", "tx_hash": TX_HASH,
    "status": {"confirmed": True, "block_height": 969140,
                "block_hash": "00000000000000000001efde09f960b64af5b04ebb68d17473061047be342f7a",
                "block_time": 1790677324},
    "inputs": [{"txid": "previous-tx", "vout": 0, "address": SRC, "value": 89201}],
    "outputs": [{"index": 0, "address": OUT1, "value": 13043},
                 {"index": 1, "address": OUT2, "value": 75876}],
}

class FixtureProvider(BitcoinProvider):
    def __init__(self): pass
    def get_transaction(self, tx_hash):
        if tx_hash == TX_HASH: return ROOT
        raise KeyError(tx_hash)
    def get_address_transactions(self, address, limit=50): return []

# Exercise the actual crawler + graph builder via the actual InvestigationEngine,
# with only the network boundary replaced by a deterministic fixture provider.
engine = InvestigationEngine(max_transactions=20, max_depth=2)
engine_provider = FixtureProvider()

# Engine currently constructs its own provider, so directly exercise the same
# crawler/graph path for an offline integration test.
from blockchain.crawler import BitcoinTransactionCrawler
from graph.builder import BitcoinGraphBuilder
crawl = BitcoinTransactionCrawler(provider=engine_provider, max_transactions=20, max_depth=2, delay=0).crawl(TX_HASH)
graph = BitcoinGraphBuilder()
G = graph.build(crawl)
summary = graph.summary()

print("SUMMARY", summary)
assert crawl["transaction_count"] == 1
assert crawl["address_count"] == 3
assert crawl["edge_count"] == 3
assert summary == {"nodes": 4, "edges": 3, "transactions": 1, "addresses": 3}
root = f"tx:{TX_HASH}"
traversal = GraphTraversal(G)
assert set(traversal.neighbors(root)) == {f"address:{OUT1}", f"address:{OUT2}"}
assert f"address:{SRC}" in traversal.incoming(root)
print("ROOT NEIGHBORS", traversal.neighbors(root))
print("CURRENT CRAWLER + GRAPH TEST: PASS")
