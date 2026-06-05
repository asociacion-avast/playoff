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


print("Actualizando actividades CAMBIO")
for actividadid in [781, 782]:
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
for actividadid in [781, 782]:
    inscritos = common.readjson(filename=f"{actividadid}")
    cache_por_actividad[actividadid] = {
        str(i["idInscripcio"])
        for i in inscritos
        if i.get("estat") in ["INSCRESTANU", "anulada"]
    }

print("Procesando socios...")

# Progress tracking
total_socios = len(socios)
processed = 0
socios_matched = 0
progress_interval = max(1, total_socios // 20)  # Show progress every 5%

# For each user check the custom fields that store the telegram ID for each tutor
for socio in socios:
    processed += 1

    # Show progress every 5%
    if (
        processed == 1
        or processed % progress_interval == 0
        or processed == total_socios
    ):
        pct = int(100 * processed / total_socios)
        print(
            f"Procesando: {processed}/{total_socios} ({pct}%) - Encontrados: {socios_matched}",
            flush=True,
        )
    activasocio = False
    cambiaactividades = False
    targetcategorias = []
    removecategorias = []
    targetprogramada = []

    # OPTIMIZATION Phase 2C: Use pre-computed validation
    if socio.get("_valid_alta", False):
        socioid = int(socio["idColegiat"])

        # OPTIMIZATION Phase 2B: Use pre-computed categories
        categoriassocio = socio.get("_cached_categorias", [])
        inscripciones = []

        saltarsocio = any(cambio in categoriassocio for cambio in [78, 79, 80, 81, 87])

        if not saltarsocio:
            for actividadid in [781, 782]:
                inscritos = common.readjson(filename=f"{actividadid}")
                for inscrito in inscritos:
                    if int(inscrito["colegiat"]["idColegiat"]) == socioid:
                        inscripciones.append(inscrito["idInscripcio"])
                        if inscrito["estat"] == "INSCRESTNOVA":
                            socios_matched += 1
                            print(f"\n{common.sociobase}{socioid}#tab=CATEGORIES")
                            print(
                                f"El socio {socioid} está inscrito en la actividad {common.traduce(actividadid)}"
                            )

                            activasocio = True

                            if actividadid == 781:
                                # Pasar a CON actividades
                                if (
                                    common.categorias["adultosinactividades"]
                                    in categoriassocio
                                ):
                                    cambiaactividades = True
                                    targetprogramada.append(79)

                                if (
                                    common.categorias["sociosinactividades"]
                                    in categoriassocio
                                ):
                                    cambiaactividades = True
                                    targetprogramada.append(81)

                            elif actividadid == 782:
                                # Pasar a SIN actividades
                                if (
                                    common.categorias["socioactividades"]
                                    in categoriassocio
                                    or common.categorias["sociohermanoactividades"]
                                    in categoriassocio
                                ):
                                    targetprogramada.append(80)

                                if (
                                    common.categorias["adultoconactividades"]
                                    in categoriassocio
                                ):
                                    targetprogramada.append(78)

        if activasocio:
            print(f"Socio debe activarse: {activasocio}")

            # Next year if we're in the last bimester
            year = today.year + 1 if today.month >= 11 else today.year
            month = common.mes_proximo_bimestre()

            targetcambio = f"{year}-{month:02}-01"

            print(f"Programando fecha cambio: {targetcambio}")

            print(
                common.escribecampo(
                    token, socioid, common.fechacambio, valor=targetcambio
                ).text
            )

            print("Altas en categorias:")
            for categoria in targetprogramada:
                print(common.traduce(categoria))
                common.addcategoria(token=token, categoria=categoria, socio=socioid)

            # Borra inscripciones a las actividades
            print("Borrando inscripciones a actividades AUTO-CAMBIO")
            for inscripcion in inscripciones:
                # Check across both activities using pre-loaded cache (OPTIMIZED)
                already_processed = False
                idActivitat = None

                for actividadid in [781, 782]:
                    cancelled_cache = cache_por_actividad.get(actividadid, set())
                    if str(inscripcion) in cancelled_cache:
                        already_processed = True
                        idActivitat = actividadid
                        break
                    # Also check which activity this belongs to
                    inscritos_data = common.readjson(filename=f"{actividadid}")
                    if any(
                        str(i.get("idInscripcio")) == str(inscripcion)
                        for i in inscritos_data
                    ):
                        idActivitat = actividadid

                # Check outbox (O(1) lookup - OPTIMIZED)
                if not already_processed and str(inscripcion) in outbox_anuladas:
                    already_processed = True

                if already_processed:
                    print(f"  Inscripción {inscripcion} ya procesada (skipping)")
                    continue

                response = common.anula_inscripcio(
                    token=token,
                    inscripcion=inscripcion,
                    comunica=False,
                    idActivitat=idActivitat,
                )
