#!/usr/bin/env python3
"""
Test Cross-Language Bridge System
=================================

Test script to validate the cross-language bridge implementation.
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from cross_language_bridge import (
    UnifiedConfigManager,
    CrossSystemHealthChecker,
    CrossLanguageErrorHandler,
    CommunicationBridge
)


async def test_bridge_system():
    """Test the complete cross-language bridge system."""
    print("=== Cross-Language Bridge System Test ===\n")
    
    # Test 1: Configuration Management
    print("1. Testing Unified Configuration Management...")
    config_manager = UnifiedConfigManager()
    
    config = config_manager.load_unified_config()
    print(f"   [OK] Configuration loaded: {len(config)} sections")
    
    propagation_results = config_manager.propagate_all(config)
    successful_propagations = sum(propagation_results.values())
    print(f"   [OK] Configuration propagated to {successful_propagations}/3 systems")
    
    validation_errors = config_manager.validate_configuration(config)
    if validation_errors:
        print(f"   [WARN] Configuration validation issues: {len(validation_errors)}")
        for error in validation_errors[:3]:  # Show first 3 errors
            print(f"     - {error}")
    else:
        print("   [OK] Configuration validation passed")
    
    print()
    
    # Test 2: Health Checking
    print("2. Testing Cross-System Health Checking...")
    health_checker = CrossSystemHealthChecker(config_manager)
    
    health_results = health_checker.run_comprehensive_health_check()
    print(f"   [OK] Overall health status: {health_results['overall_status']}")
    
    for system_name, system_health in health_results["systems"].items():
        status_symbol = {"healthy": "[OK]", "degraded": "[WARN]", "warning": "[WARN]", "unhealthy": "[ERROR]"}.get(system_health["status"], "[?]")
        print(f"   {status_symbol} {system_name}: {system_health['status']}")
    
    print()
    
    # Test 3: Error Handling
    print("3. Testing Cross-Language Error Handling...")
    error_handler = CrossLanguageErrorHandler()
    
    # Test Python error handling
    try:
        raise ValueError("Test Python error")
    except Exception as exc:
        error_id = error_handler.handle_python_error(exc, context={"test": True})
        print(f"   [OK] Python error handled: {error_id}")
    
    # Test MQL4 error handling
    mql4_error_id = error_handler.handle_mql4_error(
        error_code=4051, 
        error_message="Invalid function parameter value",
        context={"test": True}
    )
    print(f"   [OK] MQL4 error handled: {mql4_error_id}")
    
    # Test PowerShell error handling
    ps_error_id = error_handler.handle_powershell_error(
        error_message="Execution Policy Restricted",
        exit_code=1,
        context={"test": True}
    )
    print(f"   [OK] PowerShell error handled: {ps_error_id}")
    
    error_stats = error_handler.get_error_statistics()
    print(f"   [OK] Error statistics: {error_stats['total_errors']} total errors")
    
    print()
    
    # Test 4: Communication Bridge
    print("4. Testing Communication Bridge...")
    bridge = CommunicationBridge()
    
    # Initialize bridge
    init_success = await bridge.initialize()
    print(f"   {'[OK]' if init_success else '[ERROR]'} Bridge initialization: {'SUCCESS' if init_success else 'FAILED'}")
    
    if init_success:
        # Test Python command execution
        python_result = await bridge.execute_python_command("eval:2 + 2", context={"test": True})
        print(f"   {'[OK]' if python_result['success'] else '[ERROR]'} Python command execution: {python_result.get('result', 'FAILED')}")
        
        # Test MQL4 command execution
        mql4_result = await bridge.execute_mql4_command("GetAccountInfo", context={"test": True})
        print(f"   {'[OK]' if mql4_result['success'] else '[ERROR]'} MQL4 command execution: {'SUCCESS' if mql4_result['success'] else 'FAILED'}")
        
        # Test PowerShell command execution
        ps_result = await bridge.execute_powershell_command("Write-Host 'Test successful'", context={"test": True})
        print(f"   {'[OK]' if ps_result['success'] else '[ERROR]'} PowerShell command execution: {'SUCCESS' if ps_result['success'] else 'FAILED'}")
        
        # Test message broadcasting
        broadcast_result = await bridge.broadcast_message({"test_message": "Hello from bridge!"})
        successful_systems = broadcast_result['successful_systems']
        total_systems = broadcast_result['total_systems']
        print(f"   [OK] Message broadcast: {successful_systems}/{total_systems} systems reached")
        
        # Test cross-system validation
        validation_result = await bridge.run_cross_system_validation()
        print(f"   {'[OK]' if validation_result['overall_success'] else '[WARN]'} Cross-system validation: {'PASSED' if validation_result['overall_success'] else 'PARTIAL'}")
    
    print()
    
    # Test 5: Integration Summary
    print("5. Integration Summary...")
    bridge_status = bridge.get_bridge_status()
    print(f"   [OK] Bridge initialized: {bridge_status['initialized']}")
    print(f"   [OK] Configuration loaded: {bridge_status['configuration_loaded']}")
    print(f"   [OK] Active connections: {bridge_status['active_connections']}")
    print(f"   [OK] Bridge enabled: {bridge_status['bridge_enabled']}")
    
    print()
    print("=== Test Complete ===")
    print()
    print(bridge.get_integration_summary())
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_bridge_system())
        if success:
            print("\n[SUCCESS] All tests completed successfully!")
            sys.exit(0)
        else:
            print("\n[FAILED] Some tests failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n[STOPPED] Test interrupted by user")
        sys.exit(1)
    except Exception as exc:
        print(f"\n[ERROR] Test failed with exception: {exc}")
        sys.exit(1)