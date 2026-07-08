#!/usr/bin/env python

import configparser
import contextlib
import os
from datetime import date
from functools import lru_cache

# Use ujson (ultra-fast) if available, fallback to standard json (OPTIMIZATION)
try:
    import ujson as json
except ImportError:
    import json

import dateutil.parser
import requests

import sync_store

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))

# Telegramfields
tutor1 = "0_13_20231012041710"
tutor2 = "0_14_20231012045321"
socioid = "0_16_20241120130245"
telegramfields = [tutor1, tutor2, socioid]
fechacambio = "0_17_20250221121130"

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


def gettoken(user=config["auth"]["username"], password=config["auth"]["password"]):
    cache_key = (user, password)
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


def getcomunicadotutor(associat):
    true = True
    null = ""

    return {
        "comunicat": json.dumps(
            {
                "idComunicat": 0,
                "titol": "¡No te pierdas nada! Actualiza tu acceso a los canales exclusivos de AVAST",
                "descripcioIntro": """Hola, [[persona_nombre]]:<br><br>¿Sabías que nos estamos comunicando y compartiendo actividades exclusivas a través de Telegram? Para asegurarnos de que tu familia no se pierda ninguna información importante, necesitamos un pequeño paso por tu parte.<br><br>Actualmente, el acceso a nuestros grupos oficiales está restringido a socios registrados. Al actualizar tu ficha con tu ID de Telegram, podrás unirte no solo al canal general de familias, sino también a los grupos específicos de edades (+13, +15 y +18), donde se coordinan las actividades que más interesan a tus hijos.<br><br>¿Cómo hacerlo en 2 minutos?<br>Es muy sencillo y solo tienes que hacerlo una vez. Nota: No es tu número de teléfono, es tu ID de usuario.<br><br>Consulta este sencillo tutorial para obtener tu ID.<br><br>Accede a tu ficha personal aquí: [[invitacion_enlace_preinscripcion]]<br>(Este enlace es seguro y personal, recuerda que caduca en [[invitacion_horas_validez]] horas).<br><br>Una vez completado, te enviaremos automáticamente los enlaces para que te unas a los canales que corresponden a vuestra etapa.<br><br>¿Dudas? Si te atascas o necesitas ayuda técnica, nuestro equipo de soporte está disponible en este grupo de Telegram: https://t.me/+9ou2gX99KLxjNWVk<br><br>¡Gracias por ayudarnos a mantener a toda la comunidad conectada!<br><br>Atentamente,<br>Administración - AVAST""",
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


def getcomunicadosocio(associat):
    true = True
    null = ""

    return {
        "comunicat": json.dumps(
            {
                "idComunicat": 0,
                "titol": "¡Toma el control! Únete al grupo de AVAST para tu edad 🚀",
                "descripcioIntro": """¡Hola, [[persona_nombre]]!<br><br>En AVAST queremos que estés al tanto de todas las salidas, actividades y planes que preparamos para tu grupo de edad (+[Edad del socio]). Sabemos que a veces la información que llega a tus padres se pierde o no te llega a tiempo, y queremos cambiar eso.<br><br>¿Quieres enterarte de todo antes que nadie?<br>Queremos que estés en el canal oficial de Telegram de tu grupo. Para poder darte acceso directo, necesitamos que registres tu propio ID de Telegram en nuestra ficha de socio.<br><br>¿Qué ganas tú con esto?<br>Acceso directo: Recibirás las convocatorias de salidas y eventos directamente en tu móvil.<br><br>Autonomía: Serás tú quien gestione tu participación en las actividades.<br><br>Futuro: Al tener tus datos actualizados (teléfono y Telegram), estarás listo para dar el salto al grupo de adultos y seguir disfrutando de la comunidad cuando crezcas.<br><br>¿Cómo hacerlo? (Es muy fácil)<br>Mira este tutorial rápido de 1 minuto para ver cuál es tu ID.<br><br>Entra en este enlace y completa tu ficha: [[invitacion_enlace_preinscripcion]]<br><br>Nota: Solo tienes que hacerlo una vez.<br><br>Si tienes cualquier problema técnico o no encuentras tu ID, pregunta directamente en nuestro grupo de ayuda: https://t.me/+9ou2gX99KLxjNWVk<br><br>¡Nos vemos en el grupo!<br><br>El equipo de AVAST""",
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
