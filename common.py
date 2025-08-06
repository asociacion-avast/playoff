#!/usr/bin/env python

import configparser
import contextlib
import json
import os
from datetime import date

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


categorias = {
    "acogida": 74,
    "acogidaadultactiv": 112,
    "acogidaadultsinactiv": 113,
    "acogidaconactiv": 110,
    "acogidasinactiv": 111,
    "acogidacolab": 114,
    "actividades": 90,
    "adultoconactividades": 60,
    "adultosconysin": 95,
    "adultosinactividades": 53,
    "avast13": 66,
    "avast15": 65,
    "avast18": 77,
    "cambioadultoconactividades": 79,
    "cambioadultosin": 78,
    "cambiohermanoconactividades": 87,
    "cambiosocioconactividades": 81,
    "cambiosociosin": 80,
    "carnetduplicado": 102,
    "carnetincorrecto": 101,
    "carnetpendiente": 84,
    "carnettutorduplicado": 104,
    "conactividadessininscripciones": 109,
    "dana": 83,
    "gestionarcarnet": 84,
    "gestionarcarnetveterano": 98,
    "impagados": 103,
    "impagoanual": 105,
    "informerevisado": 94,
    "informevalidado": 94,
    "notienecarnet": 97,
    "nuevatanda": 74,
    "prioritario": 108,
    "revisar": 92,
    "sinactividades": 91,
    "sincarnetyactividades": 106,
    "sindoscarnetfamiliar": 100,
    "sinuncarnetfamiliar": 99,
    "socioactividades": 12,
    "socioactivo": 82,
    "sociohermanoactividades": 13,
    "sociosinactividades": 1,
}

diccionario = {
    # De la cateogria 36 a 48 son años de nacimiento, siendo 36 el año 2003
    1: "Socio principal sin actividades",
    103: "Impagados",
    105: "Impagado anualidad",
    12: "Socio principal con actividades",
    13: "Socio Hermano",
    32: "Candidato a Socio principal sin actividades",
    33: "Candidato a Socio principal con actividades",
    34: "Año 2010",
    35: "Año 2011",
    36: "Año 2003",
    37: "Año 2004",
    38: "Año 2005",
    39: "Año 2006",
    40: "Año 2007",
    41: "Año 2008",
    42: "Año 2009",
    43: "Año 2012",
    44: "Año 2013",
    45: "Año 2014",
    46: "Año 2015",
    47: "Año 2016",
    48: "Año 2017",
    50: "Año 2018",
    51: "Año 2019",
    53: "Adulto sin actividades",
    54: "Candidato a Adulto sin actividades",
    55: "Año 2002",
    56: "Año 2001",
    57: "Año 2000",
    59: "Candidato a Adulto con actividades",
    60: "Adulto con actividades",
    68: "Año 2021",
    69: "Año 2020",
    65: "Avast 15",
    66: "Avast 13",
    77: "Avast 18",
    70: "Año 2022",
    71: "Año 2024",
    72: "Año 2023",
    728: "Alta sin actividades",
    729: "Alta adulto actividades",
    730: "Alta niño actividades",
    732: "Alta Tutor actividades",
    733: "Alta Hermano Actividades",
    74: "Nueva tanda",
    748: "Alta adulto sin actividades",
    769: "Carnet tutor x2 Veterano",
    770: "Carnet tutor x1 Veterano",
    771: "Carnet Socio Veterano",
    777: "Alta unificada",
    78: "Autocambio ADULTO sin actividades",
    781: "Solicitar cambio a CON actividades",
    782: "Solicitar cambio a SIN actividades",
    79: "Autocambio ADULTO con actividades",
    80: "Autocambio SOCIO SIN actividades",
    81: "Autocambio SOCIO PRINCIPAL con actividades",
    815: "Solicitar correo ID TUTOR",
    816: "Solicitar correo ID SOCIO",
    82: "Asociado en activo",
    84: "Carnet pendiente",
    85: "Tutor con actividades",
    86: "Hermano con actividades",
    87: "Autocambio HERMANO actividades",
    90: "Socio con actividades",
    94: "Informe revisado",
    97: "Socio sin carnet",
    98: "Carnets veteranos",
}


# Definiciones

# 53: Adulto sin actividades
# 60: Adulto con actividades
# 12: Socio principal con actividades
# 1: Socio principal sin actividades


