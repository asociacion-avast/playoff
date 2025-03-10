#!/usr/bin/env python


import configparser
import os

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


resultids = {
    "activ": [],  # Con actividades
    "adult": [],  # Adultos
    "adultactiv": [],  # Adultos con actividades
    "adultsinactiv": [],  # Adultos sin actividades
    "invalid": [],  # Socios sin ALTA activa
    "kids-and-parents": [],  # Niños y tutores
    "kids": [],  # Niños (CON y SIN)
    "kidsactiv-and-parents": [],  # Niños CON Actividades y tutores
    "kidsactiv": [],  # Niños CON Actividades
    "kidsinactiv-and-parents": [],  # Niños SIN Actividades y tutores
    "kidsinactiv": [],  # Niños SIN actividades
    "profesores": [],  # Profesores
    "teen13-and-parents": [],  # Niños y tutores [13-15)
    "teen13": [],  # Niños [13-15)
    "teen15-and-parents": [],  # Niños y tutores [15-24]
    "teen15": [],  # Niños [15-24]
    "tutor": [],  # Tutores
    "valid": [],  # Cualquiera con relación avast
}


for socio in socios:
    id_socio = socio["idColegiat"]
    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTBAIXA",
    ):
        sociosbaja.append(id_socio)

    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTALTA",
        agrupaciones=["PREINSCRIPCIÓN"],
        reverseagrupaciones=True,
    ) or common.validasocio(
        socio,
        estado="COLESTPRE",
        estatcolegiat="ESTALTA",
    ):
        if "colegiatHasModalitats" in socio:
            # Iterate over all categories for the user
            for modalitat in socio["colegiatHasModalitats"]:
                if "modalitat" in modalitat:
                    # Save name for comparing the ones we target
                    agrupacionom = modalitat["modalitat"]["agrupacio"]["nom"].lower()
                    modalitatnom = modalitat["modalitat"]["nom"].lower()

                    # "activ": [], # Con actividades
                    # "adult": [], # Adultos
                    # "adultactiv": [], # Adultos con actividades
                    # "adultsinactiv": [], # Adultos sin actividades
                    # "invalid": [], # Socios sin ALTA activa
                    # "kid-and-parents": [], # Niños y tutores
                    # "kid": [], # Niños (CON y SIN)
                    # "kidactiv-and-parents": [], # Niños CON Actividades y tutores
                    # "kidactiv": [], # Niños CON Actividades
                    # "kidsinactiv-and-parents": [], # Niños SIN Actividades y tutores
                    # "kidsinactiv": [], # Niños SIN actividades
                    # "profesores": [], # Profesores
                    # "teen13-and-parents": [], # Niños y tutores [13-15)
                    # "teen13": [], # Niños [13-15)
                    # "teen15-and-parents": [], # Niños y tutores [15-24]
                    # "teen15": [], # Niños [15-24]
                    # "tutor": [], # Tutores
                    # "valid": [], # Cualquiera con relación avast

                    if "profesores".lower() in agrupacionom:
                        resultids["profesores"].append(id_socio)

                    if "Socio Adulto Actividades".lower() in agrupacionom:
                        resultids["adult"].append(id_socio)
                        resultids["adultactiv"].append(id_socio)
                        resultids["activ"].append(id_socio)
                        resultids["tutor"].append(id_socio)

                    if "Socio Adulto SIN Actividades".lower() in agrupacionom:
                        resultids["adult"].append(id_socio)
                        resultids["adultsinactiv"].append(id_socio)
                        resultids["tutor"].append(id_socio)

                    if "Socio Actividades".lower() in agrupacionom:
                        resultids["activ"].append(id_socio)
                        resultids["kidsactiv-and-parents"].append(id_socio)

                    if "Socio SIN Actividades".lower() in agrupacionom:
                        resultids["kids-and-parents"].append(id_socio)
                        resultids["kidsinactiv-and-parents"].append(id_socio)

                    if "avast15".lower() in modalitatnom:
                        resultids["teen15-and-parents"].append(id_socio)

                    if "avast13".lower() in modalitatnom:
                        resultids["teen13-and-parents"].append(id_socio)
    if id_socio not in resultids["activ"]:
        # El socio no tiene actividades, ni de adulto ni de niño

        sociosbaja.append(id_socio)


for actividad in actividades:
    myid = actividad["idActivitat"]
    nombre = actividad["nom"]

    if actividad["idNivell"] and actividad["idNivell"] != "null":
        horario = int(actividad["idNivell"])
    else:
        horario = 0

    if horario in {7, 8, 9, 10}:
        inscritos = common.readjson(filename=f"{myid}")

        actividadyusuarios[myid] = []

        for inscrito in inscritos:
            colegiat = inscrito["colegiat"]["idColegiat"]

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


inscripcionesanuladas = []

for usuario, value in usuariosyhorarios.items():
    # El usuaro tiene horarios duplicados

    # calcular horarios a borrar y verlos en las inscripciones

    url = f"https://{common.endpoint}.playoffinformatica.com/FormAssociat.php?idColegiat={usuario}#tab=ACTIVITATS"
    print("\nUsuario: %s" % url)
    print(
        f"Inscripciones usuario y horarios: {usuariosyhorariosinscripciones[usuario]}"
    )

    for horario in usuariosyhorariosinscripciones[usuario]:
        for inscripcion in usuariosyhorariosinscripciones[usuario][horario]:
            # Rellena variable para luego sacar el nombre
            inscripcionesanuladas.append(inscripcion)


print(
    "\nInscripciones anuladas en los siguientes talleres por bajas o por estar sin actividades"
)


for actividad in actividades:
    myid = actividad["idActivitat"]
    nombre = actividad["nom"]

    if actividad["idNivell"] and actividad["idNivell"] != "null":
        horario = int(actividad["idNivell"])
    else:
        horario = 0

    if horario in {7, 8, 9, 10}:
        inscritos = common.readjson(filename=f"{myid}")

        for inscrito in inscritos:
            inscripcion = inscrito["idInscripcio"]
            if inscripcion in inscripcionesanuladas:
                print(nombre)
