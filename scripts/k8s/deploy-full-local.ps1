param([string]$Cluster = 'rmc-local')

$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
Push-Location $root
try {
    & .\scripts\k8s\create-full-local-secrets.ps1
    docker build -t rmc-django:local ./backend
    docker build -t rmc-nest:local ./nest-backend
    k3d image import --cluster $Cluster rmc-django:local rmc-nest:local
    kubectl apply -f deploy/k8s/local/full-infra.yaml
    foreach ($stateful in 'postgres', 'minio', 'rabbitmq', 'clickhouse', 'opensearch') {
      kubectl rollout status "statefulset/$stateful" -n rmc --timeout=300s
    }
    kubectl rollout status deployment/redis -n rmc --timeout=120s
    kubectl delete job minio-bootstrap django-bootstrap grant-nest-source-reader -n rmc --ignore-not-found --wait
    kubectl apply -f deploy/k8s/local/full-jobs.yaml
    kubectl wait --for=condition=complete job/minio-bootstrap -n rmc --timeout=180s
    kubectl wait --for=condition=complete job/django-bootstrap -n rmc --timeout=300s
    kubectl apply -f deploy/k8s/local/full-jobs.yaml
    kubectl wait --for=condition=complete job/grant-nest-source-reader -n rmc --timeout=180s
    kubectl apply -f deploy/k8s/local/full-apps.yaml
    kubectl apply -f deploy/k8s/local/full-monitoring.yaml
    kubectl delete service flower -n monitoring --ignore-not-found
    kubectl apply -f deploy/k8s/local/k8s-view.yaml
    foreach ($deploy in 'django-api', 'nest-api', 'celery-worker', 'celery-beat', 'gateway') {
      kubectl rollout status "deployment/$deploy" -n rmc --timeout=180s
    }
    foreach ($deploy in 'flower', 'pgadmin', 'k8s-view') {
      kubectl rollout status "deployment/$deploy" -n monitoring --timeout=180s
    }
}
finally { Pop-Location }
Write-Host 'Full local Kubernetes environment is ready at http://localhost:8080'
