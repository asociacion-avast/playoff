#!/usr/bin/env python

from datetime import date, datetime, timezone

import requests

import common


def actividades_en_periodo(actividades, hoy=None):
    hoy = hoy or datetime.now(timezone.utc).date()
    if isinstance(hoy, datetime):
        hoy = hoy.date()
    if hoy.month >= 9:
        inicio_periodo = date(hoy.year, 9, 1)
        fin_periodo = date(hoy.year + 1, 6, 30)
    elif hoy.month <= 6:
        inicio_periodo = date(hoy.year - 1, 9, 1)
        fin_periodo = date(hoy.year, 6, 30)
    else:
        return []

    filtradas = []
    for actividad in actividades:
        if actividad.get("estat", "ACTIESTVIG") != "ACTIESTVIG":
            continue

        inicio = common.parse_date(actividad.get("dataHoraActivitat"))
        fin = common.parse_date(actividad.get("dataHoraFiActivitat"))
        if inicio is None or fin is None:
            continue

        inicio = inicio.date()
        fin = fin.date()
        if inicio_periodo <= inicio <= fin_periodo and fin >= hoy:
            filtradas.append(actividad)

    return filtradas


token = common.gettoken()

activar = f"{common.apiurl}/activitats/totes"
data = {"Authorization": f"Bearer {token}"}

print("Obteniendo listado de actividades")
result = requests.get(
    activar, auth=common.BearerAuth(token), headers=common.headers, timeout=15
)

actividades = actividades_en_periodo(result.json())

print("Saving file to disk")
common.writejson(filename="actividades", data=actividades)
