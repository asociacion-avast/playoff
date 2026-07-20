#!/usr/bin/env python

import base64
import configparser
import contextlib
import hashlib
import hmac
import json
import os
from datetime import date, datetime, timedelta
from functools import lru_cache

# Use ujson (ultra-fast) if available, fallback to standard json (OPTIMIZATION)
try:
    import ujson as json
except ImportError:
    import json

try:
    import dateutil.parser
except ImportError:
    import types
    from datetime import datetime

    class _SimpleDateParser:
        @staticmethod
        def parse(value):
            if isinstance(value, date):
                return datetime(value.year, value.month, value.day)
            if isinstance(value, datetime):
                return value
            if not isinstance(value, str):
                raise TypeError("Expected string or date")

            value = value.strip()
            if not value:
                raise ValueError("Empty date")

            if value.endswith("Z"):
                value = value[:-1] + "+00:00"

            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass

            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d"):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue

            raise ValueError(f"Unsupported date format: {value}")

    dateutil = types.SimpleNamespace(parser=_SimpleDateParser())

import requests

import sync_store

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))

# Campos de Telegram en PlayOff
tutor1 = "0_13_20231012041710"
tutor2 = "0_14_20231012045321"
socioid = "0_16_20241120130245"
telegramfields = [tutor1, tutor2, socioid]
fechacambio = "0_17_20250221121130"

# Campos destino en la ficha de socio por tipo de destinatario
campo_por_tipo = {
    "socio": socioid,
    "tutor1": tutor1,
    "tutor2": tutor2,
}

# Nombres legibles por código de campo
campo_nombre = {
    tutor1: "tutor1",
    tutor2: "tutor2",
    socioid: "socioid",
}


def nombre_campo_telegram(campo):
    """Devuelve el nombre legible de un campo de Telegram."""
    return campo_nombre.get(campo, campo)


# Secreto para firmar los tokens de vinculación de Telegram.
# Se lee de ~/.avast.ini [telegram] secret; si no existe se usa un valor por
# defecto (debe coincidir entre el script de envío y el bot de Telegram).
try:
    telegram_secret = config["telegram"]["secret"]
except Exception:
    telegram_secret = "CAMBIA_ESTE_SECRETO_EN_AVAST_INI"

# Caducidad por defecto de los enlaces de vinculación (días)
telegram_token_dias = int(config.get("telegram", "token_dias", fallback="30"))

# Prefijo del nombre del bot de Telegram usado en el enlace t.me/<BOT>?start=
telegram_botname = config.get("telegram", "botname", fallback="redken_bot")

# In-memory cache for JSON file loads and token requests
_json_cache = {}
_token_cache = {}

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


@lru_cache(maxsize=512)  # OPTIMIZATION Phase 3: Cache translation lookups
def traduce(id):
    return (
        f"ID {id} ({diccionario[id]})"
        if id in diccionario
        else f"ID {id} no encontrado en diccionario"
    )


apiurl = f"https://{config['auth']['endpoint']}.playoffinformatica.com/api.php/api/v1.0"
headers = {"Content-Type": "application/json", "content-encoding": "gzip"}
endpoint = config["auth"]["endpoint"]
sociobase = f"https://{endpoint}.playoffinformatica.com/FormAssociat.php?idColegiat="

# HTTP Session for connection pooling (OPTIMIZATION - Phase 2E)
# Reuses TCP connections instead of creating new ones for each request
_http_session = requests.Session()
# Don't set Content-Type globally - some endpoints need form data, some need JSON
_http_session.headers.update({"content-encoding": "gzip"})


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = f"Bearer {self.token}"
        return r


def gettoken(
    user=config["auth"]["username"],
    password=config["auth"]["password"],
    force_refresh=False,
):
    cache_key = (user, password)
    if force_refresh and cache_key in _token_cache:
        del _token_cache[cache_key]
    if cache_key in _token_cache:
        return _token_cache[cache_key]

    loginurl = f"{apiurl}/login/colegi"
    data = {"username": user, "password": password}

    result = _http_session.post(
        loginurl,
        data=json.dumps(data),
        headers={"Content-Type": "application/json"},
    )  # Use session (OPTIMIZATION)

    token = result.json()["access_token"]
    _token_cache[cache_key] = token
    return token


def writejson(filename, data):
    with open(f"data/{filename}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    _json_cache[filename] = data
    return True


def readjson(filename, refresh=False):
    if refresh and filename in _json_cache:
        del _json_cache[filename]
    if filename in _json_cache:
        return _json_cache[filename]

    with open(f"data/{filename}.json", encoding="utf-8") as f:
        data = json.load(f)
    _json_cache[filename] = data
    if filename == "socios" and isinstance(data, list):
        for socio in data:
            sync_store.enrich_socio_modalitats(socio)

            modalitats = socio.get("colegiatHasModalitats", [])
            categorias = []
            if isinstance(modalitats, list):
                # PRE-COMPUTE categories and cache on object (OPTIMIZATION - Phase 2A)
                for m in modalitats:
                    if isinstance(m, dict):
                        if "idModalitat" in m:
                            with contextlib.suppress(ValueError, TypeError):
                                categorias.append(int(m["idModalitat"]))
                        if "modalitat" in m:
                            m_data = m["modalitat"]
                            if isinstance(m_data, dict):
                                if "nom" in m_data:
                                    m_data["_nom_lower"] = m_data["nom"].lower()
                                if (
                                    "agrupacio" in m_data
                                    and isinstance(m_data["agrupacio"], dict)
                                    and "nom" in m_data["agrupacio"]
                                ):
                                    m_data["agrupacio"]["_nom_lower"] = m_data[
                                        "agrupacio"
                                    ]["nom"].lower()
            socio["_cached_categorias"] = categorias

            # PRE-CACHE dynamic fields for faster lookups (OPTIMIZATION - Item 2)
            if isinstance(socio.get("campsDinamics"), dict):
                socio["_cached_campos"] = {
                    field: socio["campsDinamics"].get(field) for field in telegramfields
                }
            else:
                socio["_cached_campos"] = {field: None for field in telegramfields}

            # PRE-COMPUTE common validations (OPTIMIZATION - Phase 2B/Item 3)
            socio["_valid_alta"] = validasocio(
                socio,
                estado="COLESTVAL",
                estatcolegiat="ESTALTA",
                agrupaciones=["PREINSCRIPCIÓN"],
                reverseagrupaciones=True,
            )
            socio["_valid_preinscripcion"] = validasocio(
                socio, estado="COLESTPRE", estatcolegiat="ESTALTA"
            )
            socio["_valid_baja"] = validasocio(
                socio, estado="COLESTVAL", estatcolegiat="ESTBAIXA"
            )
            socio["_valid_alta_or_preinscripcion"] = (
                socio["_valid_alta"] or socio["_valid_preinscripcion"]
            )
            socio["_valid_adulto_alta"] = socio["_valid_alta"] and any(
                c in [53, 60] for c in socio.get("_cached_categorias", [])
            )
    return data


def actividad_horario(actividad):
    """Return the integer horario for an actividad, using 0 when missing."""
    nivel = actividad.get("idNivell")
    if nivel and nivel != "null":
        try:
            return int(nivel)
        except (TypeError, ValueError):
            return 0
    return 0


def parse_date(value):
    """Parse a date string safely, returning None when invalid."""
    if not value:
        return None
    try:
        return dateutil.parser.parse(value)
    except Exception:
        return None


def safe_int(value, default=0):
    """Convert a value to int if possible, otherwise return default."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def is_socio_baja(socio):
    """Detect if a socio should be treated as baja for activity cleanup."""
    if socio.get("_valid_baja", False):
        return True
    if socio.get("_valid_alta_or_preinscripcion", False):
        categoriassocio = socio.get("_cached_categorias", [])
        return (
            categorias["actividades"] not in categoriassocio
            and categorias["impagoanual"] not in categoriassocio
        )
    return False


def is_online():
    return sync_store.is_online(apiurl)


def mutate(op, entity, entity_id, payload, token, *, dry_run=False, offline=False):
    """Apply optimistic local patch; call API if online, else queue mutation."""
    if dry_run:
        return None

    sync_store.apply_patch(op, entity, entity_id, payload)

    if offline or not is_online():
        sync_store.enqueue_mutation(op, entity, entity_id, payload)
        return None

    response = _execute_mutation(op, token, payload)
    if response is None or (
        hasattr(response, "status_code") and response.status_code >= 400
    ):
        sync_store.enqueue_mutation(op, entity, entity_id, payload)
    return response


def _execute_mutation(op, token, payload):
    if op == "addcategoria":
        return _addcategoria_api(
            token,
            payload["socio"],
            payload["categoria"],
            payload.get("extra") or False,
        )
    if op == "delcategoria":
        return _delcategoria_api(token, payload["socio"], payload["categoria"])
    if op == "escribecampo":
        return _escribecampo_api(
            token, payload["socioid"], payload["campo"], payload.get("valor", "")
        )
    if op == "create_inscripcio":
        return _create_inscripcio_api(
            token, payload["idActivitat"], payload["idColegiat"]
        )
    if op == "anula_inscripcio":
        return _anula_inscripcio_api(
            token, payload["inscripcion"], payload.get("comunica", False)
        )
    if op == "delete_inscripcio":
        return _delete_inscripcio_api(token, payload["inscripcion"])
    if op == "enviacomunicado":
        return _enviacomunicado_api(token, payload.get("data"))
    if op == "update_colegiat":
        return _update_colegiat_api(token, payload["socio_id"], payload["data"])
    if op == "update_tutor":
        return _update_tutor_api(
            token, payload["socio_id"], payload["tutor_id"], payload["data"]
        )
    return None


def flush_outbox(token):
    entries = sync_store.read_outbox()
    results = {"synced": 0, "failed": 0}
    for entry in entries:
        if entry.get("status") != "pending":
            continue
        response = _execute_mutation(entry["op"], token, entry["payload"])
        if response is None or (
            hasattr(response, "status_code") and response.status_code >= 400
        ):
            entry["status"] = "failed"
            entry["retries"] = entry.get("retries", 0) + 1
            if hasattr(response, "text"):
                entry["last_error"] = response.text[:500]
            else:
                entry["last_error"] = "request failed"
            results["failed"] += 1
        else:
            entry["status"] = "synced"
            entry["last_error"] = None
            results["synced"] += 1
    sync_store.write_outbox(entries)
    return results


def read_entity_colegiat(socio_id, token=None):
    def fetch(sid):
        if token is None:
            return None
        url = f"{apiurl}/colegiats/{sid}"
        response = requests.get(
            url, auth=BearerAuth(token), headers=headers, timeout=15
        )
        return response.json() if response.status_code == 200 else None

    return sync_store.read_entity(
        "colegiat", socio_id, fetch_fn=fetch if token else None
    )


def read_entity_rebuts(socio_id, token):
    def fetch(sid):
        url = f"{apiurl}/colegiats/rebuts?idColegiat={sid}&limit=1000"
        response = requests.get(
            url, headers=headers, auth=BearerAuth(token), timeout=15
        )
        return response.json() if response.status_code == 200 else None

    return sync_store.read_subresource("colegiat", socio_id, "rebuts", fetch_fn=fetch)


def read_entity_familia(socio_id, token):
    def fetch(sid):
        url = f"{apiurl}/colegiats/{sid}/familia"
        response = requests.get(
            url, headers=headers, auth=BearerAuth(token), timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            return data or []
        return None

    return sync_store.read_subresource("colegiat", socio_id, "familia", fetch_fn=fetch)


def _addcategoria_api(token, socio, categoria, extra=False):
    auth_headers = {"Authorization": f"Bearer {token}"}
    categoriaurl = f"{apiurl}/colegiats/{socio}/modalitats"
    data = {"idModalitat": categoria}
    if extra:
        data.update(extra)
    return _http_session.request(
        "POST", categoriaurl, headers=auth_headers, data=data, files=[]
    )  # Use session (OPTIMIZATION)


def addcategoria(token, socio, categoria, extra=False):
    """Adds categoria to socio."""
    payload = {
        "socio": socio,
        "categoria": categoria,
        "extra": extra or None,
    }
    return mutate("addcategoria", "colegiat", socio, payload, token)


def _delcategoria_api(token, socio, categoria):
    auth_headers = {"Authorization": f"Bearer {token}"}
    categoriaurl = f"{apiurl}/colegiats/{socio}/modalitats/{categoria}"
    return _http_session.request(  # Use session (OPTIMIZATION)
        "DELETE", categoriaurl, headers=auth_headers, data={}, files=[]
    )


def delcategoria(token, socio, categoria):
    """Removes categoria from socio."""
    payload = {"socio": socio, "categoria": categoria}
    return mutate("delcategoria", "colegiat", socio, payload, token)


def _escribecampo_api(token, socioid, campo, valor=""):
    comurl = f"{apiurl}/colegiats/{socioid}/campsdinamics"
    auth_headers = {"Authorization": f"Bearer {token}"}
    data = {f"{campo}": f"{valor}"}
    return _http_session.request(
        "PUT", comurl, headers=auth_headers, data=data, files=[]
    )  # Use session (OPTIMIZATION)


def escribecampo(token, socioid, campo, valor=""):
    """Escribe campo personalizado de socio."""
    payload = {"socioid": socioid, "campo": campo, "valor": valor}
    return mutate("escribecampo", "colegiat", socioid, payload, token)


def _update_colegiat_api(token, socio_id, payload):
    url = f"{apiurl}/colegiats"
    data = {"idColegiat": socio_id}
    data.update(payload)
    auth_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    return _http_session.put(
        url, headers=auth_headers, data=json.dumps(data), timeout=30
    )


def update_colegiat(token, socio_id, payload):
    """Actualiza datos del socio en PlayOff."""
    mutation_payload = {"socio_id": socio_id, "data": payload}
    return mutate("update_colegiat", "colegiat", socio_id, mutation_payload, token)


def _update_tutor_api(token, socio_id, tutor_id, payload):
    url = f"{apiurl}/colegiats/{socio_id}/tutors/{tutor_id}"
    auth_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    return _http_session.put(
        url, headers=auth_headers, data=json.dumps(payload), timeout=30
    )


def update_tutor(token, socio_id, tutor_id, payload):
    """Actualiza datos del tutor en PlayOff."""
    mutation_payload = {"socio_id": socio_id, "tutor_id": tutor_id, "data": payload}
    return mutate("update_tutor", "colegiat", socio_id, mutation_payload, token)


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

    if dia < 5 and mes in meses_cobro:
        return f"05/{mes:02d}/{año}"
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
        if (
            agrupaciones
            and "colegiatHasModalitats" in socio
            or not agrupaciones
            and subcategorias
            and "colegiatHasModalitats" in socio
        ):
            # Iterate over all categories for the user
            for modalitat in socio["colegiatHasModalitats"]:
                if "modalitat" in modalitat:
                    # Save name for comparing the ones we target
                    agrupacionom = modalitat["modalitat"]["agrupacio"]["nom"].lower()
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
        elif not agrupaciones and not subcategorias:
            return True
    return False


def _fetch_inscripciones_page(token, idactividad, page, page_size=100, attempts=3):
    url = f"{apiurl}/inscripcions?idActivitat={idactividad}&page={page}&pageSize={page_size}"
    for attempt in range(1, attempts + 1):
        try:
            response = _http_session.get(
                url,
                auth=BearerAuth(token),
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            print(
                f"Page fetch failed for actividad {idactividad} page {page} "
                f"(attempt {attempt}/{attempts}): {exc}",
                flush=True,
            )
            if attempt == attempts:
                raise


def _fetch_all_inscripciones(token, idactividad, *, page_size=100, max_pages=100):
    users = []
    seen_ids = set()
    page = 0

    while page < max_pages:
        print(
            f"Fetching inscripciones page {page} for actividad {idactividad}...",
            flush=True,
        )
        page_users = _fetch_inscripciones_page(
            token,
            idactividad,
            page,
            page_size,
        )

        if not isinstance(page_users, list):
            raise RuntimeError(
                f"Unexpected response format for actividad {idactividad} page {page}"
            )

        if page == 0 and not page_users:
            return []

        added = False
        for inscripcion in page_users:
            inscripcion_id = str(inscripcion.get("idInscripcio"))
            if inscripcion_id and inscripcion_id not in seen_ids:
                seen_ids.add(inscripcion_id)
                users.append(inscripcion)
                added = True

        if not added:
            break

        if len(page_users) < page_size:
            break

        page += 1

    return users


def updateactividad(token, idactividad, *, force=False, require_fresh=False):
    """Fetch inscripciones for actividad; fall back to local cache on failure."""
    cache_path = f"data/{idactividad}.json"
    error = None

    if force or is_online():
        try:
            return _extracted_from_updateactividad_8(idactividad, token, require_fresh)
        except requests.RequestException as exc:
            error = exc
            print(f"API fetch failed for actividad {idactividad}: {error}", flush=True)
        except RuntimeError as exc:
            error = exc
            print(
                f"Actividad fetch failed for actividad {idactividad}: {error}",
                flush=True,
            )
    else:
        print(
            f"Offline: skipping API fetch for actividad {idactividad}",
            flush=True,
        )

    if os.path.exists(cache_path) and not require_fresh:
        return readjson(filename=f"{idactividad}")
    if error is not None:
        raise RuntimeError(
            f"No cached inscripciones for actividad {idactividad} "
            f"and API request failed"
        ) from error
    raise RuntimeError(
        f"No cached inscripciones for actividad {idactividad} and API fetch was skipped"
    )


# TODO Rename this here and in `updateactividad`
def _extracted_from_updateactividad_8(idactividad, token, require_fresh):
    print(
        f"Fetching inscripciones for actividad {idactividad}...",
        flush=True,
    )
    users = _fetch_all_inscripciones(token, idactividad)

    if require_fresh and not users:
        raise RuntimeError(
            f"Actividad {idactividad} returned no inscripciones on fresh fetch"
        )

    writejson(filename=f"{idactividad}", data=users)
    print(
        f"Saved {len(users)} inscripciones for actividad {idactividad}",
        flush=True,
    )
    return users


def read_inscripciones_actividad(
    token,
    idactividad,
    *,
    refresh=False,
    require_fresh=False,
):
    """Load inscripciones for an actividad (cache first, else API with fallback)."""
    cache_path = f"data/{idactividad}.json"
    if not refresh and os.path.exists(cache_path):
        if require_fresh:
            return updateactividad(
                token,
                idactividad,
                force=True,
                require_fresh=True,
            )
        return readjson(filename=f"{idactividad}")
    return updateactividad(
        token,
        idactividad,
        force=refresh,
        require_fresh=require_fresh,
    )


def _create_inscripcio_api(token, idActivitat, idColegiat):
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
        timeout=30,
    )


def create_inscripcio(token, idActivitat, idColegiat):
    payload = {"idActivitat": idActivitat, "idColegiat": idColegiat}
    return mutate("create_inscripcio", "inscripcio", idColegiat, payload, token)


def _anula_inscripcio_api(token, inscripcion, comunica=False):
    url = f"{apiurl}/inscripcions/{inscripcion}/anular"
    response = _http_session.patch(
        url, headers=headers, auth=BearerAuth(token), timeout=30
    )  # Use session (OPTIMIZATION)

    if comunica:
        url = f"{apiurl}/inscripcions/{inscripcion}/comunicar_anulacio"
        _http_session.post(
            url, headers=headers, auth=BearerAuth(token), timeout=30
        )  # Use session (OPTIMIZATION)

    return response


def anula_inscripcio(token, inscripcion, comunica=False, idActivitat=None):
    payload = {
        "inscripcion": inscripcion,
        "comunica": comunica,
        "idActivitat": idActivitat,
    }
    return mutate("anula_inscripcio", "inscripcio", inscripcion, payload, token)


def _delete_inscripcio_api(token, inscripcion):
    url = f"{apiurl}/inscripcions?idInscripcio={inscripcion}"
    return _http_session.delete(
        url, headers=headers, auth=BearerAuth(token), timeout=30
    )  # Use session (OPTIMIZATION)


def delete_inscripcio(token, inscripcion, idActivitat=None):
    payload = {"inscripcion": inscripcion, "idActivitat": idActivitat}
    return mutate("delete_inscripcio", "inscripcio", inscripcion, payload, token)


def get_colegiat_json(idColegiat=False):
    """Gets json for colegiat in full."""
    return read_entity_colegiat(idColegiat)


def get_colegiat_data(idColegiat=False):
    """Get colegiat data for adding inscriptions."""
    if mydata := read_entity_colegiat(idColegiat):
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
        "idNivell": f"{horario}",
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
        "llocActivitat": f"{lloc}",
        "maxPlaces": f"{maxplaces}",
        "minPlaces": f"{minplaces}",
        "nom": f"{nom}",
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
        timeout=30,
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
    actividad = requests.get(url, headers=headers, auth=BearerAuth(token), timeout=30)

    actividad = json.loads(actividad.text)

    # Generar el nuevo json con el override de paraámetros
    payload = actividad
    payload.update(override)

    output = requests.put(
        url,
        headers=headers,
        auth=BearerAuth(token),
        data=json.dumps(payload),
        timeout=30,
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
        if mes in [m1, m2]:
            next_index = (i + 1) % len(bimestres)
            return 7 if next_index == 0 else bimestres[next_index][0]
    # Fallback por si algo falla
    return 7


def build_category_name_map(socios):
    """Build O(1) lookup map for category names to IDs (OPTIMIZATION - Item 1).
    Returns dict: {agrupacio_lower: {nom_lower: idModalitat}}
    """
    category_map = {}
    if not isinstance(socios, list):
        return category_map
    for socio in socios:
        if "colegiatHasModalitats" in socio:
            for modalitat in socio["colegiatHasModalitats"]:
                if "modalitat" in modalitat:
                    m_data = modalitat["modalitat"]
                    if "agrupacio" in m_data and "nom" in m_data:
                        agrupacio_lower = (
                            m_data["agrupacio"].get("_nom_lower")
                            or m_data["agrupacio"]["nom"].lower()
                        )
                        nom_lower = m_data.get("_nom_lower") or m_data["nom"].lower()
                        idModalitat = int(m_data.get("idModalitat", 0))
                        if agrupacio_lower not in category_map:
                            category_map[agrupacio_lower] = {}
                        category_map[agrupacio_lower][nom_lower] = idModalitat
    return category_map


def getcategoriassocio(socio):
    """Get categories for a socio (uses pre-computed cache if available - OPTIMIZATION)"""

    # Use pre-computed cache if available (FAST PATH - Phase 2A)
    if socio and isinstance(socio, dict) and "_cached_categorias" in socio:
        return socio["_cached_categorias"]

    # Fallback to original logic (for backward compatibility)
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


def es_socio_anual_activo(socio):
    """Check whether a socio has the active annual membership category."""
    if not socio or not isinstance(socio, dict):
        return False
    return categorias["socioactivo"] in getcategoriassocio(socio)


def is_personal_laboral(socio):
    """Indica si el socio es personal laboral (no debe aparecer en familias)."""
    if not socio or not isinstance(socio, dict):
        return False
    return (socio.get("estatColegiat") or {}).get("nom") == "ESTPERLAB"


def _coincide_nombre(nombre1, nombre2):
    """Compara dos nombres ignorando mayúsculas, minúsculas y acentos."""
    if not nombre1 or not nombre2:
        return False
    return normalize_name(nombre1) == normalize_name(nombre2)


def _nombre_completo(socio):
    """Obtiene el nombre completo de un socio o de un tutor."""
    if not socio or not isinstance(socio, dict):
        return ""
    if "persona" in socio:
        persona = socio.get("persona") or {}
        nom = persona.get("nom", "")
        cognoms = persona.get("cognoms", "")
    else:
        nom = socio.get("nom", "")
        cognoms = socio.get("cognoms", "")
    return f"{nom} {cognoms}".strip()


def _es_telegram_valido(valor):
    if valor is None:
        return False
    if isinstance(valor, str):
        return valor.strip() != "" and valor.strip().isdigit()
    return False


def copy_missing_telegram_from_family(socio_id, socios, familias):
    """Copia campos de Telegram de familiares si faltan en el socio.

    - Menores de edad: hereda tutor1 y tutor2 desde hermanos o familiares.
    - Mayores de edad: hereda socioid desde tutor1 o tutor2 del familiar,
      solo si el nombre del tutor coincide con el nombre del adulto.
      Los menores del grupo familiar sí se consideran como fuente.
    No limpia campos vacíos. Solo actúa si hay familiares y valores válidos.
    Retorna una lista de (campo, valor, id_familiar) copiados.
    """
    socio = next((s for s in socios if str(s.get("idColegiat")) == str(socio_id)), None)
    if not socio:
        return []
    camps = socio.get("campsDinamics", {}) or {}

    persona = socio.get("persona") or {}
    data_naixement = persona.get("dataNaixement")
    adult = False
    if data_naixement:
        try:
            born = dateutil.parser.parse(data_naixement)
            adult = date.today().year - born.year >= 18
        except Exception:
            adult = False

    miembros = familias.get("miembros") or {}
    family_list = miembros.get(str(socio_id)) or miembros.get(int(socio_id)) or []
    family_ids = {int(member) for member in family_list if member not in (None, "")}
    family_ids.discard(int(socio_id))

    missing = [
        campo
        for campo in (tutor1, tutor2, socioid)
        if not _es_telegram_valido(camps.get(campo))
    ]
    if not family_ids or not missing:
        return []

    copied = []
    adulto_nombre = _nombre_completo(socio)
    for fid in family_ids:
        if fid == socio_id:
            continue
        familiar = next(
            (s for s in socios if str(s.get("idColegiat")) == str(fid)), None
        )
        if not familiar:
            continue
        familiar_camps = familiar.get("campsDinamics", {}) or {}
        for campo in missing[:]:
            if campo in (tutor1, tutor2) and adult:
                continue
            if campo == socioid and not adult:
                continue
            valor = None
            if campo == socioid and adult:
                tutor1_nombre = _nombre_completo(familiar.get("tutor1") or {})
                tutor2_nombre = _nombre_completo(familiar.get("tutor2") or {})
                if _coincide_nombre(
                    adulto_nombre, tutor1_nombre
                ) and _es_telegram_valido(familiar_camps.get(tutor1)):
                    valor = familiar_camps[tutor1]
                elif _coincide_nombre(
                    adulto_nombre, tutor2_nombre
                ) and _es_telegram_valido(familiar_camps.get(tutor2)):
                    valor = familiar_camps[tutor2]
            else:
                valor = familiar_camps.get(campo)
            if not _es_telegram_valido(valor):
                continue
            if campo == socioid and valor in (
                familiar_camps.get(tutor1),
                familiar_camps.get(tutor2),
            ):
                if _es_telegram_valido(familiar_camps.get(socioid)):
                    continue
            if campo == socioid and valor in (camps.get(tutor1), camps.get(tutor2)):
                tutor_fields_to_clear = []
                if camps.get(tutor1) == valor:
                    tutor_fields_to_clear.append(tutor1)
                if camps.get(tutor2) == valor:
                    tutor_fields_to_clear.append(tutor2)
                if not _es_telegram_valido(camps.get(socioid)):
                    camps[socioid] = valor
                    for tf in tutor_fields_to_clear:
                        camps[tf] = ""
                    missing.remove(socioid)
                    copied.append((socioid, valor, fid))
                    for tf in tutor_fields_to_clear:
                        copied.append((tf, "", fid))
                continue
            camps[campo] = valor
            missing.remove(campo)
            copied.append((campo, valor, fid))
        if not missing:
            break
    if copied:
        socio["campsDinamics"] = camps
    return copied


_PARTICLES = {
    "de",
    "del",
    "la",
    "las",
    "el",
    "los",
    "y",
    "i",
    "van",
    "von",
    "de la",
    "de los",
    "de las",
    "la",
    "lo",
    "a",
    "da",
    "do",
    "dos",
    "del",
    "al",
    "dels",
    "d'",
}

_ACCENT_MAP = {
    "Abellan": "Abellán",
    "Adria": "Adrià",
    "Adrian": "Adrián",
    "Agullo": "Agulló",
    "Agustin": "Agustín",
    "Alcala": "Alcalá",
    "Alcazar": "Alcázar",
    "Alvarez": "Álvarez",
    "Alvaro": "Álvaro",
    "Andres": "Andrés",
    "Angel": "Ángel",
    "Angela": "Ángela",
    "Angeles": "Ángeles",
    "Arago": "Aragó",
    "Asuncion": "Asunción",
    "Avila": "Ávila",
    "Bauza": "Bauzá",
    "Beltran": "Beltrán",
    "Benjamin": "Benjamín",
    "Bermudez": "Bermúdez",
    "Bertran": "Bertrán",
    "Bondia": "Bondía",
    "Calderon": "Calderón",
    "Canto": "Cantó",
    "Cardenas": "Cárdenas",
    "Carlos Adrian": "Carlos Adrián",
    "Carlos Andres": "Carlos Andrés",
    "Carlos Angel": "Carlos Ángel",
    "Carlos Hector": "Carlos Héctor",
    "Carlos Joaquin": "Carlos Joaquín",
    "Carlos Oscar": "Carlos Óscar",
    "Carlos Ramon": "Carlos Ramón",
    "Carlos Raul": "Carlos Raúl",
    "Carlos Victor": "Carlos Víctor",
    "Carratala": "Carratalá",
    "Carrion": "Carrión",
    "Carrión": "Carrión",
    "Castan": "Castán",
    "Castañon": "Castañón",
    "Castello": "Castelló",
    "Catala": "Català",
    "Catalan": "Catalán",
    "Cebrian": "Cebrián",
    "Cerda": "Cerdà",
    "Cerdan": "Cerdán",
    "Cesar": "César",
    "Chavarrias": "Chavarrías",
    "Chavez": "Chávez",
    "Chulia": "Chulía",
    "Ciprian": "Ciprián",
    "Concepcion": "Concepción",
    "Corcoles": "Córcoles",
    "Cortes": "Cortés",
    "Cotoli": "Cotolí",
    "Cristobal": "Cristóbal",
    "Cristofol": "Cristòfol",
    "Diaz": "Díaz",
    "Dídac": "Dídac",
    "Dominguez": "Domínguez",
    "Elias": "Elías",
    "Escriva": "Escrivà",
    "Espi": "Espí",
    "Estelles": "Estellés",
    "Exposito": "Expósito",
    "Fernandez": "Fernández",
    "Ferre": "Ferré",
    "Fornes": "Fornés",
    "Frances": "Francés",
    "Fránces": "Francés",
    "Francisco Adrian": "Francisco Adrián",
    "Francisco Alberto": "Francisco Alberto",
    "Francisco Andres": "Francisco Andrés",
    "Francisco Angel": "Francisco Ángel",
    "Francisco Antonio": "Francisco Antonio",
    "Francisco Carlos": "Francisco Carlos",
    "Francisco Enrique": "Francisco Enrique",
    "Francisco Hector": "Francisco Héctor",
    "Francisco Javier": "Francisco Javier",
    "Francisco Joaquin": "Francisco Joaquín",
    "Francisco Jose": "Francisco José",
    "Francisco Luis": "Francisco Luis",
    "Francisco Manuel": "Francisco Manuel",
    "Francisco Nestor": "Francisco Néstor",
    "Francisco Oscar": "Francisco Óscar",
    "Francisco Pedro": "Francisco Pedro",
    "Francisco Ramon": "Francisco Ramón",
    "Francisco Raul": "Francisco Raúl",
    "Francisco Vicente": "Francisco Vicente",
    "Francisco Victor": "Francisco Víctor",
    "Fuste": "Fusté",
    "Gaitan": "Gaitán",
    "Galan": "Galán",
    "Gandia": "Gandía",
    "Garcia": "García",
    "Garvi": "Garví",
    "Gasco": "Gascó",
    "Gascon": "Gascón",
    "Gimenez": "Giménez",
    "Giron": "Girón",
    "Gomez": "Gómez",
    "Gonzalez": "González",
    "Guifre": "Guifré",
    "Guillen": "Guillén",
    "Gutierrez": "Gutiérrez",
    "Guzman": "Guzmán",
    "Hector": "Héctor",
    "Hernandez": "Hernández",
    "Hervas": "Hervás",
    "Ibañez": "Ibáñez",
    "Ines": "Inés",
    "Iolanda": "Iolanda",
    "Ivan": "Iván",
    "Jativa": "Játiva",
    "Jesus": "Jesús",
    "Jimenez": "Jiménez",
    "Joaquin": "Joaquín",
    "Jose Adrian": "José Adrián",
    "Jose Andres": "José Andrés",
    "Jose Angel": "José Ángel",
    "Jose Antonio": "José Antonio",
    "Jose Carlos": "José Carlos",
    "Jose Enrique": "José Enrique",
    "Jose Francisco": "José Francisco",
    "Jose Hector": "José Héctor",
    "Jose Joaquin": "José Joaquín",
    "Jose Luis": "José Luis",
    "Jose M.": "José M.",
    "Jose Manuel": "José Manuel",
    "Jose Maria": "José María",
    "Jose Miguel": "José Miguel",
    "Jose Nestor": "José Néstor",
    "Jose Oscar": "José Óscar",
    "Jose Ramon": "José Ramón",
    "Jose Raul": "José Raúl",
    "Jose Vicente": "José Vicente",
    "Jose Victor": "José Víctor",
    "Jose": "José",
    "Juan Adrian": "Juan Adrián",
    "Juan Andres": "Juan Andrés",
    "Juan Angel": "Juan Ángel",
    "Juan Hector": "Juan Héctor",
    "Juan Javier": "Juan Javier",
    "Juan Joaquin": "Juan Joaquín",
    "Juan Jose": "Juan José",
    "Juan Nestor": "Juan Néstor",
    "Juan Oscar": "Juan Óscar",
    "Juan Ramon": "Juan Ramón",
    "Juan Raul": "Juan Raúl",
    "Juan Victor": "Juan Víctor",
    "Lazaro": "Lázaro",
    "Leon": "León",
    "Llacer": "Llácer",
    "Lluis": "Lluís",
    "Lluisa": "Lluïsa",
    "Lopez": "López",
    "Lucia": "Lucía",
    "Luis Adrian": "Luis Adrián",
    "Luis Andres": "Luis Andrés",
    "Luis Angel": "Luis Ángel",
    "Luis Antonio": "Luis Antonio",
    "Luis Carlos": "Luis Carlos",
    "Luis Enrique": "Luis Enrique",
    "Luis Francisco": "Luis Francisco",
    "Luis Hector": "Luis Héctor",
    "Luis Javier": "Luis Javier",
    "Luis Joaquin": "Luis Joaquín",
    "Luis Manuel": "Luis Manuel",
    "Luis Miguel": "Luis Miguel",
    "Luis Nestor": "Luis Néstor",
    "Luis Oscar": "Luis Óscar",
    "Luis Pedro": "Luis Pedro",
    "Luis Ramon": "Luis Ramón",
    "Luis Raul": "Luis Raúl",
    "Luis Vicente": "Luis Vicente",
    "Luis Victor": "Luis Víctor",
    "Lujan": "Luján",
    "Macia": "Macía",
    "Macian": "Macián",
    "Macias": "Macías",
    "Manjon": "Manjón",
    "Mañez": "Máñez",
    "Mari": "Marí",
    "Maria Angeles": "María Ángeles",
    "Maria Antonia": "María Antonia",
    "Maria Assumpcio": "María Asunción",
    "Maria Asuncion": "María Asunción",
    "Maria Carmen": "María Carmen",
    "Maria Concepción": "María Concepción",
    "Maria Cristina": "María Cristina",
    "Maria de la Cruz": "María de la Cruz",
    "Maria de los Angeles": "María de los Ángeles",
    "Maria del Carmen": "María del Carmen",
    "Maria del Mar": "María del Mar",
    "Maria del Pilar": "María del Pilar",
    "Maria Dolores": "María Dolores",
    "Maria Gracia": "María Gracia",
    "Maria Inmaculada": "María Inmaculada",
    "Maria Isabel": "María Isabel",
    "Maria Jesus": "María Jesús",
    "Maria Jose": "María José",
    "Maria Josefa": "María Josefa",
    "Maria Lluisa": "María Lluisa",
    "Maria Luisa": "María Luisa",
    "Maria Luz": "María Luz",
    "Maria Mercedes": "María Mercedes",
    "Maria Montserrat": "María Montserrat",
    "Maria Pilar": "María Pilar",
    "Maria Rosa": "María Rosa",
    "Maria Soledad": "María Soledad",
    "Maria Teresa": "María Teresa",
    "Maria Victoria": "María Victoria",
    "Maria": "María",
    "Marin": "Marín",
    "Marmol": "Mármol",
    "Marques": "Marqués",
    "Marquez": "Márquez",
    "Marti": "Martí",
    "Martin": "Martín",
    "Martinez": "Martínez",
    "Mascaros": "Mascarós",
    "Matias": "Matías",
    "Mendez": "Méndez",
    "Merli": "Merlí",
    "Miguel Adrian": "Miguel Adrián",
    "Miguel Alberto": "Miguel Alberto",
    "Miguel Andres": "Miguel Andrés",
    "Miguel Angel": "Miguel Ángel",
    "Miguel Antonio": "Miguel Antonio",
    "Miguel Carlos": "Miguel Carlos",
    "Miguel Enrique": "Miguel Enrique",
    "Miguel Francisco": "Miguel Francisco",
    "Miguel Hector": "Miguel Héctor",
    "Miguel Javier": "Miguel Javier",
    "Miguel Joaquin": "Miguel Joaquín",
    "Miguel Manuel": "Miguel Manuel",
    "Miguel Nestor": "Miguel Néstor",
    "Miguel Oscar": "Miguel Óscar",
    "Miguel Pedro": "Miguel Pedro",
    "Miguel Ramon": "Miguel Ramón",
    "Miguel Raul": "Miguel Raúl",
    "Miguel Vicente": "Miguel Vicente",
    "Miguel Victor": "Miguel Víctor",
    "Milan": "Milán",
    "Millan": "Millán",
    "Minguet": "Minguet",
    "Miquel": "Miquel",
    "Miralpeix": "Miralpeix",
    "Mireia": "Mireia",
    "Mocholi": "Mocholí",
    "Molina": "Molina",
    "Mompo": "Mompó",
    "Mondrago": "Mondragó",
    "Monica": "Mónica",
    "Monleon": "Monleón",
    "Monros": "Monrós",
    "Monton": "Montón",
    "Montoya": "Montoya",
    "Montse": "Montse",
    "Monzo": "Monzó",
    "Moragon": "Moragón",
    "Moran": "Morán",
    "Moron": "Morón",
    "Narcis": "Narcís",
    "Navalon": "Navalón",
    "Navio": "Navío",
    "Nestor": "Néstor",
    "Nogueron": "Noguerón",
    "Nuñez": "Núñez",
    "Nuria": "Núria",
    "Orti": "Ortí",
    "Ortiz": "Ortíz",
    "Oscar": "Òscar",
    "Pallares": "Pallarès",
    "Pedron": "Pedrón",
    "Peiro": "Peiró",
    "Perez": "Pérez",
    "Pla": "Plà",
    "Ramirez": "Ramírez",
    "Ramon": "Ramón",
    "Raul": "Raúl",
    "Rene": "René",
    "Rodriguez": "Rodríguez",
    "Roldan": "Roldán",
    "Rosello": "Roselló",
    "Ruben": "Rubén",
    "Rubio": "Rubio",
    "Ruiperez": "Ruipérez",
    "Saez": "Sáez",
    "Sanchez": "Sánchez",
    "Sanchis": "Sanchís",
    "Sanjuan": "Sanjuán",
    "Sanroma": "Sanromà",
    "Santamaria": "Santamaría",
    "Sarrion": "Sarrión",
    "Sebastia": "Sebastià",
    "Sebastian": "Sebastián",
    "Segui": "Seguí",
    "Simo": "Simó",
    "Simon": "Simón",
    "Sofia": "Sofía",
    "Solis": "Solís",
    "Suarez": "Suárez",
    "Tarin": "Tarín",
    "Tarrago": "Tarragó",
    "Tellez": "Téllez",
    "Tetuan": "Tetuán",
    "Tomas": "Tomás",
    "Torra": "Torrà",
    "Tristan": "Tristán",
    "Ubeda": "Úbeda",
    "Valcarcel": "Valcárcel",
    "Valentin": "Valentín",
    "Vazquez": "Vázquez",
    "Verdu": "Verdú",
    "Veronica": "Verónica",
    "Victor": "Víctor",
    "Villanueva": "Villanueva",
    "Vivo": "Vivó",
    "Yebenes": "Yébenes",
    "Zacarias": "Zacarías",
}


def _normalize_part(part):
    part = part.lower()
    return part if part in _PARTICLES else part.capitalize()


def normalize_name(name):
    """Normaliza un nombre propio con mayúsculas/minúsculas correctas y acentos."""
    if not name or not isinstance(name, str):
        return name
    parts = name.split()
    normalized_parts = []
    for part in parts:
        subparts = part.split("-")
        normalized_subparts = []
        for sub in subparts:
            normalized = _normalize_part(sub)
            normalized_subparts.append(_ACCENT_MAP.get(normalized, normalized))
        normalized_parts.append("-".join(normalized_subparts))
    return " ".join(normalized_parts)


def clean_spaces(value):
    """Reemplaza múltiples espacios por uno solo y elimina espacios extremos."""
    if not value or not isinstance(value, str):
        return value
    return " ".join(value.split())


def _enviacomunicado_api(token, data):
    comurl = f"{apiurl}/comunicats/emails_notificacions"
    # Don't use session here - this endpoint needs form data, not JSON
    # Session has Content-Type: application/json which breaks this API
    auth_headers = {"Authorization": f"Bearer {token}"}
    return requests.request("POST", comurl, headers=auth_headers, data=data, files=[])


def enviacomunicado(token, data):
    """Sends a communication email notification."""
    payload = {"data": data}
    return mutate("enviacomunicado", "comunicat", 0, payload, token)


def getcomunicadotutor(associat, enlace=None):
    true = True
    null = ""

    text = """Hola, [[persona_nombre]]:<br><br>¿Sabías que nos estamos comunicando y compartiendo actividades exclusivas a través de Telegram? Para asegurarnos de que tu familia no se pierda ninguna información importante, necesitamos un pequeño paso por tu parte.<br><br>Actualmente, el acceso a nuestros grupos oficiales está restringido a socios registrados. Al vincular tu cuenta de Telegram, podrás unirte no solo al canal general de familias, sino también a los grupos específicos de edades (+13, +15 y +18), donde se coordinan las actividades que más interesan a tus hijos.<br><br>¿Cómo hacerlo? En un solo paso: pulsa el botón inferior y luego pulsa "Iniciar" (Start) en Telegram. No tienes que copiar ni escribir ningún número: la vinculación se hace automáticamente y de forma segura."""

    if enlace:
        text += (
            '<br><br>👉 <a href="%s">Vincular mi Telegram</a><br><br>Si el botón no funciona, copia y pega este enlace en tu navegador: %s'
            % (
                enlace,
                enlace,
            )
        )
    else:
        text += "<br><br>Accede a tu ficha personal aquí: [[invitacion_enlace_preinscripcion]]<br>(Este enlace es seguro y personal, recuerda que caduca en [[invitacion_horas_validez]] horas)."

    text += "<br><br>Una vez vinculado, te enviaremos automáticamente los enlaces para que te unas a los canales que corresponden a vuestra etapa.<br><br>¿Dudas? Si necesitas ayuda técnica, nuestro equipo de soporte está disponible en este grupo de Telegram: https://t.me/+9ou2gX99KLxjNWVk<br><br>¡Gracias por ayudarnos a mantener a toda la comunidad conectada!<br><br>Atentamente,<br>Administración - AVAST"

    # Si disponemos del enlace firmado, añadimos un botón de acción directa.
    botons = []
    if enlace:
        botons = [
            {
                "text": "Vincular mi Telegram",
                "url": enlace,
            }
        ]

    comunicat = {
        "idComunicat": 0,
        "titol": "¡No te pierdas nada! Actualiza tu acceso a los canales exclusivos de AVAST",
        "descripcioIntro": text,
        "adjunts": [],
        "estat": "COMESTESB",
        "dataEnviamentProgramada": null,
        "isLoaded": true,
    }
    if botons:
        comunicat["botons"] = botons

    return {
        "comunicat": json.dumps(comunicat),
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
                "setEstatReclamacioImpagots": 0,
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


def getcomunicadosocio(associat, enlace=None):
    true = True
    null = ""

    text = """¡Hola, [[persona_nombre]]!<br><br>En AVAST queremos que estés al tanto de todas las salidas, actividades y planes que preparamos para tu grupo de edad (+[Edad del socio]). Sabemos que a veces la información que llega a tus padres se pierde o no te llega a tiempo, y queremos cambiar eso.<br><br>¿Quieres enterarte de todo antes que nadie?<br>Queremos que estés en el canal oficial de Telegram de tu grupo. Para poder darte acceso directo, solo tienes que vincular tu cuenta de Telegram con un toque.<br><br>¿Qué ganas tú con esto?<br>Acceso directo: Recibirás las convocatorias de salidas y eventos directamente en tu móvil.<br><br>Autonomía: Serás tú quien gestione tu participación en las actividades.<br><br>Futuro: Al tener tus datos actualizados (teléfono y Telegram), estarás listo para dar el salto al grupo de adultos y seguir disfrutando de la comunidad cuando crezcas.<br><br>¿Cómo hacerlo? En un solo paso: pulsa el botón inferior y luego pulsa "Iniciar" (Start) en Telegram. No tienes que copiar ni escribir ningún número: la vinculación se hace automáticamente y de forma segura."""

    if enlace:
        text += (
            '<br><br>👉 <a href="%s">Vincular mi Telegram</a><br><br>Si el botón no funciona, copia y pega este enlace en tu navegador: %s'
            % (
                enlace,
                enlace,
            )
        )
    else:
        text += "<br><br>Entra en este enlace y completa tu ficha: [[invitacion_enlace_preinscripcion]]<br><br>Nota: Solo tienes que hacerlo una vez."

    text += "<br><br>Si tienes cualquier problema técnico o no encuentras tu ID, pregunta directamente en nuestro grupo de ayuda: https://t.me/+9ou2gX99KLxjNWVk<br><br>¡Nos vemos en el grupo!<br><br>El equipo de AVAST"

    botons = []
    if enlace:
        botons = [
            {
                "text": "Vincular mi Telegram",
                "url": enlace,
            }
        ]

    comunicat = {
        "idComunicat": 0,
        "titol": "¡Toma el control! Únete al grupo de AVAST para tu edad 🚀",
        "descripcioIntro": text,
        "adjunts": [],
        "estat": "COMESTESB",
        "dataEnviamentProgramada": null,
        "isLoaded": true,
    }
    if botons:
        comunicat["botons"] = botons

    return {
        "comunicat": json.dumps(comunicat),
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


def getcomunicado(associat, title, descripcio):
    true = True
    null = ""

    return {
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


# OPTIMIZATION Phase 4: Parallel processing helper
def process_socios_parallel(socios, worker_func, max_workers=None):
    """
    Process socios in parallel using multiprocessing.

    Args:
        socios: List of socio dictionaries
        worker_func: Function to apply to each socio (must be picklable)
        max_workers: Number of worker processes (default: CPU count - 1)

    Returns:
        List of results in the same order as input socios

    Example:
        def classify_socio(socio):
            if socio.get("_valid_alta", False):
                return ("alta", socio["idColegiat"])
            return ("other", socio["idColegiat"])

        results = process_socios_parallel(socios, classify_socio)
    """
    from multiprocessing import Pool, cpu_count

    if max_workers is None:
        max_workers = max(1, cpu_count() - 1)

    # For small datasets, parallel overhead isn't worth it
    if len(socios) < 100:
        return [worker_func(s) for s in socios]

    with Pool(processes=max_workers) as pool:
        results = pool.map(worker_func, socios)

    return results


# ---------------------------------------------------------------------------
# Vinculación automática de Telegram (token firmado)
# ---------------------------------------------------------------------------
# El script de envío de correos genera un token firmado con HMAC que contiene
# el idSocio y el tipo de destinatario (socio / tutor1 / tutor2). El bot de
# Telegram verifica la firma y la caducidad, y actualiza el campo
# correspondiente de la ficha del socio en PlayOff sin que el usuario tenga que
# copiar/pegar ningún identificador manualmente.


def base36_encode(numero: int) -> str:
    """Codifica un entero en base36 (sin prefijo) para acortar el token."""
    if numero < 0:
        raise ValueError("base36 no admite negativos")
    if numero == 0:
        return "0"
    caracteres = "0123456789abcdefghijklmnopqrstuvwxyz"
    resultado = ""
    while numero:
        numero, resto = divmod(numero, 36)
        resultado = caracteres[resto] + resultado
    return resultado


def base36_decode(texto: str) -> int:
    """Decodifica una cadena base36 a entero."""
    return int(texto, 36)


# Códigos cortos de tipo de destinatario (clave para que el token quepa en el
# límite de 64 caracteres del parámetro 'start' de los enlaces t.me).
TIPO_A_CODIGO = {
    "socio": "s",
    "tutor1": "1",
    "tutor2": "2",
    "tutor": "u",
}
CODIGO_A_TIPO = {v: k for k, v in TIPO_A_CODIGO.items()}

# La firma HMAC-SHA256 se trunca a 16 bytes (128 bits) para acortar el token.
# Sigue siendo resistente a la falsificación para este caso de uso.
_LON_FIRMA = 16


def _firma_b32(secret: str, payload: bytes) -> str:
    """Firma HMAC-SHA256 truncada y codificada en BASE32.

    El alfabeto BASE32 (A-Z, 2-7) es seguro para el parámetro 'start' de
    Telegram (no contiene '.', '_', '&' ni '|', que rompen o se ignoran en el
    enlace profundo t.me).
    """
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()
    return base64.b32encode(digest[:_LON_FIRMA]).rstrip(b"=").decode("ascii").lower()


def genera_token_telegram(
    id_socio,
    tipo="socio",
    dias=None,
    secret=None,
):
    """Genera un token firmado y compacto para vincular un Telegram ID.

    Formato: ``<idSocio>-<codigo>-<expB36>-<firmaB32>`` unido con guiones.
    Solo usa caracteres permitidos por Telegram en el parámetro 'start'
    (A-Z a-z 0-9 _ -), de modo que el enlace profundo t.me dispara
    automáticamente ``/start link_<TOKEN>`` al abrirse.

    Args:
        id_socio: idColegiat del socio en PlayOff.
        tipo: "socio", "tutor1", "tutor2" o "tutor" (ambiguous).
        dias: caducidad en días (por defecto telegram_token_dias).
        secret: secreto HMAC (por defecto telegram_secret).

    Returns:
        str: token listo para usar en /start link_<TOKEN>.
    """
    if secret is None:
        secret = telegram_secret
    if dias is None:
        dias = telegram_token_dias

    codigo = TIPO_A_CODIGO.get(tipo, "s")
    expira = int((datetime.now() + timedelta(days=dias)).timestamp())
    expira_b36 = base36_encode(expira)
    cuerpo = f"{int(id_socio)}-{codigo}-{expira_b36}".encode()
    firma = _firma_b32(secret, cuerpo)
    return f"{cuerpo.decode('ascii')}-{firma}"


def verifica_token_telegram(token, secret=None):
    """Verifica un token firmado y devuelve su contenido.

    Args:
        token: token devuelto por genera_token_telegram.
        secret: secreto HMAC (por defecto telegram_secret).

    Returns:
        dict con claves "idSocio", "tipo" y "caduca" si es válido y no ha
        caducado, o False en caso contrario (formato, firma inválida o
        expirado).
    """
    if secret is None:
        secret = telegram_secret
    if not token or "-" not in token:
        return False

    try:
        partes = token.split("-")
        if len(partes) != 4:
            return False
        id_socio_s, codigo, expira_b36, firma = partes
        payload = f"{id_socio_s}-{codigo}-{expira_b36}".encode()
    except Exception:
        return False

    esperada = _firma_b32(secret, payload)
    if not hmac.compare_digest(esperada, firma):
        return False

    try:
        id_socio = int(id_socio_s)
        tipo = CODIGO_A_TIPO.get(codigo, "socio")
        expira = base36_decode(expira_b36)
        caduca = datetime.fromtimestamp(expira)
    except Exception:
        return False

    if caduca < datetime.now():
        return False

    return {
        "idSocio": id_socio,
        "tipo": tipo,
        "caduca": caduca.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def enlace_vinculacion_telegram(id_socio, tipo="socio", dias=None, secret=None):
    """Devuelve la URL del bot con el token de vinculación embebido."""
    token = genera_token_telegram(id_socio, tipo=tipo, dias=dias, secret=secret)
    return f"https://t.me/{telegram_botname}?start=link_{token}"
