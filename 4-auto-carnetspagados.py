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


# Definiciones

# 53: Adulto sin actividades
# 60: Adulto con actividades
# 12: Socio principal con actividades
# 1: Socio principal sin actividades


cambios = {
    728: 1,
    729: 60,
    730: 12,
}


cambiospreinscrip = {32: 1, 33: 12, 54: 53, 59: 60, 85: 60, 86: 13}


diccionario = {
    1: "Socio principal sin actividades",
    12: "Socio principal con actividades",
    13: "Socio Hermano",
    32: "Candidato a Socio principal sin actividades",
    33: "Candidato a Socio principal con actividades",
    53: "Adulto sin actividades",
    54: "Candidato a Adulto sin actividades",
    59: "Candidato a Adulto con actividades",
    60: "Adulto con actividades",
    728: "Alta sin actividades",
    729: "Alta adulto actividades",
    730: "Alta niño actividades",
    732: "Alta Tutor actividades",
    733: "Alta Hermano Actividades",
    748: "Alta adulto sin actividades",
    769: "Carnet tutor x1",
    770: "Carnet tutor x2",
    771: "Carnet tutor x1",
    74: "Nueva tanda",
    84: "Carnet tutor",
    85: "Tutor con actividades",
    86: "Hermano con actividades",
    79: "Autocambio ADULTO con actividades",
    81: "Autocambio SOCIO PRINCIPAL con actividades",
    87: "Autocambio HERMANO actividades",
    97: "Socio sin carnet",
    98: "Carnets veteranos",
}


def traduce(id):
    if id in diccionario:
        text = "ID %s (%s)" % (id, diccionario[id])
    else:
        text = "ID %s no encontrado en diccionaro" % id
    return text


print("Procesando socios...")

# For each user check the custom fields that store the telegram ID for each tutor
for socio in socios:
    # try:
    #     fecha = dateutil.parser.parse(user["persona"]["dataNaixement"])
    # except Exception:
    #     fecha = False
    activasocio = False
    cambiaactividades = False
    targetcategorias = []
    removecategorias = []
    targetprogramada = []
    pagada = []

    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTALTA",
        agrupaciones=["PREINSCRIPCIÓN"],
    ):
        socioid = int(socio["idColegiat"])

        categoriassocio = []

        for categoria in socio["colegiatHasModalitats"]:
            idcategoria = int(categoria["idModalitat"])
            categoriassocio.append(idcategoria)

        for actividadid in [769]:
            inscritos = common.readjson(filename=f"{actividadid}")
            for inscrito in inscritos:
                if int(inscrito["colegiat"]["idColegiat"]) == socioid:
                    print(
                        f"https://{common.endpoint}.playoffinformatica.com/FormAssociat.php?idColegiat={socioid}#tab=CATEGORIES"
                    )
                    if inscrito["estat"] == "INSCRESTNOVA":
                        pagada.append(actividadid)
                        print(
                            f"El socio {socioid} está inscrito en la actividad y ha PAGADO {traduce(actividadid)}"
                        )

                        if actividadid == 769:  # Socio ha pagado 2x carnets
                            activasocio = True
                            targetcategorias.append(98)  # Carnet veterano
                            removecategorias.append(100)  # Socio sin carnet

                        if actividadid == 770:  # Socio ha pagado 1x carnets
                            activasocio = True
                            targetcategorias.append(98)  # Carnet veterano
                            removecategorias.append(99)  # Socio sin carnet

                        if actividadid == 771:  # Socio ha pagado carnet socio
                            activasocio = True
                            targetcategorias.append(98)  # Carnet veterano
                            removecategorias.append(97)  # Socio sin carnet

        if activasocio:
            print(f"Socio ha pagado carnet: {activasocio}")

            if 97 in categoriassocio:
                print("Altas en categorias:")
                for categoria in targetcategorias:
                    print(traduce(categoria))
                    common.addcategoria(token=token, categoria=categoria, socio=socioid)
                print("Bajas en categorias:")
                for categoria in removecategorias:
                    print(traduce(categoria))
                    common.delcategoria(token=token, categoria=categoria, socio=socioid)
