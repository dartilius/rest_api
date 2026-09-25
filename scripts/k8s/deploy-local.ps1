param(
    [string]$Cluster = 'rmc-local',
    [string]$Namespace = 'rmc'
)

$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')

& (Join-Path $root 'scripts\k8s\create-local-secrets.ps1') -Namespace $Namespace

Push-Location $root
try {
    docker build -t rmc-django:local ./backend
    docker build -t rmc-nest:local ./nest-backend
    k3d image import --cluster $Cluster rmc-django:local rmc-nest:local

    kubectl apply -f deploy/k8s/local/infra.yaml
    kubectl rollout status statefulset/postgres -n $Namespace --timeout=180s

    kubectl delete job django-migrate-and-bootstrap grant-nest-source-reader minio-bootstrap -n $Namespace --ignore-not-found --wait
    kubectl delete statefulset minio -n $Namespace --ignore-not-found --wait
    kubectl delete service minio -n $Namespace --ignore-not-found
    kubectl apply -f deploy/k8s/local/jobs.yaml
    kubectl wait --for=condition=complete job/django-migrate-and-bootstrap -n $Namespace --timeout=300s
    kubectl wait --for=condition=complete job/grant-nest-source-reader -n $Namespace --timeout=180s

    kubectl apply -f deploy/k8s/local/apps.yaml
    # Secrets may have been regenerated above; force both processes to mount
    # the same fresh RSA key pair before reporting the environment ready.
    kubectl rollout restart deployment/django-api -n $Namespace
    kubectl rollout restart deployment/nest-api -n $Namespace
    kubectl rollout status deployment/django-api -n $Namespace --timeout=180s
    kubectl rollout status deployment/nest-api -n $Namespace --timeout=180s
}
finally {
    Pop-Location
}

Write-Host 'Local RMC cluster is ready at http://localhost:8080'
