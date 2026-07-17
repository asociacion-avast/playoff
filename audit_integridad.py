"""Reglas de auditoría, sin efectos laterales, para los datos de PlayOff.

Las reglas trabajan exclusivamente sobre instantáneas locales.  La API no se
consulta y este módulo no corrige nada: los hallazgos son deliberadamente
conservadores para que puedan revisarse antes de automatizar una reparación.
"""

import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

CAT = {
    "sin_actividades": 91,
    "actividades": 90,
    "socio_principal_actividades": 12,
    "socio_hermano_actividades": 13,
    "adulto_sin_actividades": 53,
    "adulto_con_actividades": 60,
    "adulto": 95,
    "socio_activo": 82,
    "impagados": 103,
    "impago_anual": 105,
    "avast13": 66,
    "avast15": 65,
    "avast18": 77,
}
ACTIVE_INSCRIPTION_STATES = {"INSCRESTNOVA", "INSCRESTVALIDA", "INSCRESTPENDENT"}
PROFILE_URL = (
    "https://asociacionavast.playoffinformatica.com/FormAssociat.php?idColegiat={id}"
)


def parse_date(value):
    if not value or value in {"0000-00-00", "null"}:
        return None
    if isinstance(value, (datetime, date)):
        return value.date() if isinstance(value, datetime) else value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(value), fmt).date()
        except ValueError:
            pass
    return None


def member_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def categories(socio):
    result = set()
    for item in socio.get("colegiatHasModalitats") or []:
        value = member_id(item.get("idModalitat")) if isinstance(item, dict) else None
        if value is not None:
            result.add(value)
    return result


def active_member(socio):
    return (
        socio.get("estat") == "COLESTVAL"
        and (socio.get("estatColegiat") or {}).get("nom") == "ESTALTA"
    )


def is_personal_laboral(socio):
    return (socio.get("estatColegiat") or {}).get("nom") == "ESTPERLAB"


def valid_phone(number, prefix=""):
    """Acepta números españoles de 9 cifras o internacionales en E.164.

    El prefijo se guarda separado en PlayOff; por ello no se exige ``+`` en el
    campo principal cuando el prefijo ya indica un país distinto de España.
    """
    raw = str(number or "").strip()
    digits = re.sub(r"\D", "", raw)
    if not digits or len(set(digits)) == 1:
        return False
    prefix_digits = re.sub(r"\D", "", str(prefix or ""))
    if prefix_digits in {"", "34"}:
        return len(digits) == 9 and digits[0] in "6789"
    return 8 <= len(digits) <= 15


def valid_iban(value):
    """Comprueba formato básico y checksum IBAN (módulo 97)."""
    iban = re.sub(r"\s", "", str(value or "")).upper()
    if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}", iban):
        return False
    rearranged = iban[4:] + iban[:4]
    numeric = "".join(
        str(ord(char) - 55) if char.isalpha() else char for char in rearranged
    )
    return int(numeric) % 97 == 1


def near_birthday_month(birth, today):
    """Indica si hoy cae en el mes del cumpleaños o en los adyacentes."""
    previous_month = 12 if birth.month == 1 else birth.month - 1
    next_month = 1 if birth.month == 12 else birth.month + 1
    return today.month in {previous_month, birth.month, next_month}


def finding(code, severity, entity, entity_id, message, **details):
    result = {
        "code": code,
        "severity": severity,
        "entity": entity,
        "id": str(entity_id),
        "message": message,
        "details": details,
    }
    if entity in {"familia", "socio"} and member_id(entity_id) is not None:
        result["url"] = PROFILE_URL.format(id=entity_id)
    return result


def add_duplicate_findings(result, values, code, entity, label):
    for value, ids in values.items():
        ids = sorted(set(ids))
        if value and len(ids) > 1:
            result.append(
                finding(
                    code,
                    "warning",
                    entity,
                    ",".join(map(str, ids)),
                    f"{label} duplicado: {value}",
                    members=ids,
                )
            )


