#!/usr/bin/env python


import configparser
import os
import sys

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)


comurl = f"{common.apiurl}/comunicats/emails_notificacions"
headers = {"Authorization": f"Bearer {token}"}


if len(sys.argv) < 2:
    print("Missing argument: idAssociat for sending the message")
    sys.exit(-1)

socios = common.readjson(filename="socios")
socios_por_id = {
    int(socio["idColegiat"]): socio
    for socio in socios
    if "idColegiat" in socio and socio.get("idColegiat") is not None
}

for arg in sys.argv[1:]:
    try:
        associat = int(arg)
    except ValueError:
        print(f"Invalid idAssociat: {arg}")
        continue

    socio = socios_por_id.get(associat)
    if not socio:
        print(f"No se encontró el socio {associat}; se omite")
        continue
    if not common.es_socio_anual_activo(socio):
        print(
            f"Se omite idAssociat={associat}: no tiene la categoría de socio anual activa"
        )
        continue

    # Si el socio ya tiene vinculado su Telegram ID, no reenviamos.
    camps = socio.get("campsDinamics", {}) or {}
    if camps.get(common.socioid):
        print(
            f"Se omite idAssociat={associat}: ya tiene Telegram ID de socio vinculado"
        )
        continue

    enlace = common.enlace_vinculacion_telegram(associat, tipo="socio")

    print(f"Enviando comunicado de vinculación para idAssociat={associat}")
    print(f"Enlace de vinculación: {enlace}")
    response = common.enviacomunicado(
        token=token, data=common.getcomunicadosocio(associat, enlace=enlace)
    )
    print(response)
    print(response.text)
