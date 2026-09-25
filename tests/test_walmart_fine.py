"""Walmart OTIF fine — anchor A5.17.

The engine fines 3% of manufacturing cost on short units, every month, with no
monthly pass/fail gate. The old model fined the whole line's COGS whenever line
fill fell below 98%; these cases fail under that rule. Wholesale basis and
whole-case rounding are open gaps (HANDOFF.md) and are not modelled here.

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


def _line(ordered, shipped, cogs=2.0, price=4.0, sku="CHP-AS-001"):
    return {"sku": sku, "units_ordered": ordered, "units_shipped": shipped,
            "unit_price": price, "cogs": cogs}


PO_DATA = {
    # A: alone in its PO and month at 99% fill, fined 1 short unit. A line,
    # PO or month gate at 95% or 98% would not fine it.
    "RO-1": {"channel": "Walmart", "month": "2025-02",
             "lines": [_line(100, 99)]},
    # B: 90% fill, fined 10 short units (old rule: all 100 units' COGS).
    # C: full, not fined.
    "RO-3": {"channel": "Walmart", "month": "2025-01",
             "lines": [_line(100, 90, sku="CHP-PS-002"),
                       _line(50, 50, sku="CHP-HC-003")]},
    "RO-2": {"channel": "Costco", "month": "2025-01",
             "lines": [_line(20, 18)]},
}


def test_walmart_fines_every_short_case_ungated(engine):
    result = engine.compute_compliance_fines(None, PO_DATA)
    by_retailer = {r["retailer"]: r["cost"] for r in result["by_retailer"]}
    assert by_retailer["Walmart"] == pytest.approx(0.03 * (1 + 10) * 2.0)
    assert by_retailer["Costco"] == pytest.approx(250.0)
    assert result["total_cost"] == pytest.approx(0.66 + 250.0)


def test_walmart_whatif_fines_only_remaining_short_cases(engine):
    # At a 95% floor: A stays at 99 (1 short), B lifts to 95 (5 short).
    result = engine._simulate_fines_at(PO_DATA, 0.95)
    assert result["total_cost"] == pytest.approx(0.03 * (1 + 5) * 2.0 + 250.0)
