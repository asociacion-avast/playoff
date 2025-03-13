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
# 731: Carnet tutor
# 732: Alta Tutor actividades
# 733: Alta Hermano Actividades


# for actividadid in [728,729,730,731,732,733]:
#     common.updateactividad(token=token,idactividad=actividadid)


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
    731: "Carnet tutor",
    732: "Alta Tutor actividades",
    733: "Alta Hermano Actividades",
    74: "Nueva tanda",
    84: "Carnet tutor",
    85: "Tutor con actividades",
    86: "Hermano con actividades",
    79: "Autocambio ADULTO con actividades",
    81: "Autocambio SOCIO PRINCIPAL con actividades",
    87: "Autocambio HERMANO actividades",
}


def traduce(id):
    return "ID %s (%s)" % (id, diccionario[id])


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

        for actividadid in [728, 729, 730, 731, 732, 733]:
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

                        # Comprobamos que ha pagado la categoría que toca
                        if actividadid == 728:  # Alta sin actividades
                            if 32 in categoriassocio:
                                activasocio = True
                                targetcategorias.append(1)
                            if 54 in categoriassocio:
                                activasocio = True
                                targetcategorias.append(53)
                        if actividadid == 729:  # Alta adulto actividades
                            if 59 in categoriassocio:
                                activasocio = True
                                targetcategorias.append(84)  # Carnet
                                targetcategorias.append(53)
                                # Programar cambio futuro a actividades
                                cambiaactividades = True
                                targetprogramada.append(60)
                        if actividadid == 730:  # Alta niño actividades
                            if 33 in categoriassocio:
                                activasocio = True
                                targetcategorias.append(84)  # Carnet
                                targetcategorias.append(1)
                                cambiaactividades = True
                                targetprogramada.append(12)
                        if actividadid == 731:  # Carnet adicional tutor
                            targetcategorias.append(84)  # Carnet
                        if actividadid == 732:  # Alta tutor actividades
                            cambiaactividades = True
                            targetprogramada.append(60)

                        if actividadid == 733:  # Alta hermano actividades
                            cambiaactividades = True
                            targetcategorias.append(84)  # Carnet
                            targetprogramada.append(13)

        if activasocio:
            print("Socio debe activarse: %s" % activasocio)
            # Añadir socio a categoria de nueva tanda
            targetcategorias.append(74)

            if cambiaactividades:
                print("El socio cambiará a actividades")
                # Categoria CAMBIOS para cambiar automáticamente
                # 81 Socio principal actividades
                # 87 Socio Hermano actividades
                # 79 Socio adulto actividades
                if 12 in targetprogramada:
                    targetcategorias.append(81)
                if 13 in targetprogramada:
                    targetcategorias.append(87)
                if 60 in targetprogramada:
                    targetcategorias.append(79)

                # Proximo cambio:
                # Si el mes actual es superior a septiembre -> 1 de Enero
                # Si el mes actual es inferior o igual a septiembre -> 22 de Junio

                print("Programando fecha cambio")
                if today.month > 9:
                    targetcambio = f"01-01-{today.year + 1}"
                if today.month <= 9:
                    targetcambio = f"22-06-{today.year}"

                    print(
                        common.escribecampo(
                            token, socioid, common.fechacambio, valor=targetcambio
                        ).text
                    )

            # Aquí revisamos las categorías donde está, pero realmente hay que darlo de alta via CAMBIOS para actividades, y de normal estar sólo como socio sin actividades
            for categoria in categoriassocio:
                if categoria in cambiospreinscrip:
                    print(
                        "El socio pasa de categoria %s a %s"
                        % (traduce(categoria), traduce(cambiospreinscrip[categoria]))
                    )
                    # targetcategorias.append(cambiospreinscrip[categoria])
                    removecategorias.append(categoria)

            print("Altas en categorias:")
            for categoria in targetcategorias:
                print(traduce(categoria))
                common.addcategoria(token=token, categoria=categoria, socio=socioid)
            print("Bajas en categorias:")
            for categoria in removecategorias:
                print(traduce(categoria))
                common.delcategoria(token=token, categoria=categoria, socio=socioid)


# TODO: Comprobar que el socio ha pagado la categoría que corresponde para el cambio en el que está inscrito # (puede que ya esté en la comprobación que se hace tras cada actividad)
