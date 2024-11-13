#!/usr/bin/env python
import os
import pprint
import random

import dateutil.parser

import common

# Initialize random seed with ONCE number
random.seed(85535)


actividadesjson = common.readjson(filename="actividades")
sociosjson = common.readjson(filename="socios")

idsactividad = []
actividades = {}
for actividad in actividadesjson:
    idactividad = int(actividad["idActivitat"])

    idsactividad.append(idactividad)

    try:
        edatMax = int(actividad["edatMax"])
    except:
        edatMax = 9000

    try:
        edatMin = int(actividad["edatMin"])
    except:
        edatMin = 0000

    # Rellenar diccionario
    actividades[idactividad] = {
        "maxplazas": int(actividad["maxPlaces"]),
        "inscritos": [],
        "edatMax": edatMax,
        "edatMin": edatMin,
    }
idsactividad = sorted(set(idsactividad))
# pprint.pprint(actividades)


# Prefill socios con actividades y de alta
idsocios = []
mysocios = {}
for socio in sociosjson:
    idsocio = int(socio["idColegiat"])

    if (
        "estat" in socio
        and socio["estat"] == "COLESTVAL"
        and "estatColegiat" in socio
        and socio["estatColegiat"]["nom"] == "ESTALTA"
    ):
        if "colegiatHasModalitats" in socio:
            # Iterate over all categories for the socio
            for modalitat in socio["colegiatHasModalitats"]:
                if "modalitat" in modalitat:
                    # Save name for comparing the ones we target
                    modalitatnom = modalitat["modalitat"]["nom"].lower()

                    if (
                        "socio principal".lower() in modalitatnom
                        or "deudor".lower() in modalitatnom
                        or "hermano de socio".lower() in modalitatnom
                    ):
                        idsocios.append(idsocio)
                        mysocios[idsocio] = {}
                        fecha = dateutil.parser.parse(socio["persona"]["dataNaixement"])
                        mysocios[idsocio]["nacim"] = fecha.year


# Store list of socios


idsocios = sorted(set(idsocios))
print("Total socos a asignar: ", len(idsocios))

socios = {}
for socio in idsocios:
    idsocio = socio

    filename = f"sorteo/{idsocio}.txt"

    # Validar que el socio ha expresado intereses
    if os.access(filename, os.R_OK):
        if idsocio not in socios:
            socios[idsocio] = []
        with open(filename) as f:
            lineas = f.readlines()
            for linea in lineas:
                interes = int(linea.strip())
                socios[idsocio].append(interes)

sociosborrar = []
for socio in socios:
    if socios[socio] == []:
        sociosborrar.append(socio)

for socio in sociosborrar:
    del socios[socio]

print("Socios e intereses")
pprint.pprint(socios)


# TODO Use sorting method for this iteration
sortedsocios = list(reversed(sorted(set(idsocios))))


# TEST CODE TO REMOVE

actividades[588]["maxplazas"] = 2

# Procesar inscripciones

inscripciones = {}
socioinscripciones = {}

for ronda in [0, 1, 2, 3]:
    print("Ronda %s" % ronda)
    # Assign spots in activities to socios

    for socio in sortedsocios:
        if socio in socios:
            # print("Procesando socio: %s" % socio)
            # Socio ha expresado intereses
            keeprunning = True
            if socio not in socioinscripciones:
                socioinscripciones[socio] = []

            for interes in socios[socio]:
                if interes not in inscripciones:
                    inscripciones[interes] = []
                if (
                    keeprunning is True
                    and interes in actividades
                    and (
                        len(actividades[interes]["inscritos"])
                        < actividades[interes]["maxplazas"]
                    )
                ):
                    if socio not in actividades[interes]["inscritos"]:
                        anyo = mysocios[socio]["nacim"]

                        if (
                            anyo >= actividades[interes]["edatMin"]
                            and anyo <= actividades[interes]["edatMax"]
                        ):
                            # Se puede inscribir (está en rango de edad y hay plazas)
                            actividades[interes]["inscritos"].append(socio)
                            inscripciones[interes].append(socio)
                            # print(
                            #     "Plazas restantes: %s"
                            #     % (
                            #         actividades[interes]["maxplazas"]
                            #         - len(actividades[interes]["inscritos"])
                            #     )
                            # )
                            socioinscripciones[socio].append(interes)
                            keeprunning = False
    # var=input("Press enter to continue")


for actividad in actividades:
    if len(actividades[interes]["inscritos"]) < actividades[interes]["maxplazas"]:
        print(
            "Actividad %s tiene %s vacantes"
            % (
                actividad,
                actividades[interes]["maxplazas"]
                - len(actividades[interes]["inscritos"]),
            )
        )
    else:
        print(
            "Actividad %s está llena %s vacantes"
            % (
                actividad,
                actividades[interes]["maxplazas"]
                - len(actividades[interes]["inscritos"]),
            )
        )


pprint.pprint(inscripciones)
pprint.pprint(socioinscripciones)
