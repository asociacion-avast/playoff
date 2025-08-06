#!/usr/bin/env python


import configparser
import os

import requests

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken()

categoriasurl = f"{common.apiurl}/modalitats"
data = {"Authorization": f"Bearer {token}"}

print("Obteniendo listado de categorias")
result = requests.get(
    categoriasurl, auth=common.BearerAuth(token), headers=common.headers, timeout=15
)

categorias = result.json()

validids = []
invalidids = []

print("Saving file to disk")

common.writejson(filename="categorias", data=categorias)
