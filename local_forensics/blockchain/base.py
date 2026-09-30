from abc import ABC, abstractmethod

class BlockchainProvider(ABC):
    @abstractmethod
    def get_transaction(self, tx_hash: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_address_transactions(self, address: str, limit: int = 50) -> list[dict]:
        raise NotImplementedError
