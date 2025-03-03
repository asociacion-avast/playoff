#!/usr/bin/env python

import configparser
import json
import os

import dateutil.parser
import requests

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))

# Telegramfields
tutor1 = "0_13_20231012041710"
tutor2 = "0_14_20231012045321"
socioid = "0_16_20241120130245"
telegramfields = [tutor1, tutor2, socioid]
fechacambio = "0_17_20250221121130"


apiurl = f"https://{config['auth']['endpoint']}.playoffinformatica.com/api.php/api/v1.0"
headers = {"Content-Type": "application/json", "content-encoding": "gzip"}

endpoint = config["auth"]["endpoint"]


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = f"Bearer {self.token}"
        return r


def gettoken(user=config["auth"]["username"], password=config["auth"]["password"]):
    # get token

    loginurl = f"{apiurl}/login/colegi"

    data = {"username": user, "password": password}

    result = requests.post(loginurl, data=json.dumps(data), headers=headers)

    return result.json()["access_token"]


def writejson(filename, data):
    with open(f"data/{filename}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        return True


def readjson(filename):
    with open(f"data/{filename}.json", "r", encoding="utf-8") as f:
        return json.load(f)


def addcategoria(token, socio, categoria, extra=False):
    """Adds categoria to socio

    Args:
        extra:
        token (str): token for accessing API (RW)
        socio (int): Socio identifier
        categoria (int): ID for category to modify
    """

    headers = {"Authorization": f"Bearer {token}"}
    categoriaurl = f"{apiurl}/colegiats/{socio}/modalitats"

    data = {"idModalitat": categoria}

    if extra:
        data.update(extra)
    files = []

    return requests.request(
        "POST", categoriaurl, headers=headers, data=data, files=files
    )


def delcategoria(token, socio, categoria):
    """Removes categoria from socio

    Args:
        token (str): token for accessing API (RW)
        socio (int): Socio identifier
        categoria (int): ID for category to modify
    """

    headers = {"Authorization": f"Bearer {token}"}
    categoriaurl = f"{apiurl}/colegiats/{socio}/modalitats/{categoria}"

    data = {}
    files = []

    return requests.request(
        "DELETE", categoriaurl, headers=headers, data=data, files=files
    )


def escribecampo(token, socioid, campo, valor=""):
    """Escribe campo personalizado de socio

    Args:
        token (_type_): Token para operaciones
        socioid (_type_): idAssociat
        campo (_type_): Campo personalizado
        valor (_type_): Valor a establecer o vacío para borrar

    Returns:
        _type_: _description_
    """

    comurl = f"{apiurl}/colegiats/{socioid}/campsdinamics"

    headers = {"Authorization": f"Bearer {token}"}
    data = {f"{campo}": f"{valor}"}

    files = []
    return requests.request("PUT", comurl, headers=headers, data=data, files=files)


def calcular_proximo_recibo(fecha):
    """_summary_

    Args:
        fecha (datetime): Fecha for today

    Returns:
        str: fecha
    """
    meses_cobro = sorted(
        {9, 11, 1, 3, 5}
    )  # Meses de cobro (septiembre, noviembre, enero, marzo, mayo)

    fecha = dateutil.parser.parse(fecha)
    dia = fecha.day
    mes = fecha.month
    año = fecha.year

    if dia < 5:
        dia_cobro = 5
        if mes in meses_cobro:
            return f"{dia_cobro:0d2}/{mes:02d}/{año}"
        else:
            mes_cobro = next((m for m in meses_cobro if m > mes), None)
            if mes_cobro is None:
                mes_cobro = meses_cobro[0]
                año += 1
            return f"{dia_cobro:02d}/{mes_cobro:02d}/{año}"
    else:
        mes_cobro = next((m for m in meses_cobro if m > mes), None)
        if mes_cobro is None:
            mes_cobro = meses_cobro[0]
            año += 1
        return f"05/{mes_cobro:02d}/{año}"


def validasocio(
    socio,
    estado="COLESTVAL",
    estatcolegiat="ESTALTA",
    agrupaciones=[],
    subcategorias=[],
    reverseagrupaciones=False,
    reversesubcategorias=False,
):
    """Validates if socio is active

    Args:
        estatcolegiat:
        agrupaciones:
        subcategorias:
        reverseagrupaciones:
        reversesubcategorias:
        estado:
        socio (dict): Dictionary representing a socio

    Returns:
        bool: True or False is an active socio
    """
    if (
        "estat" in socio
        and socio["estat"] == estado
        and "estatColegiat" in socio
        and socio["estatColegiat"]["nom"] == estatcolegiat
    ):
        if not agrupaciones and not subcategorias:
            return True
        else:
            if "colegiatHasModalitats" in socio:
                # Iterate over all categories for the user
                for modalitat in socio["colegiatHasModalitats"]:
                    if "modalitat" in modalitat:
                        # Save name for comparing the ones we target
                        agrupacionom = modalitat["modalitat"]["agrupacio"][
                            "nom"
                        ].lower()
                        modalitatnom = modalitat["modalitat"]["nom"].lower()

                        if agrupaciones:
                            if not reverseagrupaciones:
                                rc = False
                                for agrupacion in agrupaciones:
                                    if agrupacionom == agrupacion.lower():
                                        rc = True
                                return rc
                            else:
                                rc = True
                                for agrupacion in agrupaciones:
                                    if agrupacionom == agrupacion.lower():
                                        rc = False
                                return rc
                        if subcategorias:
                            if not reversesubcategorias:
                                rc = False
                                for categoria in subcategorias:
                                    if modalitatnom == categoria.lower():
                                        rc = True
                                return rc
                            else:
                                rc = True
                                for categoria in subcategorias:
                                    if modalitatnom == categoria.lower():
                                        rc = False
                                return rc

    return False
