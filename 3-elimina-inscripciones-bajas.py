#!/usr/bin/env python


import configparser
import os
from collections import defaultdict

import common
import sync_store

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


print("Loading file from disk")

token_ro = common.gettoken()
actividades = common.readjson(filename="actividades")
socios = common.readjson(filename="socios")

print("Procesando actividades...")

# Identify socios de baja ONCE
sociosbaja = {s["idColegiat"] for s in socios if common.is_socio_baja(s)}
print(f"Found {len(sociosbaja)} socios de baja")

# Read outbox ONCE before processing (OPTIMIZATION)
outbox_entries = sync_store.read_outbox()
outbox_anuladas = {
    str(e["payload"]["inscripcion"])
    for e in outbox_entries
    if e.get("op") == "anula_inscripcio" and e.get("status") in ["pending", "synced"]
}

# Group inscriptions to cancel by user and activity (OPTIMIZATION)
usuariosyhorariosinscripciones = defaultdict(lambda: defaultdict(list))
inscripcion_actividad = {}

# Process all activities
for actividad in actividades:
    myid = actividad["idActivitat"]
    horario = common.actividad_horario(actividad)

    if horario in {7, 8, 9, 10}:
        # Read inscriptions for this activity ONCE
        inscritos = common.readjson(filename=f"{myid}")

        # Build set of already cancelled inscriptions for this activity (OPTIMIZATION)
        cancelled_ids = {
            str(i["idInscripcio"])
            for i in inscritos
            if i.get("estat") in ["INSCRESTANU", "anulada"]
        }

        for inscrito in inscritos:
            colegiat = inscrito["colegiat"]["idColegiat"]

            if colegiat in sociosbaja:
                inscripcion = inscrito["idInscripcio"]
                inscripcion_actividad[inscripcion] = myid

                # Skip if already cancelled (O(1) lookup - OPTIMIZATION)
                if (
                    str(inscripcion) not in cancelled_ids
                    and str(inscripcion) not in outbox_anuladas
                ) and inscrito["estat"] == "INSCRESTNOVA":
                    usuariosyhorariosinscripciones[colegiat][horario].append(
                        inscripcion
                    )


# Get RW token
token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)

inscripcionesanuladas = []

# Process cancellations grouped by user
for usuario, horarios in usuariosyhorariosinscripciones.items():
    url = f"{common.sociobase}{usuario}#tab=ACTIVITATS"
    print(f"\nUsuario: {url}")
    print(f"Inscripciones usuario y horarios: {dict(horarios)}")

    for horario, inscripciones in horarios.items():
        for inscripcion in inscripciones:
            inscripcionesanuladas.append(inscripcion)

            print("Anulando y Comunicando")
            response = common.anula_inscripcio(
                token=token,
                inscripcion=inscripcion,
                comunica=True,
                idActivitat=inscripcion_actividad.get(inscripcion),
            )
            print(response)

print(
    "\nInscripciones anuladas en los siguientes talleres por bajas o por estar sin actividades"
)

# Final reporting - group by activity for efficiency (OPTIMIZATION)
inscripciones_por_actividad = defaultdict(set)
for inscripcion in inscripcionesanuladas:
    if idActivitat := inscripcion_actividad.get(inscripcion):
        inscripciones_por_actividad[idActivitat].add(inscripcion)

# Build activity name lookup (OPTIMIZATION)
actividades_by_id = {a["idActivitat"]: a for a in actividades}

for idActivitat in inscripciones_por_actividad:
    if actividad := actividades_by_id.get(idActivitat):
        print(actividad["nom"])
