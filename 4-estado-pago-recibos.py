#!/usr/bin/env python

import configparser
import json
import os

import requests

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)

headers = {"Authorization": f"Bearer {token}"}

socios = common.readjson("socios")


for socio in socios:
    socioid = int(socio["idColegiat"])

    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTALTA",
        agrupaciones=["PREINSCRIPCIÓN"],
        reverseagrupaciones=True,
    ):
        categoriassocio = []

        for modalitat in socio["colegiatHasModalitats"]:
            idcategoria = int(modalitat["idModalitat"])
            categoriassocio.append(idcategoria)

        url = f"{common.apiurl}/colegiats/rebuts?idColegiat={socioid}&limit=1000"
        response = json.loads(
            requests.get(
                url, headers=common.headers, auth=common.BearerAuth(token)
            ).text
        )

        targetcategorias = []
        removecategorias = []
        for recibo in response:
            # print(
            #     recibo["base"], recibo["concepte"], recibo["dataPagament"], recibo["estat"]
            # )
            if recibo["estat"] == "REBESTRET":
                targetcategorias.append(common.categorias["impagados"])

        if len(targetcategorias) > 0:
            if common.categorias["impagados"] not in categoriassocio:
                print(
                    f"Socio {common.sociobase}{socioid}#tab=CATEGORIES Tiene recibos impagados"
                )
        else:
            if common.categorias["impagados"] in categoriassocio:
                print(
                    f"Socio {common.sociobase}{socioid}#tab=CATEGORIES Ha saldado las deudas"
                )
                removecategorias.append(common.categorias["impagados"])

        for categoria in targetcategorias:
            if categoria not in categoriassocio:
                response = common.addcategoria(
                    token=token, socio=socioid, categoria=categoria
                )

        for categoria in removecategorias:
            if categoria in categoriassocio:
                response = common.delcategoria(
                    token=token, socio=socioid, categoria=categoria
                )
