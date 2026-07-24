#!/usr/bin/env python

import calendar
import configparser
import datetime
import os
import re

import dateutil.parser

import common
import sync_store

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)

headers = {"Authorization": f"Bearer {token}"}

outbox_entries_global = sync_store.read_outbox()

# Definiciones

# Periodicidad (bimensual: 5, anual: 3)
extras = {82: 3}

# OPTIMIZATION Item 7: Cache category constants (O(1) lookup)
_cat_informevalidado = common.categorias["informevalidado"]
_cat_carnetpendiente = common.categorias["carnetpendiente"]
_cat_notienecarnet = common.categorias["notienecarnet"]
_cat_carnetincorrecto = common.categorias["carnetincorrecto"]
_cat_carnettutorduplicado = common.categorias["carnettutorduplicado"]
_cat_dana = common.categorias["dana"]

codigos_postales_dana = {
    46000,
    46012,
    46016,
    46017,
    46026,
    46110,
    46117,
    46134,
    46138,
    46149,
    46164,
    46165,
    46178,
    46190,
    46191,
    46192,
    46193,
    46195,
    46196,
    46197,
    46198,
    46200,
    46210,
    46220,
    46230,
    46240,
    46250,
    46267,
    46290,
    46300,
    46330,
    46340,
    46360,
    46367,
    46368,
    46369,
    46370,
    46380,
    46389,
    46393,
    46400,
    46410,
    46417,
    46420,
    46430,
    46440,
    46450,
    46460,
    46469,
    46470,
    46500,
    46530,
    46610,
    46614,
    46621,
    46670,
    46680,
    46687,
    46688,
    46689,
    46690,
    46700,
    46710,
    46727,
    46850,
    46894,
    46900,
    46910,
    46920,
    46930,
    46940,
    46950,
    46960,
    46970,
    46980,
}


_DIGITS_ONLY_PATTERN = re.compile(r"\D+")
_DIGITS_ONLY_VALUE_PATTERN = re.compile(r"^[0-9]+$")
_MAX_TELEGRAM_ID = 2**63 - 1


def _only_digits(value):
    return _DIGITS_ONLY_PATTERN.sub("", str(value or ""))


def _es_telegram_valido(valor):
    if valor is None:
        return True
    if isinstance(valor, bool):
        return False
    value_str = str(valor).strip()
    if not value_str:
        return True
    if not _DIGITS_ONLY_VALUE_PATTERN.fullmatch(value_str):
        return False
    if len(value_str) > 1 and value_str.startswith("0"):
        return False
    try:
        telegram_id = int(value_str, 10)
    except (ValueError, TypeError):
        return False
    return 2 <= telegram_id <= _MAX_TELEGRAM_ID


def _register_phone_variants(variants, phone_value, prefix_value=None):
    phone_digits = _only_digits(phone_value)
    if not phone_digits:
        return
    prefix_digits = _only_digits(prefix_value)
    variants.add(phone_digits)
    if prefix_digits:
        variants.add(prefix_digits + phone_digits)
    if prefix_digits and phone_digits.startswith(prefix_digits):
        local = phone_digits[len(prefix_digits) :]
        if local:
            variants.add(local)
    if len(phone_digits) > 9:
        variants.add(phone_digits[-9:])


def socio_phone_digit_variants(socio):
    variants = set()
    persona = socio.get("persona") or {}
    for phone_key, prefix_key in (
        ("telefonPrincipal", "prefixTelefonPrincipal"),
        ("telefonSecundari", "prefixTelefonSecundari"),
        ("telefon", "prefixTelefon"),
        ("mobil", "prefixMobil"),
    ):
        _register_phone_variants(
            variants, persona.get(phone_key), persona.get(prefix_key)
        )
    adreces = persona.get("adreces") or []
    if not isinstance(adreces, list):
        return variants
    for addr in adreces:
        if not isinstance(addr, dict):
            continue
        for phone_key, prefix_key in (
            ("telefonPrincipal", "prefixTelefonPrincipal"),
            ("telefonSecundari", "prefixTelefonSecundari"),
            ("telefon", "prefixTelefon"),
            ("mobil", "prefixMobil"),
        ):
            _register_phone_variants(
                variants, addr.get(phone_key), addr.get(prefix_key)
            )
    return variants


