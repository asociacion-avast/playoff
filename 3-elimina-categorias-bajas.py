#!/usr/bin/env python


import configparser
import os

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


print("Loading file from disk")

socios = common.readjson(filename="socios")


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)


for socio in socios:
    id_socio = socio["idColegiat"]
    if (
        "estat" in socio
        and socio["estat"] == "COLESTVAL"
        and "estatColegiat" in socio
        and socio["estatColegiat"]["nom"] == "ESTBAIXA"
    ):
        for categoria in socio["colegiatHasModalitats"]:
            idcategoria = int(categoria["idModalitat"])

            print(
                f"Borrando: {idcategoria} del socio https://{common.endpoint}.playoffinformatica.com/FormAssociat.php?idColegiat={id_socio}#tab=CATEGORIES"
            )
            common.delcategoria(token, id_socio, idcategoria)
