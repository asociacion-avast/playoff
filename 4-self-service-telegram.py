#!/usr/bin/env python

import configparser
import datetime
import os

import common
import sync_store

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)


print("Loading file from disk")
socios = common.readjson(filename="socios")
actividades = common.readjson(filename="actividades")


today = datetime.date.today()


print("Actualizando actividades ID TELEGRAM")
for actividadid in [815, 816]:
    common.updateactividad(token=token, idactividad=actividadid)

# Read outbox once before processing (OPTIMIZATION)
outbox_entries_global = sync_store.read_outbox()
outbox_anuladas = {
    str(e["payload"]["inscripcion"])
    for e in outbox_entries_global
    if e.get("op") == "anula_inscripcio" and e.get("status") in ["pending", "synced"]
}

# Pre-load and cache activity inscriptions (OPTIMIZATION)
cache_por_actividad = {}
for actividadid in [815, 816]:
    inscritos = common.readjson(filename=f"{actividadid}")
    cache_por_actividad[actividadid] = {
        str(i["idInscripcio"])
        for i in inscritos
        if i.get("estat") in ["INSCRESTANU", "anulada"]
    }

print("Procesando socios...")

# Progress tracking
total_socios = len(socios)
socios_matched = 0

# For each user check the custom fields that store the telegram ID for each tutor
for actividadid in [815, 816]:
    print(
        f"\nProcesando actividad {actividadid} ({common.traduce(actividadid)})...",
        flush=True,
    )
    inscritos = common.readjson(filename=f"{actividadid}")
    inscripciones = []

    processed = 0
    progress_interval = max(1, total_socios // 20)

    for socio in socios:
        processed += 1
        if processed % progress_interval == 0 or processed == total_socios:
            pct = int(100 * processed / total_socios)
            print(
                f"  Procesando: {processed}/{total_socios} ({pct}%) - Encontrados: {socios_matched}",
                flush=True,
            )
        # OPTIMIZATION Phase 2C: Use pre-computed validation
        if socio.get("_valid_alta", False):
            socioid = int(socio["idColegiat"])

            for inscrito in inscritos:
                if int(inscrito["colegiat"]["idColegiat"]) == socioid:
                    inscripciones.append(inscrito["idInscripcio"])
                    if inscrito["estat"] == "INSCRESTNOVA":
                        socios_matched += 1
                        print(f"\n{common.sociobase}{socioid}#tab=CATEGORIES")
                        print(
                            f"El socio {socioid} está inscrito en la actividad {common.traduce(actividadid)}"
                        )

                        data = []
                        if actividadid == 815:
                            data = common.getcomunicadotutor(socioid)
                        if actividadid == 816:
                            data = common.getcomunicadosocio(socioid)

                        if not data:
                            print("Error procesando inscripcion de socio: %s" % socioid)
                        else:
                            print("Enviando comunicado")
                            response = common.enviacomunicado(token=token, data=data)
                            print(response)
                            print(response.text)

                            # Borra inscripciones a las actividades
                            print("Borrando inscripciones a actividades ID Telegram")
                            for inscripcion in inscripciones:
                                # O(1) lookups using pre-loaded cache (OPTIMIZED)
                                cancelled_cache = cache_por_actividad.get(
                                    actividadid, set()
                                )

                                if (
                                    str(inscripcion) in cancelled_cache
                                    or str(inscripcion) in outbox_anuladas
                                ):
                                    print(
                                        f"  Inscripción {inscripcion} ya procesada (skipping)"
                                    )
                                    continue

                                response = common.anula_inscripcio(
                                    token=token,
                                    inscripcion=inscripcion,
                                    comunica=False,
                                    idActivitat=actividadid,
                                )