def _clear_telegram_field(
    token, socio, field_id, field_name, field_value, reason, cleared_field_ids
):
    if field_id in cleared_field_ids:
        return 0
    idcolegiat = socio["idColegiat"]
    cached_socio = common.read_entity_colegiat(idcolegiat)
    if cached_socio:
        cached_value = cached_socio.get("campsDinamics", {}).get(field_id)
        if not cached_value or cached_value == "":
            cleared_field_ids.add(field_id)
            socio["campsDinamics"][field_id] = ""
            return 0
    already_queued = any(
        e.get("op") == "escribecampo"
        and str(e.get("entity_id")) == str(idcolegiat)
        and e.get("payload", {}).get("campo") == field_id
        and e.get("payload", {}).get("valor", "X") == ""
        and e.get("status") in ["pending", "synced"]
        for e in outbox_entries_global
    )
    if already_queued:
        cleared_field_ids.add(field_id)
        return 0
    print(f"    {field_name}: Clearing field - {reason} ({field_value})")
    response = common.escribecampo(token, idcolegiat, field_id, "")
    print(f"    Response: {response}")
    cleared_field_ids.add(field_id)
    socio["campsDinamics"][field_id] = ""
    return 1


def _clean_single_telegram_field(
    socio,
    token,
    field_id,
    field_name,
    field_value,
    numcolegiat,
    phone_variants,
    cleared_field_ids,
):
    if not field_value:
        return 0
    if str(numcolegiat) == str(field_value):
        return _clear_telegram_field(
            token,
            socio,
            field_id,
            field_name,
            field_value,
            "telegram ID equals member number",
            cleared_field_ids,
        )
    field_digits = _only_digits(field_value)
    if field_digits and field_digits in phone_variants:
        return _clear_telegram_field(
            token,
            socio,
            field_id,
            field_name,
            field_value,
            "telegram value matches socio phone number",
            cleared_field_ids,
        )
    if not _es_telegram_valido(field_value):
        return _clear_telegram_field(
            token,
            socio,
            field_id,
            field_name,
            field_value,
            "invalid telegram ID",
            cleared_field_ids,
        )
    return 0


def _dedupe_telegram_values(socio, token, values, cleared_field_ids):
    if not values:
        return 0
    idcolegiat = socio["idColegiat"]
    cleaned_count = 0
    cached_socio = common.read_entity_colegiat(idcolegiat)
    cached_campos = cached_socio.get("campsDinamics", {}) if cached_socio else {}
    if values["tutor1"] == values["tutor2"] and values["tutor1"] != "":
        if not cached_campos.get(common.tutor2, "X") == "":
            if (
                _clear_telegram_field(
                    token,
                    socio,
                    common.tutor2,
                    "TUTOR2",
                    values["tutor2"],
                    "duplicate of TUTOR1",
                    cleared_field_ids,
                )
                == 1
            ):
                cleaned_count += 1
    if (values["tutor1"] == values["socioid"] and values["tutor1"] != "") or (
        values["tutor2"] == values["socioid"] and values["tutor2"] != ""
    ):
        if not cached_campos.get(common.socioid, "X") == "":
            if (
                _clear_telegram_field(
                    token,
                    socio,
                    common.socioid,
                    "SOCIO_ID",
                    values["socioid"],
                    "duplicate of tutor field",
                    cleared_field_ids,
                )
                == 1
            ):
                cleaned_count += 1
    return cleaned_count


def _limpiar_telegram_socio(socio, token):
    numcolegiat = socio["numColegiat"]
    cleared_field_ids = set()
    phone_variants = socio_phone_digit_variants(socio)
    if not isinstance(socio.get("campsDinamics"), dict):
        return 0
    values = {"tutor1": "", "tutor2": "", "socioid": ""}
    for field_id in common.telegramfields:
        if field_id in socio["campsDinamics"]:
            field_name = {
                "tutor1": "TUTOR1",
                "tutor2": "TUTOR2",
                "socioid": "SOCIO_ID",
            }.get(field_id, f"UNKNOWN_{field_id}")
            field_value = socio["campsDinamics"][field_id]
            if field_id == common.tutor1:
                values["tutor1"] = field_value
            elif field_id == common.tutor2:
                values["tutor2"] = field_value
            elif field_id == common.socioid:
                values["socioid"] = field_value
            _clean_single_telegram_field(
                socio,
                token,
                field_id,
                field_name,
                field_value,
                numcolegiat,
                phone_variants,
                cleared_field_ids,
            )
    return _dedupe_telegram_values(socio, token, values, cleared_field_ids)


