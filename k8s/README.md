# Despliegue en Kubernetes (Docker Desktop, un solo nodo)

```powershell
.\scripts\k8s-up.ps1          # levantar (ambiente demo)
.\scripts\k8s-down.ps1        # eliminar todo
```

Ambientes: `dev` (namespace `solarbi-dev`, simulador cada 10 s) y `demo` (`solarbi-demo`, cada 5 s).
Despliega uno a la vez: comparten los NodePort 30300 y 30434.

## Objeto elegido para cada necesidad

| Necesidad | Objeto | Por qué ese y no otro |
|---|---|---|
| Aislar el proyecto | Namespace | Separa recursos, permite borrar todo con un comando |
| BD que no pierda datos | StatefulSet + PVC | Identidad y volumen estables; un Deployment no garantiza el volumen |
| Grafana siempre disponible | Deployment | Sin estado propio: si el pod muere, vuelve igual por provisioning |
| Credenciales fuera del código | Secret (creado desde `.env` por el script) | No va en las imágenes ni en Git |
| Configuración separada | ConfigMap `solarbi-config` | Parámetros no sensibles por variable de entorno |
| Provisioning de Grafana | ConfigMaps montados en `/etc/grafana/provisioning` | Tableros, fuente de datos y alertas versionados |
| Comunicación por nombre | Service `postgres` (headless) | DNS interno; no se usan IP |
| Carga histórica | Job | Corre una vez, termina y conserva logs como evidencia |
| Datos periódicos | CronJob (cada minuto, `Forbid`) | Ejecución corta y repetida, no un proceso eterno |
| Salud | startup/readiness/liveness probes | `pg_isready` y `/api/health` |
| No agotar el equipo | `resources.requests/limits` | En todos los contenedores |
| Acceso desde el anfitrión | Service NodePort (30434, 30300) | Sin Ingress, como pide el nivel básico |

## Cómo llegan las imágenes propias al clúster
Docker Desktop (modo kubeadm) usa el mismo almacén de imágenes que Docker: `solarbi-etl:1.0`, construida con
`docker compose build etl`, es visible con `imagePullPolicy: IfNotPresent`, sin registro.

## Demostración de resiliencia
```powershell
kubectl -n solarbi-demo delete pod postgres-0      # los datos siguen (PVC)
kubectl -n solarbi-demo delete pod -l app=grafana  # vuelve con su tablero (provisioning)
.\scripts\demo.ps1 corte                           # (con compose) o ver el simulador en el clúster
```
