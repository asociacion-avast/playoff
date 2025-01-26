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
    horario = int(actividad["idNivell"])

    if horario in [7, 8, 9, 10]:
        print(myid, nombre)

        # get users
        usersurl = f"https://{common.endpoint}.playoffinformatica.com/api.php/api/v1.0/inscripcions?idActivitat={myid}"

        # result = requests.get(sociosurl, auth=BearerAuth(token), headers=headers)
        users = requests.get(
            usersurl, auth=common.BearerAuth(token), headers=common.headers
        ).json()

        common.writejson(filename=f"{myid}", data=users)
