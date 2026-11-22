param(
    [ValidateSet("normal", "corte", "silencio")][string]$modo = "normal",
    [ValidateSet("k8s", "compose")][string]$destino = "k8s"
)

$u = (Select-String -Path .env -Pattern '^DB_USER=(.*)$').Matches.Groups[1].Value.Trim()
$d = (Select-String -Path .env -Pattern '^DB_NAME=(.*)$').Matches.Groups[1].Value.Trim()
$sql = "UPDATE silver.control_simulador SET modo='$modo', actualizado=now() WHERE id=1;"

if ($destino -eq "k8s") {
    kubectl -n solarbi-demo exec postgres-0 -- psql -U $u -d $d -c $sql
} else {
    docker exec solarbi-postgres psql -U $u -d $d -c $sql
}
Write-Host "Simulador en modo: $modo ($destino)"