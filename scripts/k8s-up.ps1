param([ValidateSet("dev", "demo")][string]$Ambiente = "demo")

$ErrorActionPreference = "Stop"
$ns      = "solarbi-$Ambiente"
$overlay = "k8s/overlays/$Ambiente"
$utf8    = New-Object System.Text.UTF8Encoding($false)

function Verificar($mensaje) {
    if ($LASTEXITCODE -ne 0) { throw $mensaje }
}


$cfg = @{}
foreach ($linea in Get-Content .env) {
    if ($linea -match '^\s*([A-Za-z_]+)\s*=\s*(.*?)\s*$') { $cfg[$Matches[1]] = $Matches[2] }
}
foreach ($k in "DB_USER", "DB_NAME", "DB_PASSWORD", "GRAFANA_ADMIN_PASSWORD") {
    if (-not $cfg[$k]) { throw "Falta $k en .env" }
}

# 2) Ruta de la SQLite tal como la ve el nodo de Docker Desktop
$raiz   = (Get-Location).Path
$bronze = "/run/desktop/mnt/host/" + $raiz.Substring(0, 1).ToLower() + $raiz.Substring(2).Replace('\', '/') + "/data/bronze"

# 3) Namespace y Secret
kubectl apply -f "$overlay/namespace.yaml"
Verificar "No se pudo crear el namespace"
kubectl -n $ns create secret generic solarbi-secrets `
    "--from-literal=DB_USER=$($cfg.DB_USER)" `
    "--from-literal=DB_NAME=$($cfg.DB_NAME)" `
    "--from-literal=DB_PASSWORD=$($cfg.DB_PASSWORD)" `
    "--from-literal=GRAFANA_ADMIN_PASSWORD=$($cfg.GRAFANA_ADMIN_PASSWORD)" `
    --dry-run=client -o yaml | kubectl apply -f -
Verificar "No se pudo crear el Secret"

# 4) Renderizar los manifiestos 
$tmp = Join-Path $env:TEMP "solarbi-$Ambiente.yaml"
kubectl kustomize --load-restrictor LoadRestrictionsNone $overlay -o $tmp
Verificar "Kustomize falló"
$yaml = [IO.File]::ReadAllText($tmp, $utf8).Replace("__BRONZE_HOSTPATH__", $bronze)
[IO.File]::WriteAllText($tmp, $yaml, $utf8)

# 5) Aplicar 
kubectl -n $ns delete job etl --ignore-not-found
kubectl apply -f $tmp
Verificar "kubectl apply falló"

# 6) Esperar a los servicios con estado
kubectl -n $ns rollout status statefulset/postgres --timeout=300s
Verificar "PostgreSQL no quedó listo"
kubectl -n $ns rollout status deployment/grafana --timeout=300s
Verificar "Grafana no quedó listo"

Write-Host ""
Write-Host "Ambiente '$Ambiente' levantado en el namespace $ns" -ForegroundColor Green
Write-Host "  Grafana   : http://localhost:30300   (usuario admin)"
Write-Host "  PostgreSQL: localhost:30434          (DBeaver / Power BI)"
Write-Host "  Carga histórica en curso:  kubectl -n $ns logs -f job/etl"
kubectl -n $ns get pods
