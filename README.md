Create a file in `~/.avast.ini` with the following structure:

```ini
[auth]
username=myusername
password=mypass
RWusername=myRWusername
RWpassword=myRWpassword
```

This will be used by the scripts to perform the different tasks (`common.py` contains some functions used by the scripts)

Obtención de datos (saved in `data` folder):

| Script                | Función                                |
| --------------------- | -------------------------------------- |
| `0-soci.py`           | Descarga la lista de socios            |
| `1-activi.py`         | Descarga la lista de actividades       |
| `2-sociosporactiv.py` | Baja lista de socios en cada actividad |

Trabajo con los datos:

| Script                                | Función                                                  |
| ------------------------------------- | -------------------------------------------------------- |
| `3-elimina-conflictohoras.py`         | Elimina inscripciones con conflicto de horas             |
| `3-elimina-inscripciones-anuladas.py` | Elimina las inscripciones anuladas por socios            |
| `3-listadowifiupv.py`                 | Saca listado de nombres y DNI's para obtener claves wifi |
| `3-sociosconflictohoras.py`           | Informa de los socios con conflicto de horas             |
