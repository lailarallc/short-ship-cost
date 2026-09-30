"""Walmart OTIF fine — anchors A5.15 and A5.17.

The engine fines 3% of the wholesale price to Walmart on each short line's
shortfall rounded up to whole cases, every month, with no monthly pass/fail
gate (A5.17, a modeling assumption). The old model fined the whole line's COGS
whenever line fill fell below 98%, and the 2026-09-25 model fined manufacturing
cost on short units; these cases fail under both.

Runs the fine logic on synthetic POs; nothing connects to a database.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("psycopg2")

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


@pytest.fixture(scope="module")
def engine():
    # The module refuses to import without DATABASE_URL; give it one that is
    # never connected to.
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("DATABASE_URL", "postgresql://unused.invalid/none")
        mp.syspath_prepend(str(SCRIPTS))
        import rebuild_from_platform
        yield rebuild_from_platform


def _line(ordered, shipped, cogs=2.0, price=4.0, case_pack=12, sku="CHP-AS-001"):
    return {"sku": sku, "units_ordered": ordered, "units_shipped": shipped,
            "unit_price": price, "cogs": cogs, "case_pack": case_pack}


PO_DATA = {
    # A: alone in its PO and month at 99% fill, 1 short unit, fined 1 whole
    # case of 12. A line, PO or month gate at 95% or 98% would not fine it.
    "RO-1": {"channel": "Walmart", "month": "2025-02",
             "lines": [_line(100, 99)]},
    # B: 10 short units in cases of 6, fined 2 cases = 12 units.
    # C: full, not fined.
    "RO-3": {"channel": "Walmart", "month": "2025-01",
             "lines": [_line(96, 86, case_pack=6, sku="CHP-PS-002"),
                       _line(48, 48, sku="CHP-HC-003")]},
    # D: rounding up to a case of 24 would exceed the 20 ordered; capped at 20.
    "RO-4": {"channel": "Walmart", "month": "2025-03",
             "lines": [_line(20, 15, case_pack=24, sku="CHP-SJ-004")]},
    "RO-2": {"channel": "Costco", "month": "2025-01",
             "lines": [_line(20, 18)]},
}


def test_walmart_fines_whole_cases_at_wholesale_ungated(engine):
    result = engine.compute_compliance_fines(None, PO_DATA)
    by_retailer = {r["retailer"]: r["cost"] for r in result["by_retailer"]}
    walmart = 0.03 * (12 + 12 + 20) * 4.0
    assert by_retailer["Walmart"] == pytest.approx(walmart)
    assert by_retailer["Costco"] == pytest.approx(250.0)
    assert result["total_cost"] == pytest.approx(walmart + 250.0)


def test_walmart_whatif_fines_only_remaining_short_cases(engine):
    # At a 95% floor: A stays at 99 (1 short -> 12), B lifts to 91 (5 short
    # -> 6), D lifts to 19 (1 short -> 20, capped).
    result = engine._simulate_fines_at(PO_DATA, 0.95)
    assert result["total_cost"] == pytest.approx(
        0.03 * (12 + 6 + 20) * 4.0 + 250.0)