def audit_socios(socios, today):
    result, by_id = [], {}
    dni, number = (defaultdict(list) for _ in range(2))
    ranges = {
        CAT["avast13"]: range(13, 15),
        CAT["avast15"]: range(15, 18),
        CAT["avast18"]: range(18, 25),
    }
    for socio in socios:
        sid = member_id(socio.get("idColegiat"))
        if sid is None:
            result.append(
                finding(
                    "SOCIO_ID_INVALIDO",
                    "error",
                    "socio",
                    "?",
                    "idColegiat ausente o inválido",
                )
            )
            continue
        if sid in by_id:
            result.append(
                finding(
                    "SOCIO_ID_DUPLICADO", "error", "socio", sid, "idColegiat duplicado"
                )
            )
        by_id[sid] = socio
        if not active_member(socio):
            continue
        persona = socio.get("persona") or {}
        cats = categories(socio)
        missing = [
            key
            for key, value in {
                "nombre": persona.get("nom"),
                "apellidos": persona.get("cognoms"),
            }.items()
            if not str(value or "").strip()
        ]
        addresses = persona.get("adreces") or []
        address = addresses[0] if addresses and isinstance(addresses[0], dict) else {}
        if not (address.get("email") or address.get("emailOficial")):
            missing.append("email")
        if not address.get("telefonPrincipal"):
            missing.append("teléfono")
        if missing:
            result.append(
                finding(
                    "SOCIO_CAMPOS_OBLIGATORIOS",
                    "warning",
                    "socio",
                    sid,
                    "Socio activo con campos obligatorios vacíos",
                    fields=missing,
                )
            )
        birth = parse_date(persona.get("dataNaixement"))
        if birth is None:
            result.append(
                finding(
                    "SOCIO_NACIMIENTO_AUSENTE",
                    "warning",
                    "socio",
                    sid,
                    "Fecha de nacimiento ausente o inválida",
                )
            )
        elif birth > today:
            result.append(
                finding(
                    "SOCIO_NACIMIENTO_FUTURO",
                    "error",
                    "socio",
                    sid,
                    "Fecha de nacimiento futura",
                )
            )
        elif cats & set(ranges):
            age = (
                today.year
                - birth.year
                - ((today.month, today.day) < (birth.month, birth.day))
            )
            expected = {cat for cat, ages in ranges.items() if age in ages}
            actual = cats & set(ranges)
            if actual != expected and not near_birthday_month(birth, today):
                result.append(
                    finding(
                        "SOCIO_TRAMO_EDAD_INCORRECTO",
                        "warning",
                        "socio",
                        sid,
                        "Categoría Avast no corresponde a la edad",
                        age=age,
                        actual=sorted(actual),
                        expected=sorted(expected),
                    )
                )
        if CAT["actividades"] in cats and CAT["sin_actividades"] in cats:
            result.append(
                finding(
                    "SOCIO_CATEGORIAS_INCOMPATIBLES",
                    "error",
                    "socio",
                    sid,
                    "Tiene categorías con y sin actividades",
                )
            )
        base_categories = {
            1,
            CAT["socio_principal_actividades"],
            CAT["socio_hermano_actividades"],
            CAT["adulto_sin_actividades"],
            CAT["adulto_con_actividades"],
        }
        if not (cats & base_categories):
            result.append(
                finding(
                    "SOCIO_SIN_CATEGORIA_PRINCIPAL",
                    "warning",
                    "socio",
                    sid,
                    "Socio activo sin categoría principal de modalidad",
                )
            )
        if len(cats & set(ranges)) > 1:
            result.append(
                finding(
                    "SOCIO_TRAMOS_EDAD_MULTIPLES",
                    "error",
                    "socio",
                    sid,
                    "Tiene más de un tramo Avast",
                )
            )
        if CAT["impago_anual"] in cats and CAT["socio_activo"] in cats:
            result.append(
                finding(
                    "SOCIO_IMPAGO_ACTIVO",
                    "warning",
                    "socio",
                    sid,
                    "Impago anual y asociado activo simultáneamente",
                )
            )
        nif = re.sub(r"[^A-Z0-9]", "", str(persona.get("nif") or "").upper())
        if nif:
            dni[nif].append(sid)
            if len(nif) < 7:
                result.append(
                    finding(
                        "SOCIO_NIF_FORMATO",
                        "warning",
                        "socio",
                        sid,
                        "NIF/NIE demasiado corto",
                        value=nif,
                    )
                )
        num = str(socio.get("numColegiat") or "").strip().lower()
        if num and num != "-":
            number[num].append(sid)
        for field, prefix_field in (
            ("telefonPrincipal", "prefixTelefonPrincipal"),
            ("telefonSecundari", "prefixTelefonSecundari"),
        ):
            value = address.get(field)
            if value and not valid_phone(value, address.get(prefix_field)):
                result.append(
                    finding(
                        "SOCIO_TELEFONO_FORMATO",
                        "warning",
                        "socio",
                        sid,
                        "Teléfono con formato o longitud no válidos",
                        field=field,
                        value=str(value),
                    )
                )
        for bank in socio.get("bancs") or []:
            iban = re.sub(r"\s", "", str((bank or {}).get("iban") or "")).upper()
            if iban and not valid_iban(iban):
                result.append(
                    finding(
                        "SOCIO_IBAN_FORMATO",
                        "warning",
                        "socio",
                        sid,
                        "IBAN con formato o checksum no válidos",
                        value=iban,
                    )
                )
    add_duplicate_findings(result, dni, "SOCIO_NIF_DUPLICADO", "socio", "NIF/NIE")
    add_duplicate_findings(
        result, number, "SOCIO_NUMERO_DUPLICADO", "socio", "Número de socio"
    )
    return result, by_id