cambiospreinscrip = {32: 1, 33: 12, 54: 53, 59: 60, 85: 60, 86: 13}


cambios = {
    728: 1,
    729: 60,
    730: 12,
}


# Convierte numero de mes en nombre
nombremes = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}


def traduce(id):
    if id in diccionario:
        text = f"ID {id} ({diccionario[id]})"
    else:
        text = "ID %s no encontrado en diccionario" % id
    return text


apiurl = f"https://{config['auth']['endpoint']}.playoffinformatica.com/api.php/api/v1.0"
headers = {"Content-Type": "application/json", "content-encoding": "gzip"}
endpoint = config["auth"]["endpoint"]
sociobase = f"https://{endpoint}.playoffinformatica.com/FormAssociat.php?idColegiat="


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
    with open(f"data/{filename}.json", encoding="utf-8") as f:
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
    usersurl = f"{apiurl}/inscripcions?idActivitat={idactividad}"

    headers = {"Authorization": f"Bearer {token}"}
    users = requests.get(
        usersurl, auth=BearerAuth(token), headers=headers, timeout=15
    ).json()

    writejson(filename=f"{idactividad}", data=users)


def create_inscripcio(token, idActivitat, idColegiat):
    url = f"{apiurl}/inscripcions/public"

    if idColegiat is not None:
        colegiat = get_colegiat_data(idColegiat=idColegiat)

    data = {
        "inscripcions": [
            {
                "formatNouActivitat": True,
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
                "idColegiat": f"{idColegiat}",
                "idActivitat": idActivitat,
                "colegiat": colegiat,
            }
        ],
        "isEnviarNotificacio": 0,
    }
    return requests.post(
        url,
        data=json.dumps(data),
        auth=BearerAuth(token),
        headers=headers,
        allow_redirects=False,
        timeout=15,
    )


def anula_inscripcio(token, inscripcion, comunica=False):
    url = f"{apiurl}/inscripcions/{inscripcion}/anular"
    response = requests.patch(url, headers=headers, auth=BearerAuth(token), timeout=15)

    if comunica:
        url = f"{apiurl}/inscripcions/{inscripcion}/comunicar_anulacio"
        requests.post(url, headers=headers, auth=BearerAuth(token), timeout=15)

    return response


def delete_inscripcio(token, inscripcion):
    url = f"{apiurl}/inscripcions?idInscripcio={inscripcion}"
    response = requests.delete(url, headers=headers, auth=BearerAuth(token), timeout=15)

    return response


def get_colegiat_json(idColegiat=False):
    """
    Gets json for colegiat in full
    """
    socios = readjson("socios")

    for socio in socios:
        if int(socio["idColegiat"]) == int(idColegiat):
            return socio


def get_colegiat_data(idColegiat=False):
    """Get colegiat data for adding inscriptions

    Args:
        idColegiat (bool, optional): _description_. Defaults to False.

    Returns:
        _type_: _description_
    """
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


def createactividad(
    token,
    nom,
    lloc,
    maxplaces,
    minplaces,
    dataHoraActivitat,
    dataHoraFiActivitat,
    dataInici,
    dataLimit,
    descripcio,
    horario,
):
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
        "dataHoraActivitat": f"{dataHoraActivitat}",
        "dataHoraFiActivitat": f"{dataHoraFiActivitat}",
        "dataHoraIniciControlAcces": "",
        "dataInici": f"{dataInici}",
        "dataLimit": f"{dataLimit}",
        "nomCampDescripcio": "",
        "descripcio": f"{descripcio}",
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

    output = requests.post(
        url,
        headers=headers,
        auth=BearerAuth(token),
        data=json.dumps(payload),
        timeout=15,
    )
    with contextlib.suppress(Exception):
        output = json.loads(output)
    if isinstance(output, dict) and "idActivitat" in output:
        updateactividad(token=token, idactividad=output["idActivitat"])
        return output["idActivitat"]
    else:
        return output


def editaactividad(token, idActivitat, override):
    """Edita una actividad

    Args:
        token (str): Token para operaciones
        idActivitat (int): ID de la actividad a editar
        override (dict): Diccionario de parámetros a sobreescribir

    Returns:
        _type_: json de salida
    """

    url = f"{apiurl}/activitats/{idActivitat}"

    # Obtener json de  la actividad
    actividad = requests.get(url, headers=headers, auth=BearerAuth(token), timeout=15)

    actividad = json.loads(actividad.text)

    # Generar el nuevo json con el override de paraámetros
    payload = actividad
    payload.update(override)

    output = requests.put(
        url,
        headers=headers,
        auth=BearerAuth(token),
        data=json.dumps(payload),
        timeout=15,
    )
    with contextlib.suppress(Exception):
        output = json.loads(output.text)
    return output


