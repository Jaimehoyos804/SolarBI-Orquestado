<#
 Elimina toda la solución (incluye el volumen de datos y el Secret):
     .\scripts\k8s-down.ps1
     .\scripts\k8s-down.ps1 -Ambiente dev
#>
param([ValidateSet("dev", "demo")][string]$Ambiente = "demo")

kubectl delete namespace "solarbi-$Ambiente" --ignore-not-found
