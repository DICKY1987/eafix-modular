# Cross-Language Bridge Configuration for PowerShell
# Auto-generated from unified configuration

# Database Configuration
$DB_HOST = "localhost"
$DB_PORT = 5432
$DB_NAME = "cli_multi_rapid"

# API Configuration
$API_HOST = "localhost"
$API_PORT = 8000

# Bridge Configuration
$BRIDGE_ENABLED = $true
$BRIDGE_TIMEOUT = 30
$BRIDGE_RETRY_ATTEMPTS = 3

# Feature Configuration
$WORKFLOW_VALIDATION = $true
$COMPLIANCE_CHECKING = $true

# Export configuration variables
Export-ModuleMember -Variable *
