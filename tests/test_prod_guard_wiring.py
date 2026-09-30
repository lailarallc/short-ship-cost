"""The prod guard sits in front of the Postgres read in rebuild_from_platform.

DATABASE_URL usually points at localhost, which is a `fly proxy` tunnel to
production whenever one is open. This fakes a flyctl listener and asserts
nothing connects.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("psycopg2")

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
LOCAL_URL = "postgresql://localhost:5432/db"


def test_pg_connect_refuses_fly_tunnel(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", LOCAL_URL)
    monkeypatch.delenv("ALLOW_PROD_DB", raising=False)
    monkeypatch.syspath_prepend(str(SCRIPTS))
    import rebuild_from_platform as rfp

    monkeypatch.setattr(rfp, "DATABASE_URL", LOCAL_URL)
    monkeypatch.setattr(rfp.prod_guard, "_listener", lambda port: "flyctl")
    monkeypatch.setattr(rfp.psycopg2, "connect", lambda *a, **kw: pytest.fail("connected"))
    with pytest.raises(rfp.prod_guard.ProdDatabaseError):
        rfp.pg_connect()
