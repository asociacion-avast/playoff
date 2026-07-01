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
    horario = common.actividad_horario(actividad)

    max_places = common.safe_int(actividad.get("maxPlaces"), 0)
    inscritos = max_places - common.safe_int(actividad.get("placesLliures"), 0)
    porcentaje = inscritos / common.safe_int(actividad.get("maxPlaces"), 1)

    if porcentaje <= valido and horario in {7, 8, 9, 10, 19, 20, 21, 22}:
        print(
            myid,
            nombre,
            f"{porcentaje * 100:.2f}%",
            actividad["maxPlaces"],
            inscritos,
            actividad["placesLliures"],
        )

        print("Haciendo llamada API")

        override = {
            "dataLimit": "2026-03-02 00:00",
        }

        pprint.pprint(common.editaactividad(token, myid, override))
