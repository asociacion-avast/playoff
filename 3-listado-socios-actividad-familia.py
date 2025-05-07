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


for familia in familias["miembros"]:
    parientes = familias["miembros"][familia]
    parientes.append(familia)
    if familia not in procesados:
        procesados.extend(iter(parientes))
        # Si el socio ya ha sido procesado, no lo procesamos de nuevo

        sociosactividad = []
        socioshermanos = []
        sociossinactiv = []

        for pariente in parientes:
            socio = common.get_colegiat_json(idColegiat=pariente)
            categorias = common.getcategoriassocio(socio)

            if common.categorias["adultosconysin"] not in categorias:
                if common.categorias["sociohermanoactividades"] in categorias:
                    socioshermanos.append(pariente)

                if common.categorias["socioactividades"] in categorias:
                    sociosactividad.append(pariente)

                if common.categorias["sociosinactividades"] in categorias:
                    sociossinactiv.append(pariente)

        # Familia procesada
        if socioshermanos:
            if not sociosactividad:
                print(
                    f"ERROR TOODESC: Familia {familia} tiene {len(parientes)} miembros, {len(sociosactividad)} actividad, {len(sociossinactiv)} sin actividad, {len(socioshermanos)} hermanos: {common.sociobase}{familia}#tab=CATEGORIES"
                )
            if len(sociosactividad) > 1:
                print(
                    f"ERROR LOWDESC: Familia {familia} tiene {len(parientes)} miembros, {len(sociosactividad)} actividad, {len(sociossinactiv)} sin actividad, {len(socioshermanos)} hermanos: {common.sociobase}{familia}#tab=CATEGORIES"
                )
