#!/usr/bin/env python


import common

print("Loading file from disk")
socios = common.readjson(filename="socios")


print("Procesando socios...")

# For each user check the custom fields that store the telegram ID for each tutor
for socio in socios:
    # try:
    #     fecha = dateutil.parser.parse(user["persona"]["dataNaixement"])
    # except Exception:
    #     fecha = False

    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTALTA",
        agrupaciones=["PREINSCRIPCIÓN"],
    ):
        socioid = int(socio["idColegiat"])
        print(
            f"{common.sociobase}{socioid}#tab=CATEGORIES",
        )
