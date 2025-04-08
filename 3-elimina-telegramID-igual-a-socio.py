#!/usr/bin/env python


import configparser
import os

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
    numcolegiat = socio["numColegiat"]
    idcolegiat = socio["idColegiat"]
    if isinstance(socio["campsDinamics"], dict):
        if common.socioid in socio["campsDinamics"]:
            for field in [common.tutor1, common.tutor2, common.socioid]:
                if field in socio["campsDinamics"]:
                    if numcolegiat == socio["campsDinamics"][field]:
                        print(f"{count:04} {common.sociobase}{idcolegiat}")

                        response = common.escribecampo(token, idcolegiat, field, "")
                        print(response)