def _limpiar_tutor_en_campo_socio(socio, token):
    if not isinstance(socio.get("campsDinamics"), dict):
        return 0
    mysocio = socio["campsDinamics"].get(common.socioid)
    ids_a_limpiar = [
        socio["idColegiat"]
        for field in [common.tutor1, common.tutor2]
        if field in socio["campsDinamics"] and mysocio == socio["campsDinamics"][field]
    ]
    if not ids_a_limpiar:
        return 0
    cleaned = 0
    for idcolegiat in sorted(set(ids_a_limpiar)):
        cached_socio = common.read_entity_colegiat(idcolegiat)
        if cached_socio:
            cached_value = cached_socio.get("campsDinamics", {}).get(common.socioid)
            if not cached_value or cached_value == "":
                continue
        already_queued = any(
            e.get("op") == "escribecampo"
            and str(e.get("entity_id")) == str(idcolegiat)
            and e.get("payload", {}).get("campo") == common.socioid
            and e.get("payload", {}).get("valor", "X") == ""
            and e.get("status") in ["pending", "synced"]
            for e in outbox_entries_global
        )
        if already_queued:
            print("    SOCIO_ID: Already queued for clearing (skipping)")
            continue
        response = common.escribecampo(token, idcolegiat, common.socioid, "")
        print(response)
        cleaned += 1
    return cleaned


today = datetime.date.today()

# La cuota anual es el 20 de Febrero
if today.month < 2 or (today.month == 2 and today.day < 20):
    fechacambiosocio = f"20/02/{today.year}"
else:
    fechacambiosocio = f"20/02/{today.year + 1}"

# Leer datos
socios = common.readjson("socios")
categorias = common.readjson("categorias")
familias = common.readjson("familias") or {"miembros": {}}
if "miembros" in familias:
    familias["miembros"] = {
        int(k): [int(v) for v in lst] for k, lst in familias["miembros"].items()
    }
if "capfamilias" in familias:
    familias["capfamilias"] = [int(x) for x in familias["capfamilias"]]
if "procesados" in familias:
    familias["procesados"] = [int(x) for x in familias["procesados"]]
today = datetime.date.today()
fechadia = calendar.monthrange(today.year, today.month)[1]


