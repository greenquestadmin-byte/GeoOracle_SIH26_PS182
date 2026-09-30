from .bitcoin import BitcoinProvider
from .ethereum import EthereumProvider

def get_provider(network: str):
    network = network.lower().strip()
    if network == "bitcoin": return BitcoinProvider()
    if network == "ethereum": return EthereumProvider()
    raise ValueError(f"Unsupported blockchain network: {network}")
