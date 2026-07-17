#!/usr/bin/env python

import configparser
import os

import requests

import common
import sync_store

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


def download_socios():
    token = common.gettoken()

    socios = []
    tanda = -1
    page = -1
    pagesize = 100

    while tanda == -1 or len(tanda) >= pagesize:
        page += 1
        print(f"Obteniendo listado de socios, page: {page}")
        sociosurl = f"{common.apiurl}/colegiats?page={page}&pageSize={pagesize}"
        result = requests.get(
            sociosurl, auth=common.BearerAuth(token), headers=common.headers, timeout=15
        )

        try:
            tanda = result.json()
        except Exception:
            tanda = []
        socios.extend(tanda)

    print(f"Saving socios.json to disk ({len(socios)} records)", flush=True)
    common.writejson(filename="socios", data=socios)
    print("Saving per-entity cache", flush=True)
    sync_store.split_entities_from_snapshot("colegiat", socios, "idColegiat")

    validids = []
    invalidids = []

    print("Procesando socios")
    for socio in socios:
        if isinstance(socio.get("campsDinamics"), dict):
            for field in common.telegramfields:
                if field in socio["campsDinamics"]:
                    if socio.get("_valid_alta", False):
                        validids.append(f"{socio['campsDinamics'][field]}")
                    else:
                        invalidids.append(f"{socio['campsDinamics'][field]}")

    print("Valid ID's")
    print(sorted(set(validids)))
    print("Invalid ID's")
    print(sorted(set(invalidids)))
    print(f"Total socios: {len(socios)}")


def download_categorias():
    token = common.gettoken()
    categoriasurl = f"{common.apiurl}/modalitats"

    print("Obteniendo listado de categorias")
    result = requests.get(
        categoriasurl, auth=common.BearerAuth(token), headers=common.headers, timeout=15
    )

    categorias = result.json()

    print("Saving file to disk")
    common.writejson(filename="categorias", data=categorias)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        mode = "all"

    if mode in ("socios", "all"):
        download_socios()
    if mode in ("categorias", "all"):
        download_categorias()
