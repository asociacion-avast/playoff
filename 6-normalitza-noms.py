#!/usr/bin/env python

import configparser
import os

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))

token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)

print("Loading socios.json")
socios = common.readjson(filename="socios")
familias = common.readjson(filename="familias") or {"miembros": {}}

for socio in socios:
    sid = socio.get("idColegiat")
    if sid is None:
        continue
    copied = common.copy_missing_telegram_from_family(sid, socios, familias)
    if copied:
        for campo, valor, fid in copied:
            nombre = common.nombre_campo_telegram(campo)
            print(f"Copiado {nombre} del socio familiar {fid} al socio {sid}")
            common.escribecampo(token, sid, campo, valor)

if any(
    socio.get("campsDinamics")
    for socio in socios
    if common.copy_missing_telegram_from_family(
        socio.get("idColegiat"), socios, familias
    )
):
    common.writejson(filename="socios", data=socios)

socio_changes = []
tutor_changes = []

for socio in socios:
    sid = socio.get("idColegiat")
    if sid is None:
        continue
    persona = socio.get("persona") or {}

    original_nom = persona.get("nom", "")
    original_cognoms = persona.get("cognoms", "")
    normalized_nom = common.normalize_name(original_nom)
    normalized_cognoms = common.normalize_name(original_cognoms)

    socio_modificado = False
    if original_nom != normalized_nom or original_cognoms != normalized_cognoms:
        socio_modificado = True
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
        orig_tnom = tutor.get("nom", "")
        orig_tcognoms = tutor.get("cognoms", "")
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


def _update_socio(token, sid, socio, change):
    global synced, failed
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

    def _to_int(value):
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

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
            "nom": change["persona"]["new_nom"],
            "cognoms": change["persona"]["new_cognoms"],
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
    return token


def _update_tutor(token, sid, socio, change):
    global synced, failed
    tutor_key = change["tutor_key"]
    tutor = socio.get(tutor_key)
    if not tutor:
        return token
    tutor_id = change.get("idTutor")
    if not tutor_id:
        return token

    print(
        f"\nTutor {tutor_key} del socio {sid}: {change['old_nom']!r} -> {change['new_nom']!r}, {change['old_cognoms']!r} -> {change['new_cognoms']!r}"
    )
    print(f"  URL: {common.sociobase}{sid}#tab=PERFIL")

    tutor["nom"] = change["new_nom"]
    tutor["cognoms"] = change["new_cognoms"]
    tutor_payload = {
        "idTutor": int(tutor_id) if str(tutor_id).isdigit() else tutor_id,
        "nom": change["new_nom"],
        "cognoms": change["new_cognoms"],
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
    return token


for change in socio_changes:
    sid = change["idColegiat"]
    socio = next((s for s in socios if str(s["idColegiat"]) == str(sid)), None)
    if not socio:
        skipped += 1
        print(f"  OMITIDO: {sid} - no encontrado en socios.json")
        continue
    token = _update_socio(token, sid, socio, change)

for change in tutor_changes:
    sid = change["idColegiat"]
    socio = next((s for s in socios if str(s["idColegiat"]) == str(sid)), None)
    if not socio:
        skipped += 1
        print(f"  OMITIDO: {sid} - no encontrado en socios.json")
        continue
    token = _update_tutor(token, sid, socio, change)

print(f"\nSincronizados: {synced}, Fallidos: {failed}, Saltados: {skipped}")

if synced > 0 or failed == 0:
    print("Guardando socios.json actualizado")
    common.writejson(filename="socios", data=socios)
else:
    print("No se guardó socios.json por errores en la sincronización.")
