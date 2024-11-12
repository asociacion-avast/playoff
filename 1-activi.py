#!/usr/bin/env python


import requests

import common

token = common.gettoken()

activar = common.apiurl + "/activitats/totes"
data = {"Authorization": f"Bearer {token}"}

print("Obteniendo listado de actividades")
result = requests.get(activar, auth=common.BearerAuth(token), headers=common.headers)

actividades = result.json()

print("Saving file to disk")
common.writejson(filename="actividades", data=actividades)
