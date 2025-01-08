#!/usr/bin/env python


import configparser
import os

import requests

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken()

sociosurl = f"{common.apiurl}/colegiats?page=0&pageSize=4000"
data = {"Authorization": f"Bearer {token}"}


# name of the field in PlayOff
tutor1 = "0_13_20231012041710"
tutor2 = "0_14_20231012045321"
socioid = "0_16_20241120130245"

fields = [tutor1, tutor2, socioid]


print("Obteniendo listado de socios")
result = requests.get(sociosurl, auth=common.BearerAuth(token), headers=common.headers)

socios = result.json()

validids = []
invalidids = []

print("Procesando socios")
for socio in socios:
    if isinstance(socio["campsDinamics"], dict):
        for field in fields:
            if field in socio["campsDinamics"]:
                if (
                    "estat" in socio
                    and socio["estat"] == "COLESTVAL"
                    and "estatColegiat" in socio
                    and socio["estatColegiat"]["nom"] == "ESTALTA"
                ):
                    validids.append(f'{socio["campsDinamics"][field]}')
                else:
                    invalidids.append(f'{socio["campsDinamics"][field]}')


print("Saving file to disk")

common.writejson(filename="socios", data=socios)

print("Valid ID's")
print(sorted(set(validids)))
print("Invalid ID's")
print(sorted(set(invalidids)))
