#!/usr/bin/env python


import common

codigos_postales = [
    46012,
    46014,
    46117,
    46160,
    46164,
    46165,
    46166,
    46168,
    46175,
    46190,
    46191,
    46195,
    46196,
    46197,
    46198,
    46200,
    46210,
    46220,
    46230,
    46240,
    46250,
    46290,
    46300,
    46314,
    46315,
    46320,
    46330,
    46340,
    46360,
    46367,
    46368,
    46369,
    46370,
    46380,
    46388,
    46389,
    46392,
    46393,
    46410,
    46417,
    46418,
    46430,
    46440,
    46450,
    46460,
    46469,
    46470,
    46600,
    46610,
    46613,
    46614,
    46650,
    46680,
    46687,
    46688,
    46689,
    46760,
    46900,
    46910,
    46940,
    46950,
    46960,
    46970,
    46980,
]


print("Loading file from disk")

socios = common.readjson(filename="socios")


affected = []
telegramids = []

for socio in socios:
    if common.validasocio(
        socio,
        estado="COLESTVAL",
        estatcolegiat="ESTALTA",
        agrupaciones=["PREINSCRIPCIÓN"],
        reverseagrupaciones=True,
    ):
        try:
            cp = int(socio["persona"]["adreces"][0]["municipi"]["codipostal"])
        except Exception:
            cp = 0

        if cp in codigos_postales:
            affected.append(socio["idColegiat"])

            if isinstance(socio["campsDinamics"], dict):
                for field in common.telegramfields:
                    if field in socio["campsDinamics"]:
                        try:
                            userid = socio["campsDinamics"][field]
                        except Exception:
                            userid = False

                        if userid and (
                            common.validasocio(
                                socio,
                                estado="COLESTVAL",
                                estatcolegiat="ESTALTA",
                            )
                        ):
                            telegramids.append(userid)


affected = sorted(set(affected))
print("########## SOCIOS #######")
print(affected)
print(len(affected))
print("########## IDS Telegram #######")
print(sorted(set(telegramids)))
print(len(telegramids))
