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

if len(sys.argv) < 2:
    print("Missing argument: idAssociat for sending the message")
    sys.exit(-1)

socios = common.readjson(filename="socios")
socios_por_id = {
    int(socio["idColegiat"]): socio
    for socio in socios
    if "idColegiat" in socio and socio.get("idColegiat") is not None
}

familias = common.readjson(filename="familias") or {"miembros": {}}

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

    camps = socio.get("campsDinamics", {}) or {}

    missing_tutor = []
    if not camps.get(common.tutor1):
        missing_tutor.append("tutor1")
    if not camps.get(common.tutor2):
        missing_tutor.append("tutor2")

    missing_socio = not camps.get(common.socioid)

    copied = common.copy_missing_telegram_from_family(associat, socios, familias)
    if copied:
        common.writejson(filename="socios", data=socios)
        for campo, valor, fid in copied:
            nombre = common.nombre_campo_telegram(campo)
            print(f"Copiado {nombre} del socio familiar {fid} al socio {associat}")
            common.escribecampo(token, associat, campo, valor)
        continue

    if missing_tutor:
        tipo = missing_tutor[0]
        enlace = common.enlace_vinculacion_telegram(associat, tipo=tipo)
        print(f"Enviando comunicado de vinculación para idAssociat={associat} ({tipo})")
        print(f"Enlace de vinculación: {enlace}")
        response = common.enviacomunicado(
            token=token, data=common.getcomunicadotutor(associat, enlace=enlace)
        )
        print(response)
        print(response.text)
        if hasattr(response, "status_code") and response.status_code == 401:
            print(f"Token expirado para {associat} {tipo}, renovando token...")
            token = common.gettoken(
                user=config["auth"]["RWusername"],
                password=config["auth"]["RWpassword"],
                force_refresh=True,
            )
            response = common.enviacomunicado(
                token=token, data=common.getcomunicadotutor(associat, enlace=enlace)
            )
            print(response)
            print(response.text)
        continue

    if missing_socio:
        enlace = common.enlace_vinculacion_telegram(associat, tipo="socio")
        print(f"Enviando comunicado de vinculación para idAssociat={associat} (socio)")
        print(f"Enlace de vinculación: {enlace}")
        response = common.enviacomunicado(
            token=token, data=common.getcomunicadosocio(associat, enlace=enlace)
        )
        print(response)
        print(response.text)
        if hasattr(response, "status_code") and response.status_code == 401:
            print(f"Token expirado para {associat} socio, renovando token...")
            token = common.gettoken(
                user=config["auth"]["RWusername"],
                password=config["auth"]["RWpassword"],
                force_refresh=True,
            )
            response = common.enviacomunicado(
                token=token, data=common.getcomunicadosocio(associat, enlace=enlace)
            )
            print(response)
            print(response.text)
        continue

    print(f"Se omite idAssociat={associat}: ya tiene todos los Telegram ID")
