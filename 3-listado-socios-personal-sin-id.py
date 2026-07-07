#!/usr/bin/env python


import configparser
import os
from datetime import date

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


print("Loading file from disk")

socios = common.readjson(filename="socios")


print("Procesando actividades...")

usuariosyactividad = {}
actividadyusuarios = {}
usuariosyhorarios = {}
usuarioseinscripciones = {}
usuariosyhorariosinscripciones = {}

sociosbaja = []


resultids = {
    "adult": [],  # Adultos
}


for socio in socios:
    id_socio = socio["idColegiat"]

    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTALTA",
        agrupaciones=["PREINSCRIPCIÓN"],
        reverseagrupaciones=True,
    ):
        fecha_nacimiento = common.parse_date(
            socio.get("persona", {}).get("dataNaixement")
        )
        edad = None
        if fecha_nacimiento:
            today = date.today()
            edad = (
                today.year
                - fecha_nacimiento.year
                - (
                    (today.month, today.day)
                    < (fecha_nacimiento.month, fecha_nacimiento.day)
                )
            )

        if edad is not None and edad >= 13:
            if isinstance(socio.get("campsDinamics"), dict):
                socioid_val = socio["campsDinamics"].get(common.socioid)
                if not socioid_val:
                    print(f"{common.sociobase}{id_socio}")
            else:
                print(f"Problema: {common.sociobase}{id_socio}")


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)
