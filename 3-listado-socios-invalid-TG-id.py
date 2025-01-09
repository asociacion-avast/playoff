#!/usr/bin/env python


import common

# name of the field in PlayOff
tutor1 = "0_13_20231012041710"
tutor2 = "0_14_20231012045321"
socioid = "0_16_20241120130245"

fields = [tutor1, tutor2, socioid]

print("Loading file from disk")
socios = common.readjson(filename="socios")


print("Procesando socios...")

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
                    idsocio = f'{socio["campsDinamics"][field]}'
                    newidsocio = "None"

                    if idsocio is not None and idsocio != "" and idsocio != "None":
                        try:
                            newidsocio = int(idsocio)
                        except Exception:
                            print("Invalid ID socio for user: %s" % socio["idColegiat"])

                    elif idsocio != "None":
                        print("Invalid ID socio for user: %s" % socio["idColegiat"])

                    if "%s" % idsocio != "%s" % newidsocio:
                        print("Invalid ID socio for user: %s" % socio["idColegiat"])
                        print(idsocio, newidsocio)