def audit_familias(familias, socios):
    result, seen = [], defaultdict(set)
    members = (familias or {}).get("miembros") or {}
    ids = set(socios)
    normalized = {}
    for raw_key, raw_values in members.items():
        key = member_id(raw_key)
        if key is None:
            continue
        values = []
        for v in raw_values or []:
            nid = member_id(v)
            if nid is not None:
                values.append(nid)
        normalized[key] = values
    titular_map, nif_map = defaultdict(set), defaultdict(set)
    for sid, socio in socios.items():
        titular = (socio.get("titularPagador") or "").strip().upper()
        nif = (socio.get("nifPagador") or "").strip().upper()
        if titular:
            titular_map[titular].add(sid)
        if nif:
            nif_map[nif].add(sid)
    visited = set()
    for head in list(normalized.keys()):
        if head in visited:
            continue
        group = set()
        queue = [head]
        while queue:
            current = queue.pop()
            if current in group:
                continue
            group.add(current)
            for neighbor in normalized.get(current, []):
                if neighbor not in group:
                    queue.append(neighbor)
        visited.update(group)
        group = {sid for sid in group if not is_personal_laboral(socios.get(sid, {}))}
        if head not in ids:
            result.append(
                finding(
                    "FAMILIA_CABEZA_INEXISTENTE",
                    "error",
                    "familia",
                    head,
                    "Cabeza de familia inexistente",
                )
            )
        for sid in group:
            seen[sid].add(head)
            if sid not in ids:
                result.append(
                    finding(
                        "FAMILIA_MIEMBRO_INEXISTENTE",
                        "error",
                        "familia",
                        head,
                        "Miembro inexistente",
                        member=sid,
                    )
                )
        active = [
            socios[sid] for sid in group if sid in socios and active_member(socios[sid])
        ]
        primary = [
            member_id(s["idColegiat"])
            for s in active
            if CAT["socio_principal_actividades"] in categories(s)
        ]
        siblings = [
            member_id(s["idColegiat"])
            for s in active
            if CAT["socio_hermano_actividades"] in categories(s)
        ]
        if siblings and not primary:
            implicit_principals = set()
            for sid in siblings:
                socio = socios.get(sid, {})
                titular = (socio.get("titularPagador") or "").strip().upper()
                nif = (socio.get("nifPagador") or "").strip().upper()
                for candidate in titular_map.get(titular, set()) | nif_map.get(
                    nif, set()
                ):
                    if (
                        candidate != sid
                        and candidate in socios
                        and active_member(socios[candidate])
                        and CAT["socio_principal_actividades"]
                        in categories(socios[candidate])
                    ):
                        implicit_principals.add(candidate)
            primary = sorted(primary + list(implicit_principals))
            if not primary:
                sibling_cats = {
                    sid: sorted(categories(socios[sid]))
                    for sid in siblings
                    if sid in socios
                }
                result.append(
                    finding(
                        "FAMILIA_HERMANOS_SIN_PRINCIPAL",
                        "error",
                        "familia",
                        head,
                        "Hay hermanos con actividades sin socio principal",
                        members=siblings,
                        sibling_categories=sibling_cats,
                    )
                )
        if len(primary) > 1:
            result.append(
                finding(
                    "FAMILIA_PRINCIPALES_MULTIPLES",
                    "warning",
                    "familia",
                    head,
                    "Más de un socio principal con actividades",
                    members=primary,
                )
            )
    for sid, heads in seen.items():
        if len(heads) > 1:
            result.append(
                finding(
                    "FAMILIA_RELACION_MULTIPLE",
                    "warning",
                    "socio",
                    sid,
                    "El socio aparece en familias distintas",
                    heads=sorted(heads),
                )
            )
    cap = [member_id(value) for value in (familias or {}).get("capfamilias") or []]
    for sid, count in Counter(cap).items():
        if sid is not None and count > 1:
            result.append(
                finding(
                    "FAMILIA_CAP_DUPLICADO",
                    "warning",
                    "familia",
                    sid,
                    "Cabeza bancaria duplicada en caché",
                    count=count,
                )
            )
    return result


