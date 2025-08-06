#!/usr/bin/env python


import datetime
import json
import os

import dateutil.parser
import requests

user = os.environ.get("PLAYOFFUSERRO")
password = os.environ.get("PLAYOFFPASSRO")
apiurl = os.environ.get("PLAYOFFAPIURL")
headers = {"Content-Type": "application/json", "content-encoding": "gzip"}
today = datetime.datetime.now()


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

    result = requests.post(loginurl, data=json.dumps(data), headers=headers, timeout=15)

    return result.json()["access_token"]


token = gettoken(user=user, password=password)

activar = f"{apiurl}/activitats/totes"
data = {"Authorization": f"Bearer {token}"}

result = requests.get(activar, auth=BearerAuth(token), headers=headers, timeout=15)

actividades = result.json()


anyo = False


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
print("<HTML>")
print("<h1>Actividades</h1>")
print("<h2>Generado el %s</h2>" % today.strftime("%d/%m/%Y %H:%M"))
print("<table border='1'>")
print(
    "<tr><th>ID</th><th>NOMBRE</th><th>LIBRES</th><th>HORA</th><th>AÑO INICIO</th><th>AÑO FIN</th></tr>"
)

for actividad in actividades:
    myid = actividad["idActivitat"]
    nombre = actividad["nom"]
    fechalimite = dateutil.parser.parse(actividad["dataLimit"])

    if fechalimite < today:
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
                        f"<tr><td>{myid}</td><td>{nombre}</td><td>{libres}</td><td>{horarios[horario]}</td><td>{anyoinicio}</td><td>{anyofin}</td></tr>"
                    )
                elif not anyo:
                    print(
                        f"<tr><td>{myid}</td><td>{nombre}</td><td>{libres}</td><td>{horarios[horario]}</td><td>{anyoinicio}</td><td>{anyofin}</td></tr>"
                    )

print("</table>")
print("</HTML>")
