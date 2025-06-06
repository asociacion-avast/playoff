#!/usr/bin/env python
import configparser
import datetime
import os

import dateutil.parser

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


print("Loading file from disk")

actividades = common.readjson(filename="actividades")


print("Procesando actividades...")

usuariosyactividad = {}
actividadyusuarios = {}
usuariosyhorarios = {}
usuarioseinscripciones = {}
usuariosyhorariosinscripciones = {}


ahora = datetime.datetime.now()

for actividad in actividades:
    myid = actividad["idActivitat"]
    nombre = actividad["nom"]

    if actividad["idNivell"] and actividad["idNivell"] != "null":
        horario = int(actividad["idNivell"])
    else:
        horario = 0

    if horario in {7, 8, 9, 10, 19, 20, 21, 22}:
        inscritos = common.readjson(filename=f"{myid}")

        actividadyusuarios[myid] = []

        for inscrito in inscritos:
            colegiat = inscrito["colegiat"]["idColegiat"]
            fecha = inscrito["dataIntroduccio"]
            try:
                fecha = dateutil.parser.parse(fecha)

            except Exception:
                fecha = False

            if ahora - fecha > datetime.timedelta(hours=1, minutes=30):
                if inscrito["estat"] == "INSCRESTNOVA":
                    actividadyusuarios[myid].append(colegiat)
                    inscripcion = inscrito["idInscripcio"]

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

inscripcionesanuladas = []

for usuario, value in usuariosyhorarios.items():
    # El usuaro tiene horarios duplicados
    if len(value) != len(sorted(set(usuariosyhorarios[usuario]))):
        # calcular horarios a borrar y verlos en las inscripciones

        url = f"{common.sociobase}{usuario}#tab=ACTIVITATS"
        print("\nUsuario: %s" % url)
        print(
            f"Inscripciones usuario y horarios: {usuariosyhorariosinscripciones[usuario]}"
        )

        for horario in usuariosyhorariosinscripciones[usuario]:
            if len(usuariosyhorariosinscripciones[usuario][horario]) > 1:
                print(horario)
                print(usuariosyhorariosinscripciones[usuario][horario])

                for inscripcion in usuariosyhorariosinscripciones[usuario][horario]:
                    # Rellena variable para luego sacar el nombre
                    inscripcionesanuladas.append(inscripcion)

                    print("Anulando y comunicando")
                    response = common.anula_inscripcio(
                        token, inscripcion=inscripcion, comunica=True
                    )
                    print(response)

print(
    "\nInscripciones anuladas en los siguientes talleres por inscripciones a la misma hora:"
)

for actividad in actividades:
    myid = actividad["idActivitat"]
    nombre = actividad["nom"]

    if actividad["idNivell"] and actividad["idNivell"] != "null":
        horario = int(actividad["idNivell"])
    else:
        horario = 0

    if horario in {7, 8, 9, 10, 19, 20, 21, 22}:
        inscritos = common.readjson(filename=f"{myid}")

        for inscrito in inscritos:
            inscripcion = inscrito["idInscripcio"]
            if inscripcion in inscripcionesanuladas:
                print(nombre)
