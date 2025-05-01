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

# Periodicidad (bimensual: 5, anual: 3)
extras = {82: 3}

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
    fechacambiosocio = f"20/02/{today.year + 1}"

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
                f"Borrando: {idcategoria} del socio {common.sociobase}{socioid}#tab=CATEGORIES"
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
        targetcategorias = [common.categorias["socioactivo"]]
        removecategorias = [common.categorias["informevalidado"]]
        adulto = False

        # Carnet de socio
        if common.categorias["carnetpendiente"] not in categoriassocio:
            if "persona" in socio and "residencia" in socio["persona"]:
                if (
                    socio["persona"]["residencia"] == ""
                    or socio["persona"]["residencia"] == "-"
                ):
                    targetcategorias.append(common.categorias["notienecarnet"])
                else:
                    removecategorias.append(common.categorias["notienecarnet"])

                if (
                    "ANULADO".lower() in socio["persona"]["residencia"].lower()
                    or "ANUAL".lower() in socio["persona"]["residencia"].lower()
                    or socio["persona"]["residencia"] == "null"
                ):
                    targetcategorias.append(common.categorias["carnetincorrecto"])

                    # Forzar marcar que no tiene carnet
                    if common.categorias["notienecarnet"] in removecategorias:
                        removecategorias.remove(common.categorias["notienecarnet"])
                        targetcategorias.append(common.categorias["notienecarnet"])

                else:
                    removecategorias.append(common.categorias["carnetincorrecto"])

        # Carnet tutores
        carnetsocio = []

        for tutor in ["tutor1", "tutor2"]:
            if (
                tutor in socio
                and socio[tutor] is not None
                and socio[tutor]["residencia"] != ""
                and socio[tutor]["residencia"] != "-"
                and "ANULADO".lower() not in socio[tutor]["residencia"].lower()
                and "ANUAL".lower() not in socio[tutor]["residencia"].lower()
                and socio[tutor]["residencia"] != "null"
            ):
                carnetsocio.append(socio[tutor]["residencia"])

        # Probar código postal
        try:
            cp = int(socio["persona"]["adreces"][0]["municipi"]["codipostal"])
        except Exception:
            cp = 0

        if cp in codigos_postales_dana:
            targetcategorias.append(common.categorias["dana"])
        else:
            removecategorias.append(common.categorias["dana"])

        # Find our born year
        try:
            fecha = dateutil.parser.parse(socio["persona"]["dataNaixement"])
        except Exception:
            fecha = False
            print(f"ERROR: Sin fecha nacimiento para socio ID: {socioid}")

        if fecha:
            year, month, day = fecha.year, fecha.month, fecha.day
        else:
            year, month, day = False, False, False

        for modalitat in socio["colegiatHasModalitats"]:
            idcategoria = int(modalitat["idModalitat"])
            agrupacionom = modalitat["modalitat"]["agrupacio"]["nom"].lower()
            modalitatnom = modalitat["modalitat"]["nom"].lower()

            try:
                myyear = int(modalitatnom)
            except Exception:
                myyear = False

            if myyear and year:
                if myyear != year:
                    print(f"ERROR: AÑO INCORRECTO para socio ID: {socioid}")
                    common.delcategoria(token, socioid, idcategoria)

            # Attempt to find categories for a year

            for categoria in categorias:
                nombre = categoria["nom"]

                # Attempt to find categories for a year
                try:
                    mycat = int(nombre)
                except Exception:
                    mycat = False

                if mycat and mycat == year and year and year in range(2000, today.year):
                    # Our member had a match with the born year
                    targetcategorias.append(int(categoria["idModalitat"]))

            if "Socio Adulto Actividades".lower() in agrupacionom:
                adulto = True
                targetcategorias.append(common.categorias["actividades"])
                removecategorias.append(common.categorias["sinactividades"])
                targetcategorias.append(common.categorias["adultosconysin"])

            if "Socio Adulto SIN Actividades".lower() in agrupacionom:
                adulto = True
                targetcategorias.append(common.categorias["sinactividades"])
                removecategorias.append(common.categorias["actividades"])
                targetcategorias.append(common.categorias["adultosconysin"])

            if "Socio Actividades".lower() in agrupacionom:
                targetcategorias.append(common.categorias["actividades"])
                removecategorias.append(common.categorias["sinactividades"])

            if "Socio SIN Actividades".lower() in agrupacionom:
                targetcategorias.append(common.categorias["sinactividades"])
                removecategorias.append(common.categorias["actividades"])

        # Los adultos no necesitan tener tutores
        if common.categorias["carnetpendiente"] not in categoriassocio:
            if not adulto:
                if not carnetsocio:
                    targetcategorias.append(common.categorias["sindoscarnetfamiliar"])
                    removecategorias.append(common.categorias["sinuncarnetfamiliar"])

                if len(carnetsocio) == 1:
                    targetcategorias.append(common.categorias["sinuncarnetfamiliar"])
                    removecategorias.append(common.categorias["sindoscarnetfamiliar"])

                if len(carnetsocio) == 2:
                    removecategorias.extend(
                        (
                            common.categorias["sinuncarnetfamiliar"],
                            common.categorias["sindoscarnetfamiliar"],
                        )
                    )
            else:
                removecategorias.extend(
                    (
                        common.categorias["sinuncarnetfamiliar"],
                        common.categorias["sindoscarnetfamiliar"],
                    )
                )
        else:
            removecategorias.extend(
                (
                    common.categorias["sinuncarnetfamiliar"],
                    common.categorias["sindoscarnetfamiliar"],
                    common.categorias["notienecarnet"],
                )
            )

        edad = today.year - year - ((today.month, fechadia) < (month, day))

        # Add target category for +13/+15
        if edad in range(13, 15):
            # AVAST+13
            targetcategorias.append(common.categorias["avast13"])

        if edad in range(15, 21):
            # AVAST+15
            targetcategorias.append(common.categorias["avast15"])

        if edad in range(18, 30):
            # AVAST+18
            targetcategorias.append(common.categorias["avast18"])

        # El socio no debe estar en grupos A+13 o A+15 o A+18
        for i in [
            common.categorias["avast13"],
            common.categorias["avast15"],
            common.categorias["avast18"],
        ]:
            if i in categoriassocio and i not in targetcategorias:
                print(f"ERROR: Borrando categoria {i} del socio {socioid}")
                common.delcategoria(token, socioid, i)

        # Add or remove categories

        for modalitat in sorted(set(targetcategorias)):
            if modalitat not in categoriassocio:
                print(
                    "IFF",
                    f"{common.sociobase}{socioid}",
                    modalitat,
                    categoriassocio,
                    modalitat in categoriassocio,
                )
                if modalitat != common.categorias["socioactivo"]:
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

        for modalitat in sorted(set(removecategorias)):
            if modalitat in categoriassocio:
                print(
                    "RFF",
                    f"{common.sociobase}{socioid}",
                    modalitat,
                    categoriassocio,
                    modalitat in categoriassocio,
                )

                response = common.delcategoria(token, socioid, modalitat)
