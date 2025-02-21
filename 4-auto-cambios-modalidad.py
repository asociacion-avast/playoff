#!/usr/bin/env python


import configparser
import datetime
import os

import dateutil.parser

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)

headers = {"Authorization": f"Bearer {token}"}

# Campo con la fecha de cambio

# Definiciones
# 78: Cambio a Adulto sin actividades
# 79: Cambio a Adulto con actividades
# 80: Cambio a Niño sin actividades
# 81: Cambio a Niño con actividades

# 53: Adulto sin actividades
# 60: Adulto con actividades
# 12: Socio principal con actividades
# 1: Socio principal sin actividades

cambios = {78: 53, 79: 60, 80: 1, 81: 12}

# Periodicidad (bimensual: 5)
extras = {53: False, 60: 5, 12: 5, 1: False}


# Leer datos
socios = common.readjson("socios")
# Convert today to datetime.date
today = datetime.date.today()
today = datetime.date(today.year, today.month, today.day)


# Locate our member in the list of members
for socio in socios:
    # ID Socio
    socioid = socio["idColegiat"]

    if (
        "estat" in socio
        and socio["estat"] == "COLESTVAL"
        and "estatColegiat" in socio
        and socio["estatColegiat"]["nom"] == "ESTALTA"
    ):
        if isinstance(socio["campsDinamics"], dict):
            for field in [common.fechacambio]:
                if field in socio["campsDinamics"]:
                    fechacambiosocio = f'{socio["campsDinamics"][field]}'
                    # Fecha cambio
                    try:
                        fecha = dateutil.parser.parse(fechacambiosocio)
                        # convert fecha to datetime.date
                        fecha = datetime.date(fecha.year, fecha.month, fecha.day)
                    except Exception:
                        fecha = False
                        print(f"ERROR: Procesando fecha para socio ID: {socioid}")

                    if fecha and fecha <= today:
                        print(f"Fecha alcanzada: {socioid}")

                        categoriassocio = []
                        modalitatsocio = []
                        for categoria in socio["colegiatHasModalitats"]:
                            idcategoria = int(categoria["idModalitat"])
                            categoriassocio.append(idcategoria)

                            if "modalitat" in categoria:
                                # Save name for comparing the ones we target
                                agrupacionom = categoria["modalitat"]["agrupacio"][
                                    "nom"
                                ].lower()
                                modalitatnom = categoria["modalitat"]["nom"].lower()
                                modalitatid = int(categoria["modalitat"]["idModalitat"])
                                modalitatsocio.append(modalitatid)

                        print(f"Socio en categorias: {modalitatsocio}")
                        targetadd = []
                        targetremove = []
                        for categoria in modalitatsocio:
                            if categoria in cambios:
                                print(
                                    f"Categoria : {categoria} cambia a {cambios[categoria]}"
                                )
                                targetadd.append(cambios[categoria])
                                targetremove.append(categoria)

                        # Eliminar categorias en conflicto
                        targetremove.extend(
                            categoria
                            for categoria in [1, 12, 53, 60]
                            if categoria not in targetadd
                        )
                        for categoria in targetremove:
                            if categoria in modalitatsocio:
                                print(
                                    f"INFO: Borrando categoria {categoria} del socio {socioid}"
                                )
                                response = common.delcategoria(
                                    token, socioid, categoria
                                )
                                print(response)

                        for categoria in targetadd:
                            print(
                                f"INFO: Añadiendo categoria {categoria} del socio {socioid}"
                            )
                            if categoria in extras and extras[categoria]:
                                response = common.addcategoria(
                                    token,
                                    socioid,
                                    categoria,
                                    extra={
                                        "tipusperiodicitat": extras[categoria],
                                        "dataProperaGeneracio": fechacambiosocio,
                                    },
                                )
                            else:
                                response = common.addcategoria(
                                    token, socioid, categoria
                                )
                            print(response.text)

                            print("Vaciando fecha cambio")
                            print(
                                common.escribecampo(
                                    token, socioid, common.fechacambio, valor=""
                                )
                            )
                            print(response)
