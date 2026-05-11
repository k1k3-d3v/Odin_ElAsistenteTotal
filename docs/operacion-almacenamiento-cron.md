# Operacion de almacenamiento y cron

Fecha: 2026-05-11

Documento de trabajo sin secretos. No incluye tokens, claves, contrasenas ni valores de `.env`.

## Contexto

Durante la reorganizacion del servidor Odín se detectaron dos necesidades operativas:

- pausar automatizaciones antiguas de cron mientras se prepara una nueva estrategia basada en un NVMe externo de 1 TB;
- mover la biblioteca de Immich fuera del disco raiz hacia `/mnt/almacen`, para separar datos pesados del sistema y reducir presion sobre `/`.

La prioridad fue no romper servicios existentes. Por eso las acciones se hicieron con copias previas y sin borrar datos originales hasta validar que los servicios vuelven a levantar correctamente.

## Cron

El cron del usuario quedo desactivado de forma reversible. No se borraron las entradas: se comentaron y se dejo una copia historica en:

```text
/home/k1k3/odin/logs/autorepair/crontab.before_*.txt
```

Entradas pausadas:

```cron
# */30 * * * * /home/k1k3/env/bin/python3 /home/k1k3/odin/scripts/update_odin.py >> /home/k1k3/odin_sync.log 2>&1
# 0 * * * * /home/k1k3/odin/scripts/lanzar_ingesta.sh >> /home/k1k3/odin_sync.log 2>&1
# */15 * * * * /home/k1k3/odin/scripts/odin_autorepair.py --repair --alert >> /home/k1k3/odin/logs/autorepair/cron.log 2>&1
# 0 9 * * * /home/k1k3/odin/scripts/odin_autorepair.py --daily >> /home/k1k3/odin/logs/autorepair/cron.log 2>&1
```

La decision se debe a que la etapa de automatizacion cambia de fase: antes tenia sentido ejecutar ingestas y reportes sobre la estructura actual; ahora conviene esperar a que el almacenamiento definitivo este montado, probado y documentado.

## Immich

Immich almacenaba la biblioteca en:

```text
/home/k1k3/Pictures/immich
```

La nueva ubicacion aplicada es:

```text
/mnt/almacen/immich
```

Procedimiento seguido:

1. detener solo el stack de Immich con `docker compose down`;
2. guardar copia de `.env`;
3. copiar los datos mediante `rsync -aH`;
4. cambiar `UPLOAD_LOCATION` cuando la copia termine;
5. levantar Immich y verificar API/estado de contenedores;
6. validar igualdad de tamano y numero de ficheros;
7. conservar el origen antiguo hasta decidir su borrado definitivo.

Resultado validado:

| Elemento | Estado |
| --- | --- |
| `UPLOAD_LOCATION` | `/mnt/almacen/immich` |
| Contenedores Immich | `healthy` |
| API local | `http://127.0.0.1:2283/api/server/ping` responde `pong` |
| Tamano origen | 202 GB |
| Tamano destino | 202 GB |
| Ficheros origen | 77.666 |
| Ficheros destino | 77.666 |

El origen `/home/k1k3/Pictures/immich` no se borro todavia. Aunque la migracion esta validada, eliminarlo libera mucho espacio y es una accion irreversible si no hay backup adicional.

## Limpieza

La limpieza se plantea de forma conservadora:

- eliminar contenedores Docker detenidos;
- eliminar imagenes Docker no usadas;
- eliminar cache de build Docker;
- no ejecutar `docker system prune --volumes`;
- no borrar `/home/k1k3/cuarentena` ni caches de modelos sin revisar su contenido.

Esta politica libera espacio sin tocar volumenes persistentes ni datos que podrian contener bases de datos, modelos o material de experimentacion util para la memoria.

Acciones ejecutadas:

| Accion | Resultado |
| --- | --- |
| `docker container prune -f` | eliminados contenedores detenidos |
| `docker builder prune -af` | liberada cache de build |
| `docker image prune -af` | eliminadas imagenes no usadas |
| Volumenes Docker | no tocados |
| `/home/k1k3/cuarentena` | no tocado |
| `/home/k1k3/Pictures/immich` | no tocado tras migracion |
