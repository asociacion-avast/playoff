#!/usr/bin/env python

import configparser
import os

import common

# idColegiat = "1791"  # Prueba Javi
# idColegiat = "2811"  # Prueba Luz
# idColegiat = "3543"  # manolo el del bombo

# idActivitat = "718"  # Gamusino's revenge


config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)


for idColegiat in [1791, 2811, 3543]:
    print("Procesando socio %s" % idColegiat)
    for idActivitat in [718, 538, 539, 714]:
        print("Procesando actividad: %s" % idActivitat)

        print(
            common.create_inscripcio(
                token=token, idActivitat=idActivitat, idColegiat=idColegiat
            ).text
        )
