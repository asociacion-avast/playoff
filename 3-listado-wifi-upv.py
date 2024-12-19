#!/usr/bin/env python

import common

print("Loading file from disk")

actividades = common.readjson(filename="actividades")
socios = common.readjson(filename="socios")


conclavewifi = [
    661,
    660,
    625,
    622,
    652,
    653,
    654,
    655,
    601,
    600,
    605,
    620,
    624,
    629,
    623,
    621,
    628,
    590,
    648,
    649,
    650,
    651,
    553,
    552,
    551,
    554,
    559,
    556,
    557,
    558,
    547,
    548,
    549,
    550,
]


usersconclave = []


print("Procesando actividades...")


for actividad in actividades:
    myid = int(actividad["idActivitat"])
    nombre = actividad["nom"]

    if myid in conclavewifi:
        print(myid, nombre)

        users = common.readjson(filename=f"{myid}")

        for user in users:
            if user["estat"] == "INSCRESTNOVA":
                usersconclave.append(user["colegiat"]["idColegiat"])


print("Listado para politécnica")
for user in sorted(set(usersconclave)):
    for socio in socios:
        if user == socio["idColegiat"]:
            nombre = socio["persona"]["nom"]
            apellidos = socio["persona"]["cognoms"]
            nif = socio["persona"]["nif"]
            # autoriza = 0
            # if isinstance(soci["campsDinamics"], dict) and "1_3_20210707032324pm" in soci["campsDinamics"]:
            #     if soci["campsDinamics"]["1_3_20210707032324pm"] == 1:
            #         autoriza = 1
            # print("%s,%s,%s,%s" % (nif, cognom, nom, autoriza))
            print(f"{nif},{apellidos},{nombre}")
