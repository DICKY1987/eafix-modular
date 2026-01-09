# DOC_ID: DOC-CONTRACT-0009
"""
Contract testing framework for EAFIX trading system.
Implements consumer-driven contract testing with Pact-like semantics.
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import hashlib
from pathlib import Path

from pydantic import BaseModel, Field, validator
import structlog
import httpx
import pytest

logger = structlog.get_logger(__name__)


class InteractionType(str, Enum):
    """Types of service interactions."""
    HTTP_REQUEST = "http_request"
    MESSAGE_PUBLISH = "message_publish"
    MESSAGE_CONSUME = "message_consume"
    DATABASE_QUERY = "database_query"
    EXTERNAL_API = "external_api"


class MatchingRule(str, Enum):
    """Contract matching rules."""
    EQUALITY = "equality"
    REGEX = "regex"
    TYPE = "type"
    DATETIME = "datetime"
    UUID = "uuid"
    NUMERIC = "numeric"
    ARRAY_MIN_LENGTH = "array_min_length"
    OBJECT_LIKE = "object_like"


@dataclass
class Matcher:
    """Contract matching rule definition."""
    rule: MatchingRule
    value: Optional[Any] = None
    regex: Optional[str] = None
    min_length: Optional[int] = None
    
    def matches(self, actual_value: Any) -> bool:
        """Check if actual value matches this rule."""
        if self.rule == MatchingRule.EQUALITY:
            return actual_value == self.value
        elif self.rule == MatchingRule.TYPE:
            return type(actual_value).__name__ == self.value
        elif self.rule == MatchingRule.REGEX:
            import re
            return bool(re.match(self.regex, str(actual_value)))
        elif self.rule == MatchingRule.DATETIME:
            try:
                datetime.fromisoformat(str(actual_value).replace('Z', '+00:00'))
                return True
            except:
                return False
        elif self.rule == MatchingRule.UUID:
            try:
                uuid.UUID(str(actual_value))
                return True
            except:
                return False
        elif self.rule == MatchingRule.NUMERIC:
            return isinstance(actual_value, (int, float))
        elif self.rule == MatchingRule.ARRAY_MIN_LENGTH:
            return isinstance(actual_value, list) and len(actual_value) >= (self.min_length or 0)
        elif self.rule == MatchingRule.OBJECT_LIKE:
            return isinstance(actual_value, dict)
        
        return False


class ContractRequest(BaseModel):
    """HTTP request specification in contract."""
    method: str = Field(..., description="HTTP method")
    path: str = Field(..., description="Request path")
    query: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    headers: Optional[Dict[str, str]] = Field(None, description="Request headers")
    body: Optional[Any] = Field(None, description="Request body")
    
    # Matching rules for flexible matching
    path_matchers: Dict[str, Matcher] = Field(default_factory=dict)
    query_matchers: Dict[str, Matcher] = Field(default_factory=dict)
    header_matchers: Dict[str, Matcher] = Field(default_factory=dict)
    body_matchers: Dict[str, Matcher] = Field(default_factory=dict)


class ContractResponse(BaseModel):
    """HTTP response specification in contract."""
    status: int = Field(..., description="HTTP status code")
    headers: Optional[Dict[str, str]] = Field(None, description="Response headers")
    body: Optional[Any] = Field(None, description="Response body")
    
    # Matching rules for flexible matching
    header_matchers: Dict[str, Matcher] = Field(default_factory=dict)
    body_matchers: Dict[str, Matcher] = Field(default_factory=dict)


class MessageContract(BaseModel):
    """Message contract specification."""
    topic: str = Field(..., description="Message topic/channel")
    message_type: str = Field(..., description="Message type")
    schema_version: str = Field(default="1.0", description="Schema version")
    payload: Any = Field(..., description="Message payload")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Matching rules
    payload_matchers: Dict[str, Matcher] = Field(default_factory=dict)
    metadata_matchers: Dict[str, Matcher] = Field(default_factory=dict)


class Interaction(BaseModel):
    """Single interaction in a contract."""
    interaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = Field(..., description="Human-readable description")
    interaction_type: InteractionType = Field(..., description="Type of interaction")
    
    # HTTP-specific
    request: Optional[ContractRequest] = None
    response: Optional[ContractResponse] = None
    
    # Message-specific
    message: Optional[MessageContract] = None
    
    # Metadata
    given: Optional[str] = Field(None, description="Provider state description")
    tags: List[str] = Field(default_factory=list)
    
    @validator('request', 'response', 'message')
    def validate_interaction_data(cls, v, values, field):
        """Validate that interaction has appropriate data for its type."""
        interaction_type = values.get('interaction_type')
        
        if interaction_type == InteractionType.HTTP_REQUEST:
            if field.name in ('request', 'response') and v is None:
                raise ValueError(f"HTTP interactions must have {field.name}")
        elif interaction_type in (InteractionType.MESSAGE_PUBLISH, InteractionType.MESSAGE_CONSUME):
            if field.name == 'message' and v is None:
                raise ValueError(f"Message interactions must have message specification")
        
        return v


class Contract(BaseModel):
    """Complete contract between consumer and provider."""
    contract_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    consumer: str = Field(..., description="Consumer service name")
    provider: str = Field(..., description="Provider service name")
    version: str = Field(default="1.0.0", description="Contract version")
    
    interactions: List[Interaction] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    description: str = Field("", description="Contract description")
    tags: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Matcher: lambda v: {
                'rule': v.rule.value,
                'value': v.value,
                'regex': v.regex,
                'min_length': v.min_length
            }
        }


class ContractBuilder:
    """Builder for creating contracts with fluent API."""
    
    def __init__(self, consumer: str, provider: str):
        """Initialize contract builder."""
        self.contract = Contract(consumer=consumer, provider=provider)
        self.current_interaction: Optional[Interaction] = None
    
    def given(self, state: str) -> 'ContractBuilder':
        """Set provider state for current interaction."""
        if self.current_interaction:
            self.current_interaction.given = state
        return self
    
    def upon_receiving(self, description: str) -> 'ContractBuilder':
        """Start new HTTP interaction."""
        self.current_interaction = Interaction(
            description=description,
            interaction_type=InteractionType.HTTP_REQUEST
        )
        return self
    
    def with_request(
        self,
        method: str,
        path: str,
        query: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        body: Optional[Any] = None
    ) -> 'ContractBuilder':
        """Set request specification."""
        if not self.current_interaction:
            raise ValueError("Must call upon_receiving() first")
        
        self.current_interaction.request = ContractRequest(
            method=method.upper(),
            path=path,
            query=query,
            headers=headers,
            body=body
        )
        return self
    
    def will_respond_with(
        self,
        status: int,
        headers: Optional[Dict] = None,
        body: Optional[Any] = None
    ) -> 'ContractBuilder':
        """Set response specification."""
        if not self.current_interaction:
            raise ValueError("Must call upon_receiving() first")
        
        self.current_interaction.response = ContractResponse(
            status=status,
            headers=headers,
            body=body
        )
        
        # Add interaction to contract and reset
        self.contract.interactions.append(self.current_interaction)
        self.current_interaction = None
        
        return self
    
    def upon_publishing(self, description: str, topic: str) -> 'ContractBuilder':
        """Start new message publishing interaction."""
        self.current_interaction = Interaction(
            description=description,
            interaction_type=InteractionType.MESSAGE_PUBLISH
        )
        self.current_interaction.message = MessageContract(
            topic=topic,
            message_type="",
            payload={}
        )
        return self
    
    def with_message(
        self,
        message_type: str,
        payload: Any,
        schema_version: str = "1.0",
        metadata: Optional[Dict] = None
    ) -> 'ContractBuilder':
        """Set message specification."""
        if not self.current_interaction or not self.current_interaction.message:
            raise ValueError("Must call upon_publishing() first")
        
        self.current_interaction.message.message_type = message_type
        self.current_interaction.message.payload = payload
        self.current_interaction.message.schema_version = schema_version
        self.current_interaction.message.metadata = metadata or {}
        
        # Add interaction to contract and reset
        self.contract.interactions.append(self.current_interaction)
        self.current_interaction = None
        
        return self
    
    def with_matcher(self, path: str, matcher: Matcher) -> 'ContractBuilder':
        """Add matching rule to current interaction."""
        if not self.current_interaction:
            raise ValueError("Must have an active interaction to add matchers")
        
        # Add matcher based on interaction type and path
        if self.current_interaction.interaction_type == InteractionType.HTTP_REQUEST:
            if path.startswith('$.request.body'):
                if not self.current_interaction.request:
                    raise ValueError("Request must be set before adding body matchers")
                self.current_interaction.request.body_matchers[path] = matcher
            elif path.startswith('$.response.body'):
                if not self.current_interaction.response:
                    raise ValueError("Response must be set before adding body matchers")
                self.current_interaction.response.body_matchers[path] = matcher
        elif self.current_interaction.interaction_type == InteractionType.MESSAGE_PUBLISH:
            if path.startswith('$.message.payload'):
                if not self.current_interaction.message:
                    raise ValueError("Message must be set before adding payload matchers")
                self.current_interaction.message.payload_matchers[path] = matcher
        
        return self
    
    def build(self) -> Contract:
        """Build and return the contract."""
        if self.current_interaction:
            # Add any pending interaction
            self.contract.interactions.append(self.current_interaction)
        
        return self.contract


class ContractVerifier:
    """Verifies contracts against actual service implementations."""
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize contract verifier."""
        self.base_url = base_url or "http://localhost"
        self.client = httpx.AsyncClient(base_url=self.base_url)
    
    async def verify_contract(self, contract: Contract) -> List[Dict[str, Any]]:
        """Verify all interactions in a contract."""
        results = []
        
        for interaction in contract.interactions:
            try:
                if interaction.interaction_type == InteractionType.HTTP_REQUEST:
                    result = await self._verify_http_interaction(interaction)
                elif interaction.interaction_type == InteractionType.MESSAGE_PUBLISH:
                    result = await self._verify_message_interaction(interaction)
                else:
                    result = {
                        'interaction_id': interaction.interaction_id,
                        'description': interaction.description,
                        'status': 'skipped',
                        'reason': f'Unsupported interaction type: {interaction.interaction_type}'
                    }
                
                results.append(result)
                
            except Exception as e:
                logger.error(
                    "Error verifying interaction",
                    interaction_id=interaction.interaction_id,
                    error=str(e)
                )
                
                results.append({
                    'interaction_id': interaction.interaction_id,
                    'description': interaction.description,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
    
    async def _verify_http_interaction(self, interaction: Interaction) -> Dict[str, Any]:
        """Verify HTTP interaction."""
        if not interaction.request or not interaction.response:
            return {
                'interaction_id': interaction.interaction_id,
                'description': interaction.description,
                'status': 'error',
                'error': 'HTTP interaction missing request or response'
            }
        
        # Make HTTP request
        try:
            response = await self.client.request(
                method=interaction.request.method,
                url=interaction.request.path,
                params=interaction.request.query,
                headers=interaction.request.headers,
                json=interaction.request.body if interaction.request.body else None
            )
            
            # Verify response
            verification_result = self._verify_response(response, interaction.response)
            
            return {
                'interaction_id': interaction.interaction_id,
                'description': interaction.description,
                'status': 'passed' if verification_result['matches'] else 'failed',
                'expected': {
                    'status': interaction.response.status,
                    'headers': interaction.response.headers,
                    'body': interaction.response.body
                },
                'actual': {
                    'status': response.status_code,
                    'headers': dict(response.headers),
                    'body': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                },
                'verification': verification_result
            }
            
        except Exception as e:
            return {
                'interaction_id': interaction.interaction_id,
                'description': interaction.description,
                'status': 'error',
                'error': f'HTTP request failed: {str(e)}'
            }
    
    async def _verify_message_interaction(self, interaction: Interaction) -> Dict[str, Any]:
        """Verify message interaction (placeholder for message bus integration)."""
        return {
            'interaction_id': interaction.interaction_id,
            'description': interaction.description,
            'status': 'skipped',
            'reason': 'Message verification not implemented yet'
        }
    
    def _verify_response(self, actual_response, expected_response: ContractResponse) -> Dict[str, Any]:
        """Verify actual response against expected response."""
        mismatches = []
        
        # Check status code
        if actual_response.status_code != expected_response.status:
            mismatches.append(f"Status code mismatch: expected {expected_response.status}, got {actual_response.status_code}")
        
        # Check headers if specified
        if expected_response.headers:
            for header, expected_value in expected_response.headers.items():
                actual_value = actual_response.headers.get(header)
                if actual_value != expected_value:
                    mismatches.append(f"Header '{header}' mismatch: expected '{expected_value}', got '{actual_value}'")
        
        # Check body if specified
        if expected_response.body is not None:
            try:
                actual_body = actual_response.json()
            except:
                actual_body = actual_response.text
            
            if not self._match_data(actual_body, expected_response.body, expected_response.body_matchers):
                mismatches.append(f"Body mismatch: expected {expected_response.body}, got {actual_body}")
        
        return {
            'matches': len(mismatches) == 0,
            'mismatches': mismatches
        }
    
    def _match_data(self, actual: Any, expected: Any, matchers: Dict[str, Matcher]) -> bool:
        """Match actual data against expected with custom matchers."""
        # If no matchers, use equality
        if not matchers:
            return actual == expected
        
        # Apply matchers
        for path, matcher in matchers.items():
            actual_value = self._extract_value_by_path(actual, path)
            if not matcher.matches(actual_value):
                return False
        
        return True
    
    def _extract_value_by_path(self, data: Any, path: str) -> Any:
        """Extract value from data using JSONPath-like syntax."""
        # Simplified JSONPath implementation
        parts = path.replace('$.', '').split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                index = int(part)
                current = current[index] if index < len(current) else None
            else:
                return None
        
        return current
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class ContractStore:
    """Storage for contracts."""
    
    def __init__(self, storage_path: Path):
        """Initialize contract store."""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_contract(self, contract: Contract) -> str:
        """Save contract to storage."""
        filename = f"{contract.consumer}-{contract.provider}-{contract.version}.json"
        filepath = self.storage_path / filename
        
        with open(filepath, 'w') as f:
            f.write(contract.json(indent=2))
        
        logger.info(
            "Saved contract",
            consumer=contract.consumer,
            provider=contract.provider,
            version=contract.version,
            filepath=str(filepath)
        )
        
        return str(filepath)
    
    def load_contract(self, consumer: str, provider: str, version: str = "1.0.0") -> Optional[Contract]:
        """Load contract from storage."""
        filename = f"{consumer}-{provider}-{version}.json"
        filepath = self.storage_path / filename
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Convert matchers back from JSON
        contract_data = self._deserialize_matchers(data)
        return Contract.parse_obj(contract_data)
    
    def list_contracts(self) -> List[Dict[str, str]]:
        """List all stored contracts."""
        contracts = []
        
        for filepath in self.storage_path.glob("*.json"):
            parts = filepath.stem.split("-")
            if len(parts) >= 3:
                contracts.append({
                    'consumer': parts[0],
                    'provider': parts[1],
                    'version': "-".join(parts[2:]),
                    'filepath': str(filepath)
                })
        
        return contracts
    
    def _deserialize_matchers(self, data: Dict) -> Dict:
        """Convert matcher dictionaries back to Matcher objects."""
        # This would recursively find and convert matcher objects
        # Simplified implementation for now
        return data


# Pytest integration
def pytest_configure(config):
    """Configure pytest for contract testing."""
    config.addinivalue_line("markers", "contract: mark test as a contract test")
    config.addinivalue_line("markers", "consumer: mark test as consumer contract test")
    config.addinivalue_line("markers", "provider: mark test as provider contract test")


class ContractTestCase:
    """Base class for contract test cases."""
    
    def __init__(self):
        self.contracts_path = Path(__file__).parent.parent / "contracts"
        self.store = ContractStore(self.contracts_path)
        self.verifier = ContractVerifier()
    
    async def verify_contract(self, consumer: str, provider: str, version: str = "1.0.0") -> bool:
        """Verify a contract."""
        contract = self.store.load_contract(consumer, provider, version)
        if not contract:
            pytest.fail(f"Contract not found: {consumer} -> {provider} v{version}")
        
        results = await self.verifier.verify_contract(contract)
        
        failed_interactions = [r for r in results if r['status'] == 'failed']
        error_interactions = [r for r in results if r['status'] == 'error']
        
        if failed_interactions or error_interactions:
            failure_details = []
            
            for result in failed_interactions:
                failure_details.append(f"FAILED: {result['description']}")
                if 'verification' in result:
                    for mismatch in result['verification']['mismatches']:
                        failure_details.append(f"  - {mismatch}")
            
            for result in error_interactions:
                failure_details.append(f"ERROR: {result['description']} - {result.get('error', 'Unknown error')}")
            
            pytest.fail(f"Contract verification failed:\n" + "\n".join(failure_details))
        
        return True
    
    async def teardown(self):
        """Cleanup resources."""
        await self.verifier.close()