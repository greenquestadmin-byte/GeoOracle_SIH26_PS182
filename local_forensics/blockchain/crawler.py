import time
from collections import deque
from .bitcoin import BitcoinProvider


class BitcoinTransactionCrawler:

    def __init__(
        self,
        provider=None,
        max_transactions=50,
        max_depth=2,
        delay=0.2,
        on_update=None,
    ):
        self.provider = provider or BitcoinProvider()
        self.max_transactions = max_transactions
        self.max_depth = max_depth
        self.delay = delay
        self.on_update = on_update

        self.visited = set()
        self.transactions = {}
        self.addresses = set()
        self.edges = []

    def crawl(self, root_tx_hash: str) -> dict:
        queue = deque([(root_tx_hash, 0)])

        while queue and len(self.transactions) < self.max_transactions:
            tx_hash, depth = queue.popleft()

            if tx_hash in self.visited or depth > self.max_depth:
                continue

            self.visited.add(tx_hash)

            try:
                tx = self.provider.get_transaction(tx_hash)
            except Exception as exc:
                print(
                    f"[CRAWLER] Failed: {tx_hash}\n"
                    f"[CRAWLER] {exc}"
                )
                continue

            self.transactions[tx_hash] = tx
            self._process_transaction(tx)

            print(
                f"[CRAWLER] depth={depth} "
                f"transactions={len(self.transactions)} "
                f"tx={tx_hash}"
            )

            if self.on_update:
                self.on_update(self.get_result())

            for item in tx.get("inputs", []):
                previous_txid = item.get("txid")
                address = item.get("address")

                if address:
                    self.addresses.add(address)

                if (
                    previous_txid
                    and previous_txid not in self.visited
                ):
                    queue.append(
                        (previous_txid, depth + 1)
                    )

            for output in tx.get("outputs", []):
                address = output.get("address")

                if not address:
                    continue

                self.addresses.add(address)

                try:
                    for connected_tx in self.provider.get_address_transactions(
                        address
                    ):
                        connected_hash = connected_tx.get("tx_hash")

                        if (
                            connected_hash
                            and connected_hash not in self.visited
                        ):
                            queue.append(
                                (connected_hash, depth + 1)
                            )

                except Exception as exc:
                    print(
                        f"[CRAWLER] Address lookup failed: "
                        f"{address}: {exc}"
                    )

                time.sleep(self.delay)

        return self.get_result()

    def _process_transaction(self, tx: dict):
        tx_hash = tx.get("tx_hash")

        for item in tx.get("inputs", []):
            address = item.get("address")

            if address:
                self.edges.append({
                    "source": tx_hash,
                    "target": address,
                    "type": "input",
                })

        for item in tx.get("outputs", []):
            address = item.get("address")

            if address:
                self.edges.append({
                    "source": tx_hash,
                    "target": address,
                    "type": "output",
                })

    def get_result(self):
        return {
            "transactions": self.transactions,
            "addresses": list(self.addresses),
            "edges": self.edges,
            "transaction_count": len(self.transactions),
            "address_count": len(self.addresses),
            "edge_count": len(self.edges),
        }