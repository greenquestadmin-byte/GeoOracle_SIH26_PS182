from typing import Any
from .client import get_supabase_client

class SupabaseRepository:
    # Exact names used by the frontend.
    TRANSACTION_LOGS = "vda_transaction_logs"
    PORTAL_METRICS = "portal_metrics"
    FLAGGED_WALLETS = "flagged_wallets"
    PROOF_BUCKET = "vda-proof-documents"

    def __init__(self):
        self.client = get_supabase_client()

    def get_transaction_logs(self, limit: int = 100):
        return (
            self.client.table(self.TRANSACTION_LOGS)
            .select("*")
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
            .data or []
        )

    def get_transaction_log(self, row_id: Any):
        return (
            self.client.table(self.TRANSACTION_LOGS)
            .select("*")
            .eq("id", row_id)
            .single()
            .execute()
            .data
        )

    def get_portal_metrics(self):
        return (
            self.client.table(self.PORTAL_METRICS)
            .select("*")
            .limit(1)
            .single()
            .execute()
            .data
        )

    def verify_wallet(self, wallet_address: str):
        rows = (
            self.client.table(self.FLAGGED_WALLETS)
            .select("wallet_address, risk_level")
            .eq("wallet_address", wallet_address)
            .limit(1)
            .execute()
            .data or []
        )
        return rows[0] if rows else None

    def get_flagged_wallets(self, limit: int = 100):
        return (
            self.client.table(self.FLAGGED_WALLETS)
            .select("*")
            .limit(limit)
            .execute()
            .data or []
        )
