#!/usr/bin/env python


import sys

import common

id = False
if len(sys.argv) > 1:
    try:
        id = int(sys.argv[1])
    except Exception:
        id = False

if not id:
    print("Telegram ID required")
    sys.exit(-1)


print("Loading file from disk")
socios = common.readjson(filename="socios")

validids = []
invalidids = []

print("Procesando socios")
for socio in socios:
    if isinstance(socio["campsDinamics"], dict):
        for field in common.telegramfields:
            if field in socio["campsDinamics"]:
                if common.validasocio(
                    socio,
                    estado="COLESTVAL",
                    estatcolegiat="ESTALTA",
                ):
                    try:
                        idbb = int(socio["campsDinamics"][field])
                    except Exception:
                        idbb = False

                    if idbb and idbb == id:
                        print(f"Socio: {common.sociobase}{socio["idColegiat"]}")
