#!/usr/bin/env python


import common

print("Loading file from disk")

actividades = common.rewadjson(filename="actividades")


print("Procesando actividades...")

usuariosyactividad = {}
actividadyusuarios = {}
usuariosyhorarios = {}

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

            if inscrito["estat"] != "INSCRESTANULADA":
                if colegiat not in usuariosyactividad:
                    usuariosyactividad[colegiat] = []

                if colegiat not in usuariosyhorarios:
                    usuariosyhorarios[colegiat] = []

                usuariosyactividad[colegiat].append(myid)
                usuariosyhorarios[colegiat].append(horario)


for usuario in usuariosyhorarios:
    if len(usuariosyhorarios[usuario]) != len(sorted(set(usuariosyhorarios[usuario]))):
        print(
            usuario,
            usuariosyhorarios[usuario],
            "https://asociacionavast.playoffinformatica.com/FormAssociat.php?idColegiat=%s#tab=ACTIVITATS"
            % usuario,
        )
