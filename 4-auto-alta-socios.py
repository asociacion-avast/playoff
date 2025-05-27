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
for actividadid in [777]:
    common.updateactividad(token=token, idactividad=actividadid)


print("Procesando socios...")

# For each user check the custom fields that store the telegram ID for each tutor
for socio in socios:
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

        categoriassocio = common.getcategoriassocio(socio)

        for actividadid in [777]:
            inscritos = common.readjson(filename=f"{actividadid}")
            for inscrito in inscritos:
                if int(inscrito["colegiat"]["idColegiat"]) == socioid:
                    print(f"{common.sociobase}{socioid}#tab=CATEGORIES")
                    if inscrito["estat"] == "INSCRESTNOVA":
                        pagada.append(actividadid)
                        print(
                            f"El socio {socioid} está inscrito en la actividad y ha PAGADO {common.traduce(actividadid)}"
                        )

                        # Comprobamos que ha pagado la categoría que toca

                        pagada = True
                        targetcategorias.append(common.categorias["gestionarcarnet"])
                        activasocio = True

                        if 32 in categoriassocio:
                            targetcategorias.append(
                                common.categorias["sociosinactividades"]
                            )

                        if 33 in categoriassocio:
                            targetcategorias.append(
                                common.categorias["sociosinactividades"]
                            )
                            cambiaactividades = True
                            targetprogramada.append(12)

                        if 54 in categoriassocio:
                            targetcategorias.append(
                                common.categorias["adultosinactividades"]
                            )

                        if 59 in categoriassocio:
                            targetcategorias.append(
                                common.categorias["adultosinactividades"]
                            )
                            # Programar cambio futuro a actividades
                            cambiaactividades = True
                            targetprogramada.append(60)

                        if 85 in categoriassocio:  # Alta tutor actividades
                            cambiaactividades = True
                            targetprogramada.append(60)
                            targetcategorias.append(
                                common.categorias["adultosinactividades"]
                            )

                        if 86 in categoriassocio:
                            cambiaactividades = True
                            targetprogramada.append(13)
                            targetcategorias.append(
                                common.categorias["sociosinactividades"]
                            )

        if activasocio:
            print(f"Socio debe activarse: {activasocio}")
            # Añadir socio a categoria de nueva tanda
            targetcategorias.append(common.categorias["nuevatanda"])
            # Quitar de categoria de informe revisado
            removecategorias.append(common.categorias["informerevisado"])

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
                    targetcambio = f"{today.year + 1}-01-01"
                if today.month <= 9:
                    targetcambio = f"{today.year}-06-22"

                print(
                    common.escribecampo(
                        token, socioid, common.fechacambio, valor=targetcambio
                    ).text
                )

            # Aquí revisamos las categorías donde está, pero realmente hay que darlo de alta via CAMBIOS para actividades, y de normal estar sólo como socio sin actividades
            for categoria in categoriassocio:
                if categoria in common.cambiospreinscrip:
                    print(
                        f"El socio pasa de categoria {common.traduce(categoria)} a {common.traduce(common.cambiospreinscrip[categoria])}"
                    )
                    # targetcategorias.append(cambiospreinscrip[categoria])
                    removecategorias.append(categoria)

            print("Altas en categorias:")
            for categoria in targetcategorias:
                print(common.traduce(categoria))
                common.addcategoria(token=token, categoria=categoria, socio=socioid)
            print("Bajas en categorias:")
            for categoria in removecategorias:
                print(common.traduce(categoria))
                common.delcategoria(token=token, categoria=categoria, socio=socioid)
