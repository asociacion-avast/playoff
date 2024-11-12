#!/usr/bin/env python


import requests

import common

token = common.gettoken()
print("Loading file from disk")


actividades = common.readjson(filename="actividades")


print("Procesando actividades...")

for actividad in actividades:
    myid = actividad["idActivitat"]
    nombre = actividad["nom"]

    print(myid, nombre)

    # get users
    usersurl = (
        "https://asociacionavast.playoffinformatica.com/api.php/api/v1.0/inscripcions?idActivitat=%s"
        % myid
    )

    # result = requests.get(sociosurl, auth=BearerAuth(token), headers=headers)
    users = requests.get(
        usersurl, auth=common.BearerAuth(token), headers=common.headers
    ).json()

    common.writejson(filename="%s" % myid, data=users)
