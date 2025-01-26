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
                            f"Socio: https://{common.endpoint}.playoffinformatica.com/FormAssociat.php?idColegiat={socio["idColegiat"]}"
                        )
