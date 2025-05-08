# Introducción

Estos scripts permiten realizar una serie de acciones de forma automatizada para llevar a cabo labores de mantenimiento así como automatizaciones de procesos.

Entre los scripts, hay algunos de obtención de datos, que descargan los datos a local para luego trabajar contra esos datos en lugar de tener que ir consultando el API, y por ese motivo, algunas actuaciones que modifican directamente datos via el API, necesitan que luego refresquemos esos datos en local, por ejemplo:

> Al modificar categorías, los usuarios se han modificado en la web, pero nuestra copia local es de 'antes', por lo que si volvemos a ejecutar el script de categorías, volverá a mandar los cambios. Sin embargo, si tras ejecutarlo, descargamos de nuevo el listado de socios, al volver a ejecutar el script de categorías, no debería modificar nada por ver en los datos locales que las categorías ya estaban presentes.

# Configuración

Los scripts necesitan autentificación, y los scripts utilizan dos tipos:

- Lectura
- Lectura y esctitura

Aunque un mismo usuario tenga ambos derechos, en la configuración, debemos indicarlo en dos lugares, por si quisieramos hacer distinción y así podemos localizar rápidamente los scripts que pueden modificar datos.

La configuración la realizamos en un fichero `.avast.ini` en nuestra carpeta de usuario (`~`):

```ini
[auth]
endpoint=asociacionavast
username=myusername
password=mypass
RWusername=myRWusername
RWpassword=myRWpassword
```

# Los scripts

Como decíamos, tenemos scripts de obtención de datos y scripts de trabajo que realizan modificaciones o consultas sobre esos datos.

## Scripts de obtención de datos

Estos scripts obtienen datos del API de playoff y los almacenan en la carpeta `data` del repositorio:

| Script                 | Función                                                |
| ---------------------- | ------------------------------------------------------ |
| `0-soci.py`            | Descarga la lista de socios                            |
| `0-categorias.py`      | Descarga la lista de categorías                        |
| `1-activi.py`          | Descarga la lista de actividades                       |
| `1-socios-familias.py` | Actualiza las familias y los socios en cada familia    |
| `2-sociosporactiv.py`  | Baja lista de socios en cada actividad (inscripciones) |

## Scripts de trabajo con los datos

Estos scripts utilizan los datos descargados por los anteriores y toman acciones relativas a su función y a los datos que han encontrado.

Para los más complejos, existe un fichero adicional donde se explica la funcionalidad y operativa de uso en los ficheros de documentación adicionales que también enlazaremos

| Script                                   | Función                                                                                                 |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `3-actividades-con-huecos.py`            | Muestra las plazas libres en actividades                                                                |
| `3-elimina-inscripciones-anuladas.py`    | Elimina las inscripciones anuladas por socios                                                           |
| `3-elimina-inscripciones-bajas.py`       | Elimina inscripciones de socios de baja en actividades o en la asociación                               |
| `3-elimina-inscripciones-conflictos.py`  | Elimina inscripciones con conflicto de horas                                                            |
| `3-elimina-telegramID-igual-a-socio.py`  | Elimina el ID de Telegram igual al nº de socio                                                          |
| `3-elimina-tutor-en-campo-socio.py`      | Elimina ID's telegram de tutor en campo de socio                                                        |
| `3-listado-socios-actividad-familia.py`  | Muestra familias con 'socio hermano actividades' sin 'socio principal'                                  |
| `3-listado-socios-adultos-sin-id.py`     | Socios adultos sin ID Telegram                                                                          |
| `3-listado-socios-anyos.py`              | Muestra socios por año de inscripción y baja                                                            |
| `3-listado-socios-bajas.py`              | Muestra socios que están de baja con inscripciones                                                      |
| `3-listado-socios-capfamilia.py`         | Muestra socios que son cabezas de familia                                                               |
| `3-listado-socios-categoria.py`          | Muestra los socios en cada categoría                                                                    |
| `3-listado-socios-conflicto-horas.py`    | Lista socios con conflicto de horas                                                                     |
| `3-listado-socios-conflicto-nosocio.py`  | Lista de socios con conflicto en nº de socio o nº carnet                                                |
| `3-listado-socios-invalid-TG-id.py`      | Muestra socios con ID de telegram inválido (no numérico)                                                |
| `3-listado-socios-periodicidad.py`       | Comprueba socios con próximo recibo en fecha incorrecta                                                 |
| `3-listado-socios-preinscritos.py`       | Muestra socios en estado de preinscripción pero sin completar el alta                                   |
| `3-listado-socios-sin-id.py`             | Muestra socios sin ID de Telegram                                                                       |
| `3-listado-tutor-en-campo-socio.py`      | Muestra los ID's de telegram de tutores en campo de socio                                               |
| `3-listado-wifi-upv.py`                  | Saca listado de nombres y DNI's para obtener claves wifi                                                |
| `3-reescribe-descripcion-actividades.py` | Reescribe descripción de actividades                                                                    |
| `3-sociosconflictohoras.py`              | Muestra socios con conflicto de horas                                                                   |
| `3-sociosdana.py`                        | Muestra ID telegram de socios en Códigos postales afectados por la DANA                                 |
| `3-web-actividades.py`                   | Listado de talleres con inscripción abierta y plazas                                                    |
| `4-auto-alta-socios.py`                  | Procesa socios en preinscripción que han pagado las actividades para hacer el cambio a socios en activo |
| `4-auto-cambios-modalidad.py`            | Cambia socios de modalidad según campo personalizado fecha cambio y categoría objetivo                  |
| `4-auto-carnetspagados.py`               | Verifica los socios que han pagado carnet de socios 'Veteranos' para gestión                            |
| `4-auto-categoria.py`                    | Asigna categorías (año, +13/+15/+18) y borrar categorías no válidas                                     |
| `4-estado-pago-recibos.py`               | Etiqueta como con impagos o elimina etiqueta en función de estado de recibos                            |
| `4-nueva-hornada.py`                     | Añade socios a categoría de Acogida por reciente incorporación                                          |
| `4-sendupdate-telegram-socio.py`         | Manda actualización de datos para ID de telegram del SOCIO                                              |
| `4-sendupdate-telegram-tutor.py`         | Manda actualización de datos para ID de telegram de TUTORES                                             |
| `4-socio-por-idtelegram.py`              | Localiza el socio en base a la ID de Telegram                                                           |
| `5-abreactividad.py`                     | Abre plazo de inscripción en una actividad                                                              |
| `5-archivaactividades.py`                | Archiva actividades cuya fecha de fin ya ha pasado                                                      |
| `5-inscribeactividad.py`                 | Inscribe a un socio en una actividad                                                                    |
