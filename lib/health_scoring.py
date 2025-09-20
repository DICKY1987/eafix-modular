"""
Circuit Breakers & Tool Health Scoring (MOD-007)
Prevent cascading failures by pausing or rerouting around unstable tools.
"""

import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, block requests 
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class HealthMetrics:
    """Health metrics for a tool."""
    timestamp: str
    success: bool
    latency_ms: float
    error_message: Optional[str] = None

@dataclass
class HealthScore:
    """Computed health score for a tool."""
    tool_name: str
    score: float  # 0.0 to 1.0
    availability: float
    success_rate: float
    avg_latency_ms: float
    last_updated: str
    circuit_state: CircuitState
    metrics_count: int

class CircuitBreaker:
    """Circuit breaker for a single tool."""
    
    def __init__(self, tool_name: str, failure_threshold: int = 5,
                 success_threshold: int = 3, timeout_seconds: int = 300):
        self.tool_name = tool_name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds
        
        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_start_time = None
        
        # Thread safety
        self._lock = threading.Lock()
    
    def can_execute(self) -> bool:
        """Check if tool execution should be allowed."""
        with self._lock:
            current_time = time.time()
            
            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                # Check if timeout has passed
                if (self.last_failure_time and 
                    current_time - self.last_failure_time >= self.timeout_seconds):
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_start_time = current_time
                    self.success_count = 0
                    return True
                return False
            elif self.state == CircuitState.HALF_OPEN:
                # Allow limited requests in half-open state
                return True
            
            return False
    
    def record_success(self) -> None:
        """Record a successful execution."""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                self.failure_count = 0  # Reset failure count on success
            elif self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    logger.info(f"Circuit breaker for {self.tool_name} closed (recovered)")
    
    def record_failure(self) -> None:
        """Record a failed execution."""
        with self._lock:
            current_time = time.time()
            self.failure_count += 1
            self.last_failure_time = current_time
            
            if self.state == CircuitState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    logger.warning(f"Circuit breaker for {self.tool_name} opened (too many failures)")
            elif self.state == CircuitState.HALF_OPEN:
                # Failed in half-open, go back to open
                self.state = CircuitState.OPEN
                self.success_count = 0
                logger.warning(f"Circuit breaker for {self.tool_name} reopened (half-open test failed)")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        with self._lock:
            return {
                'tool_name': self.tool_name,
                'state': self.state.value,
                'failure_count': self.failure_count,
                'success_count': self.success_count,
                'failure_threshold': self.failure_threshold,
                'success_threshold': self.success_threshold,
                'timeout_seconds': self.timeout_seconds,
                'last_failure_time': self.last_failure_time,
                'can_execute': self.can_execute()
            }

