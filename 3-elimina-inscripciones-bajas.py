#!/usr/bin/env python


import configparser
import os

import requests

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


print("Loading file from disk")

actividades = common.readjson(filename="actividades")
socios = common.readjson(filename="socios")


print("Procesando actividades...")

usuariosyactividad = {}
actividadyusuarios = {}
usuariosyhorarios = {}
usuarioseinscripciones = {}
usuariosyhorariosinscripciones = {}


sociosbaja = []


for socio in socios:
    if (
        "estat" in socio
        and socio["estat"] == "COLESTVAL"
        and "estatColegiat" in socio
        and socio["estatColegiat"]["nom"] == "ESTBAIXA"
    ):
        sociosbaja.append(socio["idColegiat"])


for actividad in actividades:
    myid = actividad["idActivitat"]
    nombre = actividad["nom"]
    horario = int(actividad["idNivell"])

    if horario in {7, 8, 9, 10}:
        inscritos = common.readjson(filename=f"{myid}")

        actividadyusuarios[myid] = []

        for inscrito in inscritos:
            colegiat = inscrito["colegiat"]["idColegiat"]

            if colegiat == "594":
                print("hola")

            if colegiat in sociosbaja:
                actividadyusuarios[myid].append(colegiat)
                inscripcion = inscrito["idInscripcio"]

                if inscrito["estat"] == "INSCRESTNOVA":
                    if colegiat not in usuariosyactividad:
                        usuariosyactividad[colegiat] = []

                    if colegiat not in usuariosyhorarios:
                        usuariosyhorarios[colegiat] = []

                    if colegiat not in usuariosyhorariosinscripciones:
                        usuariosyhorariosinscripciones[colegiat] = {}

                    if horario not in usuariosyhorariosinscripciones[colegiat]:
                        usuariosyhorariosinscripciones[colegiat][horario] = []

                    if colegiat not in usuarioseinscripciones:
                        usuarioseinscripciones[colegiat] = []

                    usuariosyactividad[colegiat].append(myid)
                    usuariosyhorarios[colegiat].append(horario)
                    usuariosyhorariosinscripciones[colegiat][horario].append(
                        inscripcion
                    )
                    usuarioseinscripciones[colegiat].append(inscripcion)


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)


print(sociosbaja)


inscripcionesanuladas = []

for usuario, value in usuariosyhorarios.items():
    # El usuaro tiene horarios duplicados

    # calcular horarios a borrar y verlos en las inscripciones

    url = f"https://asociacionavast.playoffinformatica.com/FormAssociat.php?idColegiat={usuario}#tab=ACTIVITATS"
    print("\nUsuario: %s" % url)
    print(
        f"Inscripciones usuario y horarios: {usuariosyhorariosinscripciones[usuario]}"
    )

    for horario in usuariosyhorariosinscripciones[usuario]:
        for inscripcion in usuariosyhorariosinscripciones[usuario][horario]:
            # Rellena variable para luego sacar el nombre
            inscripcionesanuladas.append(inscripcion)

            print("Anulando")
            url = f"{common.apiurl}/inscripcions/{inscripcion}/anular"
            response = requests.patch(
                url, headers=common.headers, auth=common.BearerAuth(token)
            )
            print(response)

            print("Comunicando")
            url = f"{common.apiurl}/inscripcions/{inscripcion}/comunicar_anulacio"
            response = requests.post(
                url, headers=common.headers, auth=common.BearerAuth(token)
            )
            print(response)

print(
    "\nInscripciones anuladas en los siguientes talleres por inscripciones a la misma hora:"
)

for actividad in actividades:
    myid = actividad["idActivitat"]
    nombre = actividad["nom"]
    horario = actividad["idNivell"]

    inscritos = common.readjson(filename=f"{myid}")

    for inscrito in inscritos:
        inscripcion = inscrito["idInscripcio"]
        if inscripcion in inscripcionesanuladas:
            print(nombre)
