"""Demo golden lock — short-ship-cost.

The deployed dashboard renders committed JSON in web/public/data/. This locks the
cost JSON content (canonical-serialized SHA-256, stable across line endings) so
the client-mode conversion — purely additive (a new client_mode.py; nothing here
regenerates the JSON) — cannot drift the published site or its numbers.

If a SHA moves, STOP: a demo golden moved. Do not re-baseline without a logged
approval.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parent.parent / "web" / "public" / "data"

GOLDEN = {
    "cost_summary": "13b877fd90b125b698e9bb7fc5dcb58c31a3099997d0476affcd98ba63b17f03",
    "cost_by_retailer": "8371f7a3b471c9b3dcfcdbaf407d49e77d744087ccafd7b04919ec5c11a9ed7a",
    "meta": "ba2960af1378a967dcc19d2ded40d192c50ad47b7fa4162c28cc7dd9be1ec411",
}


@pytest.mark.parametrize("name", sorted(GOLDEN))
def test_demo_json_content_unchanged(name):
    data = json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))
    blob = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(blob).hexdigest()
    assert digest == GOLDEN[name], (
        f"{name}.json content changed (sha256 {digest} != golden {GOLDEN[name]}). "
        "A demo golden moved — STOP and report before re-baselining."
    )


def test_forgone_revenue_headline_is_pinned():
    summary = json.loads((DATA / "cost_summary.json").read_text(encoding="utf-8"))
    by_dim = {row["dimension"]: row for row in summary}
    assert by_dim["forgone_revenue"]["total_cost"] == 523326.17
