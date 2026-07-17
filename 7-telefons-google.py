#!/usr/bin/env python

import csv

import common

socios = common.readjson(filename="socios")

rows = []
seen = set()

for socio in socios:
    sid = socio.get("idColegiat")
    persona = socio.get("persona") or {}
    nom = persona.get("nom", "")
    cognoms = persona.get("cognoms", "")
    nombre = f"{nom} {cognoms}".strip()
    if not nombre:
        continue

    camps = socio.get("campsDinamics", {}) or {}
    telefon = (
        socio.get("telefonPrincipal")
        or camps.get("0_15_20231012042734")
        or camps.get("telefonPrincipal")
    )
    if telefon:
        key = (nombre.lower(), str(telefon))
        if key not in seen:
            seen.add(key)
            rows.append([nombre, str(telefon)])

    tutor1 = socio.get("tutor1")
    if tutor1:
        tnom = tutor1.get("nom", "")
        tcognoms = tutor1.get("cognoms", "")
        tnombre = f"{tnom} {tcognoms}".strip()
        if tnombre:
            ttelefon = tutor1.get("telefon") or camps.get("0_15_20231012042734")
            if ttelefon:
                key = (tnombre.lower(), str(ttelefon))
                if key not in seen:
                    seen.add(key)
                    rows.append([tnombre, str(ttelefon)])

    tutor2 = socio.get("tutor2")
    if tutor2:
        tnom = tutor2.get("nom", "")
        tcognoms = tutor2.get("cognoms", "")
        tnombre = f"{tnom} {tcognoms}".strip()
        if tnombre:
            ttelefon = tutor2.get("telefon") or camps.get("0_15_20231012042734")
            if ttelefon:
                key = (tnombre.lower(), str(ttelefon))
                if key not in seen:
                    seen.add(key)
                    rows.append([tnombre, str(ttelefon)])

output_path = "data/telefons_google.csv"
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Name", "Phone"])
    writer.writerows(rows)

print(f"Generado {output_path} con {len(rows)} contactos")
