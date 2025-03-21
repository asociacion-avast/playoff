#!/usr/bin/env python

import configparser
import json
import os
import pprint

import requests

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)


data = {"Authorization": f"Bearer {token}"}


print("Haciendo llamada API")

nom = "Gamusino Gamusinete"
lloc = "Talqueaquí"
maxplaces = 50
minplaces = 10
dataHoraActivitat = "2026-01-01"
dataHoraFiActivitat = "2026-12-31"
dataInici = "0005-01-01"
dataLimit = "2025-12-31"
descripcio = "<p>Akinoest&aacute;n</p>"
horario = 8


url = "https://asociacionavast.playoffinformatica.com/api.php/api/v1.0/activitats"
payload = {
    "consentimentsLegals": [],
    "activitatHasModalitats": [],
    "activitatHasTipusAdjunts": [],
    "adjunts": [
        {
            "tipusAdjunt": {
                "idTipusAdjunt": "46",
                "nom": "ACT_FOTO",
                "descripcio": "Foto Activitat",
                "isSistema": "1",
            },
            "idAdjunt": 0,
            "fileName": "",
            "descripcio": "",
            "path": "",
            "pathThumb": "",
            "pathThumbMid": "",
            "dataIntroduccio": "",
            "dataModificacio": "",
        }
    ],
    "campsDinamics": [],
    "crearUsuariPermes": True,
    "dataHoraActivitat": "%s" % dataHoraActivitat,
    "dataHoraFiActivitat": "%s" % dataHoraFiActivitat,
    "dataHoraIniciControlAcces": "",
    "dataInici": "%s" % dataInici,
    "dataLimit": "%s" % dataLimit,
    "nomCampDescripcio": "",
    "descripcio": "%s" % descripcio,
    "edatMax": "",
    "edatMin": "",
    "estat": "ACTIESTVIG",
    "idActivitat": 0,
    "urlSlug": "",
    "idColegi": 0,
    "idConfiguracioComunicat": "",
    "idConfiguracioImprimirPdf": "",
    "idConfiguracioImprimirEntrada": "",
    "idNivell": "%s" % horario,
    "isMultiplesDescomptes": True,
    "isAplicarConfiguracioQuotesPerAgrupacio": False,
    "isAplicarConfiguracioQuotesPerAgrupacioOpcionals": False,
    "horesAntelacio": 0,
    "isAssociatDadesMinim": False,
    "isCeca": False,
    "isControlAcces": False,
    "isDadesPersonalsNoModificables": False,
    "isEnviarRebutConfirmacio": True,
    "idPlantillaComunicatValidacio": "",
    "idPlantillaComunicat": "",
    "isEnviarEmailConfirmacioCapFamilia": False,
    "isLlistaEsperaActivat": False,
    "isMinimUnaQuotaXAgrupacio": False,
    "isPermetreAnularInscripcions": False,
    "isAcceptarSolicitudsAnulacioAutomaticament": True,
    "isMultiplesTipologies": False,
    "maxMembresEquip": "",
    "isPayPal": False,
    "isPermetreCrearEquipsPartPublica": False,
    "isPermetreInscripcionsMultiplePersona": False,
    "isPreinscripcioActivat": False,
    "isRedSys": False,
    "isStripe": False,
    "isMercadoPago": False,
    "isTutorsObligatori": True,
    "isVisibilitatInscripcionsPublic": False,
    "isVisibilitatPreuPublic": True,
    "isVisibleCampsPersonalitzatsPersona": True,
    "isVisibleDataActivitat": True,
    "isVisiblePlacesActivitat": True,
    "isDescripcioPublica": True,
    "iva": 0,
    "llocActivitat": "%s" % lloc,
    "maxPlaces": "%s" % maxplaces,
    "minPlaces": "%s" % minplaces,
    "nom": "%s" % nom,
    "ordre": "",
    "pagamentDiferitActivat": False,
    "pagamentDomiciliatActivat": "",
    "pagamentEfectiuActivat": "",
    "pagamentOnlineActivat": False,
    "textAdjunts": "",
    "textCondicions": "",
    "textDretsImatge": "",
    "textInicial": "",
    "textOpcionsExtres": "",
    "textPagament": "",
    "textIniciFormulari": "",
    "tipus": "TAIND",
    "tipusConfiguracioQuotes": "TPCFQMAX1",
    "isQuotesOpcionalsObligatories": False,
    "tipusConfiguracioQuotesOpcionals": "",
    "ocultarImportsQuotesObligatories": False,
    "ocultarImportsQuotesOpcionals": False,
    "desplegarAgrupacionsQuotesObligatories": False,
    "desplegarAgrupacionsQuotesOpcionals": False,
    "tipusControlEdat": "",
    "preus": [],
    "emailCopiaInscripcio": "",
    "limitacioEstatsSocis": [],
    "tipusVencimentSegonRebut": "data",
    "tipusVencimentTercerRebut": "data",
    "diesSegonRebutPagamentFraccionat": "",
    "metodeSegonRebutPagamentFraccionat": "",
    "diesTercerRebutPagamentFraccionat": "",
    "metodeTercerRebutPagamentFraccionat": "",
    "isAdjuntTransferenciaObligatori": False,
    "isPermetreInscripcionsTotesModalitats": False,
    "campsDinamicsActivitat": {},
    "usuarisRestringits": [],
    "idPlantillaComunicatInvitacio": "",
    "isEnviarArxiuCalendari": True,
    "isNoPermetreRebreEmailsEntitat": False,
    "descomptes": [],
    "codisDescomptes": [],
}


response = requests.post(
    url,
    headers=common.headers,
    auth=common.BearerAuth(token),
    data=json.dumps(payload),
)
pprint.pprint(json.loads(response.text))
