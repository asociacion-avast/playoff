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

# Build index for fast lookups
socios_by_id = {s["idColegiat"]: s for s in socios}


print("Procesando actividades...")

# Identify socios de baja ONCE
sociosbaja = set()  # Use set for O(1) membership checks


for socio in socios:
    id_socio = socio["idColegiat"]

    # OPTIMIZATION Phase 2C: Use pre-computed validation
    if socio.get("_valid_baja", False):
        sociosbaja.add(id_socio)

    # OPTIMIZATION Phase 2C: Use pre-computed validation
    if socio.get("_valid_alta_or_preinscripcion", False):
        # OPTIMIZATION Phase 2B: Use pre-computed categories
        categoriassocio = socio.get("_cached_categorias", [])

        if (
            common.categorias["actividades"] not in categoriassocio
            and common.categorias["impagoanual"] not in categoriassocio
        ):
            sociosbaja.add(id_socio)

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
    nombre = actividad["nom"]
    if actividad["idNivell"] and actividad["idNivell"] != "null":
        horario = int(actividad["idNivell"])
    else:
        horario = 0

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

                if inscrito["estat"] == "INSCRESTNOVA":
                    # Skip if already cancelled (O(1) lookup - OPTIMIZATION)
                    if (
                        str(inscripcion) in cancelled_ids
                        or str(inscripcion) in outbox_anuladas
                    ):
                        continue

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
    idActivitat = inscripcion_actividad.get(inscripcion)
    if idActivitat:
        inscripciones_por_actividad[idActivitat].add(inscripcion)

# Build activity name lookup (OPTIMIZATION)
actividades_by_id = {a["idActivitat"]: a for a in actividades}

for idActivitat, inscripciones_set in inscripciones_por_actividad.items():
    actividad = actividades_by_id.get(idActivitat)
    if actividad:
        print(actividad["nom"])
