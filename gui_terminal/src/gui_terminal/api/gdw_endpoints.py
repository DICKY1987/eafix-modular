"""
Backend API endpoints for GDW Brick Builder operations
Provides REST API for file ingestion, validation, packaging, and PR creation
"""

from __future__ import annotations
import os
import json
import yaml
import hashlib
import zipfile
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

try:
    from fastapi import FastAPI, HTTPException, UploadFile, File, Form
    from fastapi.responses import JSONResponse, FileResponse
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError:
    FastAPI = None
    HTTPException = None
    UploadFile = None
    File = None
    Form = None
    JSONResponse = None
    FileResponse = None
    BaseModel = None
    Field = None
    uvicorn = None


# Pydantic models for API requests/responses
class GDWIngestRequest(BaseModel):
    files: List[str] = Field(..., description=\"List of file paths to ingest\")

class GDWIngestResponse(BaseModel):
    success: bool
    tentative_spec: Dict[str, Any]
    file_map: Dict[str, str]
    suggestions: List[str]

class ValidationResult(BaseModel):
    file: str
    status: str
    pointer: str
    rule: str
    message: str

class GDWValidationResponse(BaseModel):
    valid: bool
    results: List[ValidationResult]
    summary: str

class GDWPackageResponse(BaseModel):
    success: bool
    package_path: str
    manifest: Dict[str, Any]
    sha256: str

class ChainUpdateRequest(BaseModel):
    gdw_id: str
    version: str
    chain_path: str = \"chains/bootstrap.commit-build-scan-deploy.v1.json\"

class PRCreateRequest(BaseModel):
    title: str
    description: str
    branch_name: str = \"gdw/auto-generated\"
    base_branch: str = \"main\"


class GDWAPIServer:
    \"\"\"Backend API server for GDW Brick Builder operations\"\"\"

    def __init__(self, app: Optional[Any] = None):
        self.app = app or (FastAPI(title=\"GDW Brick Builder API\", version=\"1.0.0\") if FastAPI else None)
        if self.app:
            self._setup_routes()

    def _setup_routes(self):
        \"\"\"Setup API routes\"\"\"
        if not self.app:
            return

        @self.app.post(\"/gdw/ingest\", response_model=GDWIngestResponse)
        async def ingest_files(files: List[str]):
            \"\"\"Ingest files and generate tentative GDW specification\"\"\"
            try:
                return self._ingest_files(files)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post(\"/gdw/validate\", response_model=GDWValidationResponse)
        async def validate_gdw(spec_path: str):
            \"\"\"Validate GDW specification using AJV\"\"\"
            try:
                return self._validate_gdw(spec_path)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post(\"/gdw/chain\")
        async def update_chain(request: ChainUpdateRequest):
            \"\"\"Update chain configuration with new GDW\"\"\"
            try:
                return self._update_chain(request)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post(\"/gdw/package\", response_model=GDWPackageResponse)
        async def package_gdw(gdw_path: str):
            \"\"\"Package GDW as timestamped ZIP\"\"\"
            try:
                return self._package_gdw(gdw_path)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post(\"/gdw/pr\")
        async def create_pr(request: PRCreateRequest):
            \"\"\"Create pull request for GDW changes\"\"\"
            try:
                return self._create_pr(request)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get(\"/registry/tools\")
        async def get_tools():
            \"\"\"Get all registered tools\"\"\"
            try:
                return self._get_tools()
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post(\"/registry/tools\")
        async def update_tools(tools_data: Dict[str, Any]):
            \"\"\"Update tool registry\"\"\"
            try:
                return self._update_tools(tools_data)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post(\"/resolver/simulate\")
        async def simulate_resolution(capability: str, context: Dict[str, Any] = None):
            \"\"\"Simulate tool resolution\"\"\"
            try:
                return self._simulate_resolution(capability, context or {})
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    def _ingest_files(self, files: List[str]) -> GDWIngestResponse:
        \"\"\"Analyze files and generate tentative GDW specification\"\"\"
        file_map = {}
        suggestions = []

        # Classify files by type and role
        for file_path in files:
            if not os.path.exists(file_path):
                continue

            ext = os.path.splitext(file_path)[1].lower()
            basename = os.path.basename(file_path).lower()

            # Determine file role
            if basename == 'spec.json':
                file_map[file_path] = 'spec'
            elif basename.startswith('readme'):
                file_map[file_path] = 'docs'
            elif 'runner' in file_path or ext in ['.py', '.ps1', '.sh']:
                file_map[file_path] = 'runner'
            elif 'test' in file_path or 'fixture' in file_path:
                file_map[file_path] = 'test'
            else:
                file_map[file_path] = 'unknown'

        # Generate tentative spec based on files
        has_python = any(f.endswith('.py') for f in files)
        has_powershell = any(f.endswith('.ps1') for f in files)
        has_bash = any(f.endswith('.sh') for f in files)

        # Suggest GDW ID
        if has_python and has_powershell:
            suggested_id = \"multi.script.runner\"\n        elif has_python:\n            suggested_id = \"python.script.runner\"\n        elif has_powershell:\n            suggested_id = \"powershell.script.runner\"\n        elif has_bash:\n            suggested_id = \"bash.script.runner\"\n        else:\n            suggested_id = \"generic.workflow.runner\"\n        \n        tentative_spec = {\n            \"id\": suggested_id,\n            \"version\": \"1.0.0\",\n            \"summary\": f\"Generated workflow from {len(files)} files\",\n            \"maturity\": \"draft\",\n            \"inputs\": {\n                \"target_path\": {\n                    \"type\": \"string\",\n                    \"required\": True,\n                    \"description\": \"Path to target directory\"\n                }\n            },\n            \"outputs\": {\n                \"result\": \"string\"\n            },\n            \"steps\": [\n                {\n                    \"id\": \"execute_main\",\n                    \"runner\": \"python\" if has_python else (\"powershell\" if has_powershell else \"bash\"),\n                    \"cmd\": \"echo 'Replace with actual implementation'\",\n                    \"timeout_sec\": 300,\n                    \"retry_count\": 1\n                }\n            ],\n            \"determinism\": {\n                \"tool_versions\": {},\n                \"idempotency_key\": \"${id}_${version}_${inputs.hash}\"\n            },\n            \"observability\": {\n                \"emit_jsonl\": True,\n                \"artifact_paths\": []\n            }\n        }\n        \n        # Generate suggestions\n        if not any(f.endswith('.md') for f in files):\n            suggestions.append(\"Consider adding README.md documentation\")\n        \n        if not any('test' in f for f in files):\n            suggestions.append(\"Consider adding test fixtures and validation\")\n            \n        if has_python and has_powershell:\n            suggestions.append(\"Multi-platform workflow detected - ensure cross-platform compatibility\")\n        \n        return GDWIngestResponse(\n            success=True,\n            tentative_spec=tentative_spec,\n            file_map=file_map,\n            suggestions=suggestions\n        )\n    \n    def _validate_gdw(self, spec_path: str) -> GDWValidationResponse:\n        \"\"\"Validate GDW specification using AJV Node.js tools\"\"\"        \n        # Check if spec file exists\n        if not os.path.exists(spec_path):\n            return GDWValidationResponse(\n                valid=False,\n                results=[ValidationResult(\n                    file=spec_path,\n                    status=\"Error\",\n                    pointer=\"/\",\n                    rule=\"file_not_found\",\n                    message=f\"Specification file not found: {spec_path}\"\n                )],\n                summary=\"Specification file not found\"\n            )\n        \n        # Check if Node.js validation tools are available\n        tools_path = os.path.join(\"tools\", \"schema\")\n        if not os.path.exists(tools_path):\n            # Fallback to basic JSON validation\n            return self._basic_json_validation(spec_path)\n        \n        try:\n            # Run AJV validation via Node.js\n            result = subprocess.run(\n                [\"node\", \"validate_gdw.mjs\", spec_path],\n                cwd=tools_path,\n                capture_output=True,\n                text=True,\n                timeout=30\n            )\n            \n            if result.returncode == 0:\n                return GDWValidationResponse(\n                    valid=True,\n                    results=[ValidationResult(\n                        file=spec_path,\n                        status=\"Success\",\n                        pointer=\"/\",\n                        rule=\"schema\",\n                        message=\"GDW specification is valid\"\n                    )],\n                    summary=\"Validation passed successfully\"\n                )\n            else:\n                # Parse validation errors from output\n                return self._parse_ajv_output(result.stdout, result.stderr)\n                \n        except subprocess.TimeoutExpired:\n            return GDWValidationResponse(\n                valid=False,\n                results=[ValidationResult(\n                    file=spec_path,\n                    status=\"Error\",\n                    pointer=\"/\",\n                    rule=\"timeout\",\n                    message=\"Validation timed out\"\n                )],\n                summary=\"Validation timeout\"\n            )\n        except Exception as e:\n            return GDWValidationResponse(\n                valid=False,\n                results=[ValidationResult(\n                    file=spec_path,\n                    status=\"Error\",\n                    pointer=\"/\",\n                    rule=\"validation_error\",\n                    message=f\"Validation failed: {str(e)}\"\n                )],\n                summary=\"Validation error\"\n            )\n    \n    def _basic_json_validation(self, spec_path: str) -> GDWValidationResponse:\n        \"\"\"Basic JSON schema validation fallback\"\"\"        \n        try:\n            with open(spec_path, 'r') as f:\n                spec_data = json.load(f)\n            \n            results = []\n            \n            # Check required fields\n            required_fields = [\"id\", \"version\", \"summary\", \"inputs\", \"outputs\", \"steps\", \"determinism\"]\n            for field in required_fields:\n                if field not in spec_data:\n                    results.append(ValidationResult(\n                        file=spec_path,\n                        status=\"Error\",\n                        pointer=f\"/{field}\",\n                        rule=\"required\",\n                        message=f\"Missing required field: {field}\"\n                    ))\n            \n            # Check ID format\n            if \"id\" in spec_data and not isinstance(spec_data[\"id\"], str):\n                results.append(ValidationResult(\n                    file=spec_path,\n                    status=\"Error\",\n                    pointer=\"/id\",\n                    rule=\"type\",\n                    message=\"ID must be a string\"\n                ))\n            \n            # If no errors, validation passed\n            if not results:\n                results.append(ValidationResult(\n                    file=spec_path,\n                    status=\"Success\",\n                    pointer=\"/\",\n                    rule=\"basic_validation\",\n                    message=\"Basic JSON validation passed\"\n                ))\n                return GDWValidationResponse(valid=True, results=results, summary=\"Basic validation passed\")\n            else:\n                return GDWValidationResponse(\n                    valid=False, \n                    results=results, \n                    summary=f\"Found {len(results)} validation errors\"\n                )\n                \n        except json.JSONDecodeError as e:\n            return GDWValidationResponse(\n                valid=False,\n                results=[ValidationResult(\n                    file=spec_path,\n                    status=\"Error\",\n                    pointer=\"/\",\n                    rule=\"json_syntax\",\n                    message=f\"JSON syntax error: {str(e)}\"\n                )],\n                summary=\"JSON syntax error\"\n            )\n    \n    def _parse_ajv_output(self, stdout: str, stderr: str) -> GDWValidationResponse:\n        \"\"\"Parse AJV validation output\"\"\"        \n        # Simplified parsing - in real implementation, this would parse structured AJV output\n        results = []\n        \n        if stderr:\n            results.append(ValidationResult(\n                file=\"spec.json\",\n                status=\"Error\",\n                pointer=\"/\",\n                rule=\"ajv_error\",\n                message=stderr\n            ))\n        \n        return GDWValidationResponse(\n            valid=False,\n            results=results,\n            summary=\"AJV validation failed\"\n        )\n    \n    def _update_chain(self, request: ChainUpdateRequest) -> Dict[str, Any]:\n        \"\"\"Update chain configuration with new GDW\"\"\"        \n        try:\n            chain_path = request.chain_path\n            \n            # Create chain file if it doesn't exist\n            if not os.path.exists(chain_path):\n                os.makedirs(os.path.dirname(chain_path), exist_ok=True)\n                \n                # Create basic chain structure\n                chain_data = {\n                    \"id\": \"bootstrap.commit-build-scan-deploy\",\n                    \"version\": \"1.0.0\",\n                    \"summary\": \"Bootstrap chain for GDW workflows\",\n                    \"nodes\": {},\n                    \"edges\": []\n                }\n            else:\n                with open(chain_path, 'r') as f:\n                    chain_data = json.load(f)\n            \n            # Add new node to chain\n            node_id = request.gdw_id.replace('.', '_')\n            chain_data[\"nodes\"][node_id] = {\n                \"ref\": f\"{request.gdw_id}@{request.version}\",\n                \"alias\": node_id\n            }\n            \n            # Save updated chain\n            with open(chain_path, 'w') as f:\n                json.dump(chain_data, f, indent=2)\n            \n            return {\"success\": True, \"message\": f\"Added {request.gdw_id} to chain {chain_path}\"}\n            \n        except Exception as e:\n            return {\"success\": False, \"error\": str(e)}\n    \n    def _package_gdw(self, gdw_path: str) -> GDWPackageResponse:\n        \"\"\"Package GDW as timestamped ZIP\"\"\"        \n        timestamp = datetime.now().strftime(\"%Y%m%d_%H%M%S\")\n        package_name = f\"gdw_project_pack_{timestamp}.zip\"\n        package_path = os.path.join(\"packages\", package_name)\n        \n        os.makedirs(\"packages\", exist_ok=True)\n        \n        try:\n            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:\n                # Add GDW files\n                if os.path.isdir(gdw_path):\n                    for root, dirs, files in os.walk(gdw_path):\n                        for file in files:\n                            file_path = os.path.join(root, file)\n                            arcname = os.path.relpath(file_path, os.path.dirname(gdw_path))\n                            zipf.write(file_path, arcname)\n                \n                # Add manifest\n                manifest = {\n                    \"created_at\": datetime.now().isoformat(),\n                    \"gdw_path\": gdw_path,\n                    \"package_version\": \"1.0.0\"\n                }\n                zipf.writestr(\"manifest.json\", json.dumps(manifest, indent=2))\n            \n            # Calculate SHA256\n            with open(package_path, 'rb') as f:\n                sha256 = hashlib.sha256(f.read()).hexdigest()\n            \n            return GDWPackageResponse(\n                success=True,\n                package_path=package_path,\n                manifest=manifest,\n                sha256=sha256\n            )\n            \n        except Exception as e:\n            raise HTTPException(status_code=500, detail=f\"Packaging failed: {str(e)}\")\n    \n    def _create_pr(self, request: PRCreateRequest) -> Dict[str, Any]:\n        \"\"\"Create pull request for GDW changes\"\"\"        \n        try:\n            # Check if gh CLI is available\n            result = subprocess.run([\"gh\", \"--version\"], capture_output=True, text=True)\n            if result.returncode != 0:\n                return {\"success\": False, \"error\": \"GitHub CLI (gh) not available\"}\n            \n            # Create branch\n            subprocess.run([\"git\", \"checkout\", \"-b\", request.branch_name], check=True)\n            \n            # Add and commit changes\n            subprocess.run([\"git\", \"add\", \".\"], check=True)\n            subprocess.run([\"git\", \"commit\", \"-m\", request.title], check=True)\n            \n            # Push branch\n            subprocess.run([\"git\", \"push\", \"-u\", \"origin\", request.branch_name], check=True)\n            \n            # Create PR\n            pr_result = subprocess.run([\n                \"gh\", \"pr\", \"create\",\n                \"--title\", request.title,\n                \"--body\", request.description,\n                \"--base\", request.base_branch\n            ], capture_output=True, text=True, check=True)\n            \n            pr_url = pr_result.stdout.strip()\n            \n            return {\n                \"success\": True,\n                \"pr_url\": pr_url,\n                \"branch\": request.branch_name\n            }\n            \n        except subprocess.CalledProcessError as e:\n            return {\"success\": False, \"error\": f\"Git/GitHub operation failed: {str(e)}\"}\n        except Exception as e:\n            return {\"success\": False, \"error\": str(e)}\n    \n    def _get_tools(self) -> Dict[str, Any]:\n        \"\"\"Get all registered tools from registry\"\"\"        \n        registry_path = os.path.join(\"capabilities\", \"tool_registry.yaml\")\n        \n        if not os.path.exists(registry_path):\n            return {\"tools\": [], \"error\": \"Tool registry not found\"}\n        \n        try:\n            with open(registry_path, 'r') as f:\n                registry_data = yaml.safe_load(f)\n            return registry_data\n        except Exception as e:\n            return {\"tools\": [], \"error\": f\"Failed to load registry: {str(e)}\"}\n    \n    def _update_tools(self, tools_data: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"Update tool registry with new data\"\"\"        \n        registry_path = os.path.join(\"capabilities\", \"tool_registry.yaml\")\n        \n        try:\n            os.makedirs(\"capabilities\", exist_ok=True)\n            with open(registry_path, 'w') as f:\n                yaml.dump(tools_data, f, default_flow_style=False)\n            return {\"success\": True, \"message\": \"Tool registry updated successfully\"}\n        except Exception as e:\n            return {\"success\": False, \"error\": f\"Failed to update registry: {str(e)}\"}\n    \n    def _simulate_resolution(self, capability: str, context: Dict[str, Any]) -> Dict[str, Any]:\n        \"\"\"Simulate tool resolution for given capability and context\"\"\"        \n        # Load capability bindings\n        bindings_path = os.path.join(\"capabilities\", \"capability_bindings.yaml\")\n        \n        if not os.path.exists(bindings_path):\n            return {\"error\": \"Capability bindings not found\"}\n        \n        try:\n            with open(bindings_path, 'r') as f:\n                bindings_data = yaml.safe_load(f)\n            \n            capability_config = bindings_data.get(\"capabilities\", {}).get(capability, {})\n            policy = capability_config.get(\"policy\", {})\n            tool_order = policy.get(\"order\", [])\n            \n            # Simulate resolution results\n            results = []\n            for i, tool_id in enumerate(tool_order):\n                status = \"Selected\" if i == 0 else \"Available\"\n                reason = \"Primary choice\" if i == 0 else f\"Fallback option #{i}\"\n                \n                results.append({\n                    \"priority\": i + 1,\n                    \"tool_id\": tool_id,\n                    \"status\": status,\n                    \"reason\": reason\n                })\n            \n            return {\n                \"capability\": capability,\n                \"context\": context,\n                \"results\": results,\n                \"selected_tool\": tool_order[0] if tool_order else None\n            }\n            \n        except Exception as e:\n            return {\"error\": f\"Resolution simulation failed: {str(e)}\"}\n\n\ndef create_app() -> Optional[Any]:\n    \"\"\"Create FastAPI application with GDW endpoints\"\"\"    \n    if not FastAPI:\n        return None\n        \n    server = GDWAPIServer()\n    return server.app\n\n\ndef run_server(host: str = \"127.0.0.1\", port: int = 8001):\n    \"\"\"Run the GDW API server\"\"\"    \n    if not uvicorn:\n        print(\"FastAPI and uvicorn required to run API server\")\n        return\n        \n    app = create_app()\n    if app:\n        uvicorn.run(app, host=host, port=port)\n    else:\n        print(\"Failed to create FastAPI application\")\n\n\nif __name__ == \"__main__\":\n    run_server()"