#!/usr/bin/env python


import common

print("Loading file from disk")
socios = common.readjson(filename="socios")


print("Procesando socios...")
count = 0

for socio in socios:
    idcolegiat = socio["idColegiat"]
    if isinstance(socio["campsDinamics"], dict):
        for field in common.telegramfields:
            if field in socio["campsDinamics"]:
                if common.validasocio(
                    socio,
                    estado="COLESTVAL",
                    estatcolegiat="ESTALTA",
                ):
                    idsocio = f'{socio["campsDinamics"][field]}'
                    newidsocio = "None"

                    if idsocio is not None and idsocio != "" and idsocio != "None":
                        try:
                            newidsocio = int(idsocio)
                        except Exception:
                            print(
                                f"{count:04} https://{common.endpoint}.playoffinformatica.com/FormAssociat.php?idColegiat={idcolegiat}"
                            )
                            print("Invalid ID socio for user: %s" % idcolegiat)

                    elif idsocio != "None":
                        print(
                            f"{count:04} https://{common.endpoint}.playoffinformatica.com/FormAssociat.php?idColegiat={idcolegiat}"
                        )
                        print("Invalid ID socio for user: %s" % idcolegiat)

                    if "%s" % idsocio != "%s" % newidsocio:
                        print(
                            f"{count:04} https://{common.endpoint}.playoffinformatica.com/FormAssociat.php?idColegiat={idcolegiat}"
                        )
                        print("Invalid ID socio for user: %s" % idcolegiat)
                        print(idsocio, newidsocio)
