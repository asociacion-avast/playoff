#!/usr/bin/env python


import common

print("Loading file from disk")

actividades = common.readjson(filename="actividades")


print("Procesando actividades...")

usuariosyactividad = {}
actividadyusuarios = {}
usuariosyhorarios = {}

horarios = {}
horarios[7] = "11:30"
horarios[8] = "09:00"
horarios[9] = "10:00"
horarios[10] = "12:30"


print("NOMBRE,PLAZAS,USADAS,LIBRES,HORA,AÑO INICIO,AÑO FIN")
for actividad in actividades:
    myid = actividad["idActivitat"]
    nombre = actividad["nom"]
    horario = int(actividad["idNivell"])
    anyoinicio = actividad["edatMin"]
    anyofin = actividad["edatMax"]

    if horario in {7, 8, 9, 10}:
        inscritos = common.readjson(filename=f"{myid}")
        usadas = 0
        for inscrito in inscritos:
            if inscrito["estat"] == "INSCRESTNOVA":
                usadas = usadas + 1
        libres = int(actividad["maxPlaces"]) - usadas
        if libres > 0:
            print(
                f'{nombre},{int(actividad["maxPlaces"])},{usadas},{libres},{horarios[horario]},{anyoinicio},{anyofin}'
            )
