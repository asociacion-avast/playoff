#!/usr/bin/env python

import configparser
import os

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


def listado_actividad_familia():
    print("Loading file from disk")
    socios = common.readjson(filename="socios")
    familias = common.readjson(filename="familias")

    socios_by_id = {}
    for socio in socios:
        sid = socio.get("idColegiat")
        if sid is not None:
            socios_by_id[int(sid)] = socio

    procesados = set()

    print("Procesando socios")

    def procesar_parientes(parientes, modfam):
        for pariente in parientes:
            try:
                pid = int(pariente)
            except (TypeError, ValueError):
                continue
            socio = socios_by_id.get(pid)
            if not socio:
                continue
            estat = (socio.get("estatColegiat") or {}).get("nom")
            if estat == "ESTPERLAB":
                continue
            if estat == "ESTBAIXA":
                modfam["baja"].append(pariente)
            if estat == "ESTALTA":
                cats = common.getcategoriassocio(socio)
                if common.categorias["adultosconysin"] not in cats:
                    if common.categorias["sociohermanoactividades"] in cats:
                        modfam["sociohermanoactividades"].append(pariente)
                    if common.categorias["socioactividades"] in cats:
                        modfam["socioactividades"].append(pariente)
                    if common.categorias["sociosinactividades"] in cats:
                        modfam["sociosinactividades"].append(pariente)
                else:
                    modfam["adultosconysin"].append(pariente)

    def buscar_principales_por_pagador(parientes):
        principales = set()
        pagadores = {}
        for pariente in parientes:
            try:
                pid = int(pariente)
            except (TypeError, ValueError):
                continue
            socio = socios_by_id.get(pid)
            if not socio:
                continue
            titular = (socio.get("titularPagador") or "").strip().upper()
            nif = (socio.get("nifPagador") or "").strip().upper()
            if titular:
                pagadores.setdefault(titular, []).append(pid)
            if nif:
                pagadores.setdefault(nif, []).append(pid)
        for pagador in pagadores:
            for pid, socio in socios_by_id.items():
                titular = (socio.get("titularPagador") or "").strip().upper()
                nif = (socio.get("nifPagador") or "").strip().upper()
                if titular == pagador or nif == pagador:
                    cats = common.getcategoriassocio(socio)
                    if (
                        common.categorias["socioactividades"] in cats
                        and common.categorias["sociohermanoactividades"] not in cats
                    ):
                        principales.add(pid)
        return sorted(principales)

    def reportar_errores(familia, parientes, modfam):
        implicit_principals = buscar_principales_por_pagador(parientes)
        modfam["socioactividades"].extend(
            [p for p in implicit_principals if p not in modfam["socioactividades"]]
        )
        if len(modfam["sociohermanoactividades"]) > 0:
            if not modfam["socioactividades"]:
                print(
                    f"ERROR TOODESC: Familia {familia} tiene {len(parientes)} miembros, "
                    f"{len(modfam['socioactividades'])} actividad, {len(modfam['sociosinactividades'])} sin actividad, "
                    f"{len(modfam['sociohermanoactividades'])} hermanos {modfam['sociohermanoactividades']}, "
                    f"{len(modfam['adultosconysin'])} adultos: {common.sociobase}{familia}#tab=CATEGORIES"
                )
                for sid in modfam["sociohermanoactividades"]:
                    socio = socios_by_id.get(int(sid))
                    cats = common.getcategoriassocio(socio) if socio else []
                    print(f"  Hermano {sid}: categorias={cats}")
                if implicit_principals:
                    print(
                        f"  Posibles principales por titular/NIF: {implicit_principals}"
                    )
                print("DISTRIBUCION", modfam)
            if len(modfam["socioactividades"]) > 1:
                print(
                    f"ERROR LOWDESC: Familia {familia} tiene {len(parientes)} miembros, "
                    f"{len(modfam['socioactividades'])} actividad, {len(modfam['sociosinactividades'])} sin actividad, "
                    f"{len(modfam['sociohermanoactividades'])} hermanos {modfam['sociohermanoactividades']}, "
                    f"{len(modfam['adultosconysin'])} adultos: {common.sociobase}{familia}#tab=CATEGORIES"
                )
                print("DISTRIBUCION", modfam)

    for familia in sorted(set(familias["miembros"])):
        parientes = list(familias["miembros"][familia])
        parientes.append(familia)

        modfam = {
            "adultosconysin": [],
            "sociohermanoactividades": [],
            "socioactividades": [],
            "sociosinactividades": [],
            "baja": [],
        }

        familia_int = int(familia)
        if familia_int in procesados:
            continue
        procesados.update(int(p) for p in parientes)
        procesar_parientes(parientes, modfam)
        reportar_errores(familia, parientes, modfam)


