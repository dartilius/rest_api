# Local Kubernetes JWT lab

Prerequisites: Docker Desktop, `kubectl`, `k3d`, Helm, the `rmc-local`
cluster, and ingress-nginx at port `8080`.

Run from the repository root:

```powershell
.\scripts\k8s\deploy-local.ps1
```

The script creates ignored local secrets and RSA keys, builds/imports the
Django and Nest images, provisions PostgreSQL, runs Django migrations, creates
the local test user, grants Nest source read access, then waits for both API
deployments. MinIO is intentionally excluded from this first JWT-only lab
because its upstream image registry is currently unavailable in this local
environment; no tested request reads or writes objects.

The generated test account is `jwt-test@local.test` with password
`LocalJwtTest!2026`. Override both values only through parameters to
`create-local-secrets.ps1`; never commit them to manifests.

## JWT smoke requests

```powershell
$login = Invoke-RestMethod -Method Post -Uri http://localhost:8080/auth/jwt/create/ `
  -ContentType application/json `
  -Body '{"email":"jwt-test@local.test","password":"LocalJwtTest!2026"}'

Invoke-RestMethod -Uri http://localhost:8080/site-api/v1/auth/me `
  -Headers @{ Authorization = "access_token $($login.access)" }
```

Expected result contains the test user UUID, `role: ordinary`, and
`tokenVersion: rs256`.

Invalid token check:

```powershell
curl.exe -i http://localhost:8080/site-api/v1/auth/me -H "Authorization: access_token invalid"
```

Expected result: `401` with `{"error":{"code":"UNAUTHORIZED",...}}`.

Legacy refresh simulation is intentionally performed only inside the local
Django pod, where the temporary HMAC secret is available:

```powershell
$legacyCommand = "import jwt; from datetime import datetime,timedelta,timezone; from uuid import uuid4; from django.conf import settings; from users.models import CustomUser; u=CustomUser.objects.get(email='jwt-test@local.test'); print(jwt.encode({'token_type':'refresh','user_id':str(u.id),'jti':uuid4().hex,'iat':datetime.now(timezone.utc),'exp':datetime.now(timezone.utc)+timedelta(minutes=5)}, settings.JWT_LEGACY_HS256_SECRET, algorithm='HS256'))"
$legacy = kubectl exec -n rmc deploy/django-api -- python manage.py shell -c $legacyCommand |
  Where-Object { $_ -match '^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$' } |
  Select-Object -Last 1
$body = @{ refresh = $legacy } | ConvertTo-Json -Compress

# Returns a new RS256 pair.
Invoke-RestMethod -Method Post -Uri http://localhost:8080/auth/jwt/legacy-refresh/ `
  -ContentType application/json -Body $body

# The same legacy refresh is blacklisted and is rejected on this second call.
curl.exe -i -X POST http://localhost:8080/auth/jwt/legacy-refresh/ `
  -H "Content-Type: application/json" -d $body
```

The external application endpoints are `/auth/...`, `/api/...`, and
`/site-api/v1/...`. Liveness/readiness health endpoints are intentionally
internal: `/healthz/` for Django and `/healthz` for Nest.

## Importing a production database snapshot

`scripts/k8s/import-production-db.ps1` copies PostgreSQL data from a remote
server into the local k3d PostgreSQL database. It never writes to the remote
server, but it **fully replaces** the local `rmc` database. MinIO objects are
not copied, so media URLs in imported records are not usable in this lab.

Ask the production PostgreSQL administrator for a temporary, read-only backup
role. A PostgreSQL 14+ example is:

```sql
CREATE ROLE rmc_local_dump LOGIN PASSWORD '<temporary-secret>';
GRANT CONNECT ON DATABASE rmc TO rmc_local_dump;
GRANT pg_read_all_data TO rmc_local_dump;
```

The administrator must revoke or remove this role after the import.

Copy the tracked template into the ignored secrets directory and fill in only
the temporary backup-role credentials:

```powershell
New-Item -ItemType Directory -Force .local-secrets | Out-Null
Copy-Item scripts/k8s/production-db-import.example.env `
  .local-secrets/production-db-import.env
```

Then run:

```powershell
.\scripts\k8s\import-production-db.ps1 -ReplaceLocalDatabase -CreateLocalTestUser
```

The script first saves the current local database and the imported production
dump in `.local-backups/`, both ignored by Git. It stops Django and Nest,
restores the snapshot, reapplies Nest's read-only database grants, and starts
the APIs again. `-CreateLocalTestUser` adds the local-only JWT test account
from `django-runtime`; omit that switch when an exact, unmodified copy is
required.
