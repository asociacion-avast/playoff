#!/usr/bin/env python

import configparser
import json
import os

import requests

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))

# Telegramfields
tutor1 = "0_13_20231012041710"
tutor2 = "0_14_20231012045321"
socioid = "0_16_20241120130245"
telegramfields = [tutor1, tutor2, socioid]

apiurl = f"https://{config['auth']['endpoint']}.playoffinformatica.com/api.php/api/v1.0"
headers = {"Content-Type": "application/json", "content-encoding": "gzip"}

endpoint = config["auth"]["endpoint"]


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = f"Bearer {self.token}"
        return r


def gettoken(user=config["auth"]["username"], password=config["auth"]["password"]):
    apiurl = (
        f"https://{config['auth']['endpoint']}.playoffinformatica.com/api.php/api/v1.0"
    )

    # get token

    loginurl = f"{apiurl}/login/colegi"

    data = {"username": user, "password": password}

    result = requests.post(loginurl, data=json.dumps(data), headers=headers)

    return result.json()["access_token"]


def writejson(filename, data):
    with open(f"data/{filename}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        return True


def readjson(filename):
    with open(f"data/{filename}.json", "r", encoding="utf-8") as f:
        return json.load(f)


def addcategoria(token, socio, categoria, extra=False):
    """Adds categoria to socio

    Args:
        token (str): token for accessing API (RW)
        socio (int): Socio identifier
        categoria (int): ID for category to modify
    """

    headers = {"Authorization": f"Bearer {token}"}
    categoriaurl = f"{apiurl}/colegiats/{socio}/modalitats"

    data = {"idModalitat": categoria}

    if extra:
        data.update(extra)
    files = []

    return requests.request(
        "POST", categoriaurl, headers=headers, data=data, files=files
    )


def delcategoria(token, socio, categoria):
    """Removes categoria from socio

    Args:
        token (str): token for accessing API (RW)
        socio (int): Socio identifier
        categoria (int): ID for category to modify
    """

    headers = {"Authorization": f"Bearer {token}"}
    categoriaurl = f"{apiurl}/colegiats/{socio}/modalitats/{categoria}"

    data = {}
    files = []

    return requests.request(
        "DELETE", categoriaurl, headers=headers, data=data, files=files
    )