# Locate our member in the list of members
for socio in socios:
    # ID Socio
    socioid = int(socio["idColegiat"])
    carnetsocio = []

    copied = common.copy_missing_telegram_from_family(socioid, socios, familias)
    if copied:
        common.writejson(filename="socios", data=socios)
        for campo, valor, fid in copied:
            nombre = common.nombre_campo_telegram(campo)
            print(f"Copiado {nombre} del socio familiar {fid} al socio {socioid}")
            common.escribecampo(token, socioid, campo, valor)

    if isinstance(socio.get("campsDinamics"), dict) and any(
        field in socio["campsDinamics"] for field in common.telegramfields
    ):
        _limpiar_telegram_socio(socio, token)

    _limpiar_tutor_en_campo_socio(socio, token)

    categoriassocio = common.getcategoriassocio(socio=socio)

    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTBAIXA",
        agrupaciones=["PREINSCRIPCIÓN"],
        reverseagrupaciones=True,
    ):
        for idcategoria in categoriassocio:
            print(
                f"Borrando: {idcategoria} del socio {common.sociobase}{socioid}#tab=CATEGORIES"
            )
            common.delcategoria(token, socioid, idcategoria)

    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTALTA",
        agrupaciones=["PREINSCRIPCIÓN"],
        reverseagrupaciones=True,
    ):
        # Default for each member
        targetcategorias = []
        removecategorias = [common.categorias["informevalidado"]]
        adulto = False

        # Carnet de socio
        if common.categorias["carnetpendiente"] not in categoriassocio and (
            "persona" in socio and "residencia" in socio["persona"]
        ):
            if socio["persona"]["residencia"] in ["", "-"]:
                targetcategorias.append(common.categorias["notienecarnet"])
            else:
                removecategorias.append(common.categorias["notienecarnet"])

            if (
                "ANULADO".lower() in socio["persona"]["residencia"].lower()
                or "ANUAL".lower() in socio["persona"]["residencia"].lower()
                or socio["persona"]["residencia"] == "null"
            ):
                targetcategorias.append(common.categorias["carnetincorrecto"])

                # Forzar marcar que no tiene carnet
                if common.categorias["notienecarnet"] in removecategorias:
                    removecategorias.remove(common.categorias["notienecarnet"])
                    targetcategorias.append(common.categorias["notienecarnet"])

            else:
                removecategorias.append(common.categorias["carnetincorrecto"])

        # Find our born year
        try:
            fecha = dateutil.parser.parse(socio["persona"]["dataNaixement"])
        except Exception:
            fecha = False
            print(f"ERROR: Sin fecha nacimiento para socio ID: {socioid}")

        if fecha:
            year, month, day = fecha.year, fecha.month, fecha.day
        else:
            year, month, day = False, False, False

        if year:
            if today.day >= 25:
                if today.month == 12:
                    corte_year = today.year + 1
                    corte_month = 1
                else:
                    corte_year = today.year
                    corte_month = today.month + 1
            else:
                corte_year = today.year
                corte_month = today.month

            corte_fechadia = calendar.monthrange(corte_year, corte_month)[1]
            edad = corte_year - year - ((corte_month, corte_fechadia) < (month, day))
        else:
            corte_year = corte_month = corte_fechadia = edad = None

        for modalitat in socio["colegiatHasModalitats"]:
            idcategoria = int(modalitat["idModalitat"])
            agrupacionom = modalitat["modalitat"]["agrupacio"]["nom"].lower()
            modalitatnom = modalitat["modalitat"]["nom"].lower()

            try:
                myyear = int(modalitatnom)
            except Exception:
                myyear = False

            if myyear and year and myyear != year:
                print(f"ERROR: AÑO INCORRECTO para socio ID: {socioid}")
            if myyear and year and myyear != year:
                print(f"ERROR: AÑO INCORRECTO para socio ID: {socioid}")
                common.delcategoria(token, socioid, idcategoria)
            for categoria in categorias:
                nombre = categoria["nom"]

                # Attempt to find categories for a year
                try:
                    mycat = int(nombre)
                except Exception:
                    mycat = False

                if mycat and mycat == year and year and year in range(2000, today.year):
                    # Our member had a match with the born year
                    targetcategorias.append(int(categoria["idModalitat"]))

            if "Socio Adulto Actividades".lower() in agrupacionom:
                adulto = True
                targetcategorias.append(common.categorias["socioactivo"])
                targetcategorias.append(common.categorias["actividades"])
                removecategorias.append(common.categorias["sinactividades"])
                targetcategorias.append(common.categorias["adultosconysin"])

            if "Socio Adulto SIN Actividades".lower() in agrupacionom:
                adulto = True
                targetcategorias.append(common.categorias["socioactivo"])
                targetcategorias.append(common.categorias["sinactividades"])
                removecategorias.append(common.categorias["actividades"])
                targetcategorias.append(common.categorias["adultosconysin"])

            if "Socio Actividades".lower() in agrupacionom:
                targetcategorias.append(common.categorias["socioactivo"])
                targetcategorias.append(common.categorias["actividades"])
                removecategorias.append(common.categorias["sinactividades"])

            if "Socio SIN Actividades".lower() in agrupacionom:
                targetcategorias.append(common.categorias["socioactivo"])
                targetcategorias.append(common.categorias["sinactividades"])
                removecategorias.append(common.categorias["actividades"])

        # Carnet tutores (después de determinar si es adulto por modalidad o edad)
        es_adulto = adulto or (year and edad >= 18)
        if es_adulto:
            carnetsocio = []
            removecategorias.extend(
                (
                    common.categorias["sinuncarnetfamiliar"],
                    common.categorias["sindoscarnetfamiliar"],
                    common.categorias["carnettutorduplicado"],
                )
            )
        else:
            carnetsocio = []

            carnetsocio.extend(
                socio[tutor]["residencia"]
                for tutor in ["tutor1", "tutor2"]
                if (
                    tutor in socio
                    and socio[tutor] is not None
                    and socio[tutor]["residencia"] != ""
                    and socio[tutor]["residencia"] != "-"
                    and "ANULADO".lower() not in socio[tutor]["residencia"].lower()
                    and "ANUAL".lower() not in socio[tutor]["residencia"].lower()
                    and socio[tutor]["residencia"] != "null"
                )
            )
            # Detectar si el carnet de tutor está indicado para ambos tutores
            if len(carnetsocio) > len(sorted(set(carnetsocio))):
                targetcategorias.append(common.categorias["carnettutorduplicado"])
            else:
                removecategorias.append(common.categorias["carnettutorduplicado"])

        # Los adultos (por modalidad o edad) no necesitan tener tutores
        if common.categorias["carnetpendiente"] not in categoriassocio:
            if not es_adulto:
                if not carnetsocio:
                    targetcategorias.append(common.categorias["sindoscarnetfamiliar"])
                    removecategorias.append(common.categorias["sinuncarnetfamiliar"])

                if len(carnetsocio) == 1:
                    targetcategorias.append(common.categorias["sinuncarnetfamiliar"])
                    removecategorias.append(common.categorias["sindoscarnetfamiliar"])

                if len(carnetsocio) == 2:
                    removecategorias.extend(
                        (
                            common.categorias["sinuncarnetfamiliar"],
                            common.categorias["sindoscarnetfamiliar"],
                        )
                    )
            else:
                removecategorias.extend(
                    (
                        common.categorias["sinuncarnetfamiliar"],
                        common.categorias["sindoscarnetfamiliar"],
                    )
                )
        else:
            removecategorias.extend(
                (
                    common.categorias["sinuncarnetfamiliar"],
                    common.categorias["sindoscarnetfamiliar"],
                    common.categorias["notienecarnet"],
                )
            )

        if common.categorias["notienecarnet"] in targetcategorias and (
            common.categorias["actividades"] in targetcategorias
            or common.categorias["cambioadultoconactividades"] in targetcategorias
            or common.categorias["cambiosocioconactividades"] in targetcategorias
            or common.categorias["cambiohermanoconactividades"] in targetcategorias
        ):
            targetcategorias.append(common.categorias["sincarnetyactividades"])

        # Calcular edad (ya calculada antes del bucle de modalidades)
        if year and edad:
            # Add target category for +13/+15
            if edad in range(13, 15):
                # AVAST+13
                targetcategorias.append(common.categorias["avast13"])

            if edad in range(15, 18):
                # AVAST+15
                targetcategorias.append(common.categorias["avast15"])

            if edad in range(18, 25):
                # AVAST+18
                targetcategorias.append(common.categorias["avast18"])

            # El socio no debe estar en grupos A+13 o A+15 o A+18
            for i in [
                common.categorias["avast13"],
                common.categorias["avast15"],
                common.categorias["avast18"],
            ]:
                if i in categoriassocio and i not in targetcategorias:
                    print(f"ERROR: Borrando categoria {i} del socio {socioid}")
                    common.delcategoria(token, socioid, i)
        else:
            edad = False

        # Socios con impago anual, dar de baja de categorías
        if common.categorias["impagoanual"] in categoriassocio:
            targetcategorias = [common.categorias["impagoanual"]]
            removecategorias = list(categoriassocio)
            if common.categorias["impagoanual"] in removecategorias:
                removecategorias.remove(common.categorias["impagoanual"])

        # Classify acogida
        if common.categorias["acogidacolab"] not in categoriassocio and (
            common.categorias["acogida"] in categoriassocio
            or common.categorias["acogida"] in targetcategorias
        ):
            if (
                common.categorias["adultoconactividades"] in categoriassocio
                or common.categorias["adultoconactividades"] in targetcategorias
            ):
                targetcategorias.append(common.categorias["acogidaadultactiv"])
            if (
                common.categorias["adultosinactividades"] in categoriassocio
                or common.categorias["adultosinactividades"] in targetcategorias
            ):
                targetcategorias.append(common.categorias["acogidaadultsinactiv"])
            if (
                common.categorias["socioactividades"] in categoriassocio
                or common.categorias["socioactividades"] in targetcategorias
            ):
                targetcategorias.append(common.categorias["acogidaconactiv"])
            if (
                common.categorias["sociosinactividades"] in categoriassocio
                or common.categorias["sociosinactividades"] in targetcategorias
            ):
                targetcategorias.append(common.categorias["acogidasinactiv"])
            if (
                common.categorias["sociohermanoactividades"] in categoriassocio
                or common.categorias["sociohermanoactividades"] in targetcategorias
            ):
                targetcategorias.append(common.categorias["acogidaconactiv"])

        if (
            common.categorias["acogida"] not in categoriassocio
            and common.categorias["acogida"] not in targetcategorias
            or common.categorias["acogidacolab"] in categoriassocio
        ):
            removecategorias.append(common.categorias["acogidaadultactiv"])
            removecategorias.append(common.categorias["acogidaadultsinactiv"])
            removecategorias.append(common.categorias["acogidaconactiv"])
            removecategorias.append(common.categorias["acogidasinactiv"])
            removecategorias.append(common.categorias["acogidaconactiv"])

        if common.categorias["acogidacolab"] in categoriassocio:
            targetcategorias.append(common.categorias["acogida"])

        # Add or remove categories
        if common.categorias["socioactivo"] in targetcategorias:
            for modalitat in sorted(set(targetcategorias)):
                if modalitat not in categoriassocio:
                    print(
                        "IFF",
                        f"{common.sociobase}{socioid}",
                        modalitat,
                        categoriassocio,
                        modalitat in categoriassocio,
                    )
                    if modalitat != common.categorias["socioactivo"]:
                        response = common.addcategoria(token, socioid, modalitat)
                    else:
                        response = common.addcategoria(
                            token,
                            socioid,
                            modalitat,
                            extra={
                                "tipusperiodicitat": extras[modalitat],
                                "dataProperaGeneracio": fechacambiosocio,
                            },
                        )

        for modalitat in sorted(set(removecategorias)):
            if modalitat in categoriassocio:
                print(
                    "RFF",
                    f"{common.sociobase}{socioid}",
                    modalitat,
                    categoriassocio,
                    modalitat in categoriassocio,
                )

                response = common.delcategoria(token, socioid, modalitat)


