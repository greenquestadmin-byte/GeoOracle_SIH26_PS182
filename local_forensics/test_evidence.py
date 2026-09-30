import json
import shutil
from pathlib import Path

from blockchain.bitcoin import BitcoinProvider
from blockchain.crawler import BitcoinTransactionCrawler
from graph.builder import BitcoinGraphBuilder
from investigation.evidence import InvestigationEvidenceStore

TX_HASH = "bf8e31192dbe4588e2f527c297aabf1d932b887fc8d917e1fa14fe533b2ddacb"
SRC = "bc1q3gqwp4mnvlpdj9gplk7h6zt42vnpjc89u3hvkf"
OUT1 = "bc1q0k3mt3envsynl89tlqrdr9xgrljlh9ux4rhu2h"
OUT2 = "bc1qglfqjnmvws70g2erjjahkzsxryyjadkufpkn99"

ROOT = {
    "network": "bitcoin", "tx_hash": TX_HASH,
    "status": {"confirmed": True, "block_height": 969140},
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

out = Path("data/test_evidence")
if out.exists(): shutil.rmtree(out)

crawl = BitcoinTransactionCrawler(provider=FixtureProvider(), max_transactions=20, max_depth=2, delay=0).crawl(TX_HASH)
builder = BitcoinGraphBuilder()
graph = builder.build(crawl)
result = {"network": "bitcoin", "tx_hash": TX_HASH, "crawl": crawl, "graph": graph, "summary": builder.summary()}

paths = InvestigationEvidenceStore(out).save(result)
for key, value in paths.items(): print(key, "=>", value)

for key in ("crawl_json", "graph_json", "graph_graphml", "manifest", "index"):
    assert Path(paths[key]).exists(), key

manifest = json.loads(Path(paths["manifest"]).read_text(encoding="utf-8"))
assert manifest["tx_hash"] == TX_HASH
assert manifest["summary"] == {"nodes": 4, "edges": 3, "transactions": 1, "addresses": 3}

graph_json = json.loads(Path(paths["graph_json"]).read_text(encoding="utf-8"))
assert len(graph_json["nodes"]) == 4
assert len(graph_json["edges"]) == 3

import networkx as nx
loaded = nx.read_graphml(paths["graph_graphml"])
assert loaded.number_of_nodes() == 4
assert loaded.number_of_edges() == 3

print("EVIDENCE STORE TEST: PASS")
