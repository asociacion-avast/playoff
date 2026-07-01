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


print("Procesando actividades...")

anuladas = []
inscripcion_actividad = {}

print("Procesando inscripciones")
for actividad in actividades:
    myid = actividad["idActivitat"]
    horario = common.actividad_horario(actividad)

    if horario in {7, 8, 9, 10}:
        inscritos = common.read_inscripciones_actividad(token_ro, myid)

        for inscrito in inscritos:
            if inscrito["estat"] != "INSCRESTANULADA":
                continue

            ID = inscrito["idInscripcio"]
            anuladas.append(ID)
            inscripcion_actividad[ID] = myid


anuladas = sorted(set(anuladas))
print(anuladas)
print(len(anuladas))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)

# Read outbox once before processing (OPTIMIZATION)
outbox_entries = sync_store.read_outbox()
outbox_anuladas = {
    str(e["payload"]["inscripcion"])
    for e in outbox_entries
    if e.get("op") == "anula_inscripcio" and e.get("status") in ["pending", "synced"]
}

# Group by activity and build cache sets (OPTIMIZATION)
anuladas_por_actividad = defaultdict(list)
for anulada in anuladas:
    if idActivitat := inscripcion_actividad.get(anulada):
        anuladas_por_actividad[idActivitat].append(anulada)

# Read each activity file once and build cache set (OPTIMIZATION)
cache_por_actividad = {}
for idActivitat in anuladas_por_actividad:
    inscritos = common.readjson(filename=f"{idActivitat}")
    cache_por_actividad[idActivitat] = {
        str(i["idInscripcio"])
        for i in inscritos
        if i.get("estat") in ["INSCRESTANU", "anulada"]
    }

# Process with O(1) lookups (OPTIMIZATION)
for anulada in anuladas:
    idActivitat = inscripcion_actividad.get(anulada)
    cancelled_cache = cache_por_actividad.get(idActivitat, set())

    # O(1) set lookups instead of O(n) any() searches
    if str(anulada) in cancelled_cache or str(anulada) in outbox_anuladas:
        print(f"Inscripción {anulada} ya procesada (skipping)")
        continue

    response = common.anula_inscripcio(
        token=token,
        inscripcion=anulada,
        idActivitat=idActivitat,
    )
    print(response)