def mes_proximo_bimestre(fecha=None):
    if fecha is None:
        fecha = date.today()
    mes = fecha.month

    # Definimos los bimestres en orden cíclico
    bimestres = [(9, 10), (11, 12), (1, 2), (3, 4), (5, 6)]

    # Regla especial: entre junio y agosto inclusive,
    # el cambio al bimestre 9–10 (septiembre–octubre) ocurre el 1 de septiembre
    if mes in [6, 7, 8]:
        return 7  # Seguimos considerando que el siguiente es septiembre

    # Buscar a qué bimestre pertenece el mes actual
    for i, (m1, m2) in enumerate(bimestres):
        if mes == m1 or mes == m2:
            next_index = (i + 1) % len(bimestres)
            if next_index == 0:
                return 7
            return bimestres[next_index][
                0
            ]  # Devolver primer mes del siguiente bimestre

    # Fallback por si algo falla
    return 7


def getcategoriassocio(socio):
    categorias = []
    if (
        socio
        and isinstance(socio, dict)
        and "colegiatHasModalitats" in socio
        and isinstance(socio["colegiatHasModalitats"], list)
    ):
        categorias.extend(
            int(categoria["idModalitat"])
            for categoria in socio["colegiatHasModalitats"]
            if "idModalitat" in categoria
        )
    return categorias


def enviacomunicado(token, data):
    """Sends a communication email notification using the provided token and data.

    This function posts a notification email to the API endpoint using the given authentication token and data payload.

    Args:
        token (str, optional): Authentication token for the API. Defaults to the global token.
        data (dict): Data payload to be sent in the notification.

    Returns:
        requests.Response: The response object from the API request.
    """

    comurl = f"{apiurl}/comunicats/emails_notificacions"
    headers = {"Authorization": f"Bearer {token}"}
    files = []
    return requests.request("POST", comurl, headers=headers, data=data, files=files)


def getcomunicadotutor(associat):
    true = True
    null = ""

    data = {
        "comunicat": json.dumps(
            {
                "idComunicat": 0,
                "titol": "Actualiza sus datos ID tutores",
                "descripcioIntro": """Hola, [[persona_nombre]]:<br><br><br>Estamos actualizando la base de datos para poder acceder al canal de Telegram oficial donde sólo participaran miembros de la asociación. Para que esto sea posible necesitas conseguir tu ID de telegram y añadirlo a tu ficha. Puedes añadir una ID por tutor. En nuestra web tienes el tutorial de como hacerlo.<br><br> https://asociacion-avast.org/registro-en-la-base-de-datos-de-avast-del-id-de-telegram/ <br><br><br>Necesitamos que accedas al siguiente enlace para configurarlo en nuestra base de datos:<br><br>[[invitacion_enlace_preinscripcion]]<br><br>*Recuerda que este enlace es válido sólo por [[invitacion_horas_validez]] horas.<br><br><br>Una vez registrado se te enviará el enlace al canal de Familias de AVAST.<br><br><br>Si tienes alguna duda o no te aclaras muy bien, tenemos un grupo de ayuda de Telegram para ayudarte: https://t.me/+9ou2gX99KLxjNWVk <br><br>Gracias por tu colaboración.<br><br>Atentamente,<br>Administración - AVAST""",
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
                "idConfiguracioFormulariColegi": "14",
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
    return data


def getcomunicadosocio(associat):
    true = True
    null = ""

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
    return data


def getcomunicado(associat, title, descripcio):
    true = True
    null = ""

    data = {
        "comunicat": json.dumps(
            {
                "idComunicat": 0,
                "titol": f"{title}",
                "descripcioIntro": f"{descripcio}",
                "adjunts": [],
                "estat": "COMESTESB",
                "dataEnviamentProgramada": null,
                "isLoaded": true,
            }
        ),
        "configBase": json.dumps(
            {
                "idConfiguracioComunicat": "1",
                "idFamiliaComunicat": 0,
                "tipusComunicat": "TPCGENERIC",
                "plantillaComunicat": "437",
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
    return data
