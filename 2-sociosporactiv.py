#!/usr/bin/env python


import common

token = common.gettoken()
print("Loading file from disk")


actividades = common.readjson(filename="actividades")


print("Procesando actividades...")


for actividad in actividades:
    myid = actividad["idActivitat"]
    nombre = actividad["nom"]
    if actividad["idNivell"] and actividad["idNivell"] != "null":
        horario = int(actividad["idNivell"])
    else:
        horario = 0

    if horario in [7, 8, 9, 10, 19, 20, 21, 22]:
        print(myid, nombre)
        common.updateactividad(token=token, idactividad=myid)
