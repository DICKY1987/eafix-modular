---
    process_name: "User Authentication Flow"
    version: "1.0.0"
    generated_at: "2025-08-22T15:59:02.700260"
    numbering: "decimal 1.001"
    source: "process-database-solution.py"
    ---

# User Authentication Flow — Atomic SOP

## Authentication

### 1.001 — Validate Credentials  `[AUTH.001]`
Validate user credentials against authentication service

- **Actor:** SYSTEM
- **Owner:** {SET_OWNER}
- **SLA:** 500 ms

**Inputs**
- **username** (string) · required
- **password** (string) · required · sensitive

**Outputs**
- **auth_token** (string)
- **user_id** (string)
- **is_valid** (boolean)

**Preconditions**
- Username not empty
- Password not empty

**Postconditions**
- Auth token generated or error returned

**Validations**
- Username format valid (regex=^[a-zA-Z0-9_]{3,}$)
- Password meets complexity (min_length=8)

**Error Handling**
- **invalid_credentials** → return_error (code AUTH_001)
- **service_unavailable** → retry · max_attempts=3; backoff=exponential

- **Tested:** yes
---
### 1.002 — Generate Session  `[AUTH.002]`
Create new user session after successful authentication

- **Actor:** SYSTEM
- **Owner:** {SET_OWNER}
- **SLA:** 100 ms

**Inputs**
- **user_id** (string) · required
- **auth_token** (string) · required

**Outputs**
- **session_id** (string)
- **session_expiry** (datetime)

**Preconditions**
- (none)

**Postconditions**
- (none)

**Validations**
- (none)

**Error Handling**
- (none)

- **Tested:** yes
---
## Flows
- **happy_path:** AUTH.001 → AUTH.002
- **password_reset:** AUTH.003