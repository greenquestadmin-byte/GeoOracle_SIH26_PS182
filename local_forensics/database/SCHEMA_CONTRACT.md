# Shared Supabase contract

## vda_transaction_logs
Fields written by the frontend:
- dispute_category
- timestamp
- jurisdiction_zone
- blockchain_network
- tx_hash
- sender_wallet
- destination_wallet
- high_risk_flag
- crypto_volume
- fiat_value
- attachment_urls
- declaration_agreed

The local app reads `*` so it can tolerate additional columns such as `id` and server-generated timestamps.

## portal_metrics
Fields read by the frontend/local contract:
- total_value_tracked
- vasps_count
- flagged_wallets_count

## flagged_wallets
Fields read by the frontend/local contract:
- wallet_address
- risk_level

## Storage
Bucket:
- vda-proof-documents
