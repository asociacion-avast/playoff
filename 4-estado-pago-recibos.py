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
        print(f"Procesando socio {socioid}")
        categoriassocio = common.getcategoriassocio(socio=socio)

        url = f"{common.apiurl}/colegiats/rebuts?idColegiat={socioid}&limit=1000"
        response = json.loads(
            requests.get(
                url, headers=common.headers, auth=common.BearerAuth(token)
            ).text
        )

        targetcategorias = []
        removecategorias = []
        recibos = {}
        reciboids = []

        for recibo in response:
            idrecibo = int(recibo["idRebut"])
            reciboids.append(idrecibo)

            recibos[idrecibo] = {}
            recibos[idrecibo]["base"] = recibo["base"]
            recibos[idrecibo]["concepte"] = recibo["concepte"]
            recibos[idrecibo]["dataPagament"] = recibo["dataPagament"]
            recibos[idrecibo]["estat"] = recibo["estat"]
            # print(
            #     recibo["base"], recibo["concepte"], recibo["dataPagament"], recibo["estat"]
            # )

        reciboids.sort(reverse=True)

        # Listar recibos anuales
        recibosanuales = []
        for idrecibo in reciboids:
            if recibos[idrecibo]["concepte"].upper().find("ANUAL") > 0:
                recibosanuales.append(idrecibo)

        for recibo in reciboids[0:3]:
            if recibos[recibo]["estat"] == "REBESTRET":
                targetcategorias.append(common.categorias["impagados"])
        # Comprobar último recibo anual
        if len(recibosanuales) > 0:
            recibo = recibosanuales[0]
            if recibos[recibo]["estat"] == "REBESTRET":
                targetcategorias.append(common.categorias["impagoanual"])
        else:
            removecategorias.append(common.categorias["impagoanual"])

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
