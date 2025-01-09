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
                "Borrando: %s del socio https://asociacionavast.playoffinformatica.com/FormAssociat.php?idColegiat=%s#tab=CATEGORIES"
                % (idcategoria, id_socio)
            )
            common.delcategoria(token, id_socio, idcategoria)
