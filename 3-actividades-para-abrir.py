#!/usr/bin/env python

import configparser
import os
import pprint

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)

data = {"Authorization": f"Bearer {token}"}


print("Loading file from disk")


actividades = common.readjson(filename="actividades")
print("Procesando actividades...")


valido = 0.6

for actividad in actividades:
    myid = actividad["idActivitat"]
    nombre = actividad["nom"]
    if actividad["idNivell"] and actividad["idNivell"] != "null":
        horario = int(actividad["idNivell"])
    else:
        horario = 0

    inscritos = int(actividad["maxPlaces"]) - int(actividad["placesLliures"])
    porcentaje = (inscritos) / int(actividad["maxPlaces"])

    if porcentaje <= valido:
        if horario in [7, 8, 9, 10, 19, 20, 21, 22]:
            print(
                myid,
                nombre,
                "{:.2f}%".format(porcentaje * 100),
                actividad["maxPlaces"],
                inscritos,
                actividad["placesLliures"],
            )

            print("Haciendo llamada API")

            override = {
                "dataLimit": "2026-03-02 00:00",
            }

            pprint.pprint(common.editaactividad(token, myid, override))
