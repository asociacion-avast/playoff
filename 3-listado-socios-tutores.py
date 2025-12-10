#!/usr/bin/env python

import common

print("Loading file from disk")
socios = common.readjson(filename="socios")

print("Procesando socios...")

resultids = {
    "activ": [],  # Con actividades
    "adult": [],  # Adultos
    "adultactiv": [],  # Adultos con actividades
    "adultsinactiv": [],  # Adultos sin actividades
    "invalid": [],  # Socios sin ALTA activa
    "kids-and-parents": [],  # Niños y tutores
    "kids": [],  # Niños (CON y SIN)
    "kidsactiv-and-parents": [],  # Niños CON Actividades y tutores
    "kidsactiv": [],  # Niños CON Actividades
    "kidsinactiv-and-parents": [],  # Niños SIN Actividades y tutores
    "kidsinactiv": [],  # Niños SIN actividades
    "preinscripcion": [],  # Socios preinscritos
    "profesores": [],  # Profesores
    "sociohermano": [],  # Socios hermanos (con actividades)
    "teen13-and-parents": [],  # Niños y tutores [13-15)
    "teen13": [],  # Niños [13-15)
    "teen15-and-parents": [],  # Niños y tutores [15-24]
    "teen15": [],  # Niños [15-24]
    "teen18-and-parents": [],  # Niños y tutores [18-29]
    "teen18": [],  # Niños [18-29]
    "tutor": [],  # Tutores
    "valid": [],  # Cualquiera con relación avast
}

# For each user check the custom fields that store the telegram ID for each tutor
for socio in socios:
    carnetssocio = []
    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTALTA",
    ):
        userid = socio["idColegiat"]
        if "colegiatHasModalitats" in socio:
            # Iterate over all categories for the user
            for modalitat in socio["colegiatHasModalitats"]:
                if "modalitat" in modalitat:
                    # Save name for comparing the ones we target
                    agrupacionom = modalitat["modalitat"]["agrupacio"]["nom"].lower()
                    modalitatnom = modalitat["modalitat"]["nom"].lower()
                    idmodalitat = int(modalitat["modalitat"]["idModalitat"])

                    if "Socio Adulto Actividades".lower() in agrupacionom:
                        resultids["activ"].append(userid)

                    if "Socio Actividades".lower() in agrupacionom:
                        resultids["activ"].append(userid)

        if userid in resultids["activ"]:
            for field in ["tutor1", "tutor2"]:
                if field in socio:
                    if socio[field]:
                        if "residencia" in socio[field]:
                            carnetssocio.append(socio[field]["residencia"])
        if carnetssocio != []:
            print(
                socio["idColegiat"],
                ",",
                socio["numColegiat"],
                socio["persona"]["nom"],
                socio["persona"]["cognoms"],
                ",",
                socio["persona"]["residencia"],
                ",",
                carnetssocio,
            )
