#!/usr/bin/env python

import configparser
import os

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken()


print("Loading file from disk")
socios = common.readjson(filename="socios")
familias = common.readjson(filename="familias")

procesados = []

print("Procesando socios")
# Iteramos sobre miembros porque cap familia hace referencia a la cuenta bancaria


def procesar_parientes(parientes, modfam):
    for pariente in parientes:
        socio = common.get_colegiat_json(idColegiat=pariente)
        if (
            socio
            and "estatColegiat" in socio
            and socio["estatColegiat"]["nom"] == "ESTBAIXA"
        ):
            modfam["baja"].append(pariente)
        if (
            socio
            and "estatColegiat" in socio
            and socio["estatColegiat"]["nom"] == "ESTALTA"
        ):
            categorias = common.getcategoriassocio(socio)

            if common.categorias["adultosconysin"] not in categorias:
                if common.categorias["sociohermanoactividades"] in categorias:
                    modfam["sociohermanoactividades"].append(pariente)

                if common.categorias["socioactividades"] in categorias:
                    modfam["socioactividades"].append(pariente)

                if common.categorias["sociosinactividades"] in categorias:
                    modfam["sociosinactividades"].append(pariente)

            else:
                modfam["adultosconysin"].append(pariente)


def reportar_errores(familia, parientes, modfam):
    if len(modfam["sociohermanoactividades"]) > 0:
        if not modfam["socioactividades"]:
            print(
                f"ERROR TOODESC: Familia {familia} tiene {len(parientes)} miembros, {len(modfam['socioactividades'])} actividad, {len(modfam['sociosinactividades'])} sin actividad, {len(modfam['sociohermanoactividades'])} hermanos: {common.sociobase}{familia}#tab=CATEGORIES"
            )
            print("DISTRIBUCION", modfam)
        if len(modfam["socioactividades"]) > 1:
            print(
                f"ERROR LOWDESC: Familia {familia} tiene {len(parientes)} miembros, {len(modfam['socioactividades'])} actividad, {len(modfam['sociosinactividades'])} sin actividad, {len(modfam['sociohermanoactividades'])} hermanos: {common.sociobase}{familia}#tab=CATEGORIES"
            )
            print("DISTRIBUCION", modfam)


for familia in sorted(set(familias["miembros"])):
    parientes = familias["miembros"][familia]
    # Añadir el socio que está siendo procesado a la lista de parientes
    parientes.append(familia)

    modfam = {
        "adultosconysin": [],
        "sociohermanoactividades": [],
        "socioactividades": [],
        "sociosinactividades": [],
        "baja": [],
    }

    if familia in procesados:
        print(f"Familia {familia} ya procesada, saltando")
    else:
        procesados.extend(iter(parientes))
        # Si el socio ya ha sido procesado, no lo procesamos de nuevo
        procesar_parientes(parientes, modfam)
        reportar_errores(familia, parientes, modfam)
