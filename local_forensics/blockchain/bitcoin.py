import requests
from .base import BlockchainProvider

class BitcoinProvider(BlockchainProvider):
    BASE_URL = "https://blockstream.info/api"

    def __init__(self, timeout: int = 20):
        self.timeout = timeout

    def _get(self, endpoint: str):
        response = requests.get(f"{self.BASE_URL}{endpoint}", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_transaction(self, tx_hash: str) -> dict:
        tx = self._get(f"/tx/{tx_hash}")
        return {
            "network": "bitcoin",
            "tx_hash": tx.get("txid"),
            "status": {
                "confirmed": tx.get("status", {}).get("confirmed"),
                "block_height": tx.get("status", {}).get("block_height"),
                "block_hash": tx.get("status", {}).get("block_hash"),
                "block_time": tx.get("status", {}).get("block_time"),
            },
            "inputs": [
                {
                    "txid": item.get("txid"), "vout": item.get("vout"),
                    "address": item.get("prevout", {}).get("scriptpubkey_address"),
                    "value": item.get("prevout", {}).get("value", 0),
                }
                for item in tx.get("vin", [])
            ],
            "outputs": [
                {"index": index, "address": output.get("scriptpubkey_address"), "value": output.get("value", 0)}
                for index, output in enumerate(tx.get("vout", []))
            ],
            "raw": tx,
        }

    def get_address_transactions(self, address: str, limit: int = 50) -> list[dict]:
        transactions = self._get(f"/address/{address}/txs")
        results = []
        for tx in transactions[:limit]:
            results.append({
                "network": "bitcoin", "tx_hash": tx.get("txid"), "status": tx.get("status", {}),
                "inputs": [
                    {"txid": item.get("txid"), "vout": item.get("vout"),
                     "address": item.get("prevout", {}).get("scriptpubkey_address"),
                     "value": item.get("prevout", {}).get("value", 0)}
                    for item in tx.get("vin", [])
                ],
                "outputs": [
                    {"index": index, "address": output.get("scriptpubkey_address"), "value": output.get("value", 0)}
                    for index, output in enumerate(tx.get("vout", []))
                ],
            })
        return results
