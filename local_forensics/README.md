# VDA Audit — Shared Supabase Architecture

## Frontend
The browser frontend uses:
- `vda_transaction_logs`
- `portal_metrics`
- `flagged_wallets`
- Storage bucket: `vda-proof-documents`

The frontend files are kept unchanged except for adding `config.js` and `supabaseClient.js`.

## Local Python application
The PySide6 application reads the same Supabase tables directly. It does not use FastAPI, a browser, or a second database.

### Setup
1. Copy `.env.example` to `.env`.
2. Put the same Supabase project URL and public anon key used by the frontend into `.env`.
3. Create/activate a virtual environment.
4. `pip install -r requirements.txt`
5. Run `python main.py`.

## Important
Use only the public anon key in browser/local client code. Never place a Supabase `service_role` key in these files.

The local application currently implements the Supabase case bridge. Blockchain providers, graph traversal, GraphSAGE, and forensic HUD are separate next modules.


## Native Cybersecurity HUD

The PySide6 application now opens as a native forensic HUD. It provides:
- real-time Supabase connection status and 1-second analyst clock
- active case / high-risk / flagged-wallet / VASP / value metrics
- live transaction and case stream from `vda_transaction_logs`
- threat-alert feed
- selected-case intelligence panel
- risk signal bar
- transaction-topology visualization placeholder
- wallet verification against `flagged_wallets`
- investigation queue controls for the upcoming blockchain crawler, graph engine and GraphSAGE modules

The HUD is intentionally implemented inside the desktop application; it does not require a browser or FastAPI.

## Step 5 — Investigation Evidence Store

Each investigation can persist local forensic evidence under `data/graphs/`.

Artifacts created per investigation:

- `crawl.json` — normalized crawler output
- `graph.json` — NetworkX node-link graph
- `graph.graphml` — GraphML graph for external analysis/import
- `manifest.json` — investigation metadata and artifact references
- `data/evidence/index.jsonl` — append-only local evidence index

The HUD's **START BLOCKCHAIN INVESTIGATION** action runs the Bitcoin crawler/graph builder and saves these artifacts automatically.

### Manual test

```bash
python test_current_offline.py
python test_evidence.py
```

The offline tests use the previously verified Bitcoin transaction payload as a deterministic fixture because live API access depends on network connectivity.
