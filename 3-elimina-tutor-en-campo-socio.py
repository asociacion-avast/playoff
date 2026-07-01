#!/usr/bin/env python


import configparser
import os

import common
import sync_store

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


socios = common.readjson("socios")

# Build index for fast lookups (OPTIMIZATION)
socios_by_id = {s["idColegiat"]: s for s in socios}

token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)
headers = {"Authorization": f"Bearer {token}"}

# Read outbox once at start (OPTIMIZATION)
outbox_entries_global = sync_store.read_outbox()


print("Procesando socios")
count = 0

idsociotoclean = []

for socio in socios:
    if (
        isinstance(socio["campsDinamics"], dict)
        and common.socioid in socio["campsDinamics"]
    ):
        mysocio = socio["campsDinamics"][common.socioid]
        idsociotoclean.extend(
            socio["idColegiat"]
            for field in [common.tutor1, common.tutor2]
            if field in socio["campsDinamics"]
            and mysocio == socio["campsDinamics"][field]
        )
for idcolegiat in sorted(set(idsociotoclean)):
    count = count + 1
    print(f"{count:04} {common.sociobase}{idcolegiat}")

    if cached_socio := common.read_entity_colegiat(idcolegiat):
        cached_value = cached_socio.get("campsDinamics", {}).get(common.socioid)
        if not cached_value or cached_value == "":
            print("    SOCIO_ID: Already cleared in cache (skipping)")
            continue

    # Check if already in outbox (use global outbox - OPTIMIZED)
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
