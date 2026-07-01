#!/usr/bin/env python


import common

print("Loading file from disk")

actividades = common.readjson(filename="actividades")


print("Procesando actividades...")

usuariosyactividad = {}
actividadyusuarios = {}
usuariosyhorarios = {}

for actividad in actividades:
    myid = actividad["idActivitat"]
    horario = common.actividad_horario(actividad)

    if horario in {7, 8, 9, 10, 19, 20, 21, 22}:
        actividadyusuarios[myid] = []
        inscritos = common.readjson(filename=f"{myid}")

        for inscrito in inscritos:
            if inscrito["estat"] != "INSCRESTNOVA":
                continue

            colegiat = inscrito["colegiat"]["idColegiat"]
            actividadyusuarios[myid].append(colegiat)
            usuariosyactividad.setdefault(colegiat, []).append(myid)
            usuariosyhorarios.setdefault(colegiat, []).append(horario)


for usuario in usuariosyhorarios:
    if len(usuariosyhorarios[usuario]) != len(sorted(set(usuariosyhorarios[usuario]))):
        print(
            usuario,
            usuariosyhorarios[usuario],
            f"{common.sociobase}{usuario}#tab=ACTIVITATS",
        )
