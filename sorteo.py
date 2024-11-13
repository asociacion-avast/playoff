#!/usr/bin/env python
import os
import pprint
import random

import dateutil.parser

import common

# Initialize random seed with ONCE number
random.seed(32768)


def durstenfeld_shuffle(arr):
    # Loop from the end of the array to the start
    for i in range(len(arr) - 1, 0, -1):
        # Pick a random index from 0 to i
        j = random.randint(0, i)
        # Swap the elements at i and j
        arr[i], arr[j] = arr[j], arr[i]
    return arr


# Read the data from disk for socios and actividades (it's an array)
actividadesjson = common.readjson(filename="actividades")
sociosjson = common.readjson(filename="socios")

# Store the ID's and build the dictionary for the data we want from actividdes
idsactividad = []
actividades = {}
for actividad in actividadesjson:
    idactividad = int(actividad["idActivitat"])

    idsactividad.append(idactividad)

    try:
        edatMax = int(actividad["edatMax"])
    except Exception:
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
        "horario": int(actividad["idNivell"]),
    }

# Sort Actividades
idsactividad = sorted(set(idsactividad))
# pprint.pprint(actividades)


# Prefill socios con actividades y de alta
id_socios = []
mis_socios = {}

for socio in sociosjson:
    id_socio = int(socio["idColegiat"])

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
                    modalitat_nombre = modalitat["modalitat"]["nom"].lower()

                    if (
                        "socio principal".lower() in modalitat_nombre
                        or "deudor".lower() in modalitat_nombre
                        or "hermano de socio".lower() in modalitat_nombre
                    ):
                        id_socios.append(id_socio)
                        mis_socios[id_socio] = {}
                        fecha = dateutil.parser.parse(socio["persona"]["dataNaixement"])
                        mis_socios[id_socio]["nacim"] = fecha.year


# Store list of socios


id_socios = sorted(set(id_socios))
print("Total socios a asignar: ", len(id_socios))

socios = {}
for socio in id_socios:
    # Fill dictionary of interests for each socio

    filename = f"sorteo/{socio}.txt"

    # Validar que el socio ha expresado intereses
    if os.access(filename, os.R_OK):
        if socio not in socios:
            socios[socio] = []
        with open(filename) as f:
            lineas = f.readlines()
            for linea in lineas:
                interes = int(linea.strip())
                socios[socio].append(interes)


# Remove socios without interests defined
socios_a_borrar = []
for socio in socios:
    if socios[socio] == []:
        socios_a_borrar.append(socio)

for socio in socios_a_borrar:
    del socios[socio]

print("Socios e intereses")
pprint.pprint(socios)


# TODO Use sorting method for this iteration
sortedsocios = durstenfeld_shuffle(id_socios)

# Procesar inscripciones

inscripciones = {}
inscripciones_por_socio = {}
horarios_por_socio = {}

for ronda in [0, 1, 2, 3]:
    print("Ronda %s" % ronda)
    # Assign spots in activities to socios

    for socio in sortedsocios:
        # Validate that socio is in the shortlist of the ones who expressed
        if socio in socios:
            # print("Procesando socio: %s" % socio)
            # Socio ha expresado intereses
            keeprunning = True
            if socio not in inscripciones_por_socio:
                inscripciones_por_socio[socio] = []

            if socio not in horarios_por_socio:
                horarios_por_socio[socio] = []

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
                        anyo = mis_socios[socio]["nacim"]

                        if (
                            anyo >= actividades[interes]["edatMin"]
                            and anyo <= actividades[interes]["edatMax"]
                        ):
                            # Se puede inscribir (está en rango de edad y hay plazas)

                            if (
                                actividades[interes]["horario"]
                                not in horarios_por_socio[socio]
                            ):
                                actividades[interes]["inscritos"].append(socio)
                                inscripciones[interes].append(socio)

                                inscripciones_por_socio[socio].append(interes)
                                horarios_por_socio[socio].append(
                                    actividades[interes]["horario"]
                                )
                                keeprunning = False


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
pprint.pprint(inscripciones_por_socio)
