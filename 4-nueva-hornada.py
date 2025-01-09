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

# Definiciones

nuevos = 74

# Leer datos
socios = common.readjson("socios")
categorias = common.readjson("categorias")
today = datetime.date.today()


# Locate our member in the list of members
for socio in socios:
    if (
        "estat" in socio
        and socio["estat"] == "COLESTVAL"
        and "estatColegiat" in socio
        and socio["estatColegiat"]["nom"] == "ESTALTA"
    ):
        # ID Socio
        socioid = socio["idColegiat"]
        alta = socio["dataAlta"]
        numsocio = int(socio["numColegiat"])

        # Find our born year
        try:
            alta = dateutil.parser.parse(alta)
        except Exception:
            alta = False
            print(f"ERROR: Sin fecha alta para socio ID: {socioid}")

        categoriassocio = []
        for categoria in socio["colegiatHasModalitats"]:
            idcategoria = int(categoria["idModalitat"])
            categoriassocio.append(idcategoria)

        if alta.year >= 2024 and alta.month >= 9:
            targetcategorias = [nuevos]
        else:
            targetcategorias = []

        if numsocio > 60000:
            targetcategorias = []

        for categoria in targetcategorias:
            if categoria not in categoriassocio:
                print(
                    "IFF",
                    socioid,
                    categoria,
                    categoriassocio,
                    categoria in categoriassocio,
                )
                response = common.addcategoria(token, socioid, categoria)

        categoria = nuevos
        if categoria in categoriassocio and (
            targetcategorias == [] or targetcategorias is None
        ):
            # Remove Temporal if not in range
            print(
                "RFF",
                socioid,
                categoria,
                categoriassocio,
                categoria in categoriassocio,
            )
            response = common.delcategoria(token, socioid, categoria)
