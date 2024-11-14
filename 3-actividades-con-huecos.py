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
        users = common.readjson(filename=f"{myid}")
        inscritos = common.readjson(filename=f"{myid}")
        libres = int(actividad["maxPlaces"]) - len(inscritos)
        if libres > 0:
            print(f'{nombre},{int(actividad["maxPlaces"])},{len(inscritos)},{libres}')
