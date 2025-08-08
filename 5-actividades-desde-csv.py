#!/usr/bin/env python

import configparser
import csv
import os
import pprint

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)


data = {"Authorization": f"Bearer {token}"}


print("Haciendo llamada API")
# CSV processing and override creation


csv_path = os.path.join(os.path.dirname(__file__), "actividades.csv")
overrides = {}
with open(csv_path, newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=";")
    for row in reader:
        # Build override dict for each activity
        override = {
            "idActividad": int(row["idActividad"]),
            "edatMin": int(row["EDAD"].split("-")[0])
            if "-" in row["EDAD"]
            else int(row["EDAD"]),
            "edatMax": int(row["EDAD"].split("-")[-1])
            if "-" in row["EDAD"]
            else int(row["EDAD"]),
            "nom": row["ACTIVIDAD"],
            "minPlaces": int(row["pzas min"]),
            "maxPlaces": int(row["pzas max"]),
            "descripcio": f"Profesor: {row['profesores']}, Aula: {row['AULA']}, Edificio: {row['EDIFICIO']}",
            "dataInici": row["fecha inicio"],
            "dataFi": row["fecha final"],
            "dataLimit": row["fecha final inscripciones"]
            or row["fecha inicio inscripciones"],
            "aula": row["AULA"],
            "edificio": row["EDIFICIO"],
            # Add more fields as needed
        }
        overrides[int(row["idActividad"])] = override


null = ""

# Map HORA to slot values
hora_slot_map = {
    "9:00": 7,
    "10:05": 8,
    "11:30": 9,
    "12:35": 10,
}

# Process each activity from CSV
for idActividad, base_override in overrides.items():
    hora = (
        base_override.get("dataInici", "").split()[1]
        if "dataInici" in base_override and base_override["dataInici"]
        else None
    )
    hora_csv = base_override.get("HORA") or None
    # Try to get slot from HORA column if available, else from dataInici
    slot = hora_slot_map.get(base_override.get("HORA", ""), None)
    # Build full override
    override = {
        "estat": "ACTIESTVIG",
        "tipusControlEdat": "CEANYS",
        "tipus": "TAIND",
        "llocActivitat": base_override.get(
            "edificio", "Cantera de Empresas, C/Pobla de Farnals 48, Valencia"
        ),
        "dataLimit": base_override.get("dataLimit", "2025-04-16 12:00"),
        "dataInici": base_override.get("dataInici", "2025-04-01 12:30"),
        "isVisibleCampsPersonalitzatsPersona": "1",
        "isDescripcioPublica": True,
        "isPermetreInscripcionsTotesModalitats": 0,
        "activitatHasModalitats": [
            {"idModalitat": "82", "idActivitat": f"{idActividad}"}
        ],
        "limitacioEstatsSocis": ["1"],
        "placesLliures": 50,
        "usuarisRestringits": [],
        "crearUsuariPermes": 0,
        "isPermetreAnularInscripcions": 1,
        "horesAntelacio": 144,
        "idNivell": slot,
    }
    override.update(base_override)
    # Optionally update name with slot time
    if slot:
        override["nom"] = f"{override['nom']} {base_override.get('HORA', '')}"
    result = common.editaactividad(token, idActividad, override)
    print(f"Editando actividad {idActividad} {override['nom']}")
    pprint.pprint(result)
    # If result is a requests.Response, check .ok
    if hasattr(result, "ok") and not result.ok:
        print(
            f"Error en la actividad {idActividad} {override['nom']}: {getattr(result, 'status_code', '')}"
        )
        print(getattr(result, "text", ""))
