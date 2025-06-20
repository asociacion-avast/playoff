#!/usr/bin/env python


import configparser
import os

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


print("Loading file from disk")

actividades = common.readjson(filename="actividades")
socios = common.readjson(filename="socios")


usuariosyactividad = {}
sociosactividades = []
sociocategorias = {}


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)

print("Procesando actividades...")
for actividad in actividades:
    myid = actividad["idActivitat"]

    if actividad["idNivell"] and actividad["idNivell"] != "null":
        horario = int(actividad["idNivell"])

        if horario in {7, 8, 9, 10}:
            inscritos = common.readjson(filename=f"{myid}")

            for inscrito in inscritos:
                colegiat = inscrito["colegiat"]["idColegiat"]

                if inscrito["estat"] == "INSCRESTNOVA":
                    if colegiat not in usuariosyactividad:
                        usuariosyactividad[colegiat] = []

                    usuariosyactividad[colegiat].append(myid)

print("Procesando socios...")
for socio in socios:
    id_socio = socio["idColegiat"]
    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTALTA",
        agrupaciones=["PREINSCRIPCIÓN"],
        reverseagrupaciones=True,
    ) or common.validasocio(
        socio,
        estado="COLESTPRE",
        estatcolegiat="ESTALTA",
    ):
        categoriassocio = common.getcategoriassocio(socio)

        if (
            common.categorias["actividades"] in categoriassocio
            and common.categorias["adultosconysin"] not in categoriassocio
        ):
            if (
                common.categorias["conactividadessininscripciones"]
                not in categoriassocio
            ):
                if id_socio not in usuariosyactividad:
                    print(
                        f"Socio {id_socio} tiene categoria de actividades, pero no inscripciones"
                    )
                    common.addcategoria(
                        token,
                        socio,
                        common.categorias["conactividadessininscripciones"],
                    )
                else:
                    if (
                        common.categorias["conactividadessininscripciones"]
                        in categoriassocio
                    ):
                        print(f"Socio {id_socio} ha resulto la situacion")
                        common.delcategoria(
                            token,
                            socio,
                            common.categorias["conactividadessininscripciones"],
                        )

        if common.categorias["sinactividades"] in categoriassocio:
            if common.categorias["conactividadessininscripciones"] in categoriassocio:
                print(f"Socio {id_socio} ha resulto la situacion")
                common.delcategoria(
                    token,
                    socio,
                    common.categorias["conactividadessininscripciones"],
                )
