#!/usr/bin/env python


import configparser
import os

import requests

import common
import sync_store

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

print("Saving socios.json to disk (%s records)" % len(socios), flush=True)
common.writejson(filename="socios", data=socios)
print("Saving per-entity cache", flush=True)
sync_store.split_entities_from_snapshot("colegiat", socios, "idColegiat")


validids = []
invalidids = []

print("Procesando socios")
for socio in socios:
    if isinstance(socio["campsDinamics"], dict):
        for field in common.telegramfields:
            if field in socio["campsDinamics"]:
                # OPTIMIZATION Phase 2C: Use pre-computed validation
                if socio.get("_valid_alta", False):
                    validids.append(f"{socio['campsDinamics'][field]}")
                else:
                    invalidids.append(f"{socio['campsDinamics'][field]}")


print("Valid ID's")
print(sorted(set(validids)))
print("Invalid ID's")
print(sorted(set(invalidids)))
print("Total socios: %s" % len(socios))
