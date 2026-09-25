param(
    [string]$Namespace = 'rmc',
    [string]$TestEmail = 'jwt-test@local.test',
    [string]$TestPassword = 'LocalJwtTest!2026',
    [string]$TestPhone = '+79990000001'
)

$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$secretsDir = Join-Path $root '.local-secrets'
$jwtDir = Join-Path $secretsDir 'jwt'
$python = Join-Path $root '.venv\Scripts\python.exe'

function New-RandomSecret {
    param([int]$Bytes = 32)
    $buffer = New-Object byte[] $Bytes
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($buffer)
    return ([BitConverter]::ToString($buffer) -replace '-', '').ToLowerInvariant()
}

if (-not (Test-Path $python)) {
    throw "Python virtual environment not found: $python"
}

New-Item -ItemType Directory -Force -Path $jwtDir | Out-Null
Push-Location $root
try {
    & $python (Join-Path $root 'scripts\k8s\generate_local_jwt_keys.py')
}
finally {
    Pop-Location
}

$legacySecret = New-RandomSecret 48
$postgresPassword = New-RandomSecret 32
$readerPassword = New-RandomSecret 32
$minioRootPassword = New-RandomSecret 32
$djangoMinioPassword = New-RandomSecret 32
$nestMinioPassword = New-RandomSecret 32
$legacyDeadline = [DateTime]::UtcNow.AddDays(7).ToString('yyyy-MM-ddTHH:mm:ssZ')

kubectl apply -f (Join-Path $root 'deploy\k8s\local\namespace.yaml')

kubectl -n $Namespace get secret postgres-credentials *> $null
if ($LASTEXITCODE -ne 0) {
    kubectl -n $Namespace create secret generic postgres-credentials `
      --from-literal=POSTGRES_DB=rmc `
      --from-literal=POSTGRES_USER=rmc_owner `
      --from-literal=POSTGRES_PASSWORD=$postgresPassword
}
else {
    Write-Host 'Preserved existing PostgreSQL credentials for the local PVC.'
}

kubectl -n $Namespace create secret generic minio-root-credentials `
  --from-literal=MINIO_ROOT_USER=minio_root `
  --from-literal=MINIO_ROOT_PASSWORD=$minioRootPassword `
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n $Namespace create secret generic django-runtime `
  --from-literal=SECRET_KEY=$legacySecret `
  --from-literal=JWT_LEGACY_HS256_SECRET=$legacySecret `
  --from-literal=JWT_LEGACY_HS256_ACCEPT_UNTIL=$legacyDeadline `
  --from-literal=POSTGRES_DB=rmc `
  --from-literal=POSTGRES_HOST=postgres `
  --from-literal=POSTGRES_PORT=5432 `
  --from-literal=POSTGRES_USER=rmc_owner `
  --from-literal=POSTGRES_PASS=$postgresPassword `
  --from-literal=MINIO_STORAGE_ACCESS_KEY=django_local `
  --from-literal=MINIO_STORAGE_SECRET_KEY=$djangoMinioPassword `
  --from-literal=LOCAL_TEST_EMAIL=$TestEmail `
  --from-literal=LOCAL_TEST_PASSWORD=$TestPassword `
  --from-literal=LOCAL_TEST_PHONE=$TestPhone `
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n $Namespace create secret generic nest-runtime `
  --from-literal=SOURCE_DB_USER=nest_source_reader `
  --from-literal=SOURCE_DB_PASSWORD=$readerPassword `
  --from-literal=MINIO_ACCESS_KEY=nest_local_read `
  --from-literal=MINIO_SECRET_KEY=$nestMinioPassword `
  --from-literal=JWT_LEGACY_HS256_SECRET=$legacySecret `
  --from-literal=JWT_LEGACY_HS256_ACCEPT_UNTIL=$legacyDeadline `
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n $Namespace create secret generic django-jwt-keys `
  --from-file=private.pem=$jwtDir\private.pem `
  --from-file=public.pem=$jwtDir\public.pem `
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n $Namespace create secret generic nest-jwt-public `
  --from-file=public.pem=$jwtDir\public.pem `
  --dry-run=client -o yaml | kubectl apply -f -

Write-Host "Created local secrets. Legacy compatibility expires at $legacyDeadline"
