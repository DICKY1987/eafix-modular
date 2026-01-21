#!/usr/bin/env python3
# DOC_LINK: DOC-CORE-SUB-GLOSSARY-VALIDATE-GLOSSARY-SCHEMA-770
"""
Glossary System Process Steps Schema Validator

Validates DOC-CONFIG-GLOSSARY-PROCESS-STEPS-SCHEMA-302__GLOSSARY_PROCESS_STEPS_SCHEMA.yaml against standardized schema
requirements for glossary term lifecycle and SSOT enforcement.

Usage:
    python validate_glossary_schema.py

Features:
    - Validates required fields per step
    - Checks artifact_registry references
    - Validates guardrail_checkpoint references
    - Checks operation_kind taxonomy compliance
    - Validates component references
    - Validates state machine transitions
    - Reports schema compliance metrics
"""
DOC_ID: DOC-CORE-SUB-GLOSSARY-VALIDATE-GLOSSARY-SCHEMA-770

import sys
from pathlib import Path
from typing import Dict, List, Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Install with: pip install pyyaml")
    sys.exit(1)


class GlossaryValidator:
    """Validates Glossary System process steps schema."""

    # Required fields per step
    REQUIRED_FIELDS = {
        "step_id",
        "phase",
        "name",
        "responsible_component",
        "operation_kind",
        "description",
        "inputs",
        "expected_outputs",
        "requires_human_confirmation",
    }

    # Valid phases from state machine
    VALID_PHASES = {
        "INIT",
        "PROPOSAL",
        "DRAFT",
        "VALIDATION",
        "ACTIVATION",
        "MAINTENANCE",
        "DEPRECATION",
        "ARCHIVAL",
        "DONE",
    }

    # Valid components
    VALID_COMPONENTS = {
        "glossary_metadata",
        "glossary_governance",
        "glossary_schema",
        "glossary_changelog",
        "validate_glossary",
        "generate_glossary",
        "update_term",
        "glossary_ssot_policy",
    }

    def __init__(self, schema_path: Path):
        self.schema_path = schema_path
        self.schema: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats: Dict[str, int] = {
            "total_steps": 0,
            "total_phases": 0,
            "total_components": 0,
            "total_operations": 0,
            "total_guardrails": 0,
            "total_artifacts": 0,
            "missing_required_fields": 0,
            "invalid_phases": 0,
            "invalid_components": 0,
            "invalid_operations": 0,
        }

    def load_schema(self) -> bool:
        """Load schema YAML file."""
        try:
            with self.schema_path.open("r", encoding="utf-8") as f:
                self.schema = yaml.safe_load(f)
            return True
        except Exception as e:
            self.errors.append(f"Failed to load schema: {e}")
            return False

    def validate_meta_section(self) -> None:
        """Validate meta section exists and has required fields."""
        if "meta" not in self.schema:
            self.errors.append("Missing 'meta' section")
            return

        meta = self.schema["meta"]
        required_meta = {
            "doc_id",
            "version",
            "last_updated",
            "description",
            "state_machine",
        }
        missing = required_meta - set(meta.keys())

        if missing:
            self.errors.append(f"Meta section missing fields: {missing}")

        # Validate state machine
        if "state_machine" in meta:
            sm = meta["state_machine"]
            if "phases" not in sm:
                self.errors.append("State machine missing 'phases'")
            if "valid_transitions" not in sm:
                self.errors.append("State machine missing 'valid_transitions'")
            if "terminal_states" not in sm:
                self.errors.append("State machine missing 'terminal_states'")

    def validate_operation_kinds(self) -> None:
        """Validate operation_kinds taxonomy exists."""
        if "operation_kinds" not in self.schema:
            self.errors.append("Missing 'operation_kinds' taxonomy")
            return

        self.stats["total_operations"] = len(self.schema["operation_kinds"])

    def validate_components(self) -> None:
        """Validate components registry."""
        if "components" not in self.schema:
            self.errors.append("Missing 'components' registry")
            return

        components = self.schema["components"]
        self.stats["total_components"] = len(components)

        for comp_id, comp_data in components.items():
            required = {"file", "role", "responsibilities"}
            missing = required - set(comp_data.keys())
            if missing:
                self.errors.append(f"Component '{comp_id}' missing fields: {missing}")

    def validate_artifact_registry(self) -> None:
        """Validate artifact_registry section."""
        if "artifact_registry" not in self.schema:
            self.warnings.append("Missing 'artifact_registry' section (optional)")
            return

        artifacts = self.schema["artifact_registry"]
        self.stats["total_artifacts"] = sum(len(v) for v in artifacts.values())

    def validate_step(self, step: Dict[str, Any], phase_id: str) -> None:
        """Validate individual step structure."""
        self.stats["total_steps"] += 1

        # Check required fields
        missing = self.REQUIRED_FIELDS - set(step.keys())
        if missing:
            self.errors.append(
                f"Step '{step.get('step_id', 'UNKNOWN')}' missing fields: {missing}"
            )
            self.stats["missing_required_fields"] += len(missing)

        # Validate phase
        if step.get("phase") not in self.VALID_PHASES:
            self.errors.append(
                f"Step '{step.get('step_id')}' has invalid phase: {step.get('phase')}"
            )
            self.stats["invalid_phases"] += 1

        # Validate component
        comp = step.get("responsible_component", "")
        if comp and comp not in self.VALID_COMPONENTS:
            self.warnings.append(
                f"Step '{step.get('step_id')}' references undocumented component: {comp}"
            )

        # Validate operation_kind exists in taxonomy
        op_kind = step.get("operation_kind", "")
        if op_kind and "operation_kinds" in self.schema:
            if op_kind not in self.schema["operation_kinds"]:
                self.errors.append(
                    f"Step '{step.get('step_id')}' has invalid operation_kind: {op_kind}"
                )
                self.stats["invalid_operations"] += 1

        # Validate inputs/outputs are lists
        if "inputs" in step and not isinstance(step["inputs"], list):
            self.errors.append(f"Step '{step.get('step_id')}' inputs must be a list")

        if "expected_outputs" in step and not isinstance(
            step["expected_outputs"], list
        ):
            self.errors.append(
                f"Step '{step.get('step_id')}' expected_outputs must be a list"
            )

    def validate_phases_section(self) -> None:
        """Validate phases section with all steps."""
        if "phases" not in self.schema:
            self.errors.append("Missing 'phases' section")
            return

        phases = self.schema["phases"]
        self.stats["total_phases"] = len(phases)

        for phase_id, phase_data in phases.items():
            if not isinstance(phase_data, dict):
                self.errors.append(f"Phase '{phase_id}' is not a dict")
                continue

            if "description" not in phase_data:
                self.warnings.append(f"Phase '{phase_id}' missing description")

            if "steps" not in phase_data:
                self.errors.append(f"Phase '{phase_id}' missing 'steps' array")
                continue

            steps = phase_data["steps"]
            if not isinstance(steps, list):
                self.errors.append(f"Phase '{phase_id}' steps must be a list")
                continue

            for step in steps:
                self.validate_step(step, phase_id)

    def validate_guardrails(self) -> None:
        """Validate guardrail_checkpoints section."""
        if "guardrail_checkpoints" not in self.schema:
            self.warnings.append("Missing 'guardrail_checkpoints' section (optional)")
            return

        guardrails = self.schema["guardrail_checkpoints"]
        self.stats["total_guardrails"] = len(guardrails)

        for gc in guardrails:
            required = {
                "checkpoint_id",
                "phase",
                "step_id",
                "description",
                "validation_logic",
                "on_fail",
            }
            missing = required - set(gc.keys())
            if missing:
                self.errors.append(
                    f"Guardrail '{gc.get('checkpoint_id', 'UNKNOWN')}' missing fields: {missing}"
                )

    def validate_anti_patterns(self) -> None:
        """Validate anti_patterns section."""
        if "anti_patterns" not in self.schema:
            self.warnings.append("Missing 'anti_patterns' section (optional)")
            return

        patterns = self.schema["anti_patterns"]
        for pattern in patterns:
            required = {"id", "description", "detection", "enforcement"}
            missing = required - set(pattern.keys())
            if missing:
                self.warnings.append(
                    f"Anti-pattern '{pattern.get('id', 'UNKNOWN')}' missing fields: {missing}"
                )

    def validate_state_machine_transitions(self) -> None:
        """Validate state machine transitions are valid."""
        if "meta" not in self.schema or "state_machine" not in self.schema["meta"]:
            return

        sm = self.schema["meta"]["state_machine"]
        phases = set(sm.get("phases", []))
        transitions = sm.get("valid_transitions", {})

        for from_state, to_states in transitions.items():
            if from_state == "*":
                continue

            if from_state not in phases:
                self.errors.append(
                    f"Invalid transition from unknown state: {from_state}"
                )

            for to_state in to_states:
                if to_state not in phases and to_state not in ["FAILED", "REJECTED"]:
                    self.errors.append(
                        f"Invalid transition to unknown state: {from_state} → {to_state}"
                    )

    def validate(self) -> bool:
        """Run all validations."""
        if not self.load_schema():
            return False

        print("Validating Glossary System Process Steps Schema...\n")

        self.validate_meta_section()
        self.validate_operation_kinds()
        self.validate_components()
        self.validate_artifact_registry()
        self.validate_phases_section()
        self.validate_guardrails()
        self.validate_anti_patterns()
        self.validate_state_machine_transitions()

        return len(self.errors) == 0

    def print_report(self) -> None:
        """Print validation report."""
        print("=" * 80)
        print("GLOSSARY SYSTEM SCHEMA VALIDATION REPORT")
        print("=" * 80)
        print(f"Schema: {self.schema_path.name}")
        print(f"Version: {self.schema.get('meta', {}).get('version', 'UNKNOWN')}")
        print()

        print("STATISTICS:")
        print(f"  Total Phases: {self.stats['total_phases']}")
        print(f"  Total Steps: {self.stats['total_steps']}")
        print(f"  Total Components: {self.stats['total_components']}")
        print(f"  Total Operations: {self.stats['total_operations']}")
        print(f"  Total Guardrails: {self.stats['total_guardrails']}")
        print(f"  Total Artifacts: {self.stats['total_artifacts']}")
        print()

        # Glossary-specific stats
        if "meta" in self.schema:
            meta = self.schema["meta"]
            print("GLOSSARY SYSTEM STATUS:")
            if (
                "automation_levels" in meta
                and "semi_automatic" in meta["automation_levels"]
            ):
                auto_level = meta["automation_levels"]["semi_automatic"]
                if "validation_score" in auto_level:
                    print(f"  Validation Score: {auto_level['validation_score']}")
                if "total_terms" in auto_level:
                    print(f"  Total Terms: {auto_level['total_terms']}")
            if "state_machine" in meta and "ssot_enforcement" in meta["state_machine"]:
                print(
                    f"  SSOT Enforcement: {meta['state_machine']['ssot_enforcement']}"
                )
            print()

        if self.errors:
            print(f"ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
            print()

        if self.warnings:
            print(f"WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
            print()

        print("=" * 80)
        if self.errors:
            print("RESULT: FAILED ❌")
            print(f"Fix {len(self.errors)} error(s) to pass validation.")
        else:
            print("RESULT: PASSED ✅")
            print("Schema is valid and compliant.")
        print("=" * 80)


def main() -> int:
    """Main entry point."""
    script_dir = Path(__file__).parent
    schema_path = (
        script_dir.parent
        / "schemas"
        / "DOC-CONFIG-GLOSSARY-PROCESS-STEPS-SCHEMA-302__GLOSSARY_PROCESS_STEPS_SCHEMA.yaml"
    )

    if not schema_path.exists():
        print(f"ERROR: Schema file not found: {schema_path}")
        return 1

    validator = GlossaryValidator(schema_path)
    success = validator.validate()
    validator.print_report()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
