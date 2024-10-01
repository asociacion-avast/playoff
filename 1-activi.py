#!/usr/bin/env python


import requests

import common

token = common.gettoken()

activurl = common.apiurl + "/activitats/totes"
data = {"Authorization": "Bearer %s" % token}

print("Obteniendo listado de actividades")
result = requests.get(activurl, auth=common.BearerAuth(token), headers=common.headers)

actividades = result.json()

print("Saving file to disk")
common.writejson(filename="actividades", data=actividades)
