#!/usr/bin/env python


import common

codigos_postales = [
    46970,
    46470,
    46687,
    46369,
    46290,
    46250,
    46960,
    46910,
    46197,
    46680,
    46230,
    46440,
    46910,
    46450,
    46469,
    46689,
    46117,
    46165,
    46360,
    46330,
    46240,
    46196,
    46470,
    46315,
    46612,
    46400,
    46350,
    46380,
    46370,
    46614,
    46687,
    46314,
    46388,
    46610,
    46160,
    46393,
    46613,
    46910,
    46195,
    46368,
    46940,
    46470,
    46920,
    46192,
    46193,
    46200,
    46980,
    46164,
    46210,
    46220,
    46688,
    46930,
    46194,
    46340,
    46190,
    46417,
    46910,
    46392,
    46460,
    46320,
    46430,
    46168,
    46410,
    46760,
    46900,
    46389,
    46300,
    46017,
    46026,
    46012,
    46012,
    46012,
    46012,
    46950,
    46367,
]


print("Loading file from disk")

users = common.rewadjson(filename="socios")


affected = []
telegramids = []

for user in users:
    if (
        "estat" in user
        and user["estat"] == "COLESTVAL"
        and "estatColegiat" in user
        and user["estatColegiat"]["nom"] == "ESTALTA"
    ):
        try:
            cp = int(user["persona"]["adreces"][0]["municipi"]["codipostal"])
        except:
            cp = 0

        if cp in codigos_postales:
            affected.append(user["idColegiat"])

            if isinstance(user["campsDinamics"], dict):
                for field in common.telegramfields:
                    if field in user["campsDinamics"]:
                        try:
                            userid = user["campsDinamics"][field]
                        except:
                            userid = False

                        if userid:
                            if (
                                "estat" in user
                                and user["estat"] == "COLESTVAL"
                                and "estatColegiat" in user
                                and user["estatColegiat"]["nom"] == "ESTALTA"
                            ):
                                # Always store if ID is valid or not

                                telegramids.append(userid)


affected = sorted(set(affected))
print("########## SOCIOS #######")
print(affected)
print(len(affected))
print("########## IDS Telegram #######")
print(sorted(set(telegramids)))
print(len(telegramids))
