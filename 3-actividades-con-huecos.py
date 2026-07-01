#!/usr/bin/env python


import sys

import common

anyo = False
if len(sys.argv) > 1:
    try:
        anyo = int(sys.argv[1])
    except Exception:
        anyo = False

print("Loading file from disk")
actividades = common.readjson(filename="actividades")


print("Procesando actividades...")

usuariosyactividad = {}
actividadyusuarios = {}
usuariosyhorarios = {}

horarios = {
    7: "11:30",
    8: "09:00",
    9: "10:00",
    10: "12:30",
    19: "",
    20: "",
    21: "",
    22: "",
}

print("ID,NOMBRE,PLAZAS,USADAS,LIBRES,HORA,AÑO INICIO,AÑO FIN")
for actividad in actividades:
    myid = actividad["idActivitat"]
    nombre = actividad["nom"]
    horario = common.actividad_horario(actividad)

    anyoinicio = common.safe_int(actividad.get("edatMin"), 0)
    anyofin = common.safe_int(actividad.get("edatMax"), 0)

    if horario in {7, 8, 9, 10, 19, 20, 21, 22}:
        usadas = common.safe_int(actividad.get("numInscripcions"), 0)
        max_places = common.safe_int(actividad.get("maxPlaces"), 0)
        libres = max_places - usadas
        if (anyo and anyoinicio <= anyo <= anyofin or not anyo) and libres > 0:
            print(
                f"{myid},{nombre},{max_places},{usadas},{libres},{horarios[horario]},{anyoinicio},{anyofin}"
            )