def listado_capfamilia():
    print("Loading file from disk")
    socios = common.readjson(filename="socios")

    print("Procesando socios...")

    for socio in socios:
        if int(socio["isBancCapFamilia"]) != 0:
            if common.validasocio(
                socio,
                estado="COLESTVAL",
                estatcolegiat="ESTALTA",
                agrupaciones=["PREINSCRIPCIÓN"],
                reverseagrupaciones=True,
            ):
                socioid = socio["idColegiat"]
                url = f"{common.sociobase}{socioid}#tab=ACTIVITATS"
                print(url)


def listado_tutores():
    print("Loading file from disk")
    socios = common.readjson(filename="socios")

    print("Procesando socios...")

    resultids = {
        "activ": [],
        "adult": [],
        "adultactiv": [],
        "adultsinactiv": [],
        "invalid": [],
        "kids-and-parents": [],
        "kids": [],
        "kidsactiv-and-parents": [],
        "kidsactiv": [],
        "kidsinactiv-and-parents": [],
        "kidsinactiv": [],
        "preinscripcion": [],
        "profesores": [],
        "sociohermano": [],
        "teen13-and-parents": [],
        "teen13": [],
        "teen15-and-parents": [],
        "teen15": [],
        "teen18-and-parents": [],
        "teen18": [],
        "tutor": [],
        "valid": [],
    }

    for socio in socios:
        carnetssocio = []
        if common.validasocio(
            socio,
            estado="COLESTVAL",
            estatcolegiat="ESTALTA",
        ):
            userid = socio["idColegiat"]
            if "colegiatHasModalitats" in socio:
                for modalitat in socio["colegiatHasModalitats"]:
                    if "modalitat" in modalitat:
                        agrupacionom = modalitat["modalitat"]["agrupacio"][
                            "nom"
                        ].lower()

                        if "Socio Adulto Actividades".lower() in agrupacionom:
                            resultids["activ"].append(userid)

                        if "Socio Actividades".lower() in agrupacionom:
                            resultids["activ"].append(userid)

            if userid in resultids["activ"]:
                for field in ["tutor1", "tutor2"]:
                    if field in socio:
                        if socio[field]:
                            if "residencia" in socio[field]:
                                carnetssocio.append(socio[field]["residencia"])
            if carnetssocio != []:
                print(
                    socio["idColegiat"],
                    ",",
                    socio["numColegiat"],
                    socio["persona"]["nom"],
                    socio["persona"]["cognoms"],
                    ",",
                    socio["persona"]["residencia"],
                    ",",
                    carnetssocio,
                )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: 3-listado-socios.py [actividad-familia|capfamilia|tutores]")
        sys.exit(1)

    modo = sys.argv[1].lower()

    if modo == "actividad-familia":
        listado_actividad_familia()
    elif modo == "capfamilia":
        listado_capfamilia()
    elif modo == "tutores":
        listado_tutores()
    else:
        print(f"Modo no reconocido: {modo}")
        print("Modos disponibles: actividad-familia, capfamilia, tutores")
        sys.exit(1)
