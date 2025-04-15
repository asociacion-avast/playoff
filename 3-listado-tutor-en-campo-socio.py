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
        if common.socioid in socio["campsDinamics"]:
            mysocio = socio["campsDinamics"][common.socioid]
            for field in [common.tutor1, common.tutor2]:
                if field in socio["campsDinamics"]:
                    if mysocio == socio["campsDinamics"][field]:
                        count = count + 1
                        print(f"{count:04} {common.sociobase}{socio['idColegiat']}")
