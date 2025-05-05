#!/usr/bin/env python

import configparser
import os

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken()


print("Loading file from disk")
socios = common.readjson(filename="socios")
familias = common.readjson(filename="familias")

procesados = []

print("Procesando socios")
# Iteramos sobre miembros porque cap familia hace referencia a la cuenta bancaria


for familia in familias["miembros"]:
    parientes = familias["miembros"][familia]
    parientes.append(familia)
    if familia not in procesados:
        procesados.extend(iter(parientes))
        # Si el socio ya ha sido procesado, no lo procesamos de nuevo

        sociosactividad = []
        socioshermanos = []
        sociossinactiv = []

        for pariente in parientes:
            socio = common.get_colegiat_json(idColegiat=pariente)
            if "colegiatHasModalitats" in socio:
                # Iterate over all categories for the user
                for modalitat in socio["colegiatHasModalitats"]:
                    if "modalitat" in modalitat:
                        # Save name for comparing the ones we target
                        agrupacionom = modalitat["modalitat"]["agrupacio"][
                            "nom"
                        ].lower()
                        modalitatnom = modalitat["modalitat"]["nom"].lower()
                        idmodalitat = int(modalitat["modalitat"]["idModalitat"])

                        if idmodalitat == common.categorias["sociohermanoactividades"]:
                            socioshermanos.append(pariente)

                        if idmodalitat == common.categorias["socioactividades"]:
                            sociosactividad.append(pariente)

                        if idmodalitat == 1:
                            sociossinactiv.append(pariente)

        # Familia procesada
        if socioshermanos:
            if not sociosactividad:
                print(
                    f"ERROR: Familia {familia} tiene {len(parientes)} miembros, {len(sociosactividad)} actividad, {len(sociossinactiv)} sin actividad, {len(socioshermanos)} hermanos: {common.sociobase}{familia}#tab=CATEGORIES"
                )
