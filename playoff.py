import configparser
import json
import os
from urllib.request import HTTPBasicAuthHandler
import logging

import requests


logging.getLogger("urllib3").setLevel(logging.DEBUG)
logging.getLogger("requests.packages.urllib3").setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)


config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))
ENDPOINT = config["auth"]["endpoint"]
USERNAME = config["auth"]["username"]
PASSWORD = config["auth"]["password"]


class PlayoffAPI:
    """Facilita el uso del API de Playoff"""

    def __init__(self):
        self.url_base = f"https://{ENDPOINT}.playoffinformatica.com"
        self.url_api = f"{self.url_base}/api.php/api/v1.0"
        self.headers = {"Content-Type": "application/json", "content-encoding": "gzip"}
        self.token = ""

    def get_bearer(self, user=USERNAME, password=PASSWORD):
        if len(self.token) > 0:
            return self.token
        loginurl = f"{self.url_api}/login/colegi"
        data = {"username": user, "password": password}
        result = requests.post(loginurl, data=json.dumps(data), headers=self.headers)
        self.token = result.json()["access_token"]
        return self.token

    def get_headers(self) -> dict:
        bearer = self.get_bearer()
        return {**self.headers, **{"Authorization": f"Bearer {bearer}"}}

    def get(self, path):
        url = f"{self.url_api}/{path}"
        result = requests.get(url, headers=self.get_headers())
        if result.status_code == 200:
            return result.json()
        else:
            return []

    def get_categorias(self):
        return self.get("modalitats")

    def get_colegiat(self, nif: str) -> dict:
        res = self.get(f"colegiats?nif={nif}")
        if len(res) > 0:
            return res[0]
        return {}

    def get_colegiat_by_passaport(self, passaport: str) -> dict:
        res = self.get(f"colegiats?residencia={passaport}")
        if len(res) > 0:
            return res[0]
        return {}

    def get_inscripcio(self, idInscripcio):
        return self.get(f"inscripcions/{idInscripcio}")

    def del_inscripcio(self, idInscripcio):
        url = f"{self.url_api}/inscripcions?idInscripcio={idInscripcio}"
        result = requests.delete(url, headers=self.get_headers())
        return result

    def create_inscripcio(self, passaport: str, idActivitat: str):
        url = f"{self.url_api}/inscripcions/public"
        # url = f"http://localhost:8000/inscripcions/public"
        colegiat = self.get_colegiat_by_passaport(passaport)
        print(colegiat)
        data = {
            "inscripcions": [
                {
                    "formatNouActivitat": True,
                    "quotesObligatories": [],
                    "unitatsQuota": {},
                    "quotesOpcionals": [],
                    "descomptesGenerals": [],
                    "descompteCodi": None,
                    "campsPersonalitzats": {},
                    "observacions": None,
                    "isAutoritzaDretsImatge": False,
                    "isAfegirAGrupFamiliar": False,
                    "isCapFamilia": False,
                    "signatura": {},
                    "idColegiat": "3543",
                    "idActivitat": idActivitat,
                    "colegiat": colegiat,
                }
            ]
        }
        print(data)
        res = requests.post(
            url,
            data=json.dumps(data),
            headers=self.get_headers(),
            allow_redirects=False,
        )
        print(res.status_code)


class PlayoffWeb:
    """Simula llamadas a la web de Playoff"""

    def __init__(self):
        self.url_base = f"https://{ENDPOINT}.playoffinformatica.com"
        self.url_api = f"{self.url_base}/api.php/api/v1.0"
        self.headers = {"Content-Type": "application/json", "content-encoding": "gzip"}
        self.api_client = PlayoffAPI()
        self.web_token = ""

    def get_token(self):
        if self.web_token != "":
            return self.web_token

        url_login = f"{self.url_base}/FormLogin.php"
        # url_login = f"http://localhost:8000/FormLogin.php"
        params = {"accio": "login", "nomUsu": USERNAME, "pasUsu": PASSWORD}
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "accept": "application/json, text/plain, */*",
        }
        res = requests.post(
            url_login, data=params, headers=headers, allow_redirects=False
        )
        self.web_token = res.headers.get("set-cookie")
        return self.web_token

    def get_headers(self) -> dict:
        bearer = self.get_token()
        return {**self.headers, **{"Authorization": f"Bearer {bearer}"}}
