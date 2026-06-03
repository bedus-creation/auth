🔐 SSO Flow Summary (Central Identity Provider)
0. System setup
Central Identity Provider (IdP): auth.company.com
Multiple tenants:
tenant-a.com
tenant-b.comEach tenant is fully isolated (own DB + app)
No shared sessions between tenants
1. First login (create central session)

User goes to:

https://auth.company.com/login
User authenticates (username/password)

IdP creates central session cookie:

idp_session=xyz123 (HttpOnly, Secure)
User is now logged into IdP (global identity session)
2. User enters a tenant (SSO redirect)

User visits:

https://tenant-a.com

Tenant detects no local session → redirects:

auth.company.com/authorize?redirect=tenant-a.com/callback

Browser automatically sends:

Cookie: idp_session=xyz123
3. Silent authentication at IdP
IdP validates idp_session
If valid → no login prompt
IdP issues tenant-scoped authorization code or JWT

Example JWT:

{
  "sub": "user_123",
  "tenant_id": "tenant_a",
  "role": "admin",
  "exp": 1710000000
}
4. Return to tenant

IdP redirects back:

Option A (recommended: auth code flow)
tenant-a.com/callback?code=abc123
5. Token exchange (backend-to-backend)

Tenant backend calls IdP:

POST auth.company.com/token
{
  "code": "abc123",
  "client_id": "tenant_a"
}

Response:

{
  "access_token": "JWT..."
}
6. Tenant session creation
Tenant validates JWT signature
Checks:
tenant_id == tenant_a

Creates local session:

tenant_session=aaa111
7. API usage (normal flow)

For every request:

Browser → Tenant API
Cookie: tenant_session=aaa111

OR stateless:

Authorization: Bearer JWT

Tenant:

verifies token locally
enforces tenant isolation
8. Login to another tenant (same user)

User goes to:

tenant-b.com
Same redirect to IdP
IdP sees same idp_session
Immediately issues new tenant-b token

No password required → true SSO
