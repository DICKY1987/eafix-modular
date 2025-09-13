#!/usr/bin/env python3
"""
Test script for the CLI Multi-Rapid Enterprise Orchestration Platform
Runs basic system checks without git integration to avoid Unicode issues
"""

import sys
import os
from pathlib import Path

def test_framework():
    """Test the main framework components"""
    print("=== CLI Multi-Rapid Enterprise Orchestration Platform Test ===\n")
    
    try:
        # Test basic imports
        print("1. Testing core imports...")
        import agentic_framework_v3
        from agentic_framework_v3 import SERVICES, TaskComplexityAnalyzer
        print("   ✓ Core framework imports successful")
        
        # Test service configuration
        print("\n2. Testing service configuration...")
        services = SERVICES
        print(f"   ✓ {len(services)} services configured:")
        for name, config in services.items():
            daily_limit = config.get('daily_limit', 'unlimited')
            cost = config.get('cost_per_request', 'free')
            print(f"     - {name}: {daily_limit} daily limit, ${cost}/request")
        
        # Test task complexity analyzer without full orchestrator
        print("\n3. Testing task complexity analysis...")
        analyzer = TaskComplexityAnalyzer()
        sample_tasks = [
            "print hello world",
            "implement user authentication with JWT",
            "design distributed microservices architecture"
        ]
        
        for task in sample_tasks:
            complexity = analyzer.analyze_complexity(task)
            print(f"   ✓ '{task}' -> {complexity}")
        
        # Test CLI package
        print("\n4. Testing CLI package...")
        try:
            import cli_multi_rapid.cli
            print("   ✓ CLI package available")
        except ImportError as e:
            print(f"   ⚠ CLI package issue: {e}")
        
        print("\n5. Configuration Files Check...")
        config_files = [
            ".env.example",
            "config/env.example", 
            "local/.env.example",
            "requirements.txt"
        ]
        
        for file in config_files:
            if Path(file).exists():
                print(f"   ✓ {file} exists")
            else:
                print(f"   ⚠ {file} missing")
        
        print("\n=== FRAMEWORK STATUS: OPERATIONAL ===")
        print("\nNext Steps:")
        print("1. Copy .env.example to .env and add your API keys")
        print("2. Start with: python agentic_framework_v3.py status (may need Unicode fix)")
        print("3. Or use CLI: cli-multi-rapid --help")
        print("4. For production: docker-compose -f config/docker-compose.yml up -d")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Run: pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Framework test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_framework()
    sys.exit(0 if success else 1)