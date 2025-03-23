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
dana = 83
actividades = 90
sinactividades = 91

codigos_postales_dana = {
    46000,
    46012,
    46016,
    46017,
    46026,
    46110,
    46117,
    46134,
    46138,
    46149,
    46164,
    46165,
    46178,
    46190,
    46191,
    46192,
    46193,
    46195,
    46196,
    46197,
    46198,
    46200,
    46210,
    46220,
    46230,
    46240,
    46250,
    46267,
    46290,
    46300,
    46330,
    46340,
    46360,
    46367,
    46368,
    46369,
    46370,
    46380,
    46389,
    46393,
    46400,
    46410,
    46417,
    46420,
    46430,
    46440,
    46450,
    46460,
    46469,
    46470,
    46500,
    46530,
    46610,
    46614,
    46621,
    46670,
    46680,
    46687,
    46688,
    46689,
    46690,
    46700,
    46710,
    46727,
    46850,
    46894,
    46900,
    46910,
    46920,
    46930,
    46940,
    46950,
    46960,
    46970,
    46980,
}


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
fechadia = calendar.monthrange(today.year, today.month)[1]


# Locate our member in the list of members
for socio in socios:
    # ID Socio
    socioid = int(socio["idColegiat"])
    categoriassocio = []

    for modalitat in socio["colegiatHasModalitats"]:
        idcategoria = int(modalitat["idModalitat"])
        categoriassocio.append(idcategoria)

    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTBAIXA",
        agrupaciones=["PREINSCRIPCIÓN"],
        reverseagrupaciones=True,
    ):
        for idcategoria in categoriassocio:
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
        # Default for each member
        targetcategorias = [socioactivo]
        removecategorias = []

        # Probar código postal
        try:
            cp = int(socio["persona"]["adreces"][0]["municipi"]["codipostal"])
        except Exception:
            cp = 0

        if cp in codigos_postales_dana:
            targetcategorias.append(dana)
        else:
            removecategorias.append(dana)

        # Find our born year
        try:
            fecha = dateutil.parser.parse(socio["persona"]["dataNaixement"])
        except Exception:
            fecha = False
            print(f"ERROR: Sin fecha nacimiento para socio ID: {socioid}")

        if fecha:
            year, month, day = fecha.year, fecha.month, fecha.day

            for modalitat in socio["colegiatHasModalitats"]:
                idcategoria = int(modalitat["idModalitat"])
                agrupacionom = modalitat["modalitat"]["agrupacio"]["nom"].lower()
                modalitatnom = modalitat["modalitat"]["nom"].lower()

                try:
                    myyear = int(modalitatnom)
                except Exception:
                    myyear = False

                if myyear:
                    if myyear != year:
                        print(f"ERROR: AÑO INCORRECTO para socio ID: {socioid}")
                        common.delcategoria(token, socioid, idcategoria)

                # Attempt to find categories for a year
                try:
                    mycat = int(modalitatnom)
                except Exception:
                    mycat = False

                if mycat and mycat == year and year in range(2000, today.year):
                    # Our member had a match with the born year
                    targetcategorias.append(int(modalitat["idModalitat"]))

                if "colegiatHasModalitats" in socio:
                    # Iterate over all categories for the user
                    for modalitat in socio["colegiatHasModalitats"]:
                        if "modalitat" in modalitat:
                            # Save name for comparing the ones we target
                            agrupacionom = modalitat["modalitat"]["agrupacio"][
                                "nom"
                            ].lower()
                            modalitatnom = modalitat["modalitat"]["nom"].lower()

                            if "Socio Adulto Actividades".lower() in agrupacionom:
                                targetcategorias.append(actividades)
                                removecategorias.append(sinactividades)

                            if "Socio Adulto SIN Actividades".lower() in agrupacionom:
                                targetcategorias.append(sinactividades)
                                removecategorias.append(actividades)

                            if "Socio Actividades".lower() in agrupacionom:
                                targetcategorias.append(actividades)
                                removecategorias.append(sinactividades)

                            if "Socio SIN Actividades".lower() in agrupacionom:
                                targetcategorias.append(sinactividades)
                                removecategorias.append(actividades)

            edad = today.year - year - ((today.month, fechadia) < (month, day))

            # Add target category for +13/+15
            if edad in range(13, 16):
                # AVAST+13
                targetcategorias.append(avast13)

            elif edad in range(15, 18):
                # AVAST+15
                targetcategorias.append(avast15)

            elif edad in range(18, 30):
                # AVAST+18
                targetcategorias.append(avast18)

            # El socio no debe estar en grupos A+13 o A+15 o A+18
            for i in [avast13, avast15, avast18]:
                if i in categoriassocio and i not in targetcategorias:
                    print(f"ERROR: Borrando categoria {i} del socio {socioid}")
                    common.delcategoria(token, socioid, i)

        # Add or remove categories

        for modalitat in targetcategorias:
            if modalitat not in categoriassocio:
                print(
                    "IFF",
                    socioid,
                    modalitat,
                    categoriassocio,
                    modalitat in categoriassocio,
                )
                if modalitat != socioactivo:
                    response = common.addcategoria(token, socioid, modalitat)
                else:
                    response = common.addcategoria(
                        token,
                        socioid,
                        modalitat,
                        extra={
                            "tipusperiodicitat": extras[modalitat],
                            "dataProperaGeneracio": fechacambiosocio,
                        },
                    )

        for modalitat in removecategorias:
            if modalitat in categoriassocio:
                print(
                    "RFF",
                    socioid,
                    modalitat,
                    categoriassocio,
                    modalitat in categoriassocio,
                )

                response = common.delcategoria(token, socioid, modalitat)
