#!/usr/bin/env python


import configparser
import os

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
    ) or common.validasocio(
        socio,
        estado="COLESTPRE",
        estatcolegiat="ESTALTA",
    ):
        procesa = False
        recuerda = False
        if "colegiatHasModalitats" in socio:
            # Iterate over all categories for the user
            for modalitat in socio["colegiatHasModalitats"]:
                if "modalitat" in modalitat:
                    # Save name for comparing the ones we target
                    agrupacionom = modalitat["modalitat"]["agrupacio"]["nom"].lower()
                    modalitatnom = modalitat["modalitat"]["nom"].lower()

                    if "Socio Adulto Actividades".lower() in agrupacionom:
                        resultids["adult"].append(id_socio)
                        procesa = True

                    if "Socio Adulto SIN Actividades".lower() in agrupacionom:
                        resultids["adult"].append(id_socio)
                        procesa = True

        if procesa and isinstance(socio["campsDinamics"], dict):
            alguno = False
            for field in common.telegramfields:
                if field in socio["campsDinamics"]:
                    idtelegramencampo = f"{socio['campsDinamics'][field]}"

                    if idtelegramencampo is not None or idtelegramencampo != "":
                        alguno = True
            if not alguno:
                print(f"{common.sociobase}{id_socio}")


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)