def audit_actividades(actividades, inscriptions, socios, today):
    result, enrolled = [], defaultdict(list)
    for activity in actividades:
        aid = str(activity.get("idActivitat") or "?")
        start, end, limit = (
            parse_date(activity.get(key))
            for key in ("dataHoraActivitat", "dataHoraFiActivitat", "dataLimit")
        )
        max_places = member_id(activity.get("maxPlaces"))
        free = member_id(activity.get("placesLliures"))
        public = activity.get("estat") == "ACTIESTVIG"
        if start and end and start > end:
            result.append(
                finding(
                    "ACTIVIDAD_FECHAS_INVERTIDAS",
                    "error",
                    "actividad",
                    aid,
                    "El inicio es posterior al fin",
                )
            )
        if start and limit and limit > start:
            result.append(
                finding(
                    "ACTIVIDAD_LIMITE_TRAS_INICIO",
                    "warning",
                    "actividad",
                    aid,
                    "El límite de inscripción es posterior al inicio",
                )
            )
        if public and end and end < today:
            result.append(
                finding(
                    "ACTIVIDAD_FINALIZADA_SIN_ARCHIVAR",
                    "warning",
                    "actividad",
                    aid,
                    "Actividad vigente cuya fecha de fin ya pasó",
                )
            )
        if activity.get("estat") == "ACTIESTARXI" and limit and limit >= today:
            result.append(
                finding(
                    "ACTIVIDAD_ARCHIVADA_ABIERTA",
                    "warning",
                    "actividad",
                    aid,
                    "Actividad archivada con plazo de inscripción abierto",
                )
            )
        if max_places is None or max_places <= 0:
            result.append(
                finding(
                    "ACTIVIDAD_PLAZAS_INVALIDAS",
                    "warning",
                    "actividad",
                    aid,
                    "Máximo de plazas ausente o no positivo",
                )
            )
        if free is not None and (
            free < 0 or (max_places is not None and free > max_places)
        ):
            result.append(
                finding(
                    "ACTIVIDAD_PLAZAS_LIBRES_INVALIDAS",
                    "error",
                    "actividad",
                    aid,
                    "Plazas libres fuera de rango",
                    free=free,
                    maximum=max_places,
                )
            )
        if public and not str(activity.get("descripcio") or "").strip():
            result.append(
                finding(
                    "ACTIVIDAD_PUBLICA_SIN_DESCRIPCION",
                    "warning",
                    "actividad",
                    aid,
                    "Actividad pública sin descripción",
                )
            )
        if public and not activity.get("idNivell"):
            result.append(
                finding(
                    "ACTIVIDAD_SIN_HORARIO",
                    "warning",
                    "actividad",
                    aid,
                    "Actividad pública sin horario/nivel configurado",
                )
            )
        teacher = any(
            "profesor" in str(field.get("nom") or "").lower()
            and str(field.get("textAjuda") or "").strip()
            for field in (activity.get("campsDinamics") or [])
            if isinstance(field, dict)
        )
        if public and not teacher:
            result.append(
                finding(
                    "ACTIVIDAD_SIN_RESPONSABLE",
                    "warning",
                    "actividad",
                    aid,
                    "Actividad pública sin profesor o responsable informado",
                )
            )
        rows = inscriptions.get(str(aid), [])
        active_rows = [
            row for row in rows if row.get("estat") in ACTIVE_INSCRIPTION_STATES
        ]
        if max_places is not None and len(active_rows) > max_places:
            result.append(
                finding(
                    "ACTIVIDAD_SOBRECUPO",
                    "error",
                    "actividad",
                    aid,
                    "Más inscripciones activas que plazas",
                    enrolled=len(active_rows),
                    maximum=max_places,
                )
            )
        if (
            free is not None
            and max_places is not None
            and rows
            and max_places - free != len(active_rows)
        ):
            result.append(
                finding(
                    "ACTIVIDAD_CONTADOR_PLAZAS_DESCUADRADO",
                    "warning",
                    "actividad",
                    aid,
                    "El contador de plazas no coincide con la caché",
                    expected=max_places - len(active_rows),
                    actual=free,
                )
            )
        per_socio = defaultdict(list)
        for row in active_rows:
            sid = member_id(
                (row.get("colegiat") or {}).get("idColegiat") or row.get("idColegiat")
            )
            iid = row.get("idInscripcio", "?")
            if sid is None or sid not in socios:
                result.append(
                    finding(
                        "INSCRIPCION_SOCIO_INEXISTENTE",
                        "error",
                        "inscripcion",
                        iid,
                        "Inscripción sin socio existente",
                        activity=aid,
                    )
                )
                continue
            per_socio[sid].append(iid)
            enrolled[sid].append((aid, activity.get("idNivell"), iid))
            if CAT["sin_actividades"] in categories(socios[sid]):
                result.append(
                    finding(
                        "INSCRIPCION_SOCIO_SIN_ACTIVIDADES",
                        "warning",
                        "inscripcion",
                        iid,
                        "Inscrito con categoría sin actividades",
                        socio=sid,
                        activity=aid,
                    )
                )
        for sid, ids in per_socio.items():
            if len(ids) > 1:
                result.append(
                    finding(
                        "INSCRIPCION_DUPLICADA",
                        "error",
                        "actividad",
                        aid,
                        "Socio inscrito más de una vez",
                        socio=sid,
                        inscriptions=ids,
                    )
                )
    for sid, rows in enrolled.items():
        cats = categories(socios[sid])
        if CAT["actividades"] not in cats:
            result.append(
                finding(
                    "SOCIO_INSCRITO_SIN_CATEGORIA",
                    "warning",
                    "socio",
                    sid,
                    "Tiene inscripciones activas sin categoría de actividades",
                    activities=[r[0] for r in rows],
                )
            )
        slots = defaultdict(list)
        for aid, slot, iid in rows:
            if slot not in (None, "", "null", "0", 0):
                slots[str(slot)].append((aid, iid))
        for slot, clashes in slots.items():
            if len(clashes) > 1:
                result.append(
                    finding(
                        "INSCRIPCION_CONFLICTO_HORARIO",
                        "warning",
                        "socio",
                        sid,
                        "Inscripciones coincidentes en el mismo horario",
                        slot=slot,
                        activities=clashes,
                    )
                )
    return result, set(enrolled)


