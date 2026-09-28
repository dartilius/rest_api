param([string]$Cluster = 'rmc-local')

$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')

# This intentionally destroys only the explicitly named k3d cluster and its
# local PVCs. It never touches Docker Compose containers or their volumes.
k3d cluster delete $Cluster
k3d cluster create $Cluster `
  --servers 1 --agents 0 `
  --k3s-arg '--disable=traefik@server:*' `
  --port '8080:80@loadbalancer' `
  --port '8443:443@loadbalancer' `
  --wait

kubectl config use-context "k3d-$Cluster"
$config = kubectl config view -o json | ConvertFrom-Json
$server = ($config.clusters | Where-Object { $_.name -eq "k3d-$Cluster" }).cluster.server
$port = ([uri]$server).Port
kubectl config set-cluster "k3d-$Cluster" --server="https://127.0.0.1:$port"

helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx `
  --namespace ingress-nginx --create-namespace `
  --set controller.service.type=LoadBalancer --wait

Push-Location $root
try { & .\scripts\k8s\deploy-full-local.ps1 -Cluster $Cluster }
finally { Pop-Location }
