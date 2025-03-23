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

idActivitat = 746


null = ""
false = False
true = True
payload = {
    "idActivitat": "%s" % idActivitat,
    "idColegi": "1",
    "idNivell": "8",
    "idConfiguracioImprimirPdf": null,
    "idConfiguracioImprimirEntrada": null,
    "idPlantillaComunicat": null,
    "idPlantillaComunicatValidacio": null,
    "idPlantillaComunicatInvitacio": null,
    "idConfiguracioComunicat": null,
    "nom": "Gamusino Gamusinete",
    "estat": "ACTIESTVIG",
    "tipus": "TAIND",
    "minPlaces": "10",
    "maxPlaces": "50",
    "maxMembresEquip": null,
    "dataHoraActivitat": "2026-01-01 00:00",
    "dataHoraFiActivitat": "2026-12-31 00:00",
    "llocActivitat": "Talqueaquí",
    "crearUsuariPermes": "0",
    "pagamentOnlineActivat": "0",
    "pagamentDiferitActivat": "0",
    "pagamentDomiciliatActivat": "0",
    "pagamentEfectiuActivat": "0",
    "pagamentAltresActivat": "0",
    "isPreinscripcioActivat": "0",
    "isLlistaEsperaActivat": "0",
    "dataLimit": "2025-12-31 00:00",
    "dataInici": "0005-01-01 00:00",
    "tipusControlEdat": "",
    "edatMin": null,
    "edatMax": null,
    "isDescripcioPublica": true,
    "isTutorsObligatori": "1",
    "isVisibilitatInscripcionsPublic": false,
    "isVisibilitatPreuPublic": true,
    "isAssociatDadesMinim": "0",
    "isControlAcces": false,
    "dataHoraIniciControlAcces": null,
    "tipusRepeticioControlAcces": null,
    "isDadesPersonalsNoModificables": "0",
    "isMultiplesTipologies": "0",
    "nomCampDescripcio": "",
    "campsDinamics": [],
    "campsDinamicsActivitat": {},
    "descripcio": "<p>Akinoestán</p>",
    "emailCopiaInscripcio": "",
    "textInicial": "",
    "textDescripcioTipologies": "",
    "textTitolOpcionsExtres": "",
    "textOpcionsExtres": "",
    "textDescomptes": "",
    "textCondicions": "",
    "textDretsImatge": "",
    "textAdjunts": "",
    "textPagament": "",
    "textIniciFormulari": "",
    "textDadesContacteError": null,
    "titolInscripcioFinal": "",
    "DescripcioInscripcioFinal": "",
    "urlRedireccio": "",
    "iva": "0",
    "isCeca": "0",
    "isRedSys": "0",
    "isPayPal": "0",
    "isStripe": "0",
    "isMercadoPago": "0",
    "isPixelPay": "0",
    "isPermetreInscripcionsMultiplePersona": "0",
    "isVisiblePlacesActivitat": true,
    "isVisibleDataActivitat": true,
    "isEnviarEmailConfirmacioCapFamilia": false,
    "isEnviarRebutConfirmacio": true,
    "isPermetreAnularInscripcions": false,
    "isAcceptarSolicitudsAnulacioAutomaticament": true,
    "isMinimUnaQuotaXAgrupacio": "0",
    "isAplicarConfiguracioQuotesPerAgrupacio": "0",
    "isAplicarConfiguracioQuotesPerAgrupacioOpcionals": false,
    "tipusConfiguracioQuotes": "TPCFQMAX1",
    "isLimitarTipologiaPerAgrupacio": null,
    "isMultiplesDescomptes": "1",
    "isQuotesOpcionalsObligatories": false,
    "tipusConfiguracioQuotesOpcionals": "",
    "ocultarImportsQuotesObligatories": false,
    "ocultarImportsQuotesOpcionals": false,
    "desplegarAgrupacionsQuotesObligatories": false,
    "desplegarAgrupacionsQuotesOpcionals": false,
    "isVisibleCampsPersonalitzatsPersona": "1",
    "isPermetreCrearEquipsPartPublica": "0",
    "ordre": null,
    "horesAntelacio": "0",
    "habilitarPagamentUnic": "1",
    "importEntradaPagamentFraccionat": null,
    "percentatgeEntradaPagamentFraccionat": null,
    "percentatgeSegonPagamentFraccionat": null,
    "dataSegonRebutPagamentFraccionat": null,
    "tipusVencimentSegonRebut": "data",
    "diesSegonRebutPagamentFraccionat": null,
    "metodeSegonRebutPagamentFraccionat": "",
    "percentatgeTercerPagamentFraccionat": null,
    "dataTercerRebutPagamentFraccionat": null,
    "tipusVencimentTercerRebut": "data",
    "diesTercerRebutPagamentFraccionat": null,
    "metodeTercerRebutPagamentFraccionat": "",
    "percentatgeQuartPagamentFraccionat": null,
    "dataQuartRebutPagamentFraccionat": null,
    "tipusVencimentQuartRebut": "",
    "diesQuartRebutPagamentFraccionat": null,
    "metodeQuartRebutPagamentFraccionat": "",
    "dataCinqueRebutPagamentFraccionat": null,
    "tipusVencimentCinqueRebut": "",
    "diesCinqueRebutPagamentFraccionat": null,
    "metodeCinqueRebutPagamentFraccionat": "",
    "isAdjuntTransferenciaObligatori": "0",
    "isNoPermetreRebreEmailsEntitat": false,
    "isPermetreInscripcionsTotesModalitats": 0,
    "isVisibleDataLimit": null,
    "numInscripcions": null,
    "numInscripcionsTotesIntern": null,
    "isEnviarArxiuCalendari": true,
    "activitatHasTipusAdjunts": [],
    "activitatHasModalitats": [
        {"idModalitat": "90", "idActivitat": "%s" % idActivitat}
    ],
    "controlAccesActivitat": {
        "idControlAccesActivitat": "922",
        "isHabilitarAccesAmbCarnet": "0",
        "controlAccesActivitatHasModalitats": [],
    },
    "adjunts": [
        {
            "idAdjunt": "31065",
            "idTipusAdjunt": "46",
            "fileName": "",
            "descripcio": "",
            "path": "",
            "pathThumb": "",
            "pathThumbMid": "",
            "filetype": "",
            "filesize": "0",
            "dataIntroduccio": "2025-03-23 18:13:28",
            "dataModificacio": "2025-03-23 22:39:25",
            "tipusAdjunt": {
                "idTipusAdjunt": "46",
                "nom": "ACT_FOTO",
                "descripcio": "Foto Activitat",
                "isSistema": "1",
            },
        }
    ],
    "consentimentsLegals": [
        {
            "idConsentimentLegal": "2239",
            "idConfiguracioFormulariColegi": null,
            "idActivitat": "%s" % idActivitat,
            "nom": "CONDICIONS_LEGALS",
            "titol": "CONSENTIMENTS_LEGALS_CONDICIONS_LEGALS",
            "contingut": null,
            "isVisible": false,
            "isObligatori": false,
            "isRequerirSignatura": "0",
        },
        {
            "idConsentimentLegal": "2240",
            "idConfiguracioFormulariColegi": null,
            "idActivitat": "%s" % idActivitat,
            "nom": "DRETS_IMATGE",
            "titol": "CONSENTIMENTS_LEGALS_DRETS_IMATGE",
            "contingut": null,
            "isVisible": false,
            "isObligatori": false,
            "isRequerirSignatura": "0",
        },
        {
            "idConsentimentLegal": "2241",
            "idConfiguracioFormulariColegi": null,
            "idActivitat": "%s" % idActivitat,
            "nom": "PERSONALITZAT",
            "titol": null,
            "contingut": null,
            "isVisible": false,
            "isObligatori": false,
            "isRequerirSignatura": "0",
        },
    ],
    "limitacioEstatsSocis": ["1"],
    "urlSlug": "https://asociacionavast.playoffinformatica.com/actividad/747/Gamusino-Gamusinete/",
    "placesLliures": 50,
    "quotaBase": 0,
    "usuarisRestringits": [
        {
            "idConfiguracioAccesUsuari": "4",
            "idUsuari": "23",
            "nom": "m00nblade@hotmail.com",
            "isActivat": 1,
        },
        {
            "idConfiguracioAccesUsuari": "5",
            "idUsuari": "26",
            "nom": "avastjove@asociacion-avast.org",
            "isActivat": 0,
        },
        {
            "idConfiguracioAccesUsuari": "12",
            "idUsuari": "136",
            "nom": "carlos.perello@gmail.com",
            "isActivat": 1,
        },
    ],
    "teDescomptesCodi": false,
    "descomptes": [],
    "codisDescomptes": [],
    "preus": [],
}

url = f"{common.apiurl}/activitats/{idActivitat}"

output = requests.put(
    url,
    headers=common.headers,
    auth=common.BearerAuth(token),
    data=json.dumps(payload),
)
try:
    output = json.loads(output)
except:
    pass

pprint.pprint(output)
