#!/usr/bin/env python

import calendar
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
avast13 = 66
avast15 = 65
avast18 = 77
socioactivo = 82
# Periodicidad (bimensual: 5, anual: 3)
extras = {82: 3}


today = datetime.date.today()

# La cuota anual es el 20 de Febrero
if today.month < 2 or (today.month == 2 and today.day < 20):
    fechacambiosocio = f"20/02/{today.year}"
else:
    fechacambiosocio = f"20/02/{today.year+1}"

# Leer datos
socios = common.readjson("socios")
categorias = common.readjson("categorias")
today = datetime.date.today()


# Locate our member in the list of members
for socio in socios:
    # ID Socio
    socioid = int(socio["idColegiat"])

    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTBAIXA",
        agrupaciones=["PREINSCRIPCIÓN"],
        reverseagrupaciones=True,
    ):
        for categoria in socio["colegiatHasModalitats"]:
            idcategoria = int(categoria["idModalitat"])

            print(
                f"Borrando: {idcategoria} del socio https://{common.endpoint}.playoffinformatica.com/FormAssociat.php?idColegiat={socioid}#tab=CATEGORIES"
            )
            common.delcategoria(token, socioid, idcategoria)

    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTALTA",
        agrupaciones=["PREINSCRIPCIÓN"],
        reverseagrupaciones=True,
    ):
        # Find our born year
        try:
            fecha = dateutil.parser.parse(socio["persona"]["dataNaixement"])
        except Exception:
            fecha = False
            print(f"ERROR: Sin fecha nacimiento para socio ID: {socioid}")

        if fecha:
            year, month, day = fecha.year, fecha.month, fecha.day

            categoriassocio = []
            for categoria in socio["colegiatHasModalitats"]:
                idcategoria = int(categoria["idModalitat"])
                categoriassocio.append(idcategoria)

                try:
                    myyear = int(categoria["modalitat"]["nom"])
                except Exception:
                    myyear = False

                if myyear:
                    if myyear != year:
                        print(f"ERROR: AÑO INCORRECTO para socio ID: {socioid}")
                        common.delcategoria(token, socioid, idcategoria)

            targetcategorias = [socioactivo]
            for categoria in categorias:
                nombre = categoria["nom"]

                # Attempt to find categories for a year
                try:
                    mycat = int(nombre)
                except Exception:
                    mycat = False

                if mycat and mycat == year and year in range(2000, today.year):
                    # Our member had a match with the born year
                    targetcategorias.append(int(categoria["idModalitat"]))

            fechadia = calendar.monthrange(today.year, today.month)[1]

            edad = today.year - year - ((today.month, fechadia) < (month, day))

            # Add target category for +13/+15
            if edad in range(13, 15):
                # AVAST+13
                targetcategorias.append(avast13)

            elif edad in range(15, 24):
                # AVAST+15
                targetcategorias.append(avast15)

            # elif edad in range(18, 29):
            #     # AVAST+18
            #     targetcategorias.append(avast18)

            # El socio no debe estar en grupos A+13 o A+15 o A+18
            for i in [
                avast13,
                avast15,
            ]:  # , avast18 #TODO Remove comment once avast18 is enabled
                if i in categoriassocio and i not in targetcategorias:
                    print(f"ERROR: Borrando categoria {i} del socio {socioid}")
                    common.delcategoria(token, socioid, i)

            for categoria in targetcategorias:
                if categoria not in categoriassocio:
                    print(
                        "IFF",
                        socioid,
                        categoria,
                        categoriassocio,
                        categoria in categoriassocio,
                    )
                    if categoria != socioactivo:
                        response = common.addcategoria(token, socioid, categoria)
                    else:
                        response = common.addcategoria(
                            token,
                            socioid,
                            categoria,
                            extra={
                                "tipusperiodicitat": extras[categoria],
                                "dataProperaGeneracio": fechacambiosocio,
                            },
                        )
