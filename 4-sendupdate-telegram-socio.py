#!/usr/bin/env python


import configparser
import json
import os
import sys

import requests

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)


comurl = f"{common.apiurl}/comunicats/emails_notificacions"
headers = {"Authorization": f"Bearer {token}"}


true = True
null = ""

if len(sys.argv) < 2:
    print("Missing argument: idAssociat  for sending the message")
    sys.exit(-1)

associat = int(sys.argv[1])


print("Enviando comunicado")


data = {
    "comunicat": json.dumps(
        {
            "idComunicat": 0,
            "titol": "Actualiza sus datos ID Socio",
            "descripcioIntro": """Hola, [[persona_nombre]]:<br><br><br>Estamos actualizando la base de datos para poder acceder a los distintos canales de Actividades AVAST donde sólo accederán los miembros de la asociación. Para que esto sea posible necesitas conseguir tu id de telegram y añadirlo a tu ficha. Puedes añadir sólo una ID para el socio. En nuestra web tienes el tutorial de como hacerlo. El tutorial esta hecho para los tutores, así que en tu caso aparecerá Telegram ID socio/a <br><br> https://asociacion-avast.org/registro-en-la-base-de-datos-de-avast-del-id-de-telegram/ <br><br><br>Necesitamos que accedas al siguiente enlace para configurarlo en nuestra base de datos:<br><br>[[invitacion_enlace_preinscripcion]]<br><br>*Recuerda que este enlace es válido sólo por [[invitacion_horas_validez]] horas.<br><br><br>Una vez registrado se te enviara el enlace al canal de Familias de AVAST.<br><br><br>Si tienes alguna duda o no te aclaras muy bien, tenemos un grupo de ayuda de Telegram para ayudarte: https://t.me/+9ou2gX99KLxjNWVk <br><br>Gracias por tu colaboración.<br><br>Atentamente,<br>Administración - AVAST""",
            "adjunts": [],
            "estat": "COMESTESB",
            "dataEnviamentProgramada": null,
            "isLoaded": true,
        }
    ),
    "configBase": json.dumps(
        {
            "idConfiguracioComunicat": "4",
            "idFamiliaComunicat": 0,
            "tipusComunicat": "TPCINVITACIO",
            "plantillaComunicat": "PCINVITACIONS",
        }
    ),
    "configExtra": json.dumps(
        {
            "idsColegiats": [f"{associat}"],
            "idsPatrocinadors": [],
            "idsRebuts": [],
            "idsInscripcions": [],
            "idsReserves": [],
            "setEstatReclamacioImpagats": 0,
            "idActivitat": null,
            "idsValorsSeccioPersonalitzada": null,
            "idEnquesta": null,
            "idRegistreAssistencia": null,
            "idConvocatoria": null,
            "idConfiguracioImprimirPdf": null,
            "idAgrupacio": null,
            "idModalitat": null,
            "idsAssociats": null,
            "idConfiguracioFormulariColegi": "17",
            "anys": null,
            "perso": null,
            "idsContactes": [],
        }
    ),
    "configIncloure": json.dumps(
        {
            "isEmail": true,
            "isEmailOficial": true,
            "isEmailTutors": true,
            "isEmailCapFamilia": true,
            "isEmailExtra": "",
            "emailsExtra": [],
        }
    ),
    "destinataris": json.dumps([f"{associat}"]),
    "destinatarisPatrocinador": "[]",
    "destinatarisContacte": "[]",
}

files = []
response = requests.request("POST", comurl, headers=headers, data=data, files=files)

print(response)
print(response.text)
