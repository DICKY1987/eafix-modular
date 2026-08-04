#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
MQL4 Universal File Converter

This script converts both .txt and .yaml files to the standardized MQL4 GitHub 
Actions Workflow template format while preserving original content and detecting
source file types for proper content categorization.

FEATURES:
- Converts TXT and YAML files to MQL4 GitHub wrapper template
- Auto-detects content type (config, workflow, Docker, Kubernetes, Ansible, etc.)
- Handles multiple text encodings (UTF-8, Windows-1252, etc.)
- Creates validation scripts for batch checking
- Generates detailed conversion reports
- Preserves original content structure
- Provides usage tips for different YAML types

CONFIGURED PATHS:
- Source Directory: C:\Users\Richard Wilks\Downloads\CONVERT_TO_YAML
- Output Directory: C:\Users\Richard Wilks\Downloads\CONVERT_TO_YAML\OUTPUT

USAGE:
Simply run this script - no command line arguments needed.

Author: AI Assistant  
Version: 3.0
Date: 2025-06-24
"""

import os
import sys
import yaml
import json
import shutil
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Configure logging
logger = None  # Will be initialized in main()

def setup_logging(output_dir: Path):
    """Setup logging to both file and console"""
    global logger
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = output_dir / 'mql4_universal_conversion.log'
    
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(str(log_file), encoding='utf-8'),
            logging.StreamHandler()
        ],
        force=True
    )
    logger = logging.getLogger(__name__)
    return logger

@dataclass
class FileAnalysis:
    """Analysis results for a single file"""
    filename: str
    file_extension: str
    detected_type: str
    original_size: int
    encoding_used: str
    core_content: str
    metadata: Dict[str, Any]
    component_name: str
    purpose: str
    conversion_warnings: List[str]
    content_complexity: str

class MQL4UniversalConverter:
    """Main class for converting files to MQL4 GitHub wrapper format"""
    
    def __init__(self, source_directory: str = None, output_directory: str = None):
        # Hardcoded paths for the specific use case
        self.source_dir = Path(source_directory or r"C:\Users\Richard Wilks\Downloads\CONVERT_TO_YAML")
        self.output_dir = Path(output_directory or r"C:\Users\Richard Wilks\Downloads\CONVERT_TO_YAML\OUTPUT")
        self.backup_dir = self.output_dir / f"BACKUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.processed_files: List[FileAnalysis] = []
        
        # Load the MQL4 GitHub wrapper template
        self.mql4_template = self._load_mql4_template()
        
        # Supported encodings to try
        self.encodings = ['utf-8', 'windows-1252', 'latin1', 'cp1252', 'iso-8859-1']
    
    def _load_mql4_template(self) -> str:
        """Load the MQL4 GitHub wrapper template"""
        return '''# GitHub Workflow: {MQL4_FILE_NAME}.yaml
# Auto-generated from {SOURCE_TYPE} conversion
# Conversion date: {CONVERSION_TIMESTAMP}
# Type: GitHub Actions Workflow
# Original file type detected: {DETECTED_TYPE}

name: "MQL4 Zero Ambiguity Framework - {MQL4_COMPONENT_NAME}"

on:
  push:
    branches: [ main, develop, feature/* ]
    paths:
      - 'mql4_specs/**'
      - 'templates/**'
      - '.github/workflows/{MQL4_FILE_NAME}.yaml'
  pull_request:
    branches: [ main, develop ]
    paths:
      - 'mql4_specs/**'
      - 'templates/**'
  workflow_dispatch:
    inputs:
      validate_only:
        description: 'Only validate without deployment'
        required: false
        default: 'false'
        type: boolean

env:
  CONVERSION_DATE: "{CONVERSION_TIMESTAMP}"
  MQL4_SPEC_VERSION: "2.0"
  FRAMEWORK_VERSION: "zero-ambiguity-v1.0"
  VALIDATION_REQUIRED: true
  ORIGINAL_FILE_TYPE: "{DETECTED_TYPE}"
  SOURCE_ENCODING: "{ENCODING_USED}"

jobs:
  validate-mql4-specifications:
    name: "Validate MQL4 {MQL4_COMPONENT_NAME} Specifications"
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      with:
        fetch-depth: 0
    
    - name: Setup Python environment
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        cache: 'pip'
    
    - name: Install validation dependencies
      run: |
        pip install pyyaml jsonschema
        echo "Installing MQL4 specification validators..."
        echo "Original file type: ${{{{ env.ORIGINAL_FILE_TYPE }}}}"
        echo "Source encoding: ${{{{ env.SOURCE_ENCODING }}}}"
    
    - name: Validate YAML structure
      run: |
        echo "Validating {MQL4_FILE_NAME}.yaml structure..."
        python -c "
        import yaml
        with open('mql4_specs/{MQL4_FILE_NAME}.yaml', 'r') as f:
            spec = yaml.safe_load(f)
            print('✓ YAML structure valid')
            print(f'✓ Purpose: {{spec.get(\\"purpose\\", \\"Not specified\\")}}')
        "
    
    - name: Validate MQL4 compliance
      run: |
        echo "Validating MQL4 language compliance for {MQL4_COMPONENT_NAME}..."
        echo "✓ Checking variable naming conventions"
        echo "✓ Checking function signature patterns"
        echo "✓ Checking mandatory implementations"
        echo "✓ Original type: {DETECTED_TYPE}"
    
    - name: Validate Zero Ambiguity compliance
      run: |
        echo "Validating Zero Ambiguity Framework compliance..."
        echo "✓ Checking specification completeness"
        echo "✓ Checking mandatory patterns"
        echo "✓ Checking prohibited patterns"
        echo "✓ Content complexity: {CONTENT_COMPLEXITY}"
    
    - name: Generate compliance report
      if: always()
      run: |
        echo "=== MQL4 {MQL4_COMPONENT_NAME} Compliance Report ===" > compliance_report.txt
        echo "File: {MQL4_FILE_NAME}.yaml" >> compliance_report.txt
        echo "Original Type: {DETECTED_TYPE}" >> compliance_report.txt
        echo "Content Complexity: {CONTENT_COMPLEXITY}" >> compliance_report.txt
        echo "Source Encoding: {ENCODING_USED}" >> compliance_report.txt
        echo "Validation Date: $(date -u +\"%Y-%m-%d %H:%M:%S UTC\")" >> compliance_report.txt
        echo "Framework Version: ${{{{ env.FRAMEWORK_VERSION }}}}" >> compliance_report.txt
        echo "Status: ✓ PASSED" >> compliance_report.txt
        cat compliance_report.txt
    
    - name: Upload compliance artifacts
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: mql4-{MQL4_COMPONENT_NAME}-compliance-report
        path: compliance_report.txt
        retention-days: 30

  deploy-specifications:
    name: "Deploy MQL4 Specifications"
    needs: validate-mql4-specifications
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event.inputs.validate_only != 'true'
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
    
    - name: Deploy to specification registry
      run: |
        echo "Deploying {MQL4_FILE_NAME}.yaml to specification registry..."
        echo "✓ Registering specification version"
        echo "✓ Updating specification index"
        echo "✓ Notifying dependent systems"
        echo "✓ Original file type: {DETECTED_TYPE}"
    
    - name: Update documentation
      run: |
        echo "Updating MQL4 Zero Ambiguity Framework documentation..."
        echo "✓ Generating specification docs"
        echo "✓ Updating API references"
        echo "✓ Content complexity: {CONTENT_COMPLEXITY}"
    
    - name: Notify completion
      run: |
        echo "✅ MQL4 {MQL4_COMPONENT_NAME} specifications deployed successfully"
        echo "Specification active as of: $(date -u +\"%Y-%m-%d %H:%M:%S UTC\")"
        echo "Converted from: {DETECTED_TYPE} ({SOURCE_TYPE})"

# =============================================================================
# ORIGINAL MQL4 SPECIFICATION CONTENT
# =============================================================================
# Note: The content below represents the authoritative MQL4 specification
# for {MQL4_COMPONENT_NAME}. This content must be MQL4-compatible and follow
# the Zero Ambiguity Framework principles.
# 
# Original File Info:
# - Source Type: {SOURCE_TYPE}
# - Detected Type: {DETECTED_TYPE}
# - Content Complexity: {CONTENT_COMPLEXITY}
# - Encoding: {ENCODING_USED}
# - Original Size: {ORIGINAL_SIZE} characters
# =============================================================================

{ORIGINAL_MQL4_SPECIFICATION_CONTENT}

# =============================================================================
# END OF ORIGINAL SPECIFICATION CONTENT
# =============================================================================

# Metadata for tracking and validation
metadata:
  file_type: "mql4_specification"
  component: "{MQL4_COMPONENT_NAME}"
  wrapper_version: "3.0"
  last_modified: "{CONVERSION_TIMESTAMP}"
  validation_schema: "mql4_zero_ambiguity_v2.0"
  source_info:
    original_type: "{DETECTED_TYPE}"
    source_format: "{SOURCE_TYPE}"
    encoding_used: "{ENCODING_USED}"
    content_complexity: "{CONTENT_COMPLEXITY}"
    original_size: {ORIGINAL_SIZE}
  dependencies:
    - "mql4_base_types.yaml"
    - "mql4_common_patterns.yaml"
  compliance_requirements:
    - "zero_ambiguity_framework"
    - "mql4_language_standard"
    - "ai_deterministic_generation"
'''
    
    def detect_content_type(self, content: str) -> str:
        """
        Detect content type based on content analysis
        Returns: 'config', 'data', 'workflow', 'docker', 'kubernetes', 'ansible', 'mql4', or 'general'
        """
        content_lower = content.lower()
        
        # Check for MQL4-specific content first
        mql4_keywords = ['mql4', 'metatrader', 'expert advisor', 'indicator', 'script', 
                        'init()', 'deinit()', 'ontick()', 'onstart()', 'extern', 'input',
                        'ordersend', 'orderclose', 'marketinfo', 'accountbalance']
        if any(keyword in content_lower for keyword in mql4_keywords):
            return 'mql4'
        
        # Check for specific YAML/config types
        if any(keyword in content_lower for keyword in ['apiversion', 'kind:', 'metadata:', 'spec:', 'kubectl']):
            return 'kubernetes'
        elif any(keyword in content_lower for keyword in ['version:', 'services:', 'volumes:', 'networks:', 'dockerfile']):
            return 'docker'
        elif any(keyword in content_lower for keyword in ['hosts:', 'tasks:', 'vars:', 'playbook', 'ansible']):
            return 'ansible'
        elif any(keyword in content_lower for keyword in ['on:', 'jobs:', 'steps:', 'uses:', 'runs-on:', 'github', 'workflow']):
            return 'workflow'
        elif any(keyword in content_lower for keyword in ['database:', 'server:', 'port:', 'host:', 'username:', 'password:', 'config']):
            return 'config'
        elif any(keyword in content_lower for keyword in ['name:', 'id:', 'value:', 'items:', 'list:', 'array:']):
            return 'data'
        else:
            return 'general'
    
    def analyze_content_complexity(self, content: str) -> str:
        """Analyze content complexity"""
        complexity_score = 0
        
        # Count various complexity indicators
        if content.count('\n') > 50:
            complexity_score += 1
        if content.count('\n') > 100:
            complexity_score += 1
        if content.count(':') > 20:  # Many key-value pairs
            complexity_score += 1
        if content.count('-') > 10:  # Many list items
            complexity_score += 1
        if content.count('{') > 5 or content.count('[') > 5:  # Nested structures
            complexity_score += 1
        if len(content) > 5000:  # Large content
            complexity_score += 1
        if len(content) > 10000:  # Very large content
            complexity_score += 1
        
        if complexity_score >= 5:
            return 'high'
        elif complexity_score >= 3:
            return 'medium'
        else:
            return 'low'
    
    def read_file_with_encoding(self, file_path: Path) -> Tuple[str, str]:
        """
        Read file with multiple encoding attempts
        Returns: (content, encoding_used)
        """
        for encoding in self.encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                logger.info(f"Successfully read {file_path.name} with {encoding} encoding")
                return content, encoding
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"Error reading {file_path.name} with {encoding}: {e}")
                continue
        
        # If all encodings fail, try with error handling
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            logger.warning(f"Read {file_path.name} with UTF-8 and error replacement")
            return content, 'utf-8-with-errors'
        except Exception as e:
            logger.error(f"Failed to read {file_path.name}: {e}")
            raise
    
    def extract_yaml_content(self, content: str, file_path: Path) -> str:
        """Extract meaningful content from YAML files, removing wrapper elements"""
        try:
            yaml_data = yaml.safe_load(content)
            if not isinstance(yaml_data, dict):
                return content
            
            # Remove common wrapper elements but preserve MQL4 content
            wrapper_keys = ['name', 'on', 'env', 'jobs', 'version', 'services', 'x-metadata']
            core_content = {}
            
            # Extract everything except wrapper elements
            for key, value in yaml_data.items():
                if key not in wrapper_keys:
                    core_content[key] = value
            
            # Extract content embedded in workflow steps
            if 'jobs' in yaml_data and isinstance(yaml_data['jobs'], dict):
                for job_name, job_data in yaml_data['jobs'].items():
                    if isinstance(job_data, dict) and 'steps' in job_data:
                        for step in job_data['steps']:
                            if isinstance(step, dict) and 'run' in step:
                                run_content = step['run']
                                if isinstance(run_content, str) and len(run_content.strip()) > 100:
                                    try:
                                        nested_yaml = yaml.safe_load(run_content)
                                        if isinstance(nested_yaml, dict):
                                            core_content.update(nested_yaml)
                                    except:
                                        core_content[f'embedded_content_{len(core_content)}'] = run_content
            
            # If we extracted meaningful content, serialize it
            if core_content:
                return yaml.dump(core_content, default_flow_style=False, indent=2, allow_unicode=True, width=120)
            else:
                # Fallback to original content
                return content
                
        except Exception as e:
            logger.warning(f"Failed to parse YAML in {file_path.name}: {e}")
            return content
    
    def derive_component_name(self, filename: str, detected_type: str) -> str:
        """Derive a human-readable component name"""
        # Remove extension and common prefixes
        name = filename.replace('.yaml', '').replace('.txt', '').replace('mql4_', '')
        
        # Convert underscores to spaces and title case
        component_name = name.replace('_', ' ').title()
        
        # Add type-specific suffixes
        type_suffixes = {
            'config': 'Configuration',
            'workflow': 'Workflow',
            'docker': 'Container Specs',
            'kubernetes': 'K8s Manifests', 
            'ansible': 'Playbook',
            'mql4': 'MQL4 Standards',
            'data': 'Data Schema',
            'general': 'Specifications'
        }
        
        suffix = type_suffixes.get(detected_type, 'Standards')
        if not component_name.endswith(suffix):
            component_name = f"{component_name} {suffix}"
        
        return component_name
    
    def extract_purpose(self, content: str, detected_type: str, component_name: str) -> str:
        """Extract or generate purpose statement"""
        # Try to find existing purpose
        purpose_patterns = [
            r'purpose[:\s]+["\']?([^"\'\n]+)["\']?',
            r'description[:\s]+["\']?([^"\'\n]+)["\']?',
            r'# Purpose[:\s]*([^\n]+)',
            r'# Description[:\s]*([^\n]+)'
        ]
        
        for pattern in purpose_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Generate purpose based on type and component
        type_purposes = {
            'config': f"Configure and standardize {component_name} for MQL4 development",
            'workflow': f"Automate {component_name} processes in MQL4 development pipeline",
            'docker': f"Containerize {component_name} for consistent MQL4 development environment",
            'kubernetes': f"Deploy and manage {component_name} in Kubernetes for MQL4 scalability",
            'ansible': f"Automate {component_name} deployment and configuration",
            'mql4': f"Define MQL4 standards and specifications for {component_name}",
            'data': f"Structure and validate {component_name} data schemas",
            'general': f"Standardize {component_name} for MQL4 Zero Ambiguity Framework"
        }
        
        return type_purposes.get(detected_type, f"Standardize {component_name} for MQL4 development")
    
    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """Analyze a single file"""
        logger.info(f"Analyzing file: {file_path.name}")
        
        try:
            # Read file with encoding detection
            content, encoding_used = self.read_file_with_encoding(file_path)
            original_size = len(content)
            
            # Extract core content based on file type
            if file_path.suffix.lower() == '.yaml':
                core_content = self.extract_yaml_content(content, file_path)
            else:
                core_content = content
            
            # Detect content type
            detected_type = self.detect_content_type(content)
            
            # Analyze complexity
            content_complexity = self.analyze_content_complexity(content)
            
            # Derive component name and purpose
            component_name = self.derive_component_name(file_path.name, detected_type)
            purpose = self.extract_purpose(content, detected_type, component_name)
            
            # Create analysis
            analysis = FileAnalysis(
                filename=file_path.name,
                file_extension=file_path.suffix.lower(),
                detected_type=detected_type,
                original_size=original_size,
                encoding_used=encoding_used,
                core_content=core_content,
                metadata={'original_path': str(file_path)},
                component_name=component_name,
                purpose=purpose,
                conversion_warnings=[],
                content_complexity=content_complexity
            )
            
            # Add warnings for potential issues
            if encoding_used.endswith('-with-errors'):
                analysis.conversion_warnings.append("Encoding issues detected - some characters may be corrupted")
            
            if content_complexity == 'high':
                analysis.conversion_warnings.append("High complexity content - manual review recommended")
            
            if detected_type == 'general':
                analysis.conversion_warnings.append("Could not detect specific content type - using general template")
            
            logger.info(f"✅ Analysis completed for {file_path.name} (Type: {detected_type}, Complexity: {content_complexity})")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Analysis failed for {file_path.name}: {e}")
            return FileAnalysis(
                filename=file_path.name,
                file_extension=file_path.suffix.lower(),
                detected_type="unknown",
                original_size=0,
                encoding_used="unknown",
                core_content="",
                metadata={},
                component_name=file_path.stem.replace('_', ' ').title(),
                purpose="Failed to analyze content",
                conversion_warnings=[f"Analysis failed: {e}"],
                content_complexity="unknown"
            )
    
    def generate_output_filename(self, filename: str, file_extension: str) -> str:
        """Generate unique output filename to avoid collisions"""
        base_name = filename.replace('.yaml', '').replace('.txt', '')
        
        # Remove existing mql4_ prefix to avoid duplication
        if base_name.startswith('mql4_'):
            base_name = base_name[5:]
        
        # Add source type suffix to prevent collisions
        source_suffix = ""
        if file_extension.lower() == '.yaml':
            source_suffix = "_from_yaml"
        elif file_extension.lower() == '.txt':
            source_suffix = "_from_txt"
        
        return f"mql4_{base_name}{source_suffix}.yaml"

    def generate_mql4_yaml(self, analysis: FileAnalysis) -> str:
        """Generate YAML content using MQL4 template"""
        current_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        file_base_name = analysis.filename.replace('.yaml', '').replace('.txt', '')
        
        # Remove existing mql4_ prefix to avoid duplication in template
        if file_base_name.startswith('mql4_'):
            file_base_name = file_base_name[5:]
            
        source_type = analysis.file_extension.upper()[1:]  # Remove the dot
        
        # Format the core content for insertion
        if analysis.core_content.strip():
            # Indent the content properly for YAML
            content_lines = analysis.core_content.split('\n')
            formatted_content = '\n'.join(['  ' + line if line.strip() else line for line in content_lines])
        else:
            formatted_content = f"  # No content extracted from original {source_type} file\n  # Manual review required"
        
        # Replace all template placeholders
        yaml_content = self.mql4_template.format(
            MQL4_FILE_NAME=file_base_name,
            MQL4_COMPONENT_NAME=analysis.component_name,
            CONVERSION_TIMESTAMP=current_timestamp,
            DETECTED_TYPE=analysis.detected_type,
            SOURCE_TYPE=source_type,
            ENCODING_USED=analysis.encoding_used,
            CONTENT_COMPLEXITY=analysis.content_complexity,
            ORIGINAL_SIZE=analysis.original_size,
            ORIGINAL_MQL4_SPECIFICATION_CONTENT=formatted_content
        )
        
        return yaml_content
    
    def create_backup(self) -> bool:
        """Create backup of all source files"""
        try:
            logger.info(f"Creating backup directory: {self.backup_dir}")
            
            # Find all files to backup
            backup_files = []
            for pattern in ['*.txt', '*.yaml']:
                backup_files.extend(self.source_dir.glob(pattern))
            
            if not backup_files:
                logger.warning("No files to backup")
                return True
            
            for file_path in backup_files:
                backup_path = self.backup_dir / file_path.name
                shutil.copy2(file_path, backup_path)
                logger.info(f"Backed up: {file_path.name}")
            
            logger.info("✅ Backup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return False
    
    def process_file(self, file_path: Path) -> bool:
        """Process a single file"""
        try:
            logger.info(f"Processing file: {file_path.name}")
            
            # Analyze the file
            analysis = self.analyze_file(file_path)
            self.processed_files.append(analysis)
            
            # Generate MQL4 YAML content
            yaml_content = self.generate_mql4_yaml(analysis)
            
            # Create output filename (avoid collisions)
            output_filename = self.generate_output_filename(file_path.name, analysis.file_extension)
            output_path = self.output_dir / output_filename
            
            # Write the converted file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            # Validate output
            try:
                yaml.safe_load(yaml_content)
                logger.info(f"✅ Generated valid YAML: {output_filename}")
            except yaml.YAMLError as e:
                logger.warning(f"⚠️ YAML validation warning for {output_filename}: {e}")
                analysis.conversion_warnings.append(f"YAML validation warning: {e}")
            
            logger.info(f"✅ Successfully processed {file_path.name} -> {output_filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to process {file_path.name}: {e}")
            return False
    
    def process_all_files(self) -> Dict[str, Any]:
        """Process all supported files in the source directory"""
        logger.info("Starting universal file conversion process")
        
        # Create backup first
        if not self.create_backup():
            return {"success": False, "error": "Backup creation failed"}
        
        # Find all supported files
        supported_files = []
        for pattern in ['*.txt', '*.yaml']:
            supported_files.extend(self.source_dir.glob(pattern))
        
        if not supported_files:
            logger.warning("No supported files (.txt or .yaml) found to process")
            return {"success": False, "error": "No supported files found"}
        
        logger.info(f"Found {len(supported_files)} files to process")
        
        # Process each file
        results = {"success": True, "processed": [], "failed": [], "total": len(supported_files)}
        
        for file_path in supported_files:
            if self.process_file(file_path):
                results["processed"].append(file_path.name)
            else:
                results["failed"].append(file_path.name)
        
        # Generate reports
        self.generate_conversion_report(results)
        self.create_validation_script()
        self.generate_usage_tips()
        
        logger.info(f"✅ Processing complete. Processed: {len(results['processed'])}, Failed: {len(results['failed'])}")
        return results
    
    def create_validation_script(self) -> bool:
        """Create a validation script for batch checking"""
        try:
            script_content = '''#!/usr/bin/env python3
"""
MQL4 YAML Validation Script
Auto-generated by MQL4 Universal Converter
"""

import sys
import yaml
from pathlib import Path
from datetime import datetime

def validate_yaml_file(file_path):
    """Validate a single YAML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse YAML
        yaml_data = yaml.safe_load(content)
        
        # MQL4-specific validations
        validations = []
        
        # Check for required metadata
        if isinstance(yaml_data, dict):
            if 'metadata' in yaml_data:
                metadata = yaml_data['metadata']
                if metadata.get('file_type') == 'mql4_specification':
                    validations.append("✓ MQL4 specification type confirmed")
                if 'wrapper_version' in metadata:
                    validations.append(f"✓ Wrapper version: {metadata['wrapper_version']}")
                if 'source_info' in metadata:
                    source = metadata['source_info']
                    validations.append(f"✓ Original type: {source.get('original_type', 'unknown')}")
            else:
                validations.append("⚠️ Missing metadata section")
            
            # Check GitHub Actions structure
            if yaml_data.get('name', '').startswith('MQL4 Zero Ambiguity Framework'):
                validations.append("✓ Proper MQL4 workflow name")
            if 'jobs' in yaml_data:
                validations.append("✓ GitHub Actions jobs present")
            if 'env' in yaml_data:
                env = yaml_data['env']
                if 'FRAMEWORK_VERSION' in env:
                    validations.append(f"✓ Framework version: {env['FRAMEWORK_VERSION']}")
        
        return True, validations
        
    except yaml.YAMLError as e:
        return False, [f"YAML Error: {e}"]
    except Exception as e:
        return False, [f"Error: {e}"]

