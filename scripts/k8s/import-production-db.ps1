param(
    [string]$Cluster = 'rmc-local',
    [string]$Namespace = 'rmc',
    [string]$ConfigPath = '.local-secrets\production-db-import.env',
    [switch]$ReplaceLocalDatabase,
    [switch]$CreateLocalTestUser
)

$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$backupDir = Join-Path $root '.local-backups'
$configFile = Join-Path $root $ConfigPath
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$localDatabase = 'rmc'
$localOwner = 'rmc_owner'

function Read-LocalEnvFile {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        throw "Import configuration is missing: $Path. Copy scripts/k8s/production-db-import.example.env into .local-secrets first."
    }

    $values = @{}
    foreach ($line in Get-Content $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
        $parts = $trimmed.Split('=', 2)
        if ($parts.Count -ne 2 -or -not $parts[0].Trim()) {
            throw "Invalid configuration line in $Path."
        }
        $values[$parts[0].Trim()] = $parts[1]
    }

    foreach ($key in 'SOURCE_DB_HOST', 'SOURCE_DB_PORT', 'SOURCE_DB_NAME', 'SOURCE_DB_USER', 'SOURCE_DB_PASSWORD') {
        if (-not $values[$key]) { throw "Missing $key in $Path." }
    }
    return $values
}

