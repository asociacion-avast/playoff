#!/usr/bin/env python


import common

print("Loading file from disk")
socios = common.readjson(filename="socios")


print("Procesando socios...")

# OPTIMIZATION Item 7: Cache constants for fast lookups
_cat_adulto_actividades = "Socio Adulto Actividades".lower()
_cat_adulto_sin_actividades = "Socio Adulto SIN Actividades".lower()
_cat_socio_actividades = "Socio Actividades".lower()
_cat_socio_sin_actividades = "Socio SIN Actividades".lower()
_cat_avast15 = "avast15".lower()
_cat_avast13 = "avast13".lower()
_cat_avast18 = "avast18".lower()
_cat_candidato = "Candidato a".lower()


def classifymembers(socios):
    # OPTIMIZATION Item 9: Use sets for O(1) membership checks
    resultids = {
        "activ": set(),
        "adult": set(),
        "adultactiv": set(),
        "adultsinactiv": set(),
        "invalid": set(),
        "kids-and-parents": set(),
        "kids": set(),
        "kidsactiv-and-parents": set(),
        "kidsactiv": set(),
        "kidsinactiv-and-parents": set(),
        "kidsinactiv": set(),
        "preinscripcion": set(),
        "profesores": set(),
        "sociohermano": set(),
        "teen13-and-parents": set(),
        "teen13": set(),
        "teen15-and-parents": set(),
        "teen15": set(),
        "teen18-and-parents": set(),
        "teen18": set(),
        "tutor": set(),
        "valid": set(),
    }

    # OPTIMIZATION Item 6: Single pass accumulation
    for socio in socios:
        # OPTIMIZATION Item 2: Use cached dynamic fields
        cached_campos = socio.get("_cached_campos", {})

        for field in common.telegramfields:
            userid = cached_campos.get(field)
            if not userid:
                continue

            # OPTIMIZATION Item 3: Use pre-computed validations
            if not socio.get("_valid_alta", False):
                if common.validasocio(
                    socio,
                    estado="COLESTVAL",
                    estatcolegiat="ESTPERLAB",
                ):
                    resultids["profesores"].add(userid)
                else:
                    resultids["invalid"].add(userid)
            else:
                resultids["valid"].add(userid)

                if "colegiatHasModalitats" in socio:
                    for modalitat in socio["colegiatHasModalitats"]:
                        if "modalitat" not in modalitat:
                            continue

                        m_data = modalitat["modalitat"]
                        agrupacio = m_data.get("agrupacio", {})

                        # OPTIMIZATION Item 4: Use pre-normalized names
                        agrupacionom = (
                            agrupacio.get("_nom_lower")
                            or agrupacio.get("nom", "").lower()
                        )
                        modalitatnom = (
                            m_data.get("_nom_lower") or m_data.get("nom", "").lower()
                        )
                        idmodalitat = int(m_data.get("idModalitat", 0))

                        if "profesores".lower() in agrupacionom:
                            resultids["profesores"].add(userid)

                        if field != common.socioid:
                            resultids["tutor"].add(userid)

                        if _cat_adulto_actividades in agrupacionom:
                            resultids["adult"].add(userid)
                            resultids["adultactiv"].add(userid)
                            resultids["activ"].add(userid)
                            resultids["tutor"].add(userid)

                        if _cat_adulto_sin_actividades in agrupacionom:
                            resultids["adult"].add(userid)
                            resultids["adultsinactiv"].add(userid)
                            resultids["tutor"].add(userid)

                        if _cat_socio_actividades in agrupacionom:
                            if field == common.socioid:
                                resultids["kids"].add(userid)
                                resultids["kidsactiv"].add(userid)
                            resultids["activ"].add(userid)
                            resultids["kidsactiv-and-parents"].add(userid)

                        if idmodalitat == 13:
                            resultids["sociohermano"].add(userid)

                        if _cat_socio_sin_actividades in agrupacionom:
                            if field == common.socioid:
                                resultids["kids"].add(userid)
                                resultids["kidsinactiv"].add(userid)
                            resultids["kids-and-parents"].add(userid)
                            resultids["kidsinactiv-and-parents"].add(userid)

                        if _cat_avast15 in modalitatnom:
                            if field == common.socioid:
                                resultids["teen15"].add(userid)
                            resultids["teen15-and-parents"].add(userid)

                        if _cat_avast13 in modalitatnom:
                            if field == common.socioid:
                                resultids["teen13"].add(userid)
                            resultids["teen13-and-parents"].add(userid)

                        if _cat_avast18 in modalitatnom:
                            if field == common.socioid:
                                resultids["teen18"].add(userid)
                            resultids["teen18-and-parents"].add(userid)

                        if _cat_candidato in modalitatnom:
                            resultids["preinscripcion"].add(userid)

    # OPTIMIZATION Item 9: Remove candidates in preinscripcion efficiently
    preinscripcion_ids = resultids["preinscripcion"]
    for categoria in resultids:
        if categoria != "preinscripcion":
            resultids[categoria] -= preinscripcion_ids

    # Convert sets back to sorted lists
    for item in resultids:
        resultids[item] = sorted(list(resultids[item]))

    return resultids


resultids = classifymembers(socios)
for item in resultids:
    print(item, len(resultids[item]))
