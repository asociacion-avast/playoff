#!/usr/bin/env python

import configparser
import datetime
import os

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)


print("Loading file from disk")
socios = common.readjson(filename="socios")
actividades = common.readjson(filename="actividades")


today = datetime.date.today()


print("Actualizando actividades CAMBIO")
for actividadid in [781, 782]:
    common.updateactividad(token=token, idactividad=actividadid)


print("Procesando socios...")

# For each user check the custom fields that store the telegram ID for each tutor
for socio in socios:
    activasocio = False
    cambiaactividades = False
    targetcategorias = []
    removecategorias = []
    targetprogramada = []

    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTALTA",
        agrupaciones=["PREINSCRIPCIÓN"],
        reverseagrupaciones=True,
    ):
        socioid = int(socio["idColegiat"])

        categoriassocio = common.getcategoriassocio(socio=socio)
        inscripciones = []

        saltarsocio = False
        for cambio in [78, 79, 80, 81, 87]:
            if cambio in categoriassocio:
                saltarsocio = True
                # print(
                # f"El socio {socioid} tiene un cambio programado ya ({common.traduce(cambio)}) saltando..."
                #  )
        if not saltarsocio:
            for actividadid in [781, 782]:
                inscritos = common.readjson(filename=f"{actividadid}")
                for inscrito in inscritos:
                    if int(inscrito["colegiat"]["idColegiat"]) == socioid:
                        inscripciones.append(inscrito["idInscripcio"])
                        if inscrito["estat"] == "INSCRESTNOVA":
                            print(f"{common.sociobase}{socioid}#tab=CATEGORIES")
                            print(
                                f"El socio {socioid} está inscrito en la actividad {common.traduce(actividadid)}"
                            )

                            activasocio = True

                            if actividadid == 781:
                                # Pasar a CON actividades
                                if (
                                    common.categorias["adultosinactividades"]
                                    in categoriassocio
                                ):
                                    cambiaactividades = True
                                    targetprogramada.append(79)

                                if (
                                    common.categorias["sociosinactividades"]
                                    in categoriassocio
                                ):
                                    cambiaactividades = True
                                    targetprogramada.append(81)

                            if actividadid == 782:
                                # Pasar a SIN actividades
                                if (
                                    common.categorias["socioactividades"]
                                    in categoriassocio
                                    or common.categorias["sociohermanoactividades"]
                                    in categoriassocio
                                ):
                                    targetprogramada.append(80)

                                if (
                                    common.categorias["adultoconactividades"]
                                    in categoriassocio
                                ):
                                    targetprogramada.append(78)

        if activasocio:
            print(f"Socio debe activarse: {activasocio}")

            # Next year if we're in the last bimester
            if today.month >= 11:
                year = today.year + 1
            else:
                year = today.year

            month = common.mes_proximo_bimestre()

            targetcambio = f"01-{month:02}-{year}"

            print(f"Programando fecha cambio: {targetcambio}")

            print(
                common.escribecampo(
                    token, socioid, common.fechacambio, valor=targetcambio
                ).text
            )

            print("Altas en categorias:")
            for categoria in targetprogramada:
                print(common.traduce(categoria))
                common.addcategoria(token=token, categoria=categoria, socio=socioid)

            # Borra inscripciones a las actividades
            print("Borrando inscripciones a actividades AUTO-CAMBIO")
            for inscripcion in inscripciones:
                response = common.anula_inscripcio(
                    token=token, inscripcion=inscripcion, comunica=False
                )
