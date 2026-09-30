from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import networkx as nx


class InvestigationEvidenceStore:
    """Persist investigation evidence locally for reproducible forensic review."""

    def __init__(self, base_dir: str | Path = "data"):
        self.base_dir = Path(base_dir)
        self.graphs_dir = self.base_dir / "graphs"
        self.evidence_dir = self.base_dir / "evidence"
        self.graphs_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_name(value: str) -> str:
        return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    def save(self, result: dict[str, Any]) -> dict[str, str]:
        network = str(result.get("network", "unknown")).lower()
        tx_hash = str(result.get("tx_hash", "unknown"))
        stamp = self._utc_now().strftime("%Y%m%dT%H%M%SZ")
        folder = self.graphs_dir / self._safe_name(network) / f"{self._safe_name(tx_hash)}_{stamp}"
        folder.mkdir(parents=True, exist_ok=True)

        crawl = result.get("crawl", {})
        graph = result.get("graph")
        summary = result.get("summary", {})

        crawl_path = folder / "crawl.json"
        graph_json_path = folder / "graph.json"
        graphml_path = folder / "graph.graphml"
        manifest_path = folder / "manifest.json"

        self._write_json(crawl_path, crawl)

        if not isinstance(graph, nx.Graph):
            raise TypeError("Investigation result must contain a NetworkX graph under result['graph'].")

        graph_data = nx.node_link_data(graph, edges="edges")
        self._write_json(graph_json_path, graph_data)
        nx.write_graphml(graph, graphml_path)

        manifest = {
            "schema_version": 1,
            "created_at": self._utc_now().isoformat(),
            "network": network,
            "tx_hash": tx_hash,
            "summary": summary,
            "artifacts": {
                "crawl_json": str(crawl_path.relative_to(self.base_dir)),
                "graph_json": str(graph_json_path.relative_to(self.base_dir)),
                "graph_graphml": str(graphml_path.relative_to(self.base_dir)),
            },
        }
        self._write_json(manifest_path, manifest)

        # Also keep a central evidence index so investigators can enumerate cases.
        index_path = self.evidence_dir / "index.jsonl"
        with index_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(manifest, ensure_ascii=False) + "\n")

        return {
            "folder": str(folder),
            "crawl_json": str(crawl_path),
            "graph_json": str(graph_json_path),
            "graph_graphml": str(graphml_path),
            "manifest": str(manifest_path),
            "index": str(index_path),
        }

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
