# AI QA Agent — Security Architecture & Guidelines

## 1. Multi-Tenant Isolation
- Every API endpoint requires an authenticated user token containing the active `organization_id`.
- Data queries strictly enforce `WHERE organization_id = :org_id`.
- Tenant cross-access tests run as part of the automated regression suite to ensure an authenticated user in Org A can never read, modify, or trigger tests in Org B.
- PostgreSQL Row-Level Security (RLS) policies are configured as a secondary defense-in-depth layer.

## 2. Server-Side Request Forgery (SSRF) Defense
Target web scanning and Playwright execution execute against remote user-provided URLs. To prevent SSRF attacks:
- **Prohibited IP Ranges**:
  - `127.0.0.0/8` (IPv4 loopback) & `::1` (IPv6 loopback)
  - `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` (Private RFC 1918)
  - `169.254.0.0/16` (Link-local & AWS/GCP/Azure instance metadata endpoints)
  - Multicast and broadcast ranges (`224.0.0.0/4`)
- **DNS Rebinding Defense**:
  - DNS resolution is performed synchronously before issuing network requests.
  - Every redirect response is intercepted and re-validated against the SSRF IP policy before the browser or HTTP client follows it.
- **Protocol Allowlist**: Only `http:` and `https:` schemes are permitted. `file:`, `ftp:`, `gopher:`, `data:` are unconditionally rejected.

## 3. Sandboxed Browser Execution
- Playwright instances run in ephemeral, unprivileged worker sandboxes.
- Workers run as non-root users (`uid 10001`).
- Egress network policy restricts sandboxes from contacting cloud metadata services or internal cluster subnets.
- Hard resource quotas: Memory limit (1.5GB per browser instance), CPU quota (1 core), execution timeout (default 60s per scenario).
- Sandbox filesystems are wiped immediately after the test run finishes and artifacts are transferred to secure object storage.

## 4. Secret & Credential Handling
- Secret keys and API tokens are never logged or returned in error payloads.
- Test user credentials provided for authenticated target app testing are stored using AES-256-GCM / Fernet symmetric encryption with environment-managed keys.
- Credential fields are masked (`***`) in screenshots, network request logs, and test step traces.

## 5. AI Guardrails & Prompt Injection Defense
- Untrusted inputs (such as website HTML, DOM text, GitHub READMEs, and issue text) are treated as raw data, never as executable instructions.
- AI system prompts are isolated with strict schema validation (Pydantic models). AI outputs that do not match the expected JSON schema are rejected before reaching any database or execution layer.
- The AI agent is not given access to unrestricted bash/shell tools; tools are strictly bounded to read-only analysis and schema-conforming test code emission.
