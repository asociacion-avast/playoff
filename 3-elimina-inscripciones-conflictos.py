#!/usr/bin/env python
import configparser
import datetime
import os
from collections import defaultdict

import common
import sync_store

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


print("Loading file from disk")

token_ro = common.gettoken()
actividades = common.readjson(filename="actividades")


print("Procesando actividades...")

usuariosyactividad = {}
actividadyusuarios = {}
usuariosyhorarios = {}
usuarioseinscripciones = {}
usuariosyhorariosinscripciones = {}
inscripcion_actividad = {}


ahora = datetime.datetime.now()

for actividad in actividades:
    myid = actividad["idActivitat"]
    horario = common.actividad_horario(actividad)

    if horario in {7, 8, 9, 10, 19, 20, 21, 22}:
        inscritos = common.read_inscripciones_actividad(token_ro, myid)
        actividadyusuarios[myid] = []

        for inscrito in inscritos:
            colegiat = inscrito["colegiat"]["idColegiat"]
            fecha = common.parse_date(inscrito["dataIntroduccio"])

            if fecha is None:
                continue

            if ahora - fecha <= datetime.timedelta(hours=1, minutes=30):
                continue

            if inscrito["estat"] != "INSCRESTNOVA":
                continue

            actividadyusuarios[myid].append(colegiat)
            inscripcion = inscrito["idInscripcio"]
            inscripcion_actividad[inscripcion] = myid

            usuariosyactividad.setdefault(colegiat, []).append(myid)
            usuariosyhorarios.setdefault(colegiat, []).append(horario)
            usuariosyhorariosinscripciones.setdefault(colegiat, {}).setdefault(
                horario, []
            ).append(inscripcion)
            usuarioseinscripciones.setdefault(colegiat, []).append(inscripcion)


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)

inscripcionesanuladas = []

# Read outbox once before processing (OPTIMIZATION)
outbox_entries = sync_store.read_outbox()
outbox_anuladas = {
    str(e["payload"]["inscripcion"])
    for e in outbox_entries
    if e.get("op") == "anula_inscripcio" and e.get("status") in ["pending", "synced"]
}

# Collect all inscriptions to check and group by activity (OPTIMIZATION)
inscripciones_por_actividad = defaultdict(list)
for usuario, value in usuariosyhorarios.items():
    if len(value) != len(sorted(set(usuariosyhorarios[usuario]))):
        for horario in usuariosyhorariosinscripciones[usuario]:
            if len(usuariosyhorariosinscripciones[usuario][horario]) > 1:
                for inscripcion in usuariosyhorariosinscripciones[usuario][horario]:
                    if idActivitat := inscripcion_actividad.get(inscripcion):
                        inscripciones_por_actividad[idActivitat].append(
                            (usuario, horario, inscripcion)
                        )

# Read each activity file once and build cache set (OPTIMIZATION)
cache_por_actividad = {}
for idActivitat in inscripciones_por_actividad.keys():
    inscritos = common.readjson(filename=f"{idActivitat}")
    cache_por_actividad[idActivitat] = {
        str(i["idInscripcio"])
        for i in inscritos
        if i.get("estat") in ["INSCRESTANU", "anulada"]
    }

# Now process with O(1) lookups
for usuario, value in usuariosyhorarios.items():
    # El usuaro tiene horarios duplicados
    if len(value) != len(sorted(set(usuariosyhorarios[usuario]))):
        # calcular horarios a borrar y verlos en las inscripciones

        url = f"{common.sociobase}{usuario}#tab=ACTIVITATS"
        print("\nUsuario: %s" % url)
        print(
            f"Inscripciones usuario y horarios: {usuariosyhorariosinscripciones[usuario]}"
        )

        for horario in usuariosyhorariosinscripciones[usuario]:
            if len(usuariosyhorariosinscripciones[usuario][horario]) > 1:
                print(horario)
                print(usuariosyhorariosinscripciones[usuario][horario])

                for inscripcion in usuariosyhorariosinscripciones[usuario][horario]:
                    # Rellena variable para luego sacar el nombre
                    inscripcionesanuladas.append(inscripcion)

                    # Check if already anulada (O(1) lookups - OPTIMIZED)
                    idActivitat = inscripcion_actividad.get(inscripcion)
                    cancelled_cache = cache_por_actividad.get(idActivitat, set())

                    if (
                        str(inscripcion) in cancelled_cache
                        or str(inscripcion) in outbox_anuladas
                    ):
                        print(f"Inscripción {inscripcion} ya procesada (skipping)")
                        continue

                    print("Anulando y comunicando")
                    response = common.anula_inscripcio(
                        token,
                        inscripcion=inscripcion,
                        comunica=True,
                        idActivitat=idActivitat,
                    )
                    print(response)

print(
    "\nInscripciones anuladas en los siguientes talleres por inscripciones a la misma hora:"
)

for actividad in actividades:
    myid = actividad["idActivitat"]
    nombre = actividad["nom"]
    horario = common.actividad_horario(actividad)

    if horario in {7, 8, 9, 10, 19, 20, 21, 22}:
        inscritos = common.read_inscripciones_actividad(token_ro, myid)

        for inscrito in inscritos:
            inscripcion = inscrito["idInscripcio"]
            if inscripcion in inscripcionesanuladas:
                print(nombre)