# Normalizar nombres y apellidos de socios y tutores
socio_changes = []
tutor_changes = []

for socio in socios:
    sid = socio.get("idColegiat")
    if sid is None:
        continue
    persona = socio.get("persona") or {}

    original_nom = common.clean_spaces(persona.get("nom", ""))
    original_cognoms = common.clean_spaces(persona.get("cognoms", ""))
    normalized_nom = common.normalize_name(original_nom)
    normalized_cognoms = common.normalize_name(original_cognoms)

    if original_nom != normalized_nom or original_cognoms != normalized_cognoms:
        socio_changes.append(
            {
                "idColegiat": sid,
                "estat": socio.get("estat", ""),
                "idEstatColegiat": socio.get("idEstatColegiat"),
                "persona": {
                    "old_nom": original_nom,
                    "new_nom": normalized_nom,
                    "old_cognoms": original_cognoms,
                    "new_cognoms": normalized_cognoms,
                },
            }
        )

    for tutor_key in ("tutor1", "tutor2"):
        tutor = socio.get(tutor_key)
        if not tutor:
            continue
        orig_tnom = common.clean_spaces(tutor.get("nom", ""))
        orig_tcognoms = common.clean_spaces(tutor.get("cognoms", ""))
        norm_tnom = common.normalize_name(orig_tnom)
        norm_tcognoms = common.normalize_name(orig_tcognoms)
        if orig_tnom != norm_tnom or orig_tcognoms != norm_tcognoms:
            tutor_changes.append(
                {
                    "idColegiat": sid,
                    "tutor_key": tutor_key,
                    "idTutor": tutor.get("idTutor"),
                    "old_nom": orig_tnom,
                    "new_nom": norm_tnom,
                    "old_cognoms": orig_tcognoms,
                    "new_cognoms": norm_tcognoms,
                }
            )

