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


def calcular_proximo_recibo(fecha):
    """_summary_

    Args:
        fecha (datetime): Fecha for today

    Returns:
        str: fecha
    """
    meses_cobro = sorted(
        set([9, 11, 1, 3, 5])
    )  # Meses de cobro (septiembre, noviembre, enero, marzo, mayo)

    fecha = dateutil.parser.parse(fecha)
    dia = fecha.day
    mes = fecha.month
    año = fecha.year

    if dia < 5:
        dia_cobro = "5"
        if mes in meses_cobro:
            return f"{dia_cobro}/{mes}/{año}"
        else:
            mes_cobro = next((m for m in meses_cobro if m > mes), None)
            if mes_cobro is None:
                mes_cobro = meses_cobro[0]
                año += 1
            return f"{dia_cobro}/{mes_cobro}/{año}"
    else:
        mes_cobro = next((m for m in meses_cobro if m > mes), None)
        if mes_cobro is None:
            mes_cobro = meses_cobro[0]
            año += 1
        return f"5/{mes_cobro}/{año}"


# get today date


today = datetime.date.today()
recibocorrecto = calcular_proximo_recibo(f"{today.year}/{today.month}/{today.day}")


for socio in socios:
    id_socio = socio["idColegiat"]

    if (
        "estat" in socio
        and "estatColegiat" in socio
        and socio["estatColegiat"]["nom"] == "ESTALTA"
        and (socio["estat"] == "COLESTVAL")
    ):
        if "colegiatHasModalitats" in socio:
            # Iterate over all categories for the user
            for modalitat in socio["colegiatHasModalitats"]:
                if int(modalitat["tipusPeriodicitat"]["idTipusPeriodicitat"]) == 5:
                    fecha = dateutil.parser.parse(modalitat["dataProperaGeneracio"])
                    # except:
                    #     fecha=False

                    fechaficha = f"{fecha.day}/{fecha.month}/{fecha.year}"
                    if fecha and fechaficha != recibocorrecto:
                        url = f"https://{common.endpoint}.playoffinformatica.com/FormAssociat.php?idColegiat={id_socio}#tab=ACTIVITATS"
                        print(fechaficha, recibocorrecto, "Usuario: %s" % url)