def audit_receipts(data_dir, socios, today):
    result = []
    root = Path(data_dir) / "entities" / "colegiat"
    if not root.exists():
        return result
    for path in root.glob("*/rebuts.json"):
        sid = member_id(path.parent.name)
        try:
            receipts = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            result.append(
                finding(
                    "RECIBOS_CACHE_INVALIDA",
                    "error",
                    "socio",
                    path.parent.name,
                    "No se puede leer la caché de recibos",
                )
            )
            continue
        returned = False
        annual_paid = False
        for receipt in receipts or []:
            concept = str(receipt.get("concepte") or "").strip().upper()
            status = str(receipt.get("estat") or "").upper()
            when = parse_date(receipt.get("dataPagament"))
            returned |= status == "REBESTRET"
            annual_paid |= bool(
                "ANUAL" in concept
                and status == "REBESTEME"
                and when
                and when.year >= today.year - 1
            )
        cats = categories(socios.get(sid, {}))
        if returned and CAT["impagados"] not in cats:
            result.append(
                finding(
                    "RECIBO_IMPAGO_SIN_CATEGORIA",
                    "warning",
                    "socio",
                    sid,
                    "Hay recibo devuelto sin categoría Impagados",
                )
            )
        if annual_paid and CAT["impago_anual"] in cats:
            result.append(
                finding(
                    "RECIBO_ANUAL_PAGADO_CON_IMPAGO",
                    "warning",
                    "socio",
                    sid,
                    "Recibo anual pagado y categoría Impago anual",
                )
            )
    return result


