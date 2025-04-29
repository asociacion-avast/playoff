#!/usr/bin/env python


import common

print("Loading file from disk")
socios = common.readjson(filename="socios")


print("Procesando socios...")


def classifymembers(socios):
    resultids = {
        "activ": [],  # Con actividades
        "adult": [],  # Adultos
        "adultactiv": [],  # Adultos con actividades
        "adultsinactiv": [],  # Adultos sin actividades
        "invalid": [],  # Socios sin ALTA activa
        "kids-and-parents": [],  # Niños y tutores
        "kids": [],  # Niños (CON y SIN)
        "kidsactiv-and-parents": [],  # Niños CON Actividades y tutores
        "kidsactiv": [],  # Niños CON Actividades
        "kidsinactiv-and-parents": [],  # Niños SIN Actividades y tutores
        "kidsinactiv": [],  # Niños SIN actividades
        "profesores": [],  # Profesores
        "teen13-and-parents": [],  # Niños y tutores [13-15)
        "teen13": [],  # Niños [13-15)
        "teen15-and-parents": [],  # Niños y tutores [15-24]
        "teen15": [],  # Niños [15-24]
        "teen18-and-parents": [],  # Niños y tutores [18-29]
        "teen18": [],  # Niños [18-29]
        "tutor": [],  # Tutores
        "valid": [],  # Cualquiera con relación avast
        "preinscripcion": [],  # Socios preinscritos
    }

    # For each user check the custom fields that store the telegram ID for each tutor
    for socio in socios:
        # try:
        #     fecha = dateutil.parser.parse(user["persona"]["dataNaixement"])
        # except Exception:
        #     fecha = False

        if isinstance(socio["campsDinamics"], dict):
            for field in common.telegramfields:
                if field in socio["campsDinamics"]:
                    try:
                        userid = socio["campsDinamics"][field]
                    except:
                        userid = False

                    if userid:
                        if not (
                            common.validasocio(
                                socio,
                                estado="COLESTVAL",
                                estatcolegiat="ESTALTA",
                            )
                        ):
                            if common.validasocio(
                                socio,
                                estado="COLESTVAL",
                                estatcolegiat="ESTPERLAB",
                            ):
                                # We've ID but it's not in good status
                                resultids["profesores"].append(userid)
                            else:
                                # We've ID but it's not in good status

                                resultids["invalid"].append(userid)

                        else:
                            resultids["valid"].append(userid)
                            # if fecha:
                            #     year, month, day = fecha.year, fecha.month, fecha.day
                            #     edad = (
                            #         today.year
                            #         - year
                            #         - ((today.month, today.day) < (month, day))
                            #     )
                            # else:
                            #     edad = False

                            if "colegiatHasModalitats" in socio:
                                # Iterate over all categories for the user
                                for modalitat in socio["colegiatHasModalitats"]:
                                    if "modalitat" in modalitat:
                                        # Save name for comparing the ones we target
                                        agrupacionom = modalitat["modalitat"][
                                            "agrupacio"
                                        ]["nom"].lower()
                                        modalitatnom = modalitat["modalitat"][
                                            "nom"
                                        ].lower()

                                        if "profesores".lower() in agrupacionom:
                                            resultids["profesores"].append(userid)

                                        if field != socios:
                                            # Si no es socio, añadir a tutores
                                            resultids["tutor"].append(userid)

                                        if (
                                            "Socio Adulto Actividades".lower()
                                            in agrupacionom
                                        ):
                                            resultids["adult"].append(userid)
                                            resultids["adultactiv"].append(userid)
                                            resultids["activ"].append(userid)
                                            resultids["tutor"].append(userid)

                                        if (
                                            "Socio Adulto SIN Actividades".lower()
                                            in agrupacionom
                                        ):
                                            resultids["adult"].append(userid)
                                            resultids["adultsinactiv"].append(userid)
                                            resultids["tutor"].append(userid)

                                        if "Socio Actividades".lower() in agrupacionom:
                                            if field == common.socioid:
                                                resultids["kids"].append(userid)
                                                resultids["kidsactiv"].append(userid)
                                            resultids["activ"].append(userid)
                                            resultids["kidsactiv-and-parents"].append(
                                                userid
                                            )

                                        if (
                                            "Socio SIN Actividades".lower()
                                            in agrupacionom
                                        ):
                                            if field == common.socioid:
                                                resultids["kids"].append(userid)
                                                resultids["kidsinactiv"].append(userid)
                                            resultids["kids-and-parents"].append(userid)
                                            resultids["kidsinactiv-and-parents"].append(
                                                userid
                                            )

                                        if "avast15".lower() in modalitatnom:
                                            if field == common.socioid:
                                                resultids["teen15"].append(userid)
                                            resultids["teen15-and-parents"].append(
                                                userid
                                            )

                                        if "avast13".lower() in modalitatnom:
                                            if field == common.socioid:
                                                resultids["teen13"].append(userid)

                                            resultids["teen13-and-parents"].append(
                                                userid
                                            )

                                        if "avast18".lower() in modalitatnom:
                                            if field == common.socioid:
                                                resultids["teen18"].append(userid)
                                            resultids["teen18-and-parents"].append(
                                                userid
                                            )

                                        if "Candidato a".lower() in modalitatnom:
                                            resultids["preinscripcion"].append(userid)

    # Remove candidates in preinscripcion
    for uid in resultids["preinscripcion"]:
        for categoria in resultids:
            if categoria != "preinscripcion":
                if uid in resultids[categoria]:
                    resultids[categoria].remove(uid)

    # Remove duplicates
    for item in resultids:
        resultids[item] = sorted(set(resultids[item]))

    # pprint.pprint(resultids)

    return resultids


resultids = classifymembers(socios)
for item in resultids:
    print(item, len(resultids[item]))
