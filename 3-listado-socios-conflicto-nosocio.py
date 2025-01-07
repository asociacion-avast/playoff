#!/usr/bin/env python

import common

print("Loading file from disk")
socios = common.readjson(filename="socios")


print("Procesando socios...")

idpasaportesociosconocidos = []
idsocioconocidos = []

sociospasaportes = {}
sociosnosocio = {}


# For each user check the custom fields that store the telegram ID for each tutor
for user in socios:
    if (
        "estat" in user
        and user["estat"] == "COLESTVAL"
        and "estatColegiat" in user
        and user["estatColegiat"]["nom"] == "ESTALTA"
    ):
        idcolegiat = user["idColegiat"]
        idsocio = user["numColegiat"].lower()
        idpasaporte = user["persona"]["residencia"].lower()

        if idpasaporte == "":
            idpasaporte = False

        if idsocio == "":
            idsocio = False

        # Fill dictionary of card support media
        if idpasaporte not in sociospasaportes:
            sociospasaportes[idpasaporte] = []

        if idpasaporte and idpasaporte != "":
            sociospasaportes[idpasaporte].append(idcolegiat)

        # Fill dictionary of associate number
        if (
            idpasaporte
            and idpasaporte not in idpasaportesociosconocidos
            and idpasaporte != ""
        ):
            idpasaportesociosconocidos.append(idpasaporte)
        elif idpasaporte and idpasaporte != "-":
            print(
                "Socio Pasaporte ID: %s duplicado: https://asociacionavast.playoffinformatica.com/FormAssociat.php?idColegiat=%s"
                % (idpasaporte, idcolegiat)
            )
            print("Conflictos: %s" % sociospasaportes[idpasaporte])

        if idsocio not in sociosnosocio:
            sociosnosocio[idsocio] = []
        if idsocio and idsocio != "":
            sociosnosocio[idsocio].append(idcolegiat)
        if idsocio and idsocio not in idsocioconocidos and idsocio != "":
            idsocioconocidos.append(idsocio)
        elif idsocio and idsocio != "-":
            print(
                "nº Socio ID: %s duplicado: https://asociacionavast.playoffinformatica.com/FormAssociat.php?idColegiat=%s"
                % (idsocio, idcolegiat)
            )
            print("Conflictos: %s" % sociosnosocio[idsocio])
