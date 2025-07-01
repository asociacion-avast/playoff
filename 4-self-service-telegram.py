#!/usr/bin/env python

import configparser
import datetime
import os

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)


print("Loading file from disk")
socios = common.readjson(filename="socios")
actividades = common.readjson(filename="actividades")


today = datetime.date.today()


print("Actualizando actividades ID TELEGRAM")
for actividadid in [815, 816]:
    common.updateactividad(token=token, idactividad=actividadid)


print("Procesando socios...")

# For each user check the custom fields that store the telegram ID for each tutor
for actividadid in [815, 816]:
    inscritos = common.readjson(filename=f"{actividadid}")
    inscripciones = []

    for socio in socios:
        if common.validasocio(
            socio,
            estado="COLESTVAL",
            estatcolegiat="ESTALTA",
            agrupaciones=["PREINSCRIPCIÓN"],
            reverseagrupaciones=True,
        ):
            socioid = int(socio["idColegiat"])

            for inscrito in inscritos:
                if int(inscrito["colegiat"]["idColegiat"]) == socioid:
                    inscripciones.append(inscrito["idInscripcio"])
                    if inscrito["estat"] == "INSCRESTNOVA":
                        print(f"{common.sociobase}{socioid}#tab=CATEGORIES")
                        print(
                            f"El socio {socioid} está inscrito en la actividad {common.traduce(actividadid)}"
                        )

                        data = []
                        if actividadid == 815:
                            data = common.getcomunicadotutor(socioid)
                        if actividadid == 816:
                            data = common.getcomunicadosocio(socioid)

                        if not data:
                            print("Error procesando inscripcion de socio: %s" % socioid)
                        else:
                            print("Enviando comunicado")
                            response = common.enviacomunicado(token=token, data=data)
                            print(response)
                            print(response.text)

                            # Borra inscripciones a las actividades
                            print("Borrando inscripciones a actividades ID Telegram")
                            for inscripcion in inscripciones:
                                response = common.anula_inscripcio(
                                    token=token, inscripcion=inscripcion, comunica=False
                                )
