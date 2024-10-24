#!/usr/bin/env python


import configparser
import os

import requests

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


print("Loading file from disk")

actividades = common.rewadjson(filename="actividades")


print("Procesando actividades...")

usuariosyactividad = {}
actividadyusuarios = {}
usuariosyhorarios = {}
usuarioseinscripciones = {}
usuariosyhorariosinscripciones = {}

for actividad in actividades:
    myid = actividad["idActivitat"]
    nombre = actividad["nom"]
    horario = int(actividad["idNivell"])

    if horario in [7, 8, 9, 10]:
        users = common.rewadjson(filename="%s" % myid)
        inscritos = common.rewadjson(filename="%s" % myid)

        actividadyusuarios[myid] = []

        for inscrito in inscritos:
            colegiat = inscrito["colegiat"]["idColegiat"]
            actividadyusuarios[myid].append(colegiat)
            inscripcion = inscrito["idInscripcio"]

            if inscrito["estat"] != "INSCRESTANULADA":
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
                usuariosyhorariosinscripciones[colegiat][horario].append(inscripcion)
                usuarioseinscripciones[colegiat].append(inscripcion)


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)

inscripcionesanuladas = []

for usuario in usuariosyhorarios:
    # El usuaro tiene horarios duplicados
    if len(usuariosyhorarios[usuario]) != len(sorted(set(usuariosyhorarios[usuario]))):
        # calcular horarios a borrar y verlos en las inscripciones

        url = (
            "https://asociacionavast.playoffinformatica.com/FormAssociat.php?idColegiat=%s#tab=ACTIVITATS"
            % usuario
        )
        print("\nUsuario: %s" % url)
        print(
            "Inscripciones usuario y horarios: %s"
            % usuariosyhorariosinscripciones[usuario]
        )

        for horario in usuariosyhorariosinscripciones[usuario]:
            if len(usuariosyhorariosinscripciones[usuario][horario]) > 1:
                print(horario)
                print(usuariosyhorariosinscripciones[usuario][horario])

                for inscripcion in usuariosyhorariosinscripciones[usuario][horario]:
                    # Rellena variable para luego sacar el nombre
                    inscripcionesanuladas.append(inscripcion)

                    print("Anulando")
                    url = common.apiurl + "/inscripcions/%s/anular" % inscripcion
                    response = requests.patch(
                        url, headers=common.headers, auth=common.BearerAuth(token)
                    )
                    print(response)

                    print("Comunicando")
                    url = (
                        common.apiurl
                        + "/inscripcions/%s/comunicar_anulacio" % inscripcion
                    )
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

    inscritos = common.rewadjson(filename="%s" % myid)

    for inscrito in inscritos:
        inscripcion = inscrito["idInscripcio"]
        if inscripcion in inscripcionesanuladas:
            print(nombre)
