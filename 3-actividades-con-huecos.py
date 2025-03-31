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

horarios = {7: "11:30", 8: "09:00", 9: "10:00", 10: "12:30"}

print("NOMBRE,PLAZAS,USADAS,LIBRES,HORA,AÑO INICIO,AÑO FIN")
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
    except:
        anyoinicio = 0
        anyofin = 0

    if horario in {7, 8, 9, 10}:
        inscritos = common.readjson(filename=f"{myid}")
        usadas = 0
        for inscrito in inscritos:
            if inscrito["estat"] == "INSCRESTNOVA":
                usadas = usadas + 1
        libres = int(actividad["maxPlaces"]) - usadas
        if libres > 0:
            if anyo and anyoinicio <= anyo <= anyofin:
                print(
                    f'{myid},{nombre},{int(actividad["maxPlaces"])},{usadas},{libres},{horarios[horario]},{anyoinicio},{anyofin}'
                )
            elif not anyo:
                print(
                    f'{myid},{nombre},{int(actividad["maxPlaces"])},{usadas},{libres},{horarios[horario]},{anyoinicio},{anyofin}'
                )