function Invoke-SourcePostgres {
    param([hashtable]$Source, [string[]]$PostgresArguments)

    & docker run --rm `
        --env "PGPASSWORD=$($Source.SOURCE_DB_PASSWORD)" `
        postgres:18.3 `
        @PostgresArguments
    if ($LASTEXITCODE -ne 0) { throw 'Source PostgreSQL command failed.' }
}

function Assert-LastExit {
    param([string]$Message)
    if ($LASTEXITCODE -ne 0) { throw $Message }
}

if (-not $ReplaceLocalDatabase) {
    throw 'This command replaces the local k3d database. Re-run with -ReplaceLocalDatabase after reviewing the target.'
}

$context = & kubectl config current-context
if ($LASTEXITCODE -ne 0 -or $context.Trim() -ne "k3d-$Cluster") {
    throw "Current kubectl context must be k3d-$Cluster; got '$context'."
}

$source = Read-LocalEnvFile $configFile
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

# Verify the production role before mutating the local cluster.
Invoke-SourcePostgres $source @(
    'psql', '-h', $source.SOURCE_DB_HOST, '-p', $source.SOURCE_DB_PORT,
    '-U', $source.SOURCE_DB_USER, '-d', $source.SOURCE_DB_NAME,
    '-v', 'ON_ERROR_STOP=1', '-c', 'SELECT current_user, current_database();'
)

$djangoReplicas = & kubectl get deployment django-api -n $Namespace -o jsonpath='{.spec.replicas}'
$nestReplicas = & kubectl get deployment nest-api -n $Namespace -o jsonpath='{.spec.replicas}'
if ($LASTEXITCODE -ne 0) { throw 'The local Django and Nest deployments must exist before import.' }

Write-Host 'Stopping local API deployments...'
& kubectl scale deployment/django-api -n $Namespace --replicas=0
Assert-LastExit 'Could not stop Django API.'
& kubectl scale deployment/nest-api -n $Namespace --replicas=0
Assert-LastExit 'Could not stop Nest API.'
& kubectl rollout status deployment/django-api -n $Namespace --timeout=120s
& kubectl rollout status deployment/nest-api -n $Namespace --timeout=120s

$localBackupName = "local-before-production-import-$timestamp.dump"
$productionDumpName = "production-$($source.SOURCE_DB_NAME)-$timestamp.dump"

try {
    Write-Host "Saving the current local database to $localBackupName..."
    & kubectl exec -n $Namespace postgres-0 -- pg_dump -Fc -U $localOwner -d $localDatabase -f "/tmp/$localBackupName"
    Assert-LastExit 'Could not create the local database backup.'
    & kubectl cp "${Namespace}/postgres-0:/tmp/$localBackupName" ".\.local-backups\$localBackupName"
    if ($LASTEXITCODE -ne 0) { throw 'Could not copy the local backup from PostgreSQL pod.' }
    & kubectl exec -n $Namespace postgres-0 -- rm -f "/tmp/$localBackupName"

    Write-Host 'Creating a consistent read-only dump from production...'
    $hostBackupDir = (Resolve-Path $backupDir).Path
    & docker run --rm `
        --env "PGPASSWORD=$($source.SOURCE_DB_PASSWORD)" `
        --volume "${hostBackupDir}:/backups" `
        postgres:18.3 `
        pg_dump -Fc --no-owner --no-privileges `
        -h $source.SOURCE_DB_HOST -p $source.SOURCE_DB_PORT `
        -U $source.SOURCE_DB_USER -d $source.SOURCE_DB_NAME `
        -f "/backups/$productionDumpName"
    if ($LASTEXITCODE -ne 0) { throw 'Production dump failed. The local database backup is preserved.' }

    Write-Host 'Replacing the local database...'
    $stagingDump = '.\.local-backups\restore-staging.dump'
    Copy-Item (Join-Path $backupDir $productionDumpName) $stagingDump
    try {
        & kubectl cp $stagingDump "${Namespace}/postgres-0:/tmp/$productionDumpName"
        if ($LASTEXITCODE -ne 0) { throw 'Could not copy the production dump to PostgreSQL pod.' }
    }
    finally {
        Remove-Item $stagingDump -ErrorAction SilentlyContinue
    }

    & kubectl exec -n $Namespace postgres-0 -- psql -U $localOwner -d postgres -v ON_ERROR_STOP=1 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$localDatabase' AND pid <> pg_backend_pid();"
    Assert-LastExit 'Could not terminate local database connections.'
    & kubectl exec -n $Namespace postgres-0 -- dropdb -U $localOwner $localDatabase
    Assert-LastExit 'Could not drop the local database.'
    & kubectl exec -n $Namespace postgres-0 -- createdb -U $localOwner -O $localOwner $localDatabase
    Assert-LastExit 'Could not create the local database.'
    foreach ($section in 'pre-data', 'data', 'post-data') {
        & kubectl exec -n $Namespace postgres-0 -- pg_restore --exit-on-error --no-owner --no-privileges "--section=$section" -U $localOwner -d $localDatabase "/tmp/$productionDumpName"
        if ($LASTEXITCODE -ne 0) { throw "Local restore failed in $section section." }
    }
    & kubectl exec -n $Namespace postgres-0 -- rm -f "/tmp/$productionDumpName"

    # The restored database has no grants for the local Nest login role.
    & kubectl delete job grant-nest-source-reader -n $Namespace --ignore-not-found --wait
    Assert-LastExit 'Could not remove the previous Nest database-grant Job.'
    & kubectl apply -f (Join-Path $root 'deploy\k8s\local\jobs.yaml')
    Assert-LastExit 'Could not apply Nest database-grant resources.'
    & kubectl wait --for=condition=complete job/grant-nest-source-reader -n $Namespace --timeout=180s
    if ($LASTEXITCODE -ne 0) { throw 'Could not grant local read-only access to Nest.' }
}
finally {
    Write-Host 'Starting local API deployments...'
    & kubectl scale deployment/django-api -n $Namespace --replicas=$djangoReplicas
    & kubectl scale deployment/nest-api -n $Namespace --replicas=$nestReplicas
    if ([int]$djangoReplicas -gt 0) { & kubectl rollout status deployment/django-api -n $Namespace --timeout=180s }
    if ([int]$nestReplicas -gt 0) { & kubectl rollout status deployment/nest-api -n $Namespace --timeout=180s }
}

if ($CreateLocalTestUser) {
    & kubectl exec -n $Namespace deployment/django-api -- sh -ec 'python manage.py shell -c "from os import environ; from users.models import CustomUser; u, _ = CustomUser.objects.get_or_create(email=environ[\"LOCAL_TEST_EMAIL\"], defaults={\"phone_number\": environ[\"LOCAL_TEST_PHONE\"], \"role\": \"ordinary\"}); u.phone_number=environ[\"LOCAL_TEST_PHONE\"]; u.role=\"ordinary\"; u.is_active=True; u.set_password(environ[\"LOCAL_TEST_PASSWORD\"]); u.save()"'
    if ($LASTEXITCODE -ne 0) { throw 'Production data was restored, but creation of the local test user failed.' }
}

& kubectl exec -n $Namespace postgres-0 -- psql -U $localOwner -d $localDatabase -c 'SELECT COUNT(*) AS brands FROM public.brands; SELECT COUNT(*) AS nomenclatures FROM public.nomenclature;'
Write-Host "Import complete. Backups are in $backupDir and are intentionally ignored by Git."
