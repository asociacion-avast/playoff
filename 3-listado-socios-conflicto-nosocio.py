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
for socio in socios:
    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTALTA",
        agrupaciones=["PREINSCRIPCIÓN"],
        reverseagrupaciones=True,
    ):
        idcolegiat = socio["idColegiat"]
        idsocio = socio["numColegiat"].lower()
        idpasaporte = socio["persona"]["residencia"].lower()

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
                "Socio Pasaporte ID: %s duplicado: https://{common.endpoint}.playoffinformatica.com/FormAssociat.php?idColegiat=%s"
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
                f"nº Socio ID: {idsocio} duplicado: https://{common.endpoint}.playoffinformatica.com/FormAssociat.php?idColegiat={idcolegiat}"
            )
            print("Conflictos: %s" % sociosnosocio[idsocio])
