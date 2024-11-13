#!/usr/bin/env python
# Fills random activities for each member to have a set of test data


import random

import common

# Initialize random seed with ONCE number
random.seed(85535)


actividadesjson = common.readjson(filename="actividades")
sociosjson = common.readjson(filename="socios")

ids_actividad = []
for actividad in actividadesjson:
    idactividad = int(actividad["idActivitat"])
    ids_actividad.append(idactividad)

id_socios = []
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
                    modalitatnom = modalitat["modalitat"]["nom"].lower()

                    if (
                        "socio principal".lower() in modalitatnom
                        or "deudor".lower() in modalitatnom
                        or "hermano de socio".lower() in modalitatnom
                    ):
                        id_socios.append(id_socio)

for id_socio in id_socios:
    filename = f"sorteo/{id_socio}.txt"
    with open(filename, "w") as f:
        for _ in range(0, 1000):
            inscripcion = random.choice(ids_actividad)
            f.write("%s\n" % inscripcion)
