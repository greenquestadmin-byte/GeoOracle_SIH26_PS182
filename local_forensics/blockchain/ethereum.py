from .base import BlockchainProvider
class EthereumProvider(BlockchainProvider):
    def get_transaction(self, tx_hash: str) -> dict:
        raise NotImplementedError("Ethereum provider will be implemented next.")
    def get_address_transactions(self, address: str, limit: int = 50) -> list[dict]:
        raise NotImplementedError("Ethereum address crawler will be implemented next.")
