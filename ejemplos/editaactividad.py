#!/usr/bin/env python

import configparser
import os
import pprint

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)


data = {"Authorization": f"Bearer {token}"}


print("Haciendo llamada API")

idActivitat = 718


null = ""
false = False
true = True

override = {
    "estat": "ACTIESTVIG",
    "tipus": "TAIND",
    "minPlaces": "10",
    "nom": "Los gamusinos molan",
    "maxPlaces": "50",
    "dataHoraActivitat": "2026-01-01 00:00",
    "dataHoraFiActivitat": "2026-12-31 00:00",
    "llocActivitat": "Talqueaquí",
    "dataLimit": "2025-12-31 00:00",
    "dataInici": "2025-01-01 00:00",
    "edatMin": null,
    "edatMax": null,
    "isVisibleCampsPersonalitzatsPersona": "1",
    "isDescripcioPublica": true,
    "descripcio": "<p>Akinoestán</p>",
    "isPermetreInscripcionsTotesModalitats": 0,
    "activitatHasModalitats": [
        {"idModalitat": "90", "idActivitat": "%s" % idActivitat}
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
}


pprint.pprint(common.editaactividad(token, idActivitat, override))
