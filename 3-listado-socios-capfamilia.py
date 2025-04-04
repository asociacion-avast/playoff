#!/usr/bin/env python


import common

print("Loading file from disk")
socios = common.readjson(filename="socios")


print("Procesando socios...")


# For each user check the custom fields that store the telegram ID for each tutor
for socio in socios:
    if int(socio["isBancCapFamilia"]) != 0:
        if common.validasocio(
            socio,
            estado="COLESTVAL",
            estatcolegiat="ESTALTA",
            agrupaciones=["PREINSCRIPCIÓN"],
            reverseagrupaciones=True,
        ):
            socioid = socio["idColegiat"]
            url = f"{common.sociobase}{socioid}#tab=ACTIVITATS"
            print(url)
