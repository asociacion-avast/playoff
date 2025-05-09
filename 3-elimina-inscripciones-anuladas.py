#!/usr/bin/env python


import configparser
import os

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


print("Loading file from disk")

actividades = common.readjson(filename="actividades")


print("Procesando actividades...")

usuariosyactividad = {}
actividadyusuarios = {}


anuladas = []

print("Procesando inscripciones")
for actividad in actividades:
    myid = actividad["idActivitat"]
    nombre = actividad["nom"]

    if actividad["idNivell"] and actividad["idNivell"] != "null":
        horario = int(actividad["idNivell"])
    else:
        horario = 0

    if horario in [7, 8, 9, 10]:
        inscritos = common.readjson(filename=f"{myid}")

        actividadyusuarios[myid] = []

        for inscrito in inscritos:
            colegiat = inscrito["colegiat"]["idColegiat"]
            actividadyusuarios[myid].append(colegiat)

            if inscrito["estat"] == "INSCRESTANULADA":
                ID = inscrito["idInscripcio"]
                anuladas.append(ID)


anuladas = sorted(set(anuladas))
print(anuladas)
print(len(anuladas))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)

for anulada in anuladas:
    response = common.anula_inscripcio(token=token, inscripcion=anulada)
    print(response)
