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


def cruzar_miembros(miembros):
    # Rellenar de forma cruzada los miembros de la familia para completar los valores

    # Paso 1: convertir todas las claves y valores a enteros (algunos son a veces cadenas)
    datos = {}
    for k, lista in miembros.items():
        k_int = int(k)
        valores_int = [int(x) for x in lista]

        # incluirse a sí mismo si no está
        grupo = set(valores_int)
        grupo.add(k_int)

        for miembro in grupo:
            if miembro not in datos:
                datos[miembro] = set()
            datos[miembro].update(grupo - {miembro})  # todos menos él mismo

    # Paso 2: convertir los sets a listas ordenadas
    return {k: sorted(v) for k, v in datos.items()}


print("Procesando socios")
for socio in socios:
    socioid = int(socio["idColegiat"])

    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTALTA",
        agrupaciones=["PREINSCRIPCIÓN"],
        reverseagrupaciones=True,
    ):
        if (
            socioid not in familias["miembros"]
            and socioid not in familias["procesados"]
        ):
            familias["miembros"][socioid] = []
            familias["procesados"].append(socioid)

            print(f"Actualizando familia del socio {socioid}")
            url = f"{common.apiurl}/colegiats/{socioid}/familia"
            response = requests.get(
                url, headers=common.headers, auth=common.BearerAuth(token), timeout=15
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


familias["miembros"] = cruzar_miembros(familias["miembros"])

# Save to disk
common.writejson(filename="familias", data=familias)
