#!/usr/bin/env python


import configparser
import os

import requests

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken()
data = {"Authorization": f"Bearer {token}"}

socios = []
tanda = -1
page = -1

pagesize = 100

while tanda == -1 or len(tanda) >= pagesize:
    page += 1
    print("Obteniendo listado de socios, page: %s" % page)
    sociosurl = f"{common.apiurl}/colegiats?page={page}&pageSize={pagesize}"
    result = requests.get(
        sociosurl, auth=common.BearerAuth(token), headers=common.headers, timeout=15
    )

    try:
        tanda = result.json()
    except:
        tanda = []
    socios.extend(tanda)

print("Saving file to disk")
common.writejson(filename="socios", data=socios)


validids = []
invalidids = []

print("Procesando socios")
for socio in socios:
    if isinstance(socio["campsDinamics"], dict):
        for field in common.telegramfields:
            if field in socio["campsDinamics"]:
                if common.validasocio(
                    socio,
                    estado="COLESTVAL",
                    estatcolegiat="ESTALTA",
                    agrupaciones=["PREINSCRIPCIÓN"],
                    reverseagrupaciones=True,
                ):
                    validids.append(f"{socio['campsDinamics'][field]}")
                else:
                    invalidids.append(f"{socio['campsDinamics'][field]}")


print("Valid ID's")
print(sorted(set(validids)))
print("Invalid ID's")
print(sorted(set(invalidids)))
print("Total socios: %s" % len(socios))
