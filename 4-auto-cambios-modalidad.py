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
# 87: Cambio a Socio Hermano con Actividades

# 53: Adulto sin actividades
# 60: Adulto con actividades
# 12: Socio principal con actividades
# 1: Socio principal sin actividades
# 13: Socio hermano con actividades

cambios = {78: 53, 79: 60, 80: 1, 81: 12, 87: 13}

# Periodicidad (bimensual: 5)
extras = {53: False, 60: 5, 12: 5, 1: False, 13: 5}


# Leer datos
socios = common.readjson("socios")
# Convert today to datetime.date
today = datetime.date.today()
today = datetime.date(today.year, today.month, today.day)


# Locate our member in the list of members
for socio in socios:
    # ID Socio
    socioid = socio["idColegiat"]

    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTALTA",
        agrupaciones=["PREINSCRIPCIÓN"],
        reverseagrupaciones=True,
    ):
        if isinstance(socio["campsDinamics"], dict):
            for field in [common.fechacambio]:
                if field in socio["campsDinamics"]:
                    fechacambiosocio = f"{socio['campsDinamics'][field]}"
                    # Fecha cambio
                    try:
                        fecha = dateutil.parser.parse(fechacambiosocio)
                        # convert fecha to datetime.date
                        fecha = datetime.date(fecha.year, fecha.month, fecha.day)
                    except Exception:
                        fecha = False
                        print(f"ERROR: Procesando fecha para socio ID: {socioid}")

                    if not (fecha and fecha <= today):
                        print(
                            f"Fecha no alcanzada {fecha}: {common.sociobase}{socioid}"
                        )
                    else:
                        print(f"Fecha alcanzada {fecha}: {common.sociobase}{socioid}")

                        categoriassocio = common.getcategoriassocio(socio)

                        print(f"Socio en categorias: {categoriassocio}")
                        targetadd = []
                        targetremove = []

                        haycambio = False
                        for categoria in categoriassocio:
                            if categoria in cambios:
                                haycambio = True
                                print(
                                    f"Categoria : {categoria} cambia a {cambios[categoria]}"
                                )
                                targetadd.append(cambios[categoria])
                                targetremove.append(categoria)

                        if not haycambio:
                            print(
                                f"INFO: No hay cambios para el socio {socioid} ({common.sociobase}{socioid}). Borrando fecha cambio."
                            )
                            print(
                                common.escribecampo(
                                    token, socioid, common.fechacambio, valor=""
                                )
                            )
                        else:
                            # Eliminar categorias en conflicto
                            targetremove.extend(
                                categoria
                                for categoria in [1, 12, 53, 60, 13]
                                if categoria not in targetadd
                            )
                            for categoria in targetremove:
                                if categoria in categoriassocio:
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
                                    # La cuota de actividades es el dia 5 del bimestre
                                    # septiembre, noviembre, enero, marzo, mayo

                                    targetrecibo = common.calcular_proximo_recibo(
                                        f"{today.year}/{today.month}/{today.day}"
                                    )

                                    response = common.addcategoria(
                                        token,
                                        socioid,
                                        categoria,
                                        extra={
                                            "tipusperiodicitat": extras[categoria],
                                            "dataProperaGeneracio": targetrecibo,
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
