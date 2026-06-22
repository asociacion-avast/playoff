#!/usr/bin/env python


import configparser
import os

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


print("Loading file from disk")

socios = common.readjson(filename="socios")


print("Procesando adultos sin ID...")

# OPTIMIZATION Item 7: Cache category constants locally for loop performance
cat_adulto_actividades = "Socio Adulto Actividades".lower()
cat_adulto_sin_actividades = "Socio Adulto SIN Actividades".lower()


# OPTIMIZATION Item 6: Accumulate results in one pass (generator-ready)
def process_socios_sin_id():
    for socio in socios:
        id_socio = socio["idColegiat"]

        # OPTIMIZATION Item 3: Use pre-computed validation
        if not (
            socio.get("_valid_alta", False) or socio.get("_valid_preinscripcion", False)
        ):
            continue

        procesa = False
        # Check modalitats for adult categories
        if "colegiatHasModalitats" in socio:
            for modalitat in socio["colegiatHasModalitats"]:
                if "modalitat" in modalitat:
                    m_data = modalitat["modalitat"]
                    # OPTIMIZATION Item 4: Use pre-normalized names
                    agrupacionom = (
                        m_data.get("agrupacio", {}).get("_nom_lower")
                        or m_data.get("agrupacio", {}).get("nom", "").lower()
                    )

                    if (
                        cat_adulto_actividades in agrupacionom
                        or cat_adulto_sin_actividades in agrupacionom
                    ):
                        procesa = True
                        break

        if procesa:
            # OPTIMIZATION Item 2: Use cached dynamic fields
            cached_campos = socio.get("_cached_campos", {})
            has_telegram_id = any(
                cached_campos.get(field) for field in common.telegramfields
            )

            if not has_telegram_id:
                yield id_socio


# Print results from generator (OPTIMIZATION Item 6)
for socio_id in process_socios_sin_id():
    print(f"{common.sociobase}{socio_id}")


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)
