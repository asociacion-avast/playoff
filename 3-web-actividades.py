#!/usr/bin/env python


import json
import os

import requests

user = os.environ.get("PLAYOFFUSERRO")
password = os.environ.get("PLAYOFFPASSRO")
apiurl = os.environ.get("PLAYOFFAPIURL")
headers = {"Content-Type": "application/json", "content-encoding": "gzip"}


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = f"Bearer {self.token}"
        return r


def gettoken(user=user, password=password):
    # get token

    loginurl = f"{apiurl}/login/colegi"

    data = {"username": user, "password": password}

    result = requests.post(loginurl, data=json.dumps(data), headers=headers)

    return result.json()["access_token"]


token = gettoken(user=user, password=password)

activar = f"{apiurl}/activitats/totes"
data = {"Authorization": f"Bearer {token}"}

print("Obteniendo listado de actividades")
result = requests.get(activar, auth=BearerAuth(token), headers=headers)

actividades = result.json()


anyo = False

print("Procesando actividades...")

usuariosyactividad = {}
actividadyusuarios = {}
usuariosyhorarios = {}

horarios = {
    7: "11:30",
    8: "09:00",
    9: "10:00",
    10: "12:30",
    19: "",
    20: "",
    21: "",
    22: "",
}

print("ID,NOMBRE,PLAZAS,USADAS,LIBRES,HORA,AÑO INICIO,AÑO FIN")
for actividad in actividades:
    myid = actividad["idActivitat"]
    nombre = actividad["nom"]
    if actividad["idNivell"] and actividad["idNivell"] != "null":
        horario = int(actividad["idNivell"])
    else:
        horario = 0

    try:
        anyoinicio = int(actividad["edatMin"])
        anyofin = int(actividad["edatMax"])
    except Exception:
        anyoinicio = 0
        anyofin = 0

    if horario in {7, 8, 9, 10, 19, 20, 21, 22}:
        usadas = int(actividad["numInscripcions"])
        libres = int(actividad["maxPlaces"]) - usadas
        if libres > 0:
            if anyo and anyoinicio <= anyo <= anyofin:
                print(
                    f"{myid},{nombre},{int(actividad['maxPlaces'])},{usadas},{libres},{horarios[horario]},{anyoinicio},{anyofin}"
                )
            elif not anyo:
                print(
                    f"{myid},{nombre},{int(actividad['maxPlaces'])},{usadas},{libres},{horarios[horario]},{anyoinicio},{anyofin}"
                )
