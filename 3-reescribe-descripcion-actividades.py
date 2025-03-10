#!/usr/bin/env python
import configparser
import os
import sys

import requests

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


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

token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)


data = {"descripcio": ""}

for actividad in actividades:
    myid = actividad["idActivitat"]
    nombre = actividad["nom"]

    if actividad["idNivell"] and actividad["idNivell"] != "null":
        horario = int(actividad["idNivell"])
    else:
        horario = 0

    if horario in {7, 8, 9, 10}:
        if int(myid) == 714:
            url = f"{common.apiurl}/activitats/{myid}/descripcio"
            response = requests.patch(
                url, headers=common.headers, auth=common.BearerAuth(token), data=data
            )
            print(response)