if not socio_changes and not tutor_changes:
    print("No hay nombres que corregir.")
    raise SystemExit(0)

if socio_changes:
    print(f"Se encontraron {len(socio_changes)} socios con nombres por corregir.")
    for change in socio_changes[:20]:
        print(
            f"  {change['idColegiat']} [{change['estat']}]: nom: {change['persona']['old_nom']!r} -> {change['persona']['new_nom']!r}, cognoms: {change['persona']['old_cognoms']!r} -> {change['persona']['new_cognoms']!r}"
        )
        print(f"    URL: {common.sociobase}{change['idColegiat']}#tab=PERFIL")

if tutor_changes:
    print(f"Se encontraron {len(tutor_changes)} tutores con nombres por corregir.")
    for change in tutor_changes[:20]:
        print(
            f"  {change['idColegiat']} [{change['tutor_key']}]: nom: {change['old_nom']!r} -> {change['new_nom']!r}, cognoms: {change['old_cognoms']!r} -> {change['new_cognoms']!r}"
        )
        print(f"    URL: {common.sociobase}{change['idColegiat']}#tab=PERFIL")

if len(socio_changes) > 20:
    print(f"  ... y {len(socio_changes) - 20} socios más.")
if len(tutor_changes) > 20:
    print(f"  ... y {len(tutor_changes) - 20} tutores más.")

