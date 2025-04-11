#!/usr/bin/env python

import configparser
import os
import pprint
import sys

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)


data = {"Authorization": f"Bearer {token}"}


print("Haciendo llamada API")


null = ""
false = False
true = True

overrides = {
    "montaje": {
        "edatMin": 6,
        "edatMax": 16,
        "nom": "@TuriaLUG y @CanteradeEmpresas: Talleres STEAM: Montaje libre con Lego",
        "minPlaces": 5,
        "maxPlaces": 15,
        "descripcio": "En este taller, un máximo de 15 participantes podrán realizar montajes por libre con Lego",
    },
    "exposicion": {
        "edatMin": null,
        "edatMax": null,
        "nom": "@TuriaLUG y @CanteradeEmpresas: Acceso a la exposición de Lego",
        "minPlaces": 0,
        "maxPlaces": 25,
        "descripcio": "Acceso libre a la exposición de Lego",
    },
    "robotica": {
        "edatMin": 6,
        "edatMax": 11,
        "nom": "@TuriaLUG y @CanteradeEmpresas: Talleres STEAM: Robótica con Lego",
        "minPlaces": 5,
        "maxPlaces": 10,
        "descripcio": "No son necesarios conocimientos previos de robótica",
    },
    "competicion": {
        "edatMin": 12,
        "edatMax": 16,
        "nom": "@TuriaLUG y @CanteradeEmpresas: Talleres STEAM: Iniciación a la robótica de competición",
        "minPlaces": "5",
        "maxPlaces": "10",
        "descripcio": "REQUISITO: necesarios conocimientos previos de robótica",
    },
    "minecraft": {
        "edatMin": 8,
        "edatMax": 12,
        "nom": "@TuriaLUG y @CanteradeEmpresas: Talleres STEAM: Programación con Minecraft Education Edition",
        "minPlaces": "5",
        "maxPlaces": "10",
        "descripcio": "No son necesarios conocimientos previos.",
    },
    "roblox": {
        "edatMin": 11,
        "edatMax": 16,
        "nom": "@TuriaLUG y @CanteradeEmpresas: Talleres STEAM: Desarrollo de videojuegos con Roblox",
        "minPlaces": 5,
        "maxPlaces": 10,
        "descripcio": "REQUISITO: necesarios conocimientos previos de ROBLOX o programación",
    },
}


horariosinicio = {
    "19": "2025-04-21 10:00",
    "20": "2025-04-21 11:30",
    "21": "2025-04-21 16:30",
    "22": "2025-04-21 18:00",
}
horariosfin = {
    "19": "2025-04-21 11:00",
    "20": "2025-04-21 12:30",
    "21": "2025-04-21 17:30",
    "22": "2025-04-21 19:00",
}


disponibilidades = {
    "19": ["montaje", "exposicion", "robotica", "competicion", "minecraft"],
    "20": ["montaje", "exposicion", "robotica", "competicion", "roblox"],
    "21": ["montaje", "exposicion", "robotica", "competicion", "roblox"],
    "22": ["montaje", "exposicion", "robotica", "competicion", "minecraft"],
}
# 749 a 768
idActivitat = 748
while idActivitat < 769:
    for hora in disponibilidades:
        for item in disponibilidades[hora]:
            idActivitat += 1

            # Actividad estándar
            override = {
                "estat": "ACTIESTVIG",
                "tipusControlEdat": "CEANYS",
                "tipus": "TAIND",
                "llocActivitat": "Cantera de Empresas, C/Pobla de Farnals 48, Valencia",
                "dataLimit": "2025-04-16 12:00",
                "dataInici": "2025-04-01 12:30",
                "isVisibleCampsPersonalitzatsPersona": "1",
                "isDescripcioPublica": true,
                "isPermetreInscripcionsTotesModalitats": 0,
                "activitatHasModalitats": [
                    {"idModalitat": "82", "idActivitat": f"{idActivitat}"}
                ],
                "limitacioEstatsSocis": ["1"],
                "placesLliures": 50,
                "usuarisRestringits": [
                    {
                        "idConfiguracioAccesUsuari": "4",
                        "idUsuari": "23",
                        "nom": "m00nblade@hotmail.com",
                        "isActivat": 1,
                    },
                    {
                        "idConfiguracioAccesUsuari": "5",
                        "idUsuari": "26",
                        "nom": "avastjove@asociacion-avast.org",
                        "isActivat": 0,
                    },
                    {
                        "idConfiguracioAccesUsuari": "12",
                        "idUsuari": "136",
                        "nom": "carlos.perello@gmail.com",
                        "isActivat": 1,
                    },
                ],
                "crearUsuariPermes": 0,
                "isPermetreAnularInscripcions": 1,
                "horesAntelacio": 144,
            }
            override.update(overrides[item])
            override["dataHoraActivitat"] = horariosinicio[hora]
            override["dataHoraFiActivitat"] = horariosfin[hora]
            override["idNivell"] = hora
            override["nom"] = (
                override["nom"] + " " + override["dataHoraActivitat"].split()[1]
            )
            result = common.editaactividad(token, idActivitat, override)
            print(f"Editando actividad {idActivitat} {override['nom']}")
            pprint.pprint(result)
            if result.ok is False:
                print(
                    f"Error en la actividad {idActivitat} {override['nom']}: {result.status_code}"
                )
                print(result.text)
            if idActivitat == 768:
                print("Fin de actividades")
                sys.exit(0)
