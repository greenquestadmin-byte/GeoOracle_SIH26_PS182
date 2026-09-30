from blockchain.crawler import BitcoinTransactionCrawler
from graph.builder import BitcoinGraphBuilder
from .evidence import InvestigationEvidenceStore


class InvestigationEngine:
    def __init__(self, max_transactions=20, max_depth=2, evidence_store=None, bitcoin_provider=None):
        self.max_transactions = max_transactions
        self.max_depth = max_depth
        self.evidence_store = evidence_store
        self.bitcoin_provider = bitcoin_provider

    def investigate(self, network: str, tx_hash: str, save_evidence: bool = False, on_update=None,):
        network = network.lower().strip()

        if not tx_hash:
            raise ValueError("Transaction hash is required.")

        if network == "bitcoin":
            crawler = BitcoinTransactionCrawler(
                provider=self.bitcoin_provider,
                max_transactions=self.max_transactions,
                max_depth=self.max_depth,
                on_update=on_update,
            )
            crawl_result = crawler.crawl(tx_hash)

            builder = BitcoinGraphBuilder()
            graph = builder.build(crawl_result)

            result = {
                "network": "bitcoin",
                "tx_hash": tx_hash,
                "crawl": crawl_result,
                "graph": graph,
                "summary": builder.summary(),
            }

            if save_evidence:
                store = self.evidence_store or InvestigationEvidenceStore()
                result["evidence"] = store.save(result)

            return result

        if network == "ethereum":
            raise NotImplementedError(
                "Ethereum investigation will be added next."
            )

        raise ValueError(f"Unsupported network: {network}")
