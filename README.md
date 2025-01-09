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
| `0-categorias.py`     | Descarga la lista de categorías        |
| `1-activi.py`         | Descarga la lista de actividades       |
| `2-sociosporactiv.py` | Baja lista de socios en cada actividad |

Trabajo con los datos:

| Script                                  | Función                                                                   |
| --------------------------------------- | ------------------------------------------------------------------------- |
| `3-actividades-con-huecos.py`           | Muestra las plazas libres en actividades                                  |
| `3-elimina-categorias-bajas.py`         | Elimina las categorías de los socios de baja                              |
| `3-elimina-inscripciones-anuladas.py`   | Elimina las inscripciones anuladas por socios                             |
| `3-elimina-inscripciones-bajas.py`      | Elimina inscripciones de socios de baja en actividades o en la asociación |
| `3-elimina-inscripciones-conflictos.py` | Elimina inscripciones con conflicto de horas                              |
| `3-elimina-tutor-en-campo-socio.py`     | Elimina ID's telegram de tutor en campo de socio                          |
| `3-listado-socios-categoria.py`         | Muestra los socios en cada categoría                                      |
| `3-listado-socios-conflicto-horas.py`   | Lista socios con conflicto de horas                                       |
| `3-listado-socios-conflicto-nosocio.py` | Lista de socios con conflicto en nº de socio o nº carnet                  |
| `3-listado-socios-invalid-TG-id.py`     | Muestra socios con ID de telegram inválido (no numérico)                  |
| `3-listado-tutor-en-campo-socio.py`     | Muestra los ID's de telegram de tutores en campo de socio                 |
| `3-listado-wifi-upv.py`                 | Saca listado de nombres y DNI's para obtener claves wifi                  |
| `3-sociosconflictohoras.py`             | Muestra socios con conflicto de horas                                     |
| `3-sociosdana.py`                       | Muestra socios en Códigos postales afectados por dana                     |
| `4-auto-categoria.py`                   | Asigna categoría +13/+15 según edad                                       |
| `4-nueva-hornada.py`                    | Añade socios a categoría de Acogida por reciente incorporación            |
| `4-sendupdate-telegram-socio.py`        | Manda actualización de datos para ID de telegram del SOCIO                |
| `4-sendupdate-telegram-tutor.py`        | Manda actualización de datos para ID de telegram de TUTORES               |
