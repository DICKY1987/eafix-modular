#!/usr/bin/env python3
"""Identity reconciliation for canonical module records."""

from __future__ import annotations

from typing import Any

from .normalizers import ALIAS_CROSSWALK, THIN_MODULES


def reconcile_module_records(module_universe: dict[str, Any]) -> list[dict[str, Any]]:
    reconciled = []
    for module in module_universe["modules"]:
        symbol = module["canonical_symbol"]
        aliases = sorted(
            [legacy for legacy, canonical in ALIAS_CROSSWALK.items() if canonical == symbol]
        )
        unresolved = []
        if symbol in THIN_MODULES:
            unresolved.append(f"thin_module:{THIN_MODULES[symbol]}")

        confidence = "high"
        if module_universe.get("fallback_used"):
            confidence = "medium"
        if unresolved:
            confidence = "low" if symbol in THIN_MODULES else confidence

        record = {
            **module,
            "legacy_aliases_applied": aliases,
            "reconciliation": {
                "canonical_source": "module_universe_vnext" if not module_universe.get("fallback_used") else "existing_draft_bundle_fallback",
                "legacy_aliases_applied": aliases,
                "source_conflicts": [],
                "unresolved_items": unresolved,
                "confidence": confidence,
            },
            "thin_module_reason": THIN_MODULES.get(symbol),
        }
        reconciled.append(record)
    return reconciled
