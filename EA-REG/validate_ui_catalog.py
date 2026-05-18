from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_CATALOG_PATH = Path("EA-REG") / "ui_catalog.json"

REQUIRED_TOP_LEVEL_SECTIONS = [
    "catalog_id",
    "catalog_name",
    "document_type",
    "status",
    "version",
    "process_context",
    "authority_model",
    "catalog_shape",
    "ui_products",
    "navigation",
    "screens",
    "shared_components",
    "data_contracts",
    "rest_apis",
    "websocket_contracts",
    "websocket_channels",
    "safety_model",
    "implementation_bindings",
    "acceptance_criteria",
]

COLLECTION_ID_FIELDS = {
    "ui_products": "product_id",
    "screens": "screen_id",
    "shared_components": "component_id",
    "data_contracts": "data_contract_id",
    "rest_apis": "api_id",
    "websocket_contracts": "websocket_id",
    "websocket_channels": "websocket_channel_id",
    "implementation_bindings": "binding_id",
    "acceptance_criteria": "criteria_id",
}

SCREEN_CHILD_ID_FIELDS = {
    "panels": "panel_id",
    "controls": "control_id",
}


class UiCatalogValidator:
    def __init__(self, repo_root: Path, catalog_path: Path) -> None:
        self.repo_root = repo_root
        self.catalog_path = catalog_path
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.catalog: dict[str, Any] = {}
        self.known_ids: set[str] = set()
        self.control_ids: set[str] = set()
        self.screen_ids: set[str] = set()
        self.data_contract_names: set[str] = set()

    def validate(self) -> bool:
        self.catalog = self._load_catalog()
        if not self.catalog:
            self._print_summary()
            return False

        self._validate_top_level_sections()
        self._validate_collection_shapes()
        self._collect_ids()
        self._validate_screen_completeness()
        self._validate_navigation_targets()
        self._validate_cross_references()
        self._validate_paths()
        self._validate_safety_model()
        self._validate_known_gaps()
        self._print_summary()
        return not self.errors

    def _load_catalog(self) -> dict[str, Any]:
        if not self.catalog_path.exists():
            self.errors.append(f"Missing UI catalog: {self.catalog_path}")
            return {}

        try:
            with self.catalog_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            self.errors.append(f"Invalid JSON: {exc}")
            return {}
        except OSError as exc:
            self.errors.append(f"Unable to read catalog: {exc}")
            return {}

        if not isinstance(payload, dict):
            self.errors.append("UI catalog root must be a JSON object.")
            return {}
        return payload

    def _validate_top_level_sections(self) -> None:
        for section in REQUIRED_TOP_LEVEL_SECTIONS:
            if section not in self.catalog:
                self.errors.append(f"Missing top-level section: {section}")

        declared_sections = (
            self.catalog.get("catalog_shape", {})
            .get("required_top_level_sections", [])
        )
        if isinstance(declared_sections, list):
            for section in declared_sections:
                if section not in self.catalog:
                    self.errors.append(
                        "catalog_shape.required_top_level_sections references "
                        f"missing section: {section}"
                    )
        else:
            self.errors.append(
                "catalog_shape.required_top_level_sections must be a list."
            )

    def _validate_collection_shapes(self) -> None:
        for section, id_field in COLLECTION_ID_FIELDS.items():
            value = self.catalog.get(section)
            if not isinstance(value, list):
                self.errors.append(f"{section} must be a list.")
                continue
            for index, item in enumerate(value):
                if not isinstance(item, dict):
                    self.errors.append(f"{section}[{index}] must be an object.")
                    continue
                if not item.get(id_field):
                    self.errors.append(
                        f"{section}[{index}] is missing required id field {id_field}."
                    )

    def _collect_ids(self) -> None:
        all_ids: list[str] = []

        for section, id_field in COLLECTION_ID_FIELDS.items():
            for item in self._objects(section):
                item_id = str(item.get(id_field, ""))
                if not item_id:
                    continue
                all_ids.append(item_id)
                if section == "screens":
                    self.screen_ids.add(item_id)

                if section == "data_contracts":
                    contract_name = item.get("contract_name")
                    if isinstance(contract_name, str) and contract_name:
                        self.data_contract_names.add(contract_name)

        for screen in self._objects("screens"):
            for child_section, id_field in SCREEN_CHILD_ID_FIELDS.items():
                for child in self._child_objects(screen, child_section):
                    child_id = str(child.get(id_field, ""))
                    if not child_id:
                        self.errors.append(
                            f"{screen.get('screen_id')} {child_section} item "
                            f"is missing {id_field}."
                        )
                        continue
                    all_ids.append(child_id)
                    if child_section == "controls":
                        self.control_ids.add(child_id)

        duplicate_ids = [
            item_id for item_id, count in Counter(all_ids).items() if count > 1
        ]
        for item_id in sorted(duplicate_ids):
            self.errors.append(f"Duplicate catalog id: {item_id}")

        self.known_ids = set(all_ids)

    def _validate_screen_completeness(self) -> None:
        for screen in self._objects("screens"):
            screen_id = screen.get("screen_id", "<unknown>")

            if not screen.get("name"):
                self.errors.append(f"{screen_id} is missing name.")
            if not screen.get("route_key"):
                self.errors.append(f"{screen_id} is missing route_key.")
            if not screen.get("purpose"):
                self.errors.append(f"{screen_id} is missing purpose.")

            panels = screen.get("panels")
            if not isinstance(panels, list) or not panels:
                self.errors.append(f"{screen_id} must define at least one panel.")

            criteria = screen.get("acceptance_criteria")
            if not isinstance(criteria, list) or not criteria:
                self.errors.append(
                    f"{screen_id} must define screen-level acceptance_criteria."
                )

            controls = screen.get("controls", [])
            if controls is not None and not isinstance(controls, list):
                self.errors.append(f"{screen_id}.controls must be a list.")

            data_inputs = screen.get("data_inputs", [])
            if data_inputs is not None and not isinstance(data_inputs, list):
                self.errors.append(f"{screen_id}.data_inputs must be a list.")

    def _validate_navigation_targets(self) -> None:
        route_keys = {
            screen.get("route_key")
            for screen in self._objects("screens")
            if isinstance(screen.get("route_key"), str)
        }
        primary_tabs = self.catalog.get("navigation", {}).get("primary_tabs", [])
        if not isinstance(primary_tabs, list):
            self.errors.append("navigation.primary_tabs must be a list.")
            return

        for route_key in primary_tabs:
            if route_key not in route_keys:
                self.errors.append(
                    f"navigation.primary_tabs references missing route_key: {route_key}"
                )

    def _validate_cross_references(self) -> None:
        for binding in self._objects("implementation_bindings"):
            binding_id = binding.get("binding_id", "<unknown>")
            self._validate_id_refs(binding_id, binding.get("binds_to", []), "binds_to")

        for api in self._objects("rest_apis"):
            api_id = api.get("api_id", "<unknown>")
            self._validate_id_refs(
                api_id,
                api.get("consumed_by_screens", []),
                "consumed_by_screens",
                allowed_ids=self.screen_ids,
            )

        for channel in self._objects("websocket_channels"):
            channel_id = channel.get("websocket_channel_id", "<unknown>")
            self._validate_id_refs(
                channel_id,
                channel.get("consumed_by_screens", []),
                "consumed_by_screens",
                allowed_ids=self.screen_ids,
            )
            payload_contract = channel.get("payload_contract")
            if (
                isinstance(payload_contract, str)
                and payload_contract
                and payload_contract not in self.data_contract_names
            ):
                self.warnings.append(
                    f"{channel_id}.payload_contract has no matching data contract: "
                    f"{payload_contract}"
                )

        for component in self._objects("shared_components"):
            component_id = component.get("component_id", "<unknown>")
            visible_on = component.get("visible_on", [])
            route_keys = {
                screen.get("route_key")
                for screen in self._objects("screens")
                if isinstance(screen.get("route_key"), str)
            }
            if isinstance(visible_on, list):
                for route_key in visible_on:
                    if route_key not in route_keys:
                        self.errors.append(
                            f"{component_id}.visible_on references missing route_key: "
                            f"{route_key}"
                        )
            elif visible_on:
                self.errors.append(f"{component_id}.visible_on must be a list.")

            controls = component.get("controls", [])
            self._validate_id_refs(
                component_id,
                controls,
                "controls",
                allowed_ids=self.control_ids,
            )

    def _validate_id_refs(
        self,
        owner_id: str,
        refs: Any,
        field_name: str,
        *,
        allowed_ids: set[str] | None = None,
    ) -> None:
        if refs is None:
            return
        if not isinstance(refs, list):
            self.errors.append(f"{owner_id}.{field_name} must be a list.")
            return
        candidates = allowed_ids if allowed_ids is not None else self.known_ids
        for ref in refs:
            if not isinstance(ref, str) or not ref:
                self.errors.append(f"{owner_id}.{field_name} contains an invalid id.")
                continue
            if ref not in candidates:
                self.errors.append(
                    f"{owner_id}.{field_name} references unknown id: {ref}"
                )

    def _validate_paths(self) -> None:
        source_priority = self.catalog.get("authority_model", {}).get(
            "source_priority", []
        )
        if isinstance(source_priority, list):
            for item in source_priority:
                if not isinstance(item, dict):
                    self.errors.append("authority_model.source_priority item is invalid.")
                    continue
                self._validate_repo_path(
                    item.get("path"),
                    f"source_priority rank {item.get('rank', '<unknown>')}",
                )
        else:
            self.errors.append("authority_model.source_priority must be a list.")

        for product in self._objects("ui_products"):
            product_id = product.get("product_id", "<unknown>")
            for path in product.get("observed_implementation_paths", []):
                self._validate_repo_path(path, product_id)

        for binding in self._objects("implementation_bindings"):
            self._validate_repo_path(
                binding.get("path"),
                binding.get("binding_id", "<unknown>"),
            )

        for api in self._objects("rest_apis"):
            observed_path = api.get("observed_in_source")
            if observed_path:
                self._validate_repo_path(observed_path, api.get("api_id", "<unknown>"))

        for websocket in self._objects("websocket_contracts"):
            observed_path = websocket.get("observed_in_source")
            if observed_path:
                self._validate_repo_path(
                    observed_path,
                    websocket.get("websocket_id", "<unknown>"),
                )

    def _validate_repo_path(self, path_value: Any, owner: str) -> None:
        if not isinstance(path_value, str) or not path_value:
            self.errors.append(f"{owner} has an empty or invalid path.")
            return
        path = self.repo_root / path_value
        if not path.exists():
            self.warnings.append(f"{owner} path does not exist on disk: {path_value}")

    def _validate_safety_model(self) -> None:
        safety_model = self.catalog.get("safety_model")
        if not isinstance(safety_model, dict):
            self.errors.append("safety_model must be an object.")
            return

        levels = safety_model.get("safety_levels", [])
        if not isinstance(levels, list) or not levels:
            self.errors.append("safety_model.safety_levels must be a non-empty list.")
            return

        known_levels = {
            level.get("level")
            for level in levels
            if isinstance(level, dict) and isinstance(level.get("level"), str)
        }
        for screen in self._objects("screens"):
            for control in self._child_objects(screen, "controls"):
                level = control.get("safety_level")
                control_id = control.get("control_id", "<unknown>")
                if level not in known_levels:
                    self.errors.append(
                        f"{control_id} uses unknown safety_level: {level}"
                    )
                if level == "critical" and control.get("requires_confirmation") is not True:
                    self.warnings.append(
                        f"{control_id} is critical but does not require confirmation."
                    )

    def _validate_known_gaps(self) -> None:
        known_gaps = self.catalog.get("known_gaps", [])
        if known_gaps is None:
            return
        if not isinstance(known_gaps, list):
            self.errors.append("known_gaps must be a list when present.")
            return
        for index, gap in enumerate(known_gaps):
            if not isinstance(gap, dict):
                self.errors.append(f"known_gaps[{index}] must be an object.")
                continue
            if not gap.get("gap_id"):
                self.errors.append(f"known_gaps[{index}] is missing gap_id.")
            if not gap.get("description"):
                self.errors.append(f"known_gaps[{index}] is missing description.")

    def _objects(self, section: str) -> list[dict[str, Any]]:
        value = self.catalog.get(section, [])
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    def _child_objects(
        self,
        parent: dict[str, Any],
        section: str,
    ) -> list[dict[str, Any]]:
        value = parent.get(section, [])
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    def _print_summary(self) -> None:
        print("UI CATALOG VALIDATION")
        print("=" * 80)
        print(f"Catalog: {self.catalog_path}")
        print(f"Errors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")

        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"- {error}")

        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f"- {warning}")

        if not self.errors:
            print("\nResult: PASS")
        else:
            print("\nResult: FAIL")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the canonical EAFIX UI catalog."
    )
    parser.add_argument(
        "--catalog",
        default=str(DEFAULT_CATALOG_PATH),
        help="Path to ui_catalog.json, relative to repo root by default.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root used for path existence checks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    catalog_path = Path(args.catalog)
    if not catalog_path.is_absolute():
        catalog_path = repo_root / catalog_path

    validator = UiCatalogValidator(repo_root=repo_root, catalog_path=catalog_path)
    return 0 if validator.validate() else 1


if __name__ == "__main__":
    sys.exit(main())