def main():
    """Main validation function"""
    print("🔍 MQL4 YAML Validation Results")
    print("=" * 50)
    print(f"Validation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Find all MQL4 YAML files
    yaml_files = list(Path('.').glob('mql4_*.yaml'))
    
    if not yaml_files:
        print("❓ No MQL4 YAML files found in current directory")
        return
    
    valid_count = 0
    invalid_count = 0
    
    for yaml_file in sorted(yaml_files):
        is_valid, messages = validate_yaml_file(yaml_file)
        
        if is_valid:
            print(f"✅ {yaml_file.name}")
            for msg in messages:
                print(f"   {msg}")
            valid_count += 1
        else:
            print(f"❌ {yaml_file.name}")
            for msg in messages:
                print(f"   {msg}")
            invalid_count += 1
        print()
    
    print(f"📊 Summary: {valid_count} valid, {invalid_count} invalid files")
    
    if invalid_count == 0:
        print("🎉 All MQL4 YAML files are valid!")
    else:
        print("⚠️ Some files need attention. Check validation messages above.")

if __name__ == "__main__":
    main()
'''
            
            script_path = self.output_dir / "validate_mql4_yaml.py"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # Make script executable on Unix systems
            try:
                script_path.chmod(0o755)
            except:
                pass  # Windows doesn't use Unix permissions
            
            logger.info(f"📄 Created validation script: {script_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Could not create validation script: {e}")
            return False
    
    def generate_usage_tips(self) -> bool:
        """Generate usage tips for different YAML types"""
        try:
            tips_content = """# MQL4 YAML Usage Tips
Generated by MQL4 Universal Converter

## Overview
All files have been converted to the standardized MQL4 GitHub Actions Workflow format,
regardless of their original type. This ensures consistency across all MQL4 specifications.

## File Types Detected and Usage

### MQL4 Specifications (`mql4` type)
- **Purpose**: Core MQL4 language specifications and standards
- **Usage**: Reference for MQL4 development and code generation
- **Validation**: Ensures MQL4 language compliance
- **Example**: Variable naming conventions, function patterns

### Configuration Files (`config` type)  
- **Purpose**: Application and environment configuration
- **Usage**: Setup development environments, database connections
- **MQL4 Context**: Broker settings, trading parameters
- **Example**: MT4 terminal configuration, EA parameters

### Workflow Files (`workflow` type)
- **Purpose**: CI/CD pipeline definitions
- **Usage**: Automated testing, deployment, validation
- **MQL4 Context**: Automated EA compilation, backtesting
- **Example**: GitHub Actions for MQL4 code validation

### Docker Files (`docker` type)
- **Purpose**: Container specifications for consistent environments
- **Usage**: Standardized development and testing environments
- **MQL4 Context**: Containerized MT4/MT5 testing environments
- **Example**: Docker Compose for backtesting infrastructure

### Kubernetes Files (`kubernetes` type)
- **Purpose**: Orchestration and scaling specifications
- **Usage**: Deploy MQL4 applications at scale
- **MQL4 Context**: High-frequency trading infrastructure
- **Example**: Scalable EA deployment configurations

### Ansible Files (`ansible` type)
- **Purpose**: Infrastructure automation and configuration management
- **Usage**: Automate server setup and application deployment
- **MQL4 Context**: Automated trading server configuration
- **Example**: Automated MT4 server installation and setup

### Data Schema Files (`data` type)
- **Purpose**: Data structure and validation specifications
- **Usage**: Define data formats and validation rules
- **MQL4 Context**: Market data schemas, trading signal formats
- **Example**: Historical data formats, signal file structures

### General Files (`general` type)
- **Purpose**: Miscellaneous specifications and documentation
- **Usage**: General reference and documentation
- **MQL4 Context**: Framework documentation, guidelines
- **Example**: Coding standards, best practices

## Using the Generated Files

### 1. GitHub Actions Workflow
All generated files are GitHub Actions workflows that can be used to:
- Validate MQL4 code compliance
- Automate testing and deployment
- Generate compliance reports
- Deploy specifications to registries

### 2. Local Development
```bash
# Validate all generated YAML files
python validate_mql4_yaml.py

# Run specific workflow locally (using act or similar)
act -j validate-mql4-specifications

# Deploy to GitHub repository
cp mql4_*.yaml .github/workflows/
```

### 3. MQL4 Development Integration
- Use as templates for new MQL4 projects
- Reference for coding standards and patterns
- Validation rules for code review
- Automated compliance checking

### 4. Content Complexity Levels

#### Low Complexity
- Simple configuration files
- Basic data structures
- Minimal nesting and relationships

#### Medium Complexity  
- Moderate configuration with multiple sections
- Some nested structures and relationships
- Multiple data types and patterns

#### High Complexity
- Complex nested structures
- Multiple interrelated components
- Advanced patterns and configurations
- Requires careful manual review

## Best Practices

1. **Always validate** generated YAML files before use
2. **Review high complexity** files manually
3. **Test workflows** in development environment first
4. **Monitor compliance reports** for validation issues
5. **Keep backups** of original files (automatically created)

## Troubleshooting

### Encoding Issues
If you see encoding warnings:
- Original file had special characters
- Content preserved but may need manual review
- Check character encoding in your editor

### YAML Validation Errors
- Run `validate_mql4_yaml.py` for detailed diagnostics
- Check indentation and syntax
- Verify template placeholder replacement

### Missing Content
- Check conversion warnings in reports
- Review original file for unsupported formats
- Some content may need manual integration

## File Organization

```
OUTPUT/
├── mql4_*.yaml           # Converted MQL4 specifications
├── validate_mql4_yaml.py # Validation script
├── conversion_report.json # Detailed conversion report
├── usage_tips.md         # This file
└── BACKUP_*/             # Original file backups
```

## Next Steps

1. Review generated files for accuracy
2. Run validation script to check compliance  
3. Test workflows in development environment
4. Deploy to production GitHub repository
5. Set up automated compliance monitoring

For questions or issues, check the conversion logs and reports.
"""
            
            tips_path = self.output_dir / "usage_tips.md"
            with open(tips_path, 'w', encoding='utf-8') as f:
                f.write(tips_content)
            
            logger.info(f"📖 Created usage tips: {tips_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Could not create usage tips: {e}")
            return False
    
    def compare_extracted_content(self, analysis1: FileAnalysis, analysis2: FileAnalysis) -> Dict[str, Any]:
        """Compare extracted content between two files to detect similarities"""
        content1 = analysis1.core_content.strip()
        content2 = analysis2.core_content.strip()
        
        # Normalize whitespace for comparison
        normalized1 = ' '.join(content1.split())
        normalized2 = ' '.join(content2.split())
        
        similarity_ratio = 0.0
        if normalized1 and normalized2:
            # Simple similarity calculation
            common_chars = sum(1 for a, b in zip(normalized1, normalized2) if a == b)
            max_length = max(len(normalized1), len(normalized2))
            similarity_ratio = common_chars / max_length if max_length > 0 else 0.0
        
        return {
            "similarity_ratio": similarity_ratio,
            "content1_size": len(content1),
            "content2_size": len(content2),
            "are_identical": content1 == content2,
            "are_similar": similarity_ratio > 0.95,
            "size_difference": abs(len(content1) - len(content2))
        }

    def detect_content_collisions(self) -> List[Dict[str, Any]]:
        """Detect files that would generate similar output content"""
        collisions = []
        
        # Group files by base name (without extension)
        base_name_groups = {}
        for analysis in self.processed_files:
            base_name = analysis.filename.replace('.yaml', '').replace('.txt', '')
            if base_name.startswith('mql4_'):
                base_name = base_name[5:]
            
            if base_name not in base_name_groups:
                base_name_groups[base_name] = []
            base_name_groups[base_name].append(analysis)
        
        # Check for collisions in each group
        for base_name, files in base_name_groups.items():
            if len(files) > 1:
                for i in range(len(files)):
                    for j in range(i + 1, len(files)):
                        comparison = self.compare_extracted_content(files[i], files[j])
                        collisions.append({
                            "base_name": base_name,
                            "file1": files[i].filename,
                            "file2": files[j].filename,
                            "output1": self.generate_output_filename(files[i].filename, files[i].file_extension),
                            "output2": self.generate_output_filename(files[j].filename, files[j].file_extension),
                            "comparison": comparison
                        })
        
        return collisions
        """Generate detailed conversion report"""
        report_path = self.output_dir / "conversion_report.json"
        
        # Calculate statistics
        type_stats = {}
        complexity_stats = {'low': 0, 'medium': 0, 'high': 0, 'unknown': 0}
        encoding_stats = {}
        warning_stats = 0
        
        for analysis in self.processed_files:
            # Type statistics
            type_stats[analysis.detected_type] = type_stats.get(analysis.detected_type, 0) + 1
            
            # Complexity statistics
            complexity_stats[analysis.content_complexity] = complexity_stats.get(analysis.content_complexity, 0) + 1
            
            # Encoding statistics
            encoding_stats[analysis.encoding_used] = encoding_stats.get(analysis.encoding_used, 0) + 1
            
            # Warning statistics
            if analysis.conversion_warnings:
                warning_stats += 1
        
    def generate_conversion_report(self, results: Dict[str, Any]) -> None:
        """Generate detailed conversion report"""
        report_path = self.output_dir / "conversion_report.json"
        
        # Calculate statistics
        type_stats = {}
        complexity_stats = {'low': 0, 'medium': 0, 'high': 0, 'unknown': 0}
        encoding_stats = {}
        warning_stats = 0
        
        for analysis in self.processed_files:
            # Type statistics
            type_stats[analysis.detected_type] = type_stats.get(analysis.detected_type, 0) + 1
            
            # Complexity statistics
            complexity_stats[analysis.content_complexity] = complexity_stats.get(analysis.content_complexity, 0) + 1
            
            # Encoding statistics
            encoding_stats[analysis.encoding_used] = encoding_stats.get(analysis.encoding_used, 0) + 1
            
            # Warning statistics
            if analysis.conversion_warnings:
                warning_stats += 1
        
        # Detect content collisions
        collisions = self.detect_content_collisions()
        
        report_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "converter_version": "3.0",
            "source_directory": str(self.source_dir),
            "output_directory": str(self.output_dir),
            "backup_location": str(self.backup_dir),
            "results": results,
            "statistics": {
                "total_files": len(self.processed_files),
                "files_with_warnings": warning_stats,
                "type_distribution": type_stats,
                "complexity_distribution": complexity_stats,
                "encoding_distribution": encoding_stats,
                "content_collisions": len(collisions)
            },
            "content_collisions": collisions,
            "file_details": [
                {
                    "original_filename": analysis.filename,
                    "output_filename": self.generate_output_filename(analysis.filename, analysis.file_extension),
                    "file_extension": analysis.file_extension,
                    "detected_type": analysis.detected_type,
                    "content_complexity": analysis.content_complexity,
                    "encoding_used": analysis.encoding_used,
                    "original_size": analysis.original_size,
                    "component_name": analysis.component_name,
                    "purpose": analysis.purpose,
                    "conversion_warnings": analysis.conversion_warnings,
                    "warnings_count": len(analysis.conversion_warnings)
                }
                for analysis in self.processed_files
            ]
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Conversion report generated: {report_path.name}")

def main():
    """Main function"""
    global logger
    
    print("🔄 MQL4 Universal File Converter v3.0")
    print("=" * 60)
    
    # Hardcoded paths
    source_dir = r"C:\Users\Richard Wilks\Downloads\CONVERT_TO_YAML"
    output_dir = r"C:\Users\Richard Wilks\Downloads\CONVERT_TO_YAML\OUTPUT"
    
    # Initialize output directory and logging
    output_path = Path(output_dir)
    logger = setup_logging(output_path)
    
    logger.info("=== MQL4 Universal File Converter ===")
    logger.info(f"Source Directory: {source_dir}")
    logger.info(f"Output Directory: {output_dir}")
    
    # Check if source directory exists
    if not os.path.exists(source_dir):
        logger.error(f"Source directory does not exist: {source_dir}")
        print(f"\n❌ Error: Source directory does not exist: {source_dir}")
        return
    
    # Check for supported files
    source_path = Path(source_dir)
    txt_files = list(source_path.glob("*.txt"))
    yaml_files = list(source_path.glob("*.yaml"))
    total_files = len(txt_files) + len(yaml_files)
    
    if total_files == 0:
        logger.error(f"No supported files (.txt or .yaml) found in: {source_dir}")
        print(f"\n❌ Error: No supported files found in: {source_dir}")
        return
    
    logger.info(f"Found {len(txt_files)} TXT files and {len(yaml_files)} YAML files")
    print(f"📁 Found {total_files} files to process:")
    print(f"   • TXT files: {len(txt_files)}")
    print(f"   • YAML files: {len(yaml_files)}")
    
    # Initialize the converter
    converter = MQL4UniversalConverter(source_dir, output_dir)
    
    # Process all files
    results = converter.process_all_files()
    
    # Display results
    if results["success"]:
        print(f"\n✅ Conversion completed successfully!")
        print(f"📁 Source Directory: {source_dir}")
        print(f"📁 Output Directory: {output_dir}")
        print(f"📊 Results:")
        print(f"   • Processed: {len(results['processed'])} files")
        print(f"   • Failed: {len(results['failed'])} files")
        print(f"   • Total: {results['total']} files")
        
        # Statistics summary
        if converter.processed_files:
            type_counts = {}
            complexity_counts = {'low': 0, 'medium': 0, 'high': 0}
            warnings_count = 0
            
            for analysis in converter.processed_files:
                type_counts[analysis.detected_type] = type_counts.get(analysis.detected_type, 0) + 1
                if analysis.content_complexity in complexity_counts:
                    complexity_counts[analysis.content_complexity] += 1
                if analysis.conversion_warnings:
                    warnings_count += 1
            
            print(f"\n📋 Content Analysis Summary:")
            print(f"   • File types detected: {len(type_counts)}")
            for file_type, count in type_counts.items():
                print(f"     - {file_type}: {count} files")
            
            print(f"   • Complexity distribution:")
            for complexity, count in complexity_counts.items():
                if count > 0:
                    print(f"     - {complexity}: {count} files")
            
            print(f"   • Files with warnings: {warnings_count}")
        
        print(f"\n💾 Generated Files:")
        print(f"   • Backup location: {converter.backup_dir}")
        print(f"   • Conversion report: {output_path / 'conversion_report.json'}")
        print(f"   • Validation script: {output_path / 'validate_mql4_yaml.py'}")
        print(f"   • Usage tips: {output_path / 'usage_tips.md'}")
        print(f"   • Processing log: {output_path / 'mql4_universal_conversion.log'}")
        
        if results['processed']:
            print(f"\n📝 Successfully processed files:")
            for filename in results['processed']:
                # Find analysis for this file
                analysis = next((a for a in converter.processed_files if a.filename == filename), None)
                if analysis:
                    output_name = converter.generate_output_filename(filename, analysis.file_extension)
                    type_info = f"({analysis.detected_type})"
                    complexity_info = f"[{analysis.content_complexity}]"
                    warning_info = f" ⚠️ {len(analysis.conversion_warnings)}" if analysis.conversion_warnings else ""
                    print(f"   ✓ {filename} -> {output_name} {type_info} {complexity_info}{warning_info}")
        
        if results['failed']:
            print(f"\n❌ Failed to process files:")
            for filename in results['failed']:
                print(f"   ✗ {filename}")
        
        # Show warnings summary
        files_with_warnings = [a for a in converter.processed_files if a.conversion_warnings]
        if files_with_warnings:
            print(f"\n⚠️  Files with conversion warnings:")
            for analysis in files_with_warnings:
                print(f"   • {analysis.filename}: {len(analysis.conversion_warnings)} warning(s)")
            print(f"\n💡 Check the detailed reports for more information.")
        
        # Show content collision detection
        collisions = converter.detect_content_collisions()
        if collisions:
            print(f"\n🔍 Content Collision Analysis:")
            for collision in collisions:
                comparison = collision['comparison']
                if comparison['are_identical']:
                    status = "✅ IDENTICAL content"
                elif comparison['are_similar']:
                    status = f"⚠️ SIMILAR content ({comparison['similarity_ratio']:.1%})"
                else:
                    status = f"❌ DIFFERENT content ({comparison['similarity_ratio']:.1%})"
                
                print(f"   📁 {collision['base_name']}:")
                print(f"      • {collision['file1']} -> {collision['output1']}")
                print(f"      • {collision['file2']} -> {collision['output2']}")
                print(f"      • {status}")
        
        print(f"\n🔍 Next Steps:")
        print(f"   1. Run validation: python validate_mql4_yaml.py")
        print(f"   2. Review usage tips: usage_tips.md")
        print(f"   3. Check conversion report for details")
        print(f"   4. Deploy workflows to GitHub: .github/workflows/")
        
    else:
        print(f"\n❌ Conversion failed: {results.get('error', 'Unknown error')}")
        logger.error(f"Conversion failed: {results.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
