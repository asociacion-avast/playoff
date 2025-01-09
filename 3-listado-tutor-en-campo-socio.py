#!/usr/bin/env python


import configparser
import os

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


socios = common.readjson("socios")


print("Procesando socios")
count = 0
for socio in socios:
    if isinstance(socio["campsDinamics"], dict):
        if common.idsocios in socio["campsDinamics"]:
            mysocio = socio["campsDinamics"][common.idsocios]
            for field in [common.idtutor1, common.idtutor2]:
                if field in socio["campsDinamics"]:
                    if mysocio == socio["campsDinamics"][field]:
                        count = count + 1
                        print(
                            "%s https://asociacionavast.playoffinformatica.com/FormAssociat.php?idColegiat=%s"
                            % (f"{count:04}", socio["idColegiat"])
                        )
