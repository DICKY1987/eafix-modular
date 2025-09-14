# PowerShell GDW Validator Module
# Minimal placeholder for Windows environments.
# Provides Invoke-GDWValidation that performs basic JSON loading and pattern checks.

function Invoke-GDWValidation {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string] $SpecPath
    )

    if (-not (Test-Path -Path $SpecPath)) {
        Write-Error "Spec file not found: $SpecPath"
        return $false
    }
    try {
        $json = Get-Content -Raw -Path $SpecPath | ConvertFrom-Json
    } catch {
        Write-Error "Invalid JSON: $($_.Exception.Message)"
        return $false
    }

    # Basic field presence checks
    $required = @('id','version','summary','inputs','outputs','steps','determinism')
    foreach ($f in $required) {
        if (-not ($json.PSObject.Properties.Name -contains $f)) {
            Write-Error "Missing required field: $f"
            return $false
        }
    }
    # ID pattern: domain.action.target
    if ($json.id -notmatch '^[a-z]+\.[a-z_]+\.[a-z_]+$') {
        Write-Error "Invalid id format: $($json.id)"
        return $false
    }
    # Version semver
    if ($json.version -notmatch '^\d+\.\d+\.\d+$') {
        Write-Error "Invalid version: $($json.version)"
        return $false
    }
    Write-Output "valid"
    return $true
}

Export-ModuleMember -Function Invoke-GDWValidation

