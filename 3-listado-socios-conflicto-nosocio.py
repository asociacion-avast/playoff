#!/usr/bin/env python


import common

print("Loading file from disk")
socios = common.readjson(filename="socios")


print("Procesando socios...")

idsociosconocidos = []


# For each user check the custom fields that store the telegram ID for each tutor
for user in socios:
    if (
        "estat" in user
        and user["estat"] == "COLESTVAL"
        and "estatColegiat" in user
        and user["estatColegiat"]["nom"] == "ESTALTA"
    ):
        idsocio = user["persona"]["residencia"]
        idcolegiat = user["idColegiat"]

        if idsocio == "":
            idsocio = False

        if idsocio and idsocio not in idsociosconocidos and idsocio != "":
            idsociosconocidos.append(idsocio)
        elif idsocio and idsocio != "-":
            print(
                "Socio ID: %s duplicado: https://asociacionavast.playoffinformatica.com/FormAssociat.php?idColegiat=%s"
                % (idsocio, idcolegiat)
            )
