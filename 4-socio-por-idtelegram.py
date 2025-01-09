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


# name of the field in PlayOff
tutor1 = "0_13_20231012041710"
tutor2 = "0_14_20231012045321"
socioid = "0_16_20241120130245"

fields = [tutor1, tutor2, socioid]


print("Loading file from disk")
socios = common.readjson(filename="socios")

validids = []
invalidids = []

print("Procesando socios")
for socio in socios:
    if isinstance(socio["campsDinamics"], dict):
        for field in fields:
            if field in socio["campsDinamics"]:
                if (
                    "estat" in socio
                    and socio["estat"] == "COLESTVAL"
                    and "estatColegiat" in socio
                    and socio["estatColegiat"]["nom"] == "ESTALTA"
                ):
                    try:
                        idbb = int(socio["campsDinamics"][field])
                    except Exception:
                        idbb = False

                    if idbb and idbb == id:
                        print(
                            "Socio: https://asociacionavast.playoffinformatica.com/FormAssociat.php?idColegiat=%s"
                            % socio["idColegiat"]
                        )