def audit_sync(data_dir, today):
    result, root = [], Path(data_dir)
    for name in ("socios.json", "actividades.json", "familias.json", "categorias.json"):
        path = root / name
        if not path.exists():
            result.append(
                finding(
                    "CACHE_AUSENTE",
                    "error",
                    "cache",
                    name,
                    "Falta la instantánea requerida",
                )
            )
            continue
        age = today - datetime.fromtimestamp(path.stat().st_mtime).date()
        if age > timedelta(days=2):
            result.append(
                finding(
                    "CACHE_DESACTUALIZADA",
                    "warning",
                    "cache",
                    name,
                    "Instantánea con más de dos días",
                    days=age.days,
                )
            )
        outbox = root / "outbox.json"
        if outbox.exists():
            try:
                entries = json.loads(outbox.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return result + [
                    finding(
                        "OUTBOX_INVALIDA",
                        "error",
                        "sync",
                        "outbox",
                        "No se puede leer outbox.json",
                    )
                ]
            pending = set()
            for entry in entries:
                status = entry.get("status", "pending")
                age = parse_date(entry.get("created_at"))
                if status == "failed":
                    result.append(
                        finding(
                            "OUTBOX_FALLIDA",
                            "error",
                            "sync",
                            entry.get("id", "?"),
                            "Mutación fallida",
                            op=entry.get("op"),
                            error=entry.get("last_error"),
                        )
                    )
                if status == "pending" and age and today - age > timedelta(days=2):
                    result.append(
                        finding(
                            "OUTBOX_PENDIENTE_ANTIGUA",
                            "warning",
                            "sync",
                            entry.get("id", "?"),
                            "Mutación pendiente más de dos días",
                            op=entry.get("op"),
                        )
                    )
                key = (
                    entry.get("op"),
                    entry.get("entity_id"),
                    json.dumps(entry.get("payload", {}), sort_keys=True),
                )
                if status == "pending" and key in pending:
                    result.append(
                        finding(
                            "OUTBOX_DUPLICADA",
                            "warning",
                            "sync",
                            entry.get("id", "?"),
                            "Mutación pendiente duplicada",
                            op=entry.get("op"),
                        )
                    )
                pending.add(key)
    return result


def run(data_dir="data", today=None):
    """Ejecuta todas las reglas y devuelve una lista ordenada de hallazgos."""
    root, today = Path(data_dir), today or date.today()

    def load(name, default):
        try:
            return json.loads((root / name).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default

    socios, activities, families = (
        load("socios.json", []),
        load("actividades.json", []),
        load("familias.json", {}),
    )
    inscriptions = {}
    activity_ids = {str(a.get("idActivitat")) for a in activities}
    for aid in activity_ids:
        rows = load(f"{aid}.json", [])
        if isinstance(rows, list):
            inscriptions[aid] = rows
    socio_findings, by_id = audit_socios(socios, today)
    activity_findings, enrolled = audit_actividades(
        activities, inscriptions, by_id, today
    )
    for sid, socio in by_id.items():
        if (
            active_member(socio)
            and CAT["actividades"] in categories(socio)
            and sid not in enrolled
        ):
            socio_findings.append(
                finding(
                    "SOCIO_CON_CATEGORIA_SIN_INSCRIPCIONES",
                    "warning",
                    "socio",
                    sid,
                    "Categoría de actividades sin inscripciones activas",
                )
            )
    findings = (
        socio_findings
        + audit_familias(families, by_id)
        + activity_findings
        + audit_receipts(root, by_id, today)
        + audit_sync(root, today)
    )
    return sorted(
        findings, key=lambda item: (item["severity"], item["code"], item["id"])
    )
