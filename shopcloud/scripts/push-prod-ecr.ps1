# Build all Shopcloud service images from the monorepo root and push to prod ECR as :latest.
# Prerequisites: AWS CLI credentials (ecr:BatchCheckLayerAvailability, ecr:PutImage, ...), Docker.
# Usage (from anywhere):  pwsh -File shopcloud/scripts/push-prod-ecr.ps1
# Or:  cd shopcloud; ../shopcloud/scripts/push-prod-ecr.ps1   — script cd's to repo root automatically.

param(
    [string]$AwsRegion = "eu-central-1",
    [string]$AwsAccount = "712044128773",
    [string]$RepoPrefix = "shopcloud-prod"
)

$ErrorActionPreference = "Stop"
$ShopcloudRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ShopcloudRoot

$registry = "$AwsAccount.dkr.ecr.$AwsRegion.amazonaws.com"
Write-Host "Logging in to $registry ..."
aws ecr get-login-password --region $AwsRegion | docker login --username AWS --password-stdin $registry

$services = @(
    "api-gateway",
    "auth",
    "cart",
    "catalog",
    "checkout",
    "admin",
    "customer-web"
)

foreach ($svc in $services) {
    $image = "$registry/${RepoPrefix}-${svc}:latest"
    Write-Host "`n=== Building $svc -> $image ===" -ForegroundColor Cyan
    if ($svc -eq "customer-web") {
        # Dockerfile COPY paths are relative to services/customer-web (not monorepo root).
        # Empty VITE_BACKEND_URL => SPA calls same-origin `/api` (matches public ingress /api -> api-gateway).
        docker build `
            -f "services/$svc/Dockerfile" `
            --build-arg "VITE_BACKEND_URL=" `
            -t $image `
            "services/$svc"
    }
    else {
        docker build -f "services/$svc/Dockerfile" -t $image .
    }
    if ($LASTEXITCODE -ne 0) { throw "docker build failed for $svc (exit $LASTEXITCODE)" }
    docker push $image
    if ($LASTEXITCODE -ne 0) { throw "docker push failed for $svc (exit $LASTEXITCODE)" }
}

Write-Host "`nDone. Restart workloads: kubectl rollout restart deployment -n app" -ForegroundColor Green
