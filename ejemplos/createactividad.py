#!/usr/bin/env python

import configparser
import json
import os
import pprint

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)


data = {"Authorization": f"Bearer {token}"}


print("Haciendo llamada API")

nom = "Gamusino Gamusinete"
lloc = "Talqueaquí"
maxplaces = 50
minplaces = 10
dataHoraActivitat = "2026-01-01"
dataHoraFiActivitat = "2026-12-31"
dataInici = "0005-01-01"
dataLimit = "2025-12-31"
descripcio = "<p>Akinoest&aacute;n</p>"
horario = 8


response = common.createactividad(
    token,
    nom,
    lloc,
    maxplaces,
    minplaces,
    dataHoraActivitat,
    dataHoraFiActivitat,
    dataInici,
    dataLimit,
    descripcio,
    horario,
)
pprint.pprint(json.loads(response.text))
