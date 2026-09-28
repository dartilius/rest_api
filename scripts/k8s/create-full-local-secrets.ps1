param(
    [string]$Namespace = 'rmc',
    [string]$SuperuserEmail = 'admin@local.test',
    [string]$SuperuserPassword = 'LocalAdmin!2026'
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
    ([BitConverter]::ToString($buffer) -replace '-', '').ToLowerInvariant()
}

function Apply-Secret {
    param([string]$Name, [string[]]$Values)
    $args = @('-n', $Namespace, 'create', 'secret', 'generic', $Name)
    foreach ($value in $Values) { $args += "--from-literal=$value" }
    $args += @('--dry-run=client', '-o', 'yaml')
    & kubectl @args | kubectl apply -f -
}

if (-not (Test-Path $python)) { throw "Python virtual environment not found: $python" }
New-Item -ItemType Directory -Force -Path $jwtDir | Out-Null
& $python (Join-Path $root 'scripts\k8s\generate_local_jwt_keys.py')

$postgresPassword = New-RandomSecret
$rabbitPassword = New-RandomSecret
$clickhousePassword = New-RandomSecret
$minioRootPassword = New-RandomSecret
$djangoMinioPassword = New-RandomSecret
$nestReaderPassword = New-RandomSecret
$djangoSecret = New-RandomSecret 48

kubectl apply -f (Join-Path $root 'deploy\k8s\local\namespace.yaml')
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
Apply-Secret 'postgres-credentials' @('POSTGRES_DB=rmc', 'POSTGRES_USER=rmc_owner', "POSTGRES_PASSWORD=$postgresPassword")
Apply-Secret 'minio-root-credentials' @('MINIO_ROOT_USER=minio_root', "MINIO_ROOT_PASSWORD=$minioRootPassword")
Apply-Secret 'rabbitmq-credentials' @('RABBITMQ_DEFAULT_USER=rmc', "RABBITMQ_DEFAULT_PASS=$rabbitPassword")
Apply-Secret 'clickhouse-credentials' @('CLICKHOUSE_DB=default', 'CLICKHOUSE_USER=default', "CLICKHOUSE_PASSWORD=$clickhousePassword")
Apply-Secret 'django-runtime' @(
    "SECRET_KEY=$djangoSecret", "JWT_LEGACY_HS256_SECRET=$djangoSecret", 'DEBUG=true', 'ALLOWED_HOSTS=*', 'FRONTEND_DOMEN=http://127.0.0.1:8080, http://localhost:8080',
    'POSTGRES_DB=rmc', 'POSTGRES_HOST=postgres', 'POSTGRES_PORT=5432', 'POSTGRES_USER=rmc_owner', "POSTGRES_PASS=$postgresPassword",
    'MINIO_ENDPOINT=minio:9000', 'MINIO_EXTERNAL_ENDPOINT=localhost:8080', 'MINIO_HTTPS=false', 'MINIO_EXTERNAL_HTTPS=false', 'MINIO_REGION=us-east-1', 'MINIO_ROOT_USER=minio_root', "MINIO_ROOT_PASSWORD=$minioRootPassword",
    'MINIO_STORAGE_ACCESS_KEY=django_local', "MINIO_STORAGE_SECRET_KEY=$djangoMinioPassword",
    "CELERY_BROKER=amqp://rmc:$rabbitPassword@rabbitmq:5672//", 'CELERY_BACKEND=redis://redis:6379/0',
    'CLICKHOUSE_DB=default', 'CLICKHOUSE_HOST=clickhouse', 'CLICKHOUSE_PORT=9000', 'CLICKHOUSE_USER=default', "CLICKHOUSE_PASSWORD=$clickhousePassword",
    'URL_1C=http://1c-disabled.local', 'FRONTEND_DOMEN=http://localhost:8080',
    "LOCAL_SUPERUSER_EMAIL=$SuperuserEmail", "LOCAL_SUPERUSER_PASSWORD=$SuperuserPassword"
)
Apply-Secret 'nest-runtime' @(
    'SOURCE_DB_USER=nest_source_reader', "SOURCE_DB_PASSWORD=$nestReaderPassword", 'SOURCE_DB_SCHEMA=public',
    'MINIO_ACCESS_KEY=nest_local_read', 'MINIO_SECRET_KEY=read-only-placeholder'
)
kubectl -n monitoring create secret generic flower-runtime `
  --from-literal="CELERY_BROKER=amqp://rmc:$rabbitPassword@rabbitmq.rmc.svc.cluster.local:5672//" `
  --dry-run=client -o yaml | kubectl apply -f -
kubectl -n $Namespace create secret generic django-jwt-keys --from-file=private.pem=$jwtDir\private.pem --from-file=public.pem=$jwtDir\public.pem --dry-run=client -o yaml | kubectl apply -f -
kubectl -n $Namespace create secret generic nest-jwt-public --from-file=public.pem=$jwtDir\public.pem --dry-run=client -o yaml | kubectl apply -f -
Write-Host 'Full local Kubernetes secrets created.'
