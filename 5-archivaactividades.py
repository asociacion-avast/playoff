#!/usr/bin/env python

import configparser
import datetime
import os

import dateutil.parser

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


print("Loading file from disk")
actividades = common.readjson(filename="actividades")


print("Procesando actividades...")

today = datetime.datetime.now()
override = {
    "estat": "ACTIESTARXI",
}


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)


for actividad in actividades:
    if (
        "dataHoraFiActivitat" in actividad
        and actividad["dataHoraFiActivitat"] is not None
    ):
        myid = actividad["idActivitat"]
        nombre = actividad["nom"]

        fecha = dateutil.parser.parse(actividad["dataHoraFiActivitat"])
        if today > fecha:
            print(f"{myid},{nombre},{fecha}")
            common.editaactividad(token=token, idActivitat=myid, override=override)
