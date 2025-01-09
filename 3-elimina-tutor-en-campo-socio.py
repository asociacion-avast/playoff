#!/usr/bin/env python


import configparser
import os

import requests

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


socios = common.readjson("socios")


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)
headers = {"Authorization": f"Bearer {token}"}


print("Procesando socios")
count = 0

idsociotoclean = []

for socio in socios:
    if isinstance(socio["campsDinamics"], dict):
        if common.socioid in socio["campsDinamics"]:
            mysocio = socio["campsDinamics"][common.socioid]
            for field in [common.tutor1, common.tutor2]:
                if field in socio["campsDinamics"]:
                    if mysocio == socio["campsDinamics"][field]:
                        idsociotoclean.append(socio["idColegiat"])

for idcolegiat in sorted(set(idsociotoclean)):
    count = count + 1
    print(
        "%s https://asociacionavast.playoffinformatica.com/FormAssociat.php?idColegiat=%s"
        % (f"{count:04}", idcolegiat)
    )

    comurl = f"{common.apiurl}/colegiats/{idcolegiat}/campsdinamics"

    data = {f"{common.socioid}": ""}

    files = []
    response = requests.request("PUT", comurl, headers=headers, data=data, files=files)

    print(response)
