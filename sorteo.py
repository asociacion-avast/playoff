#!/usr/bin/env python
import os
import pprint
import random

import dateutil.parser

import common

# Initialize random seed with ONCE number
random.seed(12768)


def durstenfeld_shuffle(arr):
    # Loop from the end of the array to the start
    for i in range(len(arr) - 1, 0, -1):
        # Pick a random index from 0 to i
        j = random.randint(0, i)
        # Swap the elements at i and j
        arr[i], arr[j] = arr[j], arr[i]
    return arr


# Build array of actividades either from previous run or from original list
try:
    actividades = common.readjson(filename="sorteo-actividades")
except:
    actividadesjson = common.readjson(filename="actividades")

    actividades = {}
    for actividad in actividadesjson:
        idactividad = "%s" % int(actividad["idActivitat"])
        horario = int(actividad["idNivell"])

        if horario in {7, 8, 9, 10}:
            try:
                edatMax = int(actividad["edatMax"])
            except Exception:
                edatMax = 9000

            try:
                edatMin = int(actividad["edatMin"])
            except Exception:
                edatMin = 0000

            # Rellenar diccionario
            actividades[idactividad] = {
                "maxplazas": int(actividad["maxPlaces"]),
                "inscritos": [],
                "edatMax": edatMax,
                "edatMin": edatMin,
                "horario": horario,
            }

# Store the ID's and build the dictionary for the data we want from actividades
idsactividad = []

# Prefll in case it's empty
for actividad in actividades:
    idsactividad.append(actividad)

# Sort Actividades
idsactividad = sorted(set(idsactividad))


# Read the data from disk for socios
sociosjson = common.readjson(filename="socios")


# Prefill socios con actividades y de alta
id_socios = []
mis_socios = {}

for socio in sociosjson:
    id_socio = "%s" % int(socio["idColegiat"])

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


id_socios = sorted(set(id_socios))
print("Total socios a asignar: ", len(id_socios))

socios = {}
for socio in mis_socios:
    # Fill dictionary of interests for each socio

    filename = f"sorteo/{socio}.txt"

    # Validar que el socio ha expresado intereses
    if os.access(filename, os.R_OK):
        if socio not in socios:
            socios[socio] = []
        with open(filename) as f:
            lineas = f.readlines()
            for linea in lineas:
                interes = "%s" % int(linea.strip())
                socios[socio].append(interes)


# Remove socios without interests defined
socios_a_borrar = []
for socio in socios:
    if socios[socio] == []:
        socios_a_borrar.append(socio)

for socio in socios_a_borrar:
    del socios[socio]

# Use sorting method for this iteration
sortedsocios = durstenfeld_shuffle(id_socios)

# Procesar inscripciones

# Leer inscripciones desde disco
try:
    inscripciones_por_actividad = common.readjson(
        filename="sorteo-inscripciones_por_actividad"
    )
except:
    print("Fallo leyendo inscripciones por actividad")
    inscripciones_por_actividad = {}

try:
    inscripciones_por_socio = common.readjson(filename="sorteo-inscripciones_por_socio")

except:
    print("Fallo leyendo inscripciones por socio")
    inscripciones_por_socio = {}

try:
    horarios_por_socio = common.readjson(filename="sorteo-horarios_por_socio")
except:
    print("Fallo leyendo horarios por socio")
    horarios_por_socio = {}


# Assign spots in activities to socios

for socio in sortedsocios:
    # Validate that socio is in the shortlist of the ones who expressed
    if socio in socios:
        # print("Procesando socio: %s" % socio)
        # Socio ha expresado intereses
        keep_running = True
        if socio not in inscripciones_por_socio:
            inscripciones_por_socio[socio] = []

        if socio not in horarios_por_socio:
            horarios_por_socio[socio] = []

        for interes in socios[socio]:
            if interes not in inscripciones_por_actividad:
                inscripciones_por_actividad[interes] = []
            if (
                keep_running
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
                            inscripciones_por_actividad[interes].append(socio)

                            inscripciones_por_socio[socio].append(interes)
                            horarios_por_socio[socio].append(
                                actividades[interes]["horario"]
                            )
                            keep_running = False


# Salvar datos
common.writejson(
    filename="sorteo-inscripciones_por_actividad", data=inscripciones_por_actividad
)
common.writejson(
    filename="sorteo-inscripciones_por_socio", data=inscripciones_por_socio
)
common.writejson(filename="sorteo-horarios_por_socio", data=horarios_por_socio)
common.writejson(filename="sorteo-actividades", data=actividades)


# Resultados de inscripciones por actividad e inscripcones por socio
print("Inscripciones por actividad")
pprint.pprint(inscripciones_por_actividad)
print("Inscripciones por socio")
pprint.pprint(inscripciones_por_socio)


for interes in actividades:
    if len(actividades[interes]["inscritos"]) < actividades[interes]["maxplazas"]:
        print(
            "Quedan %s plazas en la actividad %s con horario %s"
            % (
                actividades[interes]["maxplazas"]
                - len(actividades[interes]["inscritos"]),
                interes,
                actividades[interes]["horario"],
            )
        )