print("Procesando sincronización automáticamente...")

synced = 0
failed = 0
skipped = 0


def _to_int(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


for change in socio_changes:
    sid = change["idColegiat"]
    socio = next((s for s in socios if str(s["idColegiat"]) == str(sid)), None)
    if not socio:
        skipped += 1
        print(f"  OMITIDO: {sid} - no encontrado en socios.json")
        continue

    estat = change.get("estat", "")
    idestat = change.get("idEstatColegiat")
    warning = ""
    if estat != "COLESTVAL" or str(idestat) != "1":
        warning = " [SOCIO NO ACTIVO]"

    print(
        f"\nSocio {sid}{warning}: {change['persona']['old_nom']!r} -> {change['persona']['new_nom']!r}, {change['persona']['old_cognoms']!r} -> {change['persona']['new_cognoms']!r}"
    )
    print(f"  URL: {common.sociobase}{sid}#tab=PERFIL")
    if warning:
        print("  ATENCIÓN: este socio no está activo. Se actualizará igualmente.")

    socio["persona"]["nom"] = change["persona"]["new_nom"]
    socio["persona"]["cognoms"] = change["persona"]["new_cognoms"]

    persona = socio.get("persona") or {}
    payload = {
        "idColegiat": _to_int(sid),
        "idColegi": _to_int(socio.get("idColegi")),
        "numColegiat": _to_int(socio.get("numColegiat")),
        "idEstatColegiat": _to_int(socio.get("idEstatColegiat")),
        "estat": socio.get("estat", ""),
        "dataAlta": socio.get("dataAlta", ""),
        "dataBaixa": socio.get("dataBaixa", ""),
        "dataJubilacio": socio.get("dataJubilacio", ""),
        "tipusBaixa": socio.get("tipusBaixa", ""),
        "viaBaixa": socio.get("viaBaixa", ""),
        "descripcioBaixa": socio.get("descripcioBaixa", ""),
        "codiLlicencia": socio.get("codiLlicencia", ""),
        "metodePagament": socio.get("metodePagament", ""),
        "observacions": socio.get("observacions", ""),
        "persona": {
            "idPersona": _to_int(persona.get("idPersona")),
            "nom": common.clean_spaces(change["persona"]["new_nom"]),
            "cognoms": common.clean_spaces(change["persona"]["new_cognoms"]),
        },
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    payload["persona"] = {k: v for k, v in payload["persona"].items() if v is not None}

    result = common.update_colegiat(token, sid, payload)
    if result is None:
        failed += 1
        print(f"  ERROR: {sid} persona - sin respuesta (posiblemente offline)")
    elif hasattr(result, "status_code") and result.status_code == 401:
        print(f"  Token expirado para {sid} persona, renovando token...")
        token = common.gettoken(
            user=config["auth"]["RWusername"],
            password=config["auth"]["RWpassword"],
            force_refresh=True,
        )
        result = common.update_colegiat(token, sid, payload)
        if result is None:
            failed += 1
            print(f"  ERROR: {sid} persona - sin respuesta tras renovar token")
        elif hasattr(result, "status_code") and result.status_code >= 400:
            failed += 1
            print(
                f"  ERROR: {sid} persona - HTTP {result.status_code}: {result.text[:200]}"
            )
        else:
            synced += 1
            print(f"  OK: {sid} persona (tras renovar token)")
    elif hasattr(result, "status_code") and result.status_code >= 400:
        failed += 1
        print(
            f"  ERROR: {sid} persona - HTTP {result.status_code}: {result.text[:200]}"
        )
    else:
        synced += 1
        print(f"  OK: {sid} persona")

for change in tutor_changes:
    sid = change["idColegiat"]
    socio = next((s for s in socios if str(s["idColegiat"]) == str(sid)), None)
    if not socio:
        skipped += 1
        print(f"  OMITIDO: {sid} - no encontrado en socios.json")
        continue

    tutor_key = change["tutor_key"]
    tutor = socio.get(tutor_key)
    if not tutor:
        skipped += 1
        print(f"  OMITIDO: {sid} {tutor_key} - no encontrado en socio")
        continue
    tutor_id = change.get("idTutor")
    if not tutor_id:
        skipped += 1
        print(f"  OMITIDO: {sid} {tutor_key} - sin idTutor")
        continue

    print(
        f"\nTutor {tutor_key} del socio {sid}: {change['old_nom']!r} -> {change['new_nom']!r}, {change['old_cognoms']!r} -> {change['new_cognoms']!r}"
    )
    print(f"  URL: {common.sociobase}{sid}#tab=PERFIL")

    tutor["nom"] = change["new_nom"]
    tutor["cognoms"] = change["new_cognoms"]
    tutor_payload = {
        "idTutor": int(tutor_id) if str(tutor_id).isdigit() else tutor_id,
        "nom": common.clean_spaces(change["new_nom"]),
        "cognoms": common.clean_spaces(change["new_cognoms"]),
        "residencia": tutor.get("residencia", ""),
        "nif": tutor.get("nif", ""),
        "dataNaixement": tutor.get("dataNaixement", ""),
        "relacio": tutor.get("relacio", ""),
        "adreces": tutor.get("adreces", []),
    }
    result = common.update_tutor(token, sid, tutor_id, tutor_payload)
    if result is None:
        failed += 1
        print(f"  ERROR: {sid} {tutor_key} - sin respuesta")
    elif hasattr(result, "status_code") and result.status_code == 401:
        print(f"  Token expirado para {sid} {tutor_key}, renovando token...")
        token = common.gettoken(
            user=config["auth"]["RWusername"],
            password=config["auth"]["RWpassword"],
            force_refresh=True,
        )
        result = common.update_tutor(token, sid, tutor_id, tutor_payload)
        if result is None:
            failed += 1
            print(f"  ERROR: {sid} {tutor_key} - sin respuesta tras renovar token")
        elif hasattr(result, "status_code") and result.status_code >= 400:
            failed += 1
            print(
                f"  ERROR: {sid} {tutor_key} - HTTP {result.status_code}: {result.text[:200]}"
            )
        else:
            synced += 1
            print(f"  OK: {sid} {tutor_key} (tras renovar token)")
    elif hasattr(result, "status_code") and result.status_code >= 400:
        failed += 1
        print(
            f"  ERROR: {sid} {tutor_key} - HTTP {result.status_code}: {result.text[:200]}"
        )
    else:
        synced += 1
        print(f"  OK: {sid} {tutor_key}")

print(f"\nSincronizados: {synced}, Fallidos: {failed}, Saltados: {skipped}")

if synced > 0:
    print("Guardando socios.json actualizado")
    common.writejson(filename="socios", data=socios)
