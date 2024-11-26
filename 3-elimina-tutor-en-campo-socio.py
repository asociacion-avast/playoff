#!/usr/bin/env python


import configparser
import os

import requests

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


idtutor1 = "0_13_20231012041710"
idtutor2 = "0_14_20231012045321"
idsocios = "0_16_20241120130245"


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
        if idsocios in socio["campsDinamics"]:
            mysocio = socio["campsDinamics"][idsocios]
            for field in [idtutor1, idtutor2]:
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

    data = {f"{idsocios}": ""}

    files = []
    response = requests.request("PUT", comurl, headers=headers, data=data, files=files)

    print(response)
