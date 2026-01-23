"""
Write Policy Validator

doc_id: DOC-AUTO-DESC-0013
purpose: Enforces tool_only/immutable/derived field policies
phase: Phase 5 - Registry Writer
"""

from typing import Dict, Any, List, Optional


class WritePolicyValidator:
    """
    Validates registry writes against write policies.
    
    Policy types:
    - tool_only: Only automation tools can write (users blocked)
    - immutable: Cannot be changed after creation
    - derived: Auto-computed, manual writes blocked
    """
    
    def __init__(self, column_dictionary_path: str):
        """
        Initialize validator.
        
        Args:
            column_dictionary_path: Path to COLUMN_DICTIONARY.md
        """
        self.column_dictionary_path = column_dictionary_path
        self._policies: Optional[Dict[str, str]] = None
        
    def load_policies(self) -> None:
        """Load write policies from COLUMN_DICTIONARY.md."""
        # TODO: Implement in Phase 5
        raise NotImplementedError("Phase 5")
        
    def validate_patch(
        self,
        patch: Dict[str, Any],
        current_record: Optional[Dict[str, Any]] = None,
        actor: str = "user"
    ) -> tuple:
        """
        Validate patch against write policies.
        
        Args:
            patch: Patch operations
            current_record: Current registry record (for immutability checks)
            actor: Who is making the change ("user" or "tool")
            
        Returns:
            (is_valid, violations)
        """
        # TODO: Implement in Phase 5
        raise NotImplementedError("Phase 5")
        
    def check_tool_only(self, field: str, actor: str) -> bool:
        """Check if field can be written by actor."""
        # TODO: Implement in Phase 5
        raise NotImplementedError("Phase 5")
        
    def check_immutable(self, field: str, current_value: Any, new_value: Any) -> bool:
        """Check if immutable field is being changed."""
        # TODO: Implement in Phase 5
        raise NotImplementedError("Phase 5")
