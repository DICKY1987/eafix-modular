"""
Test suite initialization

doc_id: DOC-AUTO-DESC-TEST-0001
purpose: Test package initialization
phase: Phase 1 - Architecture
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
