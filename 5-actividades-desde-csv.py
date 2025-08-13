#!/usr/bin/env python

import configparser
import csv
import os
import pprint
import random
import time

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
hora_slot_map = {
    "9:00": "8",
    "10:05": "9",
    "11:30": "7",
    "12:35": "10",
}
with open(csv_path, newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=";")
    for row in reader:
        print(row)
        try:
            idActividad = int(row["idActividad"])
        except:
            idActividad = False

        if idActividad:
            horain = row.get("HORA", "").split("-")[0].strip()
            horaout = row.get("HORA", "").split("-")[1].strip()

            slot = hora_slot_map.get(horain)

            # Clean up newlines in relevant fields
            actividad_nom = (
                row["ACTIVIDAD"].replace("\n", " ").replace("\r", " ").strip()
            )
            hora_nom = f"{horain}-{horaout}"
            aula_nom = row["AULA"].replace("\n", " ").replace("\r", " ").strip()
            edificio_nom = row["EDIFICIO"].replace("\n", " ").replace("\r", " ").strip()
            profesores_nom = (
                row["profesores"].replace("\n", " ").replace("\r", " ").strip()
            )
            piso = row["PLANTA"].replace("\n", " ").replace("\r", " ").strip()
            profesor_email = (
                row["email"].replace("\n", " ").replace("\r", " ").strip()
                or "desconocido"
            )
            # Build descripcio with additional requirements
            descripcio = f"Profesor: {profesores_nom}. Detalle de actividades en <a href=https://asociacion-avast.org/detalle-de-actividades/>https://asociacion-avast.org/detalle-de-actividades/</a>"
            if row.get("WIFI", "").strip():
                descripcio += "\n<p>Esta actividad requiere acceso a la red WiFi. Recoja sus credenciales en la Cabina cristales conserjería UPV - Edif. 5F 1ª planta ETSII. Más información en <a href=https://asociacion-avast.org/clave-informatica/>https://asociacion-avast.org/clave-informatica/</a></p>"
            if row.get("DISPOSITIVO", "").strip():
                descripcio += "\n<p>Esta actividad requiere que el participante traiga su propio dispositivo (portátil, tablet, etc.).</p>"
            if row.get("DESCRIPCION", "").strip():
                descripcio += f"\n<p>{row['DESCRIPCION'].replace(chr(10), ' ').replace(chr(13), ' ').strip()}</p>"
            if row.get("MATERIALES", "").strip():
                descripcio += f"\n<p>Materiales necesarios: {row['MATERIALES'].replace(chr(10), ' ').replace(chr(13), ' ').strip()}</p>"
            if row.get("URL", "").strip():
                descripcio += f"\n<p>Más información en <a href='{row['URL'].strip()}'>{row['URL'].strip()}</a></p>"

            override = {
                "estat": "ACTIESTPRIV",
                "tipusControlEdat": "CENAIXEMENT",
                "tipus": "TAIND",
                "llocActivitat": f"Aula: {aula_nom}, Planta: {piso}, Edificio: {edificio_nom}",
                "dataLimit": "2025-10-31 23:59:59",
                "dataInici": "2025-09-01 00:00:00",
                "dataFi": "2025-10-31 23:59:59",
                "isVisibleCampsPersonalitzatsPersona": "1",
                "isDescripcioPublica": True,
                "isPermetreInscripcionsTotesModalitats": 0,
                "activitatHasModalitats": [
                    {"idModalitat": "90", "idActivitat": f"{idActividad}"}
                ],
                "limitacioEstatsSocis": ["1"],
                "isEnviarEmailConfirmacioCapFamilia": 1,
                "isEnviarRebutConfirmacio": 0,
                "isNoPermetreRebreEmailsEntitat": True,
                "isEnviarArxiuCalendari": 0,
                "placesLliures": 50,
                "usuarisRestringits": [],
                "crearUsuariPermes": 0,
                "isPermetreAnularInscripcions": 1,
                "horesAntelacio": 0,
                "idNivell": "%s" % slot,
                "edatMin": int(row["AÑO INICIO"]),
                "edatMax": int(row["AÑO FIN"]),
                "nom": f"{actividad_nom}: ({int(row['AÑO INICIO'])}-{int(row['AÑO FIN'])}) : {hora_nom}",
                "minPlaces": int(row["pzas min"]),
                "maxPlaces": int(row["pzas max"]),
                "descripcio": descripcio,
                "aula": aula_nom,
                "edificio": edificio_nom,
                "dataHoraActivitat": f"2025-09-13 {horain}:00",
                "dataHoraFiActivitat": "2026-06-20",
                "campsDinamics": [
                    {
                        "nom": "profesor1",
                        "format": "CD_FORMAT_TEXT",
                        "textAjuda": f"<p>{profesor_email}</p>",
                        "opcionsDesplegable": [],
                        "ordre": 0,
                        "nomIntern": "0_0_20250811100011",
                        "campsCondicionatAmb": [],
                        "campsCondicionatAmbVisual": [],
                        "ocultarPartPublica": 1,
                    }
                ],
                "isDadesPersonalsNoModificables": 1,
                "isAssociatDadesMinim": 1,
                "idPlantillaComunicat": 203,
            }

            result = common.editaactividad(token, idActividad, override)
            print(f"Editando actividad {idActividad} {override['nom']}")
            pprint.pprint(result)
            if hasattr(result, "ok") and not result.ok:
                print(
                    f"Error en la actividad {idActividad} {override['nom']}: {getattr(result, 'status_code', '')}"
                )
                print(getattr(result, "text", ""))

            delay = random.uniform(1, 5)
            time.sleep(delay)
