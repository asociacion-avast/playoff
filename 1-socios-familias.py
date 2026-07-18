#!/usr/bin/env python

import configparser
import os

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken()


def normalizar_familias(familias):
    familias["capfamilias"] = [int(x) for x in familias.get("capfamilias", [])]
    familias["procesados"] = [int(x) for x in familias.get("procesados", [])]
    familias["miembros"] = {
        int(k): [int(v) for v in lista]
        for k, lista in familias.get("miembros", {}).items()
    }


print("Loading file from disk")
socios = common.readjson(filename="socios")

try:
    familias = common.readjson(filename="familias")
    normalizar_familias(familias)
except Exception:
    familias = {"capfamilias": [], "miembros": {}, "procesados": []}


def cruzar_miembros(miembros):
    datos = {}
    for k, lista in miembros.items():
        k_int = int(k)
        valores_int = [int(x) for x in lista]

        grupo = set(valores_int)
        grupo.add(k_int)

        for miembro in grupo:
            if miembro not in datos:
                datos[miembro] = set()
            datos[miembro].update(grupo - {miembro})

    return {k: sorted(v) for k, v in datos.items()}


def normalizar_familias(familias):
    familias["capfamilias"] = [int(x) for x in familias.get("capfamilias", [])]
    familias["procesados"] = [int(x) for x in familias.get("procesados", [])]
    familias["miembros"] = {
        int(k): [int(v) for v in lista]
        for k, lista in familias.get("miembros", {}).items()
    }


def procesar_familia(socioid, family):
    # Procesar tanto capFamilia como familiars para asegurar que el cabeza de familia esta incluido
    miembros_raw = []
    for cap in family.get("capFamilia", []):
        miembros_raw.append(
            {
                "idColegiat": cap["idColegiat"],
                "isBancCapFamilia": cap.get("isBancCapFamilia", "0"),
            }
        )
    for miembro in family.get("familiars", []):
        miembros_raw.append(
            {
                "idColegiat": miembro["idColegiat"],
                "isBancCapFamilia": miembro.get("isBancCapFamilia", "0"),
            }
        )

    for miembro in miembros_raw:
        miembroid = int(miembro["idColegiat"])
        if miembroid != socioid:
            if miembroid not in familias["miembros"]:
                familias["miembros"][miembroid] = []
            if socioid not in familias["miembros"][miembroid]:
                familias["miembros"][miembroid].append(socioid)
            if miembroid not in familias["miembros"][socioid]:
                familias["miembros"][socioid].append(miembroid)

            if miembro["isBancCapFamilia"] == "1":
                if miembroid not in familias["capfamilias"]:
                    familias["capfamilias"].append(miembroid)


def es_personal_laboral(socio):
    return (socio.get("estatColegiat") or {}).get("nom") == "ESTPERLAB"


print("Procesando socios")
for socio in socios:
    socioid = int(socio["idColegiat"])

    if es_personal_laboral(socio):
        continue

    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTALTA",
        agrupaciones=["PREINSCRIPCIÓN"],
        reverseagrupaciones=True,
    ):
        if (
            socioid not in familias["miembros"]
            and socioid not in familias["procesados"]
        ):
            familias["miembros"][socioid] = []
            familias["procesados"].append(socioid)

            family = common.read_entity_familia(socioid, token)
            if family and family != []:
                procesar_familia(socioid, family)
    else:
        # Socio no válido
        removed = False
        if socioid in familias["miembros"]:
            del familias["miembros"][socioid]
            removed = True
        if socioid in familias["capfamilias"]:
            familias["capfamilias"].remove(socioid)
        if removed and socioid in familias["procesados"]:
            familias["procesados"].remove(socioid)


# Limpiar: eliminar personal laboral de familias existentes
print("Limpiando personal laboral de familias...")
laborales_eliminados = 0
socios_laborales = {int(s["idColegiat"]) for s in socios if es_personal_laboral(s)}

for laboral in socios_laborales:
    if laboral in familias["miembros"]:
        del familias["miembros"][laboral]
        laborales_eliminados += 1
    for sid in list(familias["miembros"].keys()):
        if laboral in familias["miembros"][sid]:
            familias["miembros"][sid].remove(laboral)
            laborales_eliminados += 1
    if laboral in familias["capfamilias"]:
        familias["capfamilias"].remove(laboral)
        laborales_eliminados += 1

if laborales_eliminados > 0:
    print(f"Eliminados {laborales_eliminados} vinculos de personal laboral")
else:
    print("No se detecto personal laboral en familias")

# Reparar: re-procesar socios que estan en procesados pero no en miembros
# (fueron eliminados en ejecuciones anteriores por no pasar validacion)
print("Reparando familias incompletas...")
reparados = 0
for socio in socios:
    socioid = int(socio["idColegiat"])
    if socioid in familias["procesados"] and socioid not in familias["miembros"]:
        if common.validasocio(
            socio,
            estado="COLESTVAL",
            estatcolegiat="ESTALTA",
            agrupaciones=["PREINSCRIPCIÓN"],
            reverseagrupaciones=True,
        ):
            print(f"Reparando familia del socio {socioid}")
            familias["miembros"][socioid] = []
            family = common.read_entity_familia(socioid, token)
            if family and family != []:
                procesar_familia(socioid, family)
            reparados += 1

if reparados > 0:
    print(f"Reparados {reparados} socios")
else:
    print("No se detectaron familias incompletas")


familias["miembros"] = cruzar_miembros(familias["miembros"])
familias["capfamilias"] = sorted(set(familias.get("capfamilias", [])))

# Verificar consistencia bidireccional de las relaciones de familia
inconsistentes = []
for socio_id, lista in familias["miembros"].items():
    socio_id_int = int(socio_id)
    for miembro in lista:
        miembro_int = int(miembro)
        if socio_id_int not in familias["miembros"].get(miembro_int, []):
            inconsistentes.append((socio_id, miembro))

if inconsistentes:
    print(
        f"ADVERTENCIA: {len(inconsistentes)} relaciones familiares inconsistentes (no bidireccionales):"
    )
    for a, b in inconsistentes[:10]:
        print(f"  {a} -> {b} pero {b} -> {familias['miembros'].get(b, [])}")

# Save to disk
common.writejson(filename="familias", data=familias)
