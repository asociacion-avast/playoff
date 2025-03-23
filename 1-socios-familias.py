#!/usr/bin/env python

import configparser
import json
import os

import requests

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken()


print("Loading file from disk")
socios = common.readjson(filename="socios")

try:
    familias = common.readjson(filename="familias")
except Exception:
    familias = {"capfamilias": [], "miembros": {}, "procesados": []}


print("Procesando socios")
for socio in socios:
    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTALTA",
        agrupaciones=["PREINSCRIPCIÓN"],
        reverseagrupaciones=True,
    ):
        socioid = int(socio["idColegiat"])

        if (
            socioid not in familias["miembros"]
            and socioid not in familias["procesados"]
        ):
            familias["miembros"][socioid] = []
            familias["procesados"].append(socioid)

            print("Actualizando familia del socio %s" % socioid)
            url = f"{common.apiurl}/colegiats/{socioid}/familia"
            response = requests.get(
                url, headers=common.headers, auth=common.BearerAuth(token)
            )
            if response.status_code == 200:
                family = json.loads(response.text)
                if family != []:
                    for miembro in family["familiars"]:
                        miembroid = int(miembro["idColegiat"])
                        if miembroid != socioid:
                            if miembroid not in familias["miembros"]:
                                familias["miembros"][miembroid] = []
                            familias["miembros"][socioid].append(miembroid)
                            familias["miembros"][miembroid].append(socioid)

                            if miembro["isBancCapFamilia"] == "1":
                                familias["capfamilias"].append(miembroid)
    else:
        # Socio no válido
        if socioid in familias["miembros"]:
            del familias["miembros"][socioid]
        if socioid in familias["capfamilias"]:
            familias["capfamilias"].remove(socioid)


# Find empty elements
toclean = []
for familia in familias["miembros"]:
    if len(familias["miembros"][familia]) == 0:
        toclean.append(familia)

# Cleanup
for familia in toclean:
    del familias["miembros"][familia]

familias["capfamilias"] = sorted(set(familias["capfamilias"]))
familias["miembros"] = {k: list(set(v)) for k, v in familias["miembros"].items()}

# Save to disk
common.writejson(filename="familias", data=familias)
