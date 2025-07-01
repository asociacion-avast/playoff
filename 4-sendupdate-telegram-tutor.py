#!/usr/bin/env python


import configparser
import os
import sys

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)


comurl = f"{common.apiurl}/comunicats/emails_notificacions"
headers = {"Authorization": f"Bearer {token}"}


if len(sys.argv) < 2:
    print("Missing argument: idAssociat  for sending the message")
    sys.exit(-1)

associat = int(sys.argv[1])


print("Enviando comunicado")


response = common.enviacomunicado(token=token, data=common.getcomunicadotutor(associat))

print(response)
print(response.text)