class HealthScoringSystem:
    """Manages health scoring and circuit breakers for all tools."""
    
    def __init__(self, history_path: str = "state/tool_health_history.jsonl"):
        self.history_path = Path(history_path)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Circuit breakers for each tool
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Recent metrics for scoring (in-memory cache)
        self.recent_metrics: Dict[str, List[HealthMetrics]] = {}
        self.max_metrics_per_tool = 100
        
        # Scoring weights
        self.weights = {
            'availability': 0.4,
            'success_rate': 0.3,
            'latency': 0.2,
            'cost_efficiency': 0.1
        }
        
        # Load existing history
        self._load_history()
    
    def _load_history(self) -> None:
        """Load recent health history from file."""
        if not self.history_path.exists():
            return
        
        try:
            with open(self.history_path, 'r') as f:
                for line in f:
                    if line.strip():
                        metric_data = json.loads(line)
                        tool_name = metric_data['tool_name']
                        
                        metric = HealthMetrics(
                            timestamp=metric_data['timestamp'],
                            success=metric_data['success'],
                            latency_ms=metric_data['latency_ms'],
                            error_message=metric_data.get('error_message')
                        )
                        
                        if tool_name not in self.recent_metrics:
                            self.recent_metrics[tool_name] = []
                        
                        self.recent_metrics[tool_name].append(metric)
                        
                        # Limit size
                        if len(self.recent_metrics[tool_name]) > self.max_metrics_per_tool:
                            self.recent_metrics[tool_name] = self.recent_metrics[tool_name][-self.max_metrics_per_tool:]
                            
        except Exception as e:
            logger.error(f"Failed to load health history: {e}")
    
    def get_or_create_circuit_breaker(self, tool_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for a tool."""
        if tool_name not in self.circuit_breakers:
            self.circuit_breakers[tool_name] = CircuitBreaker(tool_name)
        return self.circuit_breakers[tool_name]
    
    def record_execution(self, tool_name: str, success: bool, latency_ms: float, 
                        error_message: Optional[str] = None) -> None:
        """Record a tool execution result."""
        
        # Create health metric
        metric = HealthMetrics(
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=success,
            latency_ms=latency_ms,
            error_message=error_message
        )
        
        # Add to recent metrics
        if tool_name not in self.recent_metrics:
            self.recent_metrics[tool_name] = []
        
        self.recent_metrics[tool_name].append(metric)
        
        # Limit cache size
        if len(self.recent_metrics[tool_name]) > self.max_metrics_per_tool:
            self.recent_metrics[tool_name] = self.recent_metrics[tool_name][-self.max_metrics_per_tool:]
        
        # Record in circuit breaker
        circuit_breaker = self.get_or_create_circuit_breaker(tool_name)
        if success:
            circuit_breaker.record_success()
        else:
            circuit_breaker.record_failure()
        
        # Write to history file
        try:
            with open(self.history_path, 'a') as f:
                history_entry = {
                    'tool_name': tool_name,
                    **asdict(metric)
                }
                f.write(json.dumps(history_entry) + '\\n')
        except Exception as e:
            logger.error(f"Failed to write health history: {e}")
    
    def calculate_health_score(self, tool_name: str, cost_hint: float = 0.0) -> HealthScore:
        """Calculate health score for a tool."""
        
        metrics = self.recent_metrics.get(tool_name, [])
        circuit_breaker = self.get_or_create_circuit_breaker(tool_name)
        
        if not metrics:
            # No metrics, return default score
            return HealthScore(
                tool_name=tool_name,
                score=0.5,  # Neutral score
                availability=0.5,
                success_rate=0.5,
                avg_latency_ms=0.0,
                last_updated=datetime.now(timezone.utc).isoformat(),
                circuit_state=circuit_breaker.state,
                metrics_count=0
            )
        
        # Filter recent metrics (last 24 hours)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_metrics = [
            m for m in metrics 
            if datetime.fromisoformat(m.timestamp.replace('Z', '+00:00')) >= cutoff_time
        ]
        
        if not recent_metrics:
            recent_metrics = metrics[-10:]  # Use last 10 if no recent ones
        
        # Calculate availability (non-zero latency indicates tool is available)
        availability = len([m for m in recent_metrics if m.latency_ms > 0]) / len(recent_metrics)
        
        # Calculate success rate
        success_rate = len([m for m in recent_metrics if m.success]) / len(recent_metrics)
        
        # Calculate average latency
        latencies = [m.latency_ms for m in recent_metrics if m.latency_ms > 0]
        avg_latency_ms = sum(latencies) / len(latencies) if latencies else 0.0
        
        # Latency score (normalize to 0-1, lower is better)
        max_acceptable_latency = 5000.0  # 5 seconds
        latency_score = max(0.0, 1.0 - (avg_latency_ms / max_acceptable_latency))
        
        # Cost efficiency score (lower cost is better)
        max_cost = 1.0  # $1 per request as max
        cost_efficiency_score = max(0.0, 1.0 - (cost_hint / max_cost)) if cost_hint > 0 else 1.0
        
        # Calculate weighted score
        score = (
            availability * self.weights['availability'] +
            success_rate * self.weights['success_rate'] +
            latency_score * self.weights['latency'] +
            cost_efficiency_score * self.weights['cost_efficiency']
        )
        
        return HealthScore(
            tool_name=tool_name,
            score=round(score, 3),
            availability=round(availability, 3),
            success_rate=round(success_rate, 3),
            avg_latency_ms=round(avg_latency_ms, 2),
            last_updated=datetime.now(timezone.utc).isoformat(),
            circuit_state=circuit_breaker.state,
            metrics_count=len(recent_metrics)
        )
    
    def get_all_health_scores(self, cost_hints: Optional[Dict[str, float]] = None) -> Dict[str, HealthScore]:
        """Get health scores for all tools."""
        
        cost_hints = cost_hints or {}
        scores = {}
        
        # Get scores for tools with metrics
        for tool_name in self.recent_metrics.keys():
            cost_hint = cost_hints.get(tool_name, 0.0)
            scores[tool_name] = self.calculate_health_score(tool_name, cost_hint)
        
        # Get scores for tools with circuit breakers but no recent metrics
        for tool_name in self.circuit_breakers.keys():
            if tool_name not in scores:
                cost_hint = cost_hints.get(tool_name, 0.0)
                scores[tool_name] = self.calculate_health_score(tool_name, cost_hint)
        
        return scores
    
    def can_execute_tool(self, tool_name: str) -> bool:
        """Check if a tool can execute (circuit breaker check)."""
        circuit_breaker = self.get_or_create_circuit_breaker(tool_name)
        return circuit_breaker.can_execute()
    
    def get_healthy_tools(self, threshold: float = 0.7) -> List[str]:
        """Get list of tools above health threshold."""
        scores = self.get_all_health_scores()
        return [
            tool_name for tool_name, score in scores.items()
            if score.score >= threshold and self.can_execute_tool(tool_name)
        ]
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        
        scores = self.get_all_health_scores()
        circuit_states = {
            tool_name: cb.get_state() 
            for tool_name, cb in self.circuit_breakers.items()
        }
        
        if not scores:
            return {
                'overall_health': 'unknown',
                'total_tools': 0,
                'healthy_tools': 0,
                'degraded_tools': 0,
                'unhealthy_tools': 0,
                'circuit_breaker_summary': {},
                'tool_scores': {}
            }
        
        # Categorize tools
        healthy_count = len([s for s in scores.values() if s.score >= 0.8])
        degraded_count = len([s for s in scores.values() if 0.5 <= s.score < 0.8])
        unhealthy_count = len([s for s in scores.values() if s.score < 0.5])
        
        # Determine overall health
        if unhealthy_count == 0 and degraded_count <= len(scores) * 0.2:
            overall_health = 'healthy'
        elif unhealthy_count <= len(scores) * 0.3:
            overall_health = 'degraded'
        else:
            overall_health = 'unhealthy'
        
        # Circuit breaker summary
        cb_summary = {
            'total_circuit_breakers': len(circuit_states),
            'open_circuits': len([cb for cb in circuit_states.values() if cb['state'] == 'open']),
            'half_open_circuits': len([cb for cb in circuit_states.values() if cb['state'] == 'half_open']),
            'closed_circuits': len([cb for cb in circuit_states.values() if cb['state'] == 'closed'])
        }
        
        return {
            'overall_health': overall_health,
            'total_tools': len(scores),
            'healthy_tools': healthy_count,
            'degraded_tools': degraded_count,
            'unhealthy_tools': unhealthy_count,
            'circuit_breaker_summary': cb_summary,
            'tool_scores': {name: asdict(score) for name, score in scores.items()},
            'last_updated': datetime.now(timezone.utc).isoformat()
        }

def main():
    """CLI interface for health scoring system."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Health scoring and circuit breaker management")
    parser.add_argument("command", 
                       choices=["record", "score", "status", "summary"], 
                       help="Command to run")
    parser.add_argument("--tool", help="Tool name")
    parser.add_argument("--success", action="store_true", help="Record successful execution")
    parser.add_argument("--latency", type=float, help="Latency in milliseconds")
    parser.add_argument("--error", help="Error message for failed execution")
    parser.add_argument("--threshold", type=float, default=0.7, help="Health threshold")
    
    args = parser.parse_args()
    
    health_system = HealthScoringSystem()
    
    if args.command == "record":
        if not args.tool or args.latency is None:
            print("Error: --tool and --latency are required for record command", file=sys.stderr)
            sys.exit(1)
        
        health_system.record_execution(
            tool_name=args.tool,
            success=args.success,
            latency_ms=args.latency,
            error_message=args.error
        )
        print(f"Recorded execution for {args.tool}: success={args.success}, latency={args.latency}ms")
    
    elif args.command == "score":
        if args.tool:
            score = health_system.calculate_health_score(args.tool)
            print(json.dumps(asdict(score), indent=2))
        else:
            scores = health_system.get_all_health_scores()
            print(json.dumps({name: asdict(score) for name, score in scores.items()}, indent=2))
    
    elif args.command == "status":
        healthy_tools = health_system.get_healthy_tools(args.threshold)
        print(f"Healthy tools (threshold >= {args.threshold}):")
        for tool in healthy_tools:
            print(f"  ✅ {tool}")
            
        # Show circuit breaker states
        print("\\nCircuit Breaker States:")
        for tool_name, cb in health_system.circuit_breakers.items():
            state = cb.get_state()
            emoji = "✅" if state['can_execute'] else "❌"
            print(f"  {emoji} {tool_name}: {state['state']} (failures: {state['failure_count']})")
    
    elif args.command == "summary":
        summary = health_system.get_system_health_summary()
        print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()