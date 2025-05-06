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
    if actividad["idNivell"] and actividad["idNivell"] != "null":
        horario = int(actividad["idNivell"])
    else:
        horario = 0

    try:
        anyoinicio = int(actividad["edatMin"])
        anyofin = int(actividad["edatMax"])
    except Exception:
        anyoinicio = 0
        anyofin = 0

    if horario in {7, 8, 9, 10, 19, 20, 21, 22}:
        usadas = 0
        usadas = int(actividad["numInscripcions"])
        libres = int(actividad["maxPlaces"]) - usadas
        if libres > 0:
            if anyo and anyoinicio <= anyo <= anyofin:
                print(
                    f"{myid},{nombre},{int(actividad['maxPlaces'])},{usadas},{libres},{horarios[horario]},{anyoinicio},{anyofin}"
                )
            elif not anyo:
                print(
                    f"{myid},{nombre},{int(actividad['maxPlaces'])},{usadas},{libres},{horarios[horario]},{anyoinicio},{anyofin}"
                )
