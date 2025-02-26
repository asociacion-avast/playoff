#!/usr/bin/env python


import configparser
import datetime
import os

import dateutil.parser

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


print("Loading file from disk")
socios = common.readjson(filename="socios")


# get today date


today = datetime.date.today()
recibocorrecto = common.calcular_proximo_recibo(
    f"{today.year}/{today.month}/{today.day}"
)


for socio in socios:
    id_socio = socio["idColegiat"]

    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTALTA",
        agrupaciones=["PREINSCRIPCIÓN"],
        reverseagrupaciones=True,
    ):
        if "colegiatHasModalitats" in socio:
            # Iterate over all categories for the user
            for modalitat in socio["colegiatHasModalitats"]:
                if int(modalitat["tipusPeriodicitat"]["idTipusPeriodicitat"]) == 5:
                    fecha = dateutil.parser.parse(modalitat["dataProperaGeneracio"])
                    # except:
                    #     fecha=False

                    fechaficha = f"{fecha.day:02d}/{fecha.month:02d}/{fecha.year}"
                    if fecha and fechaficha != recibocorrecto:
                        url = f"https://{common.endpoint}.playoffinformatica.com/FormAssociat.php?idColegiat={id_socio}#tab=ACTIVITATS"
                        print(fechaficha, recibocorrecto, "Usuario: %s" % url)
