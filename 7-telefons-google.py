#!/usr/bin/env python

import csv

import common

socios = common.readjson(filename="socios")

rows = []
seen = set()


def _extraer_telefonos(socio):
    telefon = socio.get("telefonPrincipal") or (socio.get("campsDinamics") or {}).get(
        "0_15_20231012042734"
    )
    if telefon:
        yield str(telefon)

    for adreca in socio.get("adreces", []) or []:
        if adreca.get("telefonPrincipal"):
            yield str(adreca["telefonPrincipal"])
        if adreca.get("telefonSecundari"):
            yield str(adreca["telefonSecundari"])


def _validar_telefon_mobil(raw):
    if not raw:
        return None
    digits = "".join(ch for ch in str(raw) if ch.isdigit())
    if len(digits) == 9 and digits[0] in ("6", "7"):
        return f"+34{digits}"
    if len(digits) == 11 and digits.startswith("34") and digits[2] in ("6", "7"):
        return f"+{digits}"
    return None


for socio in socios:
    persona = socio.get("persona") or {}
    nom = persona.get("nom", "")
    cognoms = persona.get("cognoms", "")
    nombre = f"{nom} {cognoms}".strip()
    if not nombre:
        continue

    telefonos = []
    for raw in _extraer_telefonos(socio):
        valid = _validar_telefon_mobil(raw)
        if valid:
            telefonos.append(valid)

    for telefon in telefonos:
        key = (nombre.lower(), telefon)
        if key not in seen:
            seen.add(key)
            rows.append([nombre, telefon])

    for tutor_key in ("tutor1", "tutor2"):
        tutor = socio.get(tutor_key)
        if not tutor:
            continue
        tnom = tutor.get("nom", "")
        tcognoms = tutor.get("cognoms", "")
        tnombre = f"{tnom} {tcognoms}".strip()
        if not tnombre:
            continue

        telefonos_tutor = []
        for raw in _extraer_telefonos(tutor):
            valid = _validar_telefon_mobil(raw)
            if valid:
                telefonos_tutor.append(valid)

        for telefon in telefonos_tutor:
            key = (tnombre.lower(), telefon)
            if key not in seen:
                seen.add(key)
                rows.append([tnombre, telefon])

output_path = "data/telefons_google.csv"
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Name", "Phone"])
    writer.writerows(rows)

print(f"Generado {output_path} con {len(rows)} contactos")
