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


print("Actualizando actividades ALTA")
# 728: Alta sin actividades
# 729: Alta adulto actividades
# 730: Alta niño actividades
# 732: Alta Tutor actividades
# 733: Alta Hermano Actividades
# 748: Alta Adulto sin actividades
# 769: Carnets tutor x2
# 770: Carnets tutor x1
# 771: Carnet socio


for actividadid in [769, 770, 771]:
    common.updateactividad(token=token, idactividad=actividadid)


print("Procesando socios...")

# For each user check the custom fields that store the telegram ID for each tutor
for socio in socios:
    # try:
    #     fecha = dateutil.parser.parse(user["persona"]["dataNaixement"])
    # except Exception:
    #     fecha = False
    activasocio = False
    targetcategorias = []
    removecategorias = []

    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTALTA",
        agrupaciones=["PREINSCRIPCIÓN"],
        reverseagrupaciones=True,
    ):
        socioid = int(socio["idColegiat"])

        categoriassocio = common.getcategoriassocio(socio=socio)

        for actividadid in [769, 770, 771]:
            inscritos = common.readjson(filename=f"{actividadid}")
            for inscrito in inscritos:
                if int(inscrito["colegiat"]["idColegiat"]) == socioid:
                    print(f"{common.sociobase}{socioid}#tab=CATEGORIES")
                    if inscrito["estat"] == "INSCRESTNOVA":
                        print(
                            f"El socio {socioid} está inscrito en la actividad y ha PAGADO {common.traduce(actividadid)}"
                        )

                        if actividadid == 769:  # Socio ha pagado 2x carnets
                            activasocio = True
                            targetcategorias.append(
                                common.categorias["gestionarcarnetveterano"]
                            )  # Carnet veterano
                            removecategorias.append(
                                common.categorias["sindoscarnetfamiliar"]
                            )  # Socio sin carnet

                        if actividadid == 770:  # Socio ha pagado 1x carnets
                            activasocio = True
                            targetcategorias.append(
                                common.categorias["gestionarcarnetveterano"]
                            )  # Carnet veterano
                            removecategorias.append(
                                common.categorias["sinuncarnetfamiliar"]
                            )  # Socio sin carnet

                        if actividadid == 771:  # Socio ha pagado carnet socio
                            activasocio = True
                            targetcategorias.append(
                                common.categorias["gestionarcarnetveterano"]
                            )  # Carnet veterano
                            removecategorias.append(
                                common.categorias["notienecarnet"]
                            )  # Socio sin carnet

        if activasocio:
            print(f"Socio ha pagado carnet: {activasocio}")

            if (
                common.categorias["notienecarnet"] in categoriassocio
                or common.categorias["sinuncarnetfamiliar"] in categoriassocio
                or common.categorias["sindoscarnetfamiliar"] in categoriassocio
            ):
                print("Altas en categorias:")
                for categoria in targetcategorias:
                    print(common.traduce(categoria))
                    common.addcategoria(token=token, categoria=categoria, socio=socioid)
                print("Bajas en categorias:")
                for categoria in removecategorias:
                    print(common.traduce(categoria))
                    common.delcategoria(token=token, categoria=categoria, socio=socioid)
