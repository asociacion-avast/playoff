#!/usr/bin/env python

import configparser
import json
import os

import dateutil.parser
import requests

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))

# Telegramfields
tutor1 = "0_13_20231012041710"
tutor2 = "0_14_20231012045321"
socioid = "0_16_20241120130245"
telegramfields = [tutor1, tutor2, socioid]
fechacambio = "0_17_20250221121130"


apiurl = f"https://{config['auth']['endpoint']}.playoffinformatica.com/api.php/api/v1.0"
headers = {"Content-Type": "application/json", "content-encoding": "gzip"}

endpoint = config["auth"]["endpoint"]


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = f"Bearer {self.token}"
        return r


def gettoken(user=config["auth"]["username"], password=config["auth"]["password"]):
    # get token

    loginurl = f"{apiurl}/login/colegi"

    data = {"username": user, "password": password}

    result = requests.post(loginurl, data=json.dumps(data), headers=headers)

    return result.json()["access_token"]


def writejson(filename, data):
    with open(f"data/{filename}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        return True


def readjson(filename):
    with open(f"data/{filename}.json", "r", encoding="utf-8") as f:
        return json.load(f)


def addcategoria(token, socio, categoria, extra=False):
    """Adds categoria to socio

    Args:
        extra:
        token (str): token for accessing API (RW)
        socio (int): Socio identifier
        categoria (int): ID for category to modify
    """

    headers = {"Authorization": f"Bearer {token}"}
    categoriaurl = f"{apiurl}/colegiats/{socio}/modalitats"

    data = {"idModalitat": categoria}

    if extra:
        data.update(extra)
    files = []

    return requests.request(
        "POST", categoriaurl, headers=headers, data=data, files=files
    )


def delcategoria(token, socio, categoria):
    """Removes categoria from socio

    Args:
        token (str): token for accessing API (RW)
        socio (int): Socio identifier
        categoria (int): ID for category to modify
    """

    headers = {"Authorization": f"Bearer {token}"}
    categoriaurl = f"{apiurl}/colegiats/{socio}/modalitats/{categoria}"

    data = {}
    files = []

    return requests.request(
        "DELETE", categoriaurl, headers=headers, data=data, files=files
    )


def escribecampo(token, socioid, campo, valor=""):
    """Escribe campo personalizado de socio

    Args:
        token (_type_): Token para operaciones
        socioid (_type_): idAssociat
        campo (_type_): Campo personalizado
        valor (_type_): Valor a establecer o vacío para borrar

    Returns:
        _type_: _description_
    """

    comurl = f"{apiurl}/colegiats/{socioid}/campsdinamics"

    headers = {"Authorization": f"Bearer {token}"}
    data = {f"{campo}": f"{valor}"}

    files = []
    return requests.request("PUT", comurl, headers=headers, data=data, files=files)


def calcular_proximo_recibo(fecha):
    """_summary_

    Args:
        fecha (datetime): Fecha for today

    Returns:
        str: fecha
    """
    meses_cobro = sorted(
        {9, 11, 1, 3, 5}
    )  # Meses de cobro (septiembre, noviembre, enero, marzo, mayo)

    fecha = dateutil.parser.parse(fecha)
    dia = fecha.day
    mes = fecha.month
    año = fecha.year

    if dia < 5:
        if mes in meses_cobro:
            return f"05/{mes:02d}/{año}"
        else:
            mes_cobro = next((m for m in meses_cobro if m > mes), None)
            if mes_cobro is None:
                mes_cobro = meses_cobro[0]
                año += 1
            return f"05/{mes_cobro:02d}/{año}"
    else:
        mes_cobro = next((m for m in meses_cobro if m > mes), None)
        if mes_cobro is None:
            mes_cobro = meses_cobro[0]
            año += 1
        return f"05/{mes_cobro:02d}/{año}"


def validasocio(
    socio,
    estado="COLESTVAL",
    estatcolegiat="ESTALTA",
    agrupaciones=[],
    subcategorias=[],
    reverseagrupaciones=False,
    reversesubcategorias=False,
):
    """Validates if socio is active

    Args:
        estatcolegiat:
        agrupaciones:
        subcategorias:
        reverseagrupaciones:
        reversesubcategorias:
        estado:
        socio (dict): Dictionary representing a socio

    Returns:
        bool: True or False is an active socio
    """
    if (
        "estat" in socio
        and socio["estat"] == estado
        and "estatColegiat" in socio
        and socio["estatColegiat"]["nom"] == estatcolegiat
    ):
        if not agrupaciones and not subcategorias:
            return True
        else:
            if "colegiatHasModalitats" in socio:
                # Iterate over all categories for the user
                for modalitat in socio["colegiatHasModalitats"]:
                    if "modalitat" in modalitat:
                        # Save name for comparing the ones we target
                        agrupacionom = modalitat["modalitat"]["agrupacio"][
                            "nom"
                        ].lower()
                        modalitatnom = modalitat["modalitat"]["nom"].lower()

                        if agrupaciones:
                            if not reverseagrupaciones:
                                rc = False
                                for agrupacion in agrupaciones:
                                    if agrupacionom == agrupacion.lower():
                                        rc = True
                                return rc
                            else:
                                rc = True
                                for agrupacion in agrupaciones:
                                    if agrupacionom == agrupacion.lower():
                                        rc = False
                                return rc
                        if subcategorias:
                            if not reversesubcategorias:
                                rc = False
                                for categoria in subcategorias:
                                    if modalitatnom == categoria.lower():
                                        rc = True
                                return rc
                            else:
                                rc = True
                                for categoria in subcategorias:
                                    if modalitatnom == categoria.lower():
                                        rc = False
                                return rc

    return False


def updateactividad(token, idactividad):
    "Update Users for actividad using token and actividadID"
    # get users
    usersurl = f"https://{apiurl}/inscripcions?idActivitat={idactividad}"

    headers = {"Authorization": f"Bearer {token}"}
    users = requests.get(usersurl, auth=BearerAuth(token), headers=headers).json()

    writejson(filename=f"{idactividad}", data=users)


def create_inscripcio(token, idActivitat, idColegiat):
    url = f"{apiurl}/inscripcions/public"

    if idColegiat is not None:
        colegiat = get_colegiat_data(idColegiat=idColegiat)

    data = {
        "inscripcions": [
            {
                "formatNouActivitat": True,  # Activa o desactivada llega el aviso de 'finalidad y funcionamiento'
                "quotesObligatories": [],
                "unitatsQuota": {},
                "quotesOpcionals": [],
                "descomptesGenerals": [],
                "descompteCodi": None,
                "campsPersonalitzats": {},
                "observacions": None,
                "isAutoritzaDretsImatge": False,
                "isAfegirAGrupFamiliar": False,
                "isCapFamilia": False,
                "signatura": {},
                "idColegiat": "%s" % idColegiat,
                "idActivitat": idActivitat,
                "colegiat": colegiat,
            }
        ],
        "isEnviarNotificacio": 0,
    }
    res = requests.post(
        url,
        data=json.dumps(data),
        auth=BearerAuth(token),
        headers=headers,
        allow_redirects=False,
    )
    return res


def get_colegiat_data(idColegiat=False):
    socios = readjson("socios")
    mydata = False

    for socio in socios:
        if int(socio["idColegiat"]) == int(idColegiat):
            mydata = socio

    # Tenemos el socio
    # Tenemos que prepararlo al formato que usa la inscripción

    if mydata:
        return {
            "": None,
            "idColegiat": mydata["idColegiat"],
            "idModalitat": "33",
            "fotoThumbnail": "",
            "numColegiat": mydata["numColegiat"],
            "nomEstat": "Alta",
            "nom": mydata["persona"]["nom"],
            "cognoms": mydata["persona"]["cognoms"],
            "nif": "",
            "residencia": "",
            "tePassaport": "S",
            "dataNaixement": "",
            "edat": 44,
            "sexe": "Otros / No binario",
            "estatCivil": "",
            "escola": "",
            "telefonPrincipal": "",
            "telefonSecundari": "",
            "codipostal": "46017",
            "domicili": "",
            "municipi": "VALENCIA",
            "nomProvincia": "VALENCIA",
            "prefixPais": None,
            "prefixNacionalitat": "España",
            "emailOficial": "",
            "web": "",
            "dataAlta": "",
            "dataBaixa": "",
            "iban": "",
            "titular": "",
            "teApp": "Sí",
            "observacionsColegiat": "",
            "numeroRebutsRetornats": None,
            "importRebutsRetornats": None,
            "dataRebutRetornat": "",
            "pendents": "1",
            "importTotalPendent": "0.00",
            "metodePagament": "Domiciliación bancaria",
            "nomTutor1": "",
            "cognomsTutor1": "",
            "telefonFixTutor1": "",
            "mobilTutor1": "",
            "emailTutor1": "",
            "nomTutor2": "",
            "cognomsTutor2": "",
            "telefonFixTutor2": "",
            "mobilTutor2": "",
            "emailTutor2": "",
            "adjunts": [],
            "1_0_20220126102039am": '["No tengo"]',
            "1_1_20220908054836am": None,
            "1_0_20190831085222am": None,
            "1_1_20210606061659am": '["Fotos en Sitio Web AVAST "]',
            "1_4_20210707032324pm": None,
            "1_3_20210707032324pm": "NO",
            "1_5_20210708123547pm": "NO",
            "1_6_20210708123547pm": "SI",
            "1_7_20210708124318pm": None,
            "1_8_20220221034044pm": "Los abajo firmantes, reconocen haber leído las normas de uso del carnet durante la inscripción",
            "0_13_20231012041710": "",
            "0_14_20231012045321": "",
            "0_16_20241120130245": None,
            "1_9_20220308034849pm": '["No ceder mis datos"]',
            "1_10_20220309040836pm": "NO",
            "1_11_20220309113126pm": "NO",
            "0_15_20241120112536": None,
            "0_17_20250221121130": "22-06-2025",
            "paramsExtraFila": {
                "idColegiat": mydata["idColegiat"],
                "idModalitat": "33",
                "numColegiat": mydata["numColegiat"],
                "nomEstat": "ESTALTA",
                "nom": mydata["persona"]["nom"],
                "cognoms": mydata["persona"]["cognoms"],
                "nif": "",
                "residencia": "",
                "dataNaixement": "",
            },
        }


def createactividad(token,nom,lloc,maxplaces,minplaces,dataHoraActivitat,dataHoraFiActivitat,dataInici,dataLimit,descripcio,horario):

    url = f"{apiurl}/activitats"
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


    return requests.post(
        url,
        headers=headers,
        auth=BearerAuth(token),
        data=json.dumps(payload),
    )
