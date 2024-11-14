#!/usr/bin/env python


import common

print("Loading file from disk")

actividades = common.readjson(filename="actividades")


print("Procesando actividades...")

usuariosyactividad = {}
actividadyusuarios = {}
usuariosyhorarios = {}

for actividad in actividades:
    myid = actividad["idActivitat"]
    nombre = actividad["nom"]
    horario = int(actividad["idNivell"])

    if horario in {7, 8, 9, 10}:
        inscritos = common.readjson(filename=f"{myid}")
        usadas = 0
        for inscrito in inscritos:
            if inscrito["estat"] == "INSCRESTNOVA":
                usadas = usadas + 1
        libres = int(actividad["maxPlaces"]) - usadas
        if libres > 0:
            print(f'{nombre},{int(actividad["maxPlaces"])},{usadas},{libres}')
