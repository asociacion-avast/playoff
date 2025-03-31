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


idActivitat = False
idColegiat = False
if len(sys.argv) > 2:
    try:
        idActivitat = int(sys.argv[1])
    except Exception:
        idActivitat = False
    try:
        idColegiat = int(sys.argv[2])
    except Exception:
        idColegiat = False


if not idActivitat:
    print("Actividad no indicada")
    print("inscribeactividad.py idActivitat idColegiat")
    sys.exit(-1)

if not idColegiat:
    print("Colegiat no indicado")
    print("inscribeactividad.py idActivitat idColegiat")
    sys.exit(-1)


print(f"Procesando actividad: {idActivitat}")

print(
    common.create_inscripcio(
        token=token, idActivitat=idActivitat, idColegiat=idColegiat
    ).text
)
