import configparser
import json
import logging
import os
from urllib.request import HTTPBasicAuthHandler

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
        self.headers = {
            "Content-Type": "application/json",
            "content-encoding": "gzip",
        }
        self.token = None
        self.client_web: PlayoffWeb | None = None

    def get_bearer(self, user=USERNAME, password=PASSWORD):
        if self.token is not None:
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

    def get_colegiat_by_nif(self, nif: str) -> dict:
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

    def del_inscripcio(self, idInscripcio: str):
        url = f"{self.url_api}/inscripcions?idInscripcio={idInscripcio}"
        result = requests.delete(url, headers=self.get_headers())
        return result

    def create_inscripcio(
        self, idActivitat: str, passaport: str = None, idColegiat: str = None
    ):
        url = f"{self.url_api}/inscripcions/public"
        # url = f"http://localhost:8000/inscripcions/public"
        if passaport is not None:
            colegiat = self.get_colegiat_by_passaport(passaport)

        if idColegiat is not None:
            colegiat = self.client_web.get_colegiat_by_id(idColegiat)

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
        res = requests.post(
            url,
            data=json.dumps(data),
            headers=self.get_headers(),
            allow_redirects=False,
        )
        return res

    def get_inscripcions_by_idActivitat(self, idActivitat):
        return self.get(f"inscripcions?idActivitat={idActivitat}")

    def get_inscripcions_by_idActivitat_passaport(self, idActivitat, passaport):
        inscripcions = self.get_inscripcions_by_idActivitat(idActivitat)


class PlayoffWeb:
    """Simula llamadas a la web de Playoff"""

    def __init__(self):
        self.url_base = f"https://{ENDPOINT}.playoffinformatica.com"
        self.url_api = f"{self.url_base}/api.php/api/v1.0"
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "content-encoding": "gzip",
        }
        self.client_api: PlayoffAPI | None = None
        self.web_token = None

    def get_token(self):
        if self.web_token is not None:
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
        self.web_token = res.headers.get("set-cookie", "=").split("=")[1]
        return self.web_token

    def get_headers(self) -> dict:
        bearer = self.get_token()
        return {**self.headers, **{"Authorization": f"Bearer {bearer}"}}

    def get_colegiat_by_id(self, idColegiat: str):
        data = (
            "draw=4&columns%5B0%5D%5Bdata%5D=&columns%5B0%5D%5Bname%5D=&columns%5B0%5D%5Bsearchable%5D=0&columns%5B0%5D%5Borderable%5D=0&columns%5B0%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B0%5D%5Bvisible%5D=true&columns%5B0%5D%5Btype%5D=selector&columns%5B1%5D%5Bdata%5D=idColegiat&columns%5B1%5D%5Bname%5D=Colegiat.idColegiat&columns%5B1%5D%5Bsearchable%5D=0&columns%5B1%5D%5Borderable%5D=1&columns%5B1%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B1%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B1%5D%5Bvisible%5D=false&columns%5B1%5D%5Btype%5D=num&columns%5B2%5D%5Bdata%5D=idModalitat&columns%5B2%5D%5Bname%5D=Colegiat_has_Modalitat.idModalitat&columns%5B2%5D%5Bsearchable%5D=0&columns%5B2%5D%5Borderable%5D=1&columns%5B2%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B2%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B2%5D%5Bvisible%5D=false&columns%5B2%5D%5Btype%5D=num&columns%5B3%5D%5Bdata%5D=fotoThumbnail&columns%5B3%5D%5Bname%5D=fotoThumbnail&columns%5B3%5D%5Bsearchable%5D=0&columns%5B3%5D%5Borderable%5D=1&columns%5B3%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B3%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B3%5D%5Bvisible%5D=false&columns%5B3%5D%5Btype%5D=fotoPerfil&columns%5B4%5D%5Bdata%5D=numColegiat&columns%5B4%5D%5Bname%5D=Colegiat.numColegiat&columns%5B4%5D%5Bsearchable%5D=0&columns%5B4%5D%5Borderable%5D=1&columns%5B4%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B4%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B4%5D%5Bvisible%5D=false&columns%5B4%5D%5Btype%5D=num&columns%5B5%5D%5Bdata%5D=nomEstat&columns%5B5%5D%5Bname%5D=EstatColegiat.idEstatColegiat&columns%5B5%5D%5Bsearchable%5D=0&columns%5B5%5D%5Borderable%5D=1&columns%5B5%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B5%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B5%5D%5Bvisible%5D=false&columns%5B5%5D%5Bclase%5D=true&columns%5B5%5D%5Btype%5D=string&columns%5B5%5D%5BcampATraduir%5D=true&columns%5B6%5D%5Bdata%5D=nom&columns%5B6%5D%5Bname%5D=Persona.nom&columns%5B6%5D%5Bsearchable%5D=1&columns%5B6%5D%5Borderable%5D=1&columns%5B6%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B6%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B6%5D%5Bvisible%5D=true&columns%5B6%5D%5Btype%5D=string&columns%5B7%5D%5Bdata%5D=cognoms&columns%5B7%5D%5Bname%5D=Persona.cognoms&columns%5B7%5D%5Bsearchable%5D=1&columns%5B7%5D%5Borderable%5D=1&columns%5B7%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B7%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B7%5D%5Bvisible%5D=true&columns%5B7%5D%5Btype%5D=string-utf8&columns%5B8%5D%5Bdata%5D=nif&columns%5B8%5D%5Bname%5D=Persona.nif&columns%5B8%5D%5Bsearchable%5D=1&columns%5B8%5D%5Borderable%5D=1&columns%5B8%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B8%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B8%5D%5Bvisible%5D=true&columns%5B8%5D%5Btype%5D=num-fmt&columns%5B9%5D%5Bdata%5D=residencia&columns%5B9%5D%5Bname%5D=Persona.residencia&columns%5B9%5D%5Bsearchable%5D=1&columns%5B9%5D%5Borderable%5D=1&columns%5B9%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B9%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B9%5D%5Bvisible%5D=true&columns%5B9%5D%5Btype%5D=num&columns%5B10%5D%5Bdata%5D=tePassaport&columns%5B10%5D%5Bname%5D=tePassaport&columns%5B10%5D%5Bsearchable%5D=0&columns%5B10%5D%5Borderable%5D=1&columns%5B10%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B10%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B10%5D%5Bvisible%5D=false&columns%5B10%5D%5Btype%5D=string&columns%5B10%5D%5BisHaving%5D=true&columns%5B11%5D%5Bdata%5D=dataNaixement&columns%5B11%5D%5Bname%5D=Persona.dataNaixement&columns%5B11%5D%5Bsearchable%5D=1&columns%5B11%5D%5Borderable%5D=1&columns%5B11%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B11%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B11%5D%5Bvisible%5D=true&columns%5B11%5D%5Btype%5D=moment-DD%2FMM%2FYYYY&columns%5B12%5D%5Bdata%5D=edat&columns%5B12%5D%5Bname%5D=Persona.dataNaixement&columns%5B12%5D%5Bsearchable%5D=1&columns%5B12%5D%5Borderable%5D=1&columns%5B12%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B12%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B12%5D%5Bvisible%5D=true&columns%5B12%5D%5Btype%5D=edat&columns%5B13%5D%5Bdata%5D=sexe&columns%5B13%5D%5Bname%5D=Persona.sexe&columns%5B13%5D%5Bsearchable%5D=0&columns%5B13%5D%5Borderable%5D=1&columns%5B13%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B13%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B13%5D%5Bvisible%5D=false&columns%5B13%5D%5Btype%5D=string&columns%5B13%5D%5BcampATraduir%5D=true&columns%5B14%5D%5Bdata%5D=estatCivil&columns%5B14%5D%5Bname%5D=Persona.estatCivil&columns%5B14%5D%5Bsearchable%5D=0&columns%5B14%5D%5Borderable%5D=1&columns%5B14%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B14%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B14%5D%5Bvisible%5D=false&columns%5B14%5D%5Btype%5D=string&columns%5B14%5D%5BcampATraduir%5D=true&columns%5B15%5D%5Bdata%5D=escola&columns%5B15%5D%5Bname%5D=Colegiat.escola&columns%5B15%5D%5Bsearchable%5D=1&columns%5B15%5D%5Borderable%5D=1&columns%5B15%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B15%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B15%5D%5Bvisible%5D=true&columns%5B15%5D%5Btype%5D=string&columns%5B16%5D%5Bdata%5D=telefonPrincipal&columns%5B16%5D%5Bname%5D=Adreca.telefonPrincipal&columns%5B16%5D%5Bsearchable%5D=0&columns%5B16%5D%5Borderable%5D=1&columns%5B16%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B16%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B16%5D%5Bvisible%5D=false&columns%5B16%5D%5Btype%5D=num&columns%5B17%5D%5Bdata%5D=telefonSecundari&columns%5B17%5D%5Bname%5D=Adreca.telefonSecundari&columns%5B17%5D%5Bsearchable%5D=0&columns%5B17%5D%5Borderable%5D=1&columns%5B17%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B17%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B17%5D%5Bvisible%5D=false&columns%5B17%5D%5Btype%5D=string&columns%5B18%5D%5Bdata%5D=codipostal&columns%5B18%5D%5Bname%5D=Adreca.codipostal&columns%5B18%5D%5Bsearchable%5D=0&columns%5B18%5D%5Borderable%5D=1&columns%5B18%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B18%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B18%5D%5Bvisible%5D=false&columns%5B18%5D%5Btype%5D=num&columns%5B19%5D%5Bdata%5D=domicili&columns%5B19%5D%5Bname%5D=Adreca.domicili&columns%5B19%5D%5Bsearchable%5D=0&columns%5B19%5D%5Borderable%5D=1&columns%5B19%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B19%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B19%5D%5Bvisible%5D=false&columns%5B19%5D%5Btype%5D=string-utf8&columns%5B20%5D%5Bdata%5D=municipi&columns%5B20%5D%5Bname%5D=Municipi.nom&columns%5B20%5D%5Bsearchable%5D=0&columns%5B20%5D%5Borderable%5D=1&columns%5B20%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B20%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B20%5D%5Bvisible%5D=false&columns%5B20%5D%5Btype%5D=string-utf8&columns%5B21%5D%5Bdata%5D=nomProvincia&columns%5B21%5D%5Bname%5D=Provincia.nom&columns%5B21%5D%5Bsearchable%5D=0&columns%5B21%5D%5Borderable%5D=1&columns%5B21%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B21%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B21%5D%5Bvisible%5D=false&columns%5B21%5D%5Btype%5D=string-utf8&columns%5B22%5D%5Bdata%5D=prefixPais&columns%5B22%5D%5Bname%5D=prefixPais&columns%5B22%5D%5Bsearchable%5D=0&columns%5B22%5D%5Borderable%5D=1&columns%5B22%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B22%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B22%5D%5Bvisible%5D=false&columns%5B22%5D%5Btype%5D=string&columns%5B22%5D%5BcampATraduir%5D=true&columns%5B22%5D%5BisHaving%5D=true&columns%5B23%5D%5Bdata%5D=prefixNacionalitat&columns%5B23%5D%5Bname%5D=prefixNacionalitat&columns%5B23%5D%5Bsearchable%5D=0&columns%5B23%5D%5Borderable%5D=1&columns%5B23%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B23%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B23%5D%5Bvisible%5D=false&columns%5B23%5D%5Btype%5D=string-utf8&columns%5B23%5D%5BcampATraduir%5D=true&columns%5B23%5D%5BisHaving%5D=true&columns%5B24%5D%5Bdata%5D=email&columns%5B24%5D%5Bname%5D=Adreca.email&columns%5B24%5D%5Bsearchable%5D=0&columns%5B24%5D%5Borderable%5D=1&columns%5B24%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B24%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B24%5D%5Bvisible%5D=false&columns%5B24%5D%5Btype%5D=string&columns%5B25%5D%5Bdata%5D=emailOficial&columns%5B25%5D%5Bname%5D=Adreca.emailOficial&columns%5B25%5D%5Bsearchable%5D=0&columns%5B25%5D%5Borderable%5D=1&columns%5B25%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B25%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B25%5D%5Bvisible%5D=false&columns%5B25%5D%5Btype%5D=string&columns%5B26%5D%5Bdata%5D=web&columns%5B26%5D%5Bname%5D=Adreca.web&columns%5B26%5D%5Bsearchable%5D=0&columns%5B26%5D%5Borderable%5D=1&columns%5B26%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B26%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B26%5D%5Bvisible%5D=false&columns%5B26%5D%5Btype%5D=string&columns%5B27%5D%5Bdata%5D=dataAlta&columns%5B27%5D%5Bname%5D=Colegiat.dataAlta&columns%5B27%5D%5Bsearchable%5D=1&columns%5B27%5D%5Borderable%5D=1&columns%5B27%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B27%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B27%5D%5Bvisible%5D=true&columns%5B27%5D%5Btype%5D=moment-DD%2FMM%2FYYYY&columns%5B28%5D%5Bdata%5D=dataBaixa&columns%5B28%5D%5Bname%5D=Colegiat.dataBaixa&columns%5B28%5D%5Bsearchable%5D=0&columns%5B28%5D%5Borderable%5D=1&columns%5B28%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B28%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B28%5D%5Bvisible%5D=false&columns%5B28%5D%5Btype%5D=moment-DD%2FMM%2FYYYY&columns%5B29%5D%5Bdata%5D=iban&columns%5B29%5D%5Bname%5D=Banc.iban&columns%5B29%5D%5Bsearchable%5D=0&columns%5B29%5D%5Borderable%5D=1&columns%5B29%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B29%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B29%5D%5Bvisible%5D=false&columns%5B29%5D%5Btype%5D=string&columns%5B30%5D%5Bdata%5D=titular&columns%5B30%5D%5Bname%5D=Banc.titular&columns%5B30%5D%5Bsearchable%5D=0&columns%5B30%5D%5Borderable%5D=1&columns%5B30%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B30%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B30%5D%5Bvisible%5D=false&columns%5B30%5D%5Btype%5D=string&columns%5B31%5D%5Bdata%5D=teApp&columns%5B31%5D%5Bname%5D=teApp&columns%5B31%5D%5Bsearchable%5D=0&columns%5B31%5D%5Borderable%5D=1&columns%5B31%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B31%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B31%5D%5Bvisible%5D=false&columns%5B31%5D%5Btype%5D=string&columns%5B31%5D%5BcampATraduir%5D%5B0%5D%5Busr%5D=No&columns%5B31%5D%5BcampATraduir%5D%5B0%5D%5Bbd%5D=0&columns%5B31%5D%5BcampATraduir%5D%5B1%5D%5Busr%5D=S%C3%AD&columns%5B31%5D%5BcampATraduir%5D%5B1%5D%5Bbd%5D=1&columns%5B31%5D%5BisHaving%5D=true&columns%5B32%5D%5Bdata%5D=observacionsColegiat&columns%5B32%5D%5Bname%5D=Colegiat.observacions&columns%5B32%5D%5Bsearchable%5D=0&columns%5B32%5D%5Borderable%5D=1&columns%5B32%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B32%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B32%5D%5Bvisible%5D=false&columns%5B32%5D%5Btype%5D=string-utf8&columns%5B33%5D%5Bdata%5D=numeroRebutsRetornats&columns%5B33%5D%5Bname%5D=Colegiat.numeroRebutsRetornats&columns%5B33%5D%5Bsearchable%5D=0&columns%5B33%5D%5Borderable%5D=1&columns%5B33%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B33%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B33%5D%5Bvisible%5D=false&columns%5B33%5D%5Btype%5D=num&columns%5B34%5D%5Bdata%5D=importRebutsRetornats&columns%5B34%5D%5Bname%5D=Colegiat.importRebutsRetornats&columns%5B34%5D%5Bsearchable%5D=0&columns%5B34%5D%5Borderable%5D=1&columns%5B34%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B34%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B34%5D%5Bvisible%5D=false&columns%5B34%5D%5Btype%5D=num&columns%5B35%5D%5Bdata%5D=dataRebutRetornat&columns%5B35%5D%5Bname%5D=Colegiat.dataRebutRetornat&columns%5B35%5D%5Bsearchable%5D=0&columns%5B35%5D%5Borderable%5D=1&columns%5B35%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B35%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B35%5D%5Bvisible%5D=false&columns%5B35%5D%5Btype%5D=moment-DD%2FMM%2FYYYY&columns%5B36%5D%5Bdata%5D=pendents&columns%5B36%5D%5Bname%5D=RebutsPendents.pendents&columns%5B36%5D%5Bsearchable%5D=0&columns%5B36%5D%5Borderable%5D=1&columns%5B36%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B36%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B36%5D%5Bvisible%5D=false&columns%5B36%5D%5Btype%5D=string&columns%5B37%5D%5Bdata%5D=importTotalPendent&columns%5B37%5D%5Bname%5D=RebutsPendents.importTotalPendent&columns%5B37%5D%5Bsearchable%5D=0&columns%5B37%5D%5Borderable%5D=1&columns%5B37%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B37%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B37%5D%5Bvisible%5D=false&columns%5B37%5D%5Btype%5D=string&columns%5B38%5D%5Bdata%5D=metodePagament&columns%5B38%5D%5Bname%5D=Colegiat.metodePagament&columns%5B38%5D%5Bsearchable%5D=0&columns%5B38%5D%5Borderable%5D=1&columns%5B38%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B38%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B38%5D%5Bvisible%5D=false&columns%5B38%5D%5Btype%5D=string-utf8&columns%5B38%5D%5BcampATraduir%5D=true&columns%5B39%5D%5Bdata%5D=nomTutor1&columns%5B39%5D%5Bname%5D=Tutor1.nom&columns%5B39%5D%5Bsearchable%5D=0&columns%5B39%5D%5Borderable%5D=1&columns%5B39%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B39%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B39%5D%5Bvisible%5D=false&columns%5B39%5D%5Btype%5D=string&columns%5B40%5D%5Bdata%5D=cognomsTutor1&columns%5B40%5D%5Bname%5D=Tutor1.cognoms&columns%5B40%5D%5Bsearchable%5D=0&columns%5B40%5D%5Borderable%5D=1&columns%5B40%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B40%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B40%5D%5Bvisible%5D=false&columns%5B40%5D%5Btype%5D=string&columns%5B41%5D%5Bdata%5D=telefonFixTutor1&columns%5B41%5D%5Bname%5D=AdrecaTutor1.telefonPrincipal&columns%5B41%5D%5Bsearchable%5D=0&columns%5B41%5D%5Borderable%5D=1&columns%5B41%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B41%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B41%5D%5Bvisible%5D=false&columns%5B41%5D%5Btype%5D=num&columns%5B42%5D%5Bdata%5D=mobilTutor1&columns%5B42%5D%5Bname%5D=AdrecaTutor1.telefonSecundari&columns%5B42%5D%5Bsearchable%5D=0&columns%5B42%5D%5Borderable%5D=1&columns%5B42%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B42%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B42%5D%5Bvisible%5D=false&columns%5B42%5D%5Btype%5D=string&columns%5B43%5D%5Bdata%5D=emailTutor1&columns%5B43%5D%5Bname%5D=AdrecaTutor1.email&columns%5B43%5D%5Bsearchable%5D=0&columns%5B43%5D%5Borderable%5D=1&columns%5B43%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B43%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B43%5D%5Bvisible%5D=false&columns%5B43%5D%5Btype%5D=string&columns%5B44%5D%5Bdata%5D=nomTutor2&columns%5B44%5D%5Bname%5D=Tutor2.nom&columns%5B44%5D%5Bsearchable%5D=0&columns%5B44%5D%5Borderable%5D=1&columns%5B44%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B44%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B44%5D%5Bvisible%5D=false&columns%5B44%5D%5Btype%5D=string-utf8&columns%5B45%5D%5Bdata%5D=cognomsTutor2&columns%5B45%5D%5Bname%5D=Tutor2.cognoms&columns%5B45%5D%5Bsearchable%5D=0&columns%5B45%5D%5Borderable%5D=1&columns%5B45%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B45%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B45%5D%5Bvisible%5D=false&columns%5B45%5D%5Btype%5D=string&columns%5B46%5D%5Bdata%5D=telefonFixTutor2&columns%5B46%5D%5Bname%5D=AdrecaTutor2.telefonPrincipal&columns%5B46%5D%5Bsearchable%5D=0&columns%5B46%5D%5Borderable%5D=1&columns%5B46%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B46%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B46%5D%5Bvisible%5D=false&columns%5B46%5D%5Btype%5D=num&columns%5B47%5D%5Bdata%5D=mobilTutor2&columns%5B47%5D%5Bname%5D=AdrecaTutor2.telefonSecundari&columns%5B47%5D%5Bsearchable%5D=0&columns%5B47%5D%5Borderable%5D=1&columns%5B47%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B47%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B47%5D%5Bvisible%5D=false&columns%5B47%5D%5Btype%5D=string&columns%5B48%5D%5Bdata%5D=emailTutor2&columns%5B48%5D%5Bname%5D=AdrecaTutor2.email&columns%5B48%5D%5Bsearchable%5D=0&columns%5B48%5D%5Borderable%5D=1&columns%5B48%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B48%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B48%5D%5Bvisible%5D=false&columns%5B48%5D%5Btype%5D=string&columns%5B49%5D%5Bdata%5D=adjunts&columns%5B49%5D%5Bname%5D=&columns%5B49%5D%5Bsearchable%5D=0&columns%5B49%5D%5Borderable%5D=1&columns%5B49%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B49%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B49%5D%5Bvisible%5D=true&columns%5B49%5D%5Btype%5D=html&columns%5B49%5D%5BcercaGeneralServidor%5D=0&columns%5B49%5D%5Bmultivalor%5D=true&columns%5B50%5D%5Bdata%5D=1_0_20220126102039am&columns%5B50%5D%5Bname%5D=Colegiat.campsDinamics.1_0_20220126102039am&columns%5B50%5D%5Bsearchable%5D=0&columns%5B50%5D%5Borderable%5D=1&columns%5B50%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B50%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B50%5D%5Bvisible%5D=false&columns%5B50%5D%5Btype%5D%5B%5D=json&columns%5B50%5D%5Btype%5D%5B%5D=CD_FORMAT_MULTIPLESVALORS&columns%5B51%5D%5Bdata%5D=1_1_20220908054836am&columns%5B51%5D%5Bname%5D=Colegiat.campsDinamics.1_1_20220908054836am&columns%5B51%5D%5Bsearchable%5D=0&columns%5B51%5D%5Borderable%5D=1&columns%5B51%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B51%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B51%5D%5Bvisible%5D=false&columns%5B51%5D%5Btype%5D=json&columns%5B52%5D%5Bdata%5D=1_0_20190831085222am&columns%5B52%5D%5Bname%5D=Colegiat.campsDinamics.1_0_20190831085222am&columns%5B52%5D%5Bsearchable%5D=0&columns%5B52%5D%5Borderable%5D=1&columns%5B52%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B52%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B52%5D%5Bvisible%5D=false&columns%5B52%5D%5Btype%5D=json&columns%5B53%5D%5Bdata%5D=1_1_20210606061659am&columns%5B53%5D%5Bname%5D=Colegiat.campsDinamics.1_1_20210606061659am&columns%5B53%5D%5Bsearchable%5D=0&columns%5B53%5D%5Borderable%5D=1&columns%5B53%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B53%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B53%5D%5Bvisible%5D=false&columns%5B53%5D%5Btype%5D%5B%5D=json&columns%5B53%5D%5Btype%5D%5B%5D=CD_FORMAT_MULTIPLESVALORS&columns%5B54%5D%5Bdata%5D=1_4_20210707032324pm&columns%5B54%5D%5Bname%5D=Colegiat.campsDinamics.1_4_20210707032324pm&columns%5B54%5D%5Bsearchable%5D=0&columns%5B54%5D%5Borderable%5D=1&columns%5B54%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B54%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B54%5D%5Bvisible%5D=false&columns%5B54%5D%5Btype%5D%5B%5D=json&columns%5B54%5D%5Btype%5D%5B%5D=CD_FORMAT_MULTIPLESVALORS&columns%5B55%5D%5Bdata%5D=1_3_20210707032324pm&columns%5B55%5D%5Bname%5D=Colegiat.campsDinamics.1_3_20210707032324pm&columns%5B55%5D%5Bsearchable%5D=0&columns%5B55%5D%5Borderable%5D=1&columns%5B55%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B55%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B55%5D%5Bvisible%5D=false&columns%5B55%5D%5Btype%5D=json&columns%5B55%5D%5BcampATraduir%5D%5B0%5D%5Busr%5D=NO&columns%5B55%5D%5BcampATraduir%5D%5B0%5D%5Bbd%5D=0&columns%5B55%5D%5BcampATraduir%5D%5B1%5D%5Busr%5D=SI&columns%5B55%5D%5BcampATraduir%5D%5B1%5D%5Bbd%5D=1&columns%5B56%5D%5Bdata%5D=1_5_20210708123547pm&columns%5B56%5D%5Bname%5D=Colegiat.campsDinamics.1_5_20210708123547pm&columns%5B56%5D%5Bsearchable%5D=0&columns%5B56%5D%5Borderable%5D=1&columns%5B56%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B56%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B56%5D%5Bvisible%5D=false&columns%5B56%5D%5Btype%5D=json&columns%5B56%5D%5BcampATraduir%5D%5B0%5D%5Busr%5D=NO&columns%5B56%5D%5BcampATraduir%5D%5B0%5D%5Bbd%5D=0&columns%5B56%5D%5BcampATraduir%5D%5B1%5D%5Busr%5D=SI&columns%5B56%5D%5BcampATraduir%5D%5B1%5D%5Bbd%5D=1&columns%5B57%5D%5Bdata%5D=1_6_20210708123547pm&columns%5B57%5D%5Bname%5D=Colegiat.campsDinamics.1_6_20210708123547pm&columns%5B57%5D%5Bsearchable%5D=0&columns%5B57%5D%5Borderable%5D=1&columns%5B57%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B57%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B57%5D%5Bvisible%5D=false&columns%5B57%5D%5Btype%5D=json&columns%5B57%5D%5BcampATraduir%5D%5B0%5D%5Busr%5D=NO&columns%5B57%5D%5BcampATraduir%5D%5B0%5D%5Bbd%5D=0&columns%5B57%5D%5BcampATraduir%5D%5B1%5D%5Busr%5D=SI&columns%5B57%5D%5BcampATraduir%5D%5B1%5D%5Bbd%5D=1&columns%5B58%5D%5Bdata%5D=1_7_20210708124318pm&columns%5B58%5D%5Bname%5D=Colegiat.campsDinamics.1_7_20210708124318pm&columns%5B58%5D%5Bsearchable%5D=0&columns%5B58%5D%5Borderable%5D=1&columns%5B58%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B58%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B58%5D%5Bvisible%5D=false&columns%5B58%5D%5Btype%5D=json&columns%5B59%5D%5Bdata%5D=1_8_20220221034044pm&columns%5B59%5D%5Bname%5D=Colegiat.campsDinamics.1_8_20220221034044pm&columns%5B59%5D%5Bsearchable%5D=0&columns%5B59%5D%5Borderable%5D=1&columns%5B59%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B59%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B59%5D%5Bvisible%5D=false&columns%5B59%5D%5Btype%5D%5B%5D=json&columns%5B59%5D%5Btype%5D%5B%5D=CD_FORMAT_MULTIPLESVALORS&columns%5B60%5D%5Bdata%5D=0_13_20231012041710&columns%5B60%5D%5Bname%5D=Colegiat.campsDinamics.0_13_20231012041710&columns%5B60%5D%5Bsearchable%5D=0&columns%5B60%5D%5Borderable%5D=1&columns%5B60%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B60%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B60%5D%5Bvisible%5D=false&columns%5B60%5D%5Btype%5D%5B%5D=json&columns%5B60%5D%5Btype%5D%5B%5D=CD_FORMAT_NUM&columns%5B61%5D%5Bdata%5D=0_14_20231012045321&columns%5B61%5D%5Bname%5D=Colegiat.campsDinamics.0_14_20231012045321&columns%5B61%5D%5Bsearchable%5D=0&columns%5B61%5D%5Borderable%5D=1&columns%5B61%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B61%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B61%5D%5Bvisible%5D=false&columns%5B61%5D%5Btype%5D%5B%5D=json&columns%5B61%5D%5Btype%5D%5B%5D=CD_FORMAT_NUM&columns%5B62%5D%5Bdata%5D=0_16_20241120130245&columns%5B62%5D%5Bname%5D=Colegiat.campsDinamics.0_16_20241120130245&columns%5B62%5D%5Bsearchable%5D=0&columns%5B62%5D%5Borderable%5D=1&columns%5B62%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B62%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B62%5D%5Bvisible%5D=false&columns%5B62%5D%5Btype%5D%5B%5D=json&columns%5B62%5D%5Btype%5D%5B%5D=CD_FORMAT_NUM&columns%5B63%5D%5Bdata%5D=1_9_20220308034849pm&columns%5B63%5D%5Bname%5D=Colegiat.campsDinamics.1_9_20220308034849pm&columns%5B63%5D%5Bsearchable%5D=0&columns%5B63%5D%5Borderable%5D=1&columns%5B63%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B63%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B63%5D%5Bvisible%5D=false&columns%5B63%5D%5Btype%5D%5B%5D=json&columns%5B63%5D%5Btype%5D%5B%5D=CD_FORMAT_MULTIPLESVALORS&columns%5B64%5D%5Bdata%5D=1_10_20220309040836pm&columns%5B64%5D%5Bname%5D=Colegiat.campsDinamics.1_10_20220309040836pm&columns%5B64%5D%5Bsearchable%5D=0&columns%5B64%5D%5Borderable%5D=1&columns%5B64%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B64%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B64%5D%5Bvisible%5D=false&columns%5B64%5D%5Btype%5D=json&columns%5B64%5D%5BcampATraduir%5D%5B0%5D%5Busr%5D=NO&columns%5B64%5D%5BcampATraduir%5D%5B0%5D%5Bbd%5D=0&columns%5B64%5D%5BcampATraduir%5D%5B1%5D%5Busr%5D=SI&columns%5B64%5D%5BcampATraduir%5D%5B1%5D%5Bbd%5D=1&columns%5B65%5D%5Bdata%5D=1_11_20220309113126pm&columns%5B65%5D%5Bname%5D=Colegiat.campsDinamics.1_11_20220309113126pm&columns%5B65%5D%5Bsearchable%5D=0&columns%5B65%5D%5Borderable%5D=1&columns%5B65%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B65%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B65%5D%5Bvisible%5D=false&columns%5B65%5D%5Btype%5D=json&columns%5B65%5D%5BcampATraduir%5D%5B0%5D%5Busr%5D=NO&columns%5B65%5D%5BcampATraduir%5D%5B0%5D%5Bbd%5D=0&columns%5B65%5D%5BcampATraduir%5D%5B1%5D%5Busr%5D=SI&columns%5B65%5D%5BcampATraduir%5D%5B1%5D%5Bbd%5D=1&columns%5B66%5D%5Bdata%5D=0_15_20241120112536&columns%5B66%5D%5Bname%5D=Colegiat.campsDinamics.0_15_20241120112536&columns%5B66%5D%5Bsearchable%5D=0&columns%5B66%5D%5Borderable%5D=1&columns%5B66%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B66%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B66%5D%5Bvisible%5D=false&columns%5B66%5D%5Btype%5D%5B%5D=json&columns%5B66%5D%5Btype%5D%5B%5D=CD_FORMAT_MULTIPLESVALORS&columns%5B67%5D%5Bdata%5D=0_17_20250221121130&columns%5B67%5D%5Bname%5D=Colegiat.campsDinamics.0_17_20250221121130&columns%5B67%5D%5Bsearchable%5D=0&columns%5B67%5D%5Borderable%5D=1&columns%5B67%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B67%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B67%5D%5Bvisible%5D=false&columns%5B67%5D%5Btype%5D%5B%5D=json&columns%5B67%5D%5Btype%5D%5B%5D=moment-DD%2FMM%2FYYYY&start=0&length=15&search%5Bvalue%5D=&search%5Bregex%5D=false&sqlKey=Colegiats&preparedQuery=true&ColReorder%5B%5D=0&ColReorder%5B%5D=1&ColReorder%5B%5D=2&ColReorder%5B%5D=3&ColReorder%5B%5D=4&ColReorder%5B%5D=5&ColReorder%5B%5D=6&ColReorder%5B%5D=7&ColReorder%5B%5D=8&ColReorder%5B%5D=9&ColReorder%5B%5D=10&ColReorder%5B%5D=11&ColReorder%5B%5D=12&ColReorder%5B%5D=13&ColReorder%5B%5D=14&ColReorder%5B%5D=15&ColReorder%5B%5D=16&ColReorder%5B%5D=17&ColReorder%5B%5D=18&ColReorder%5B%5D=19&ColReorder%5B%5D=20&ColReorder%5B%5D=21&ColReorder%5B%5D=22&ColReorder%5B%5D=23&ColReorder%5B%5D=24&ColReorder%5B%5D=25&ColReorder%5B%5D=26&ColReorder%5B%5D=27&ColReorder%5B%5D=28&ColReorder%5B%5D=29&ColReorder%5B%5D=30&ColReorder%5B%5D=31&ColReorder%5B%5D=32&ColReorder%5B%5D=33&ColReorder%5B%5D=34&ColReorder%5B%5D=35&ColReorder%5B%5D=36&ColReorder%5B%5D=37&ColReorder%5B%5D=38&ColReorder%5B%5D=39&ColReorder%5B%5D=40&ColReorder%5B%5D=41&ColReorder%5B%5D=42&ColReorder%5B%5D=43&ColReorder%5B%5D=44&ColReorder%5B%5D=45&ColReorder%5B%5D=46&ColReorder%5B%5D=47&ColReorder%5B%5D=48&ColReorder%5B%5D=49&ColReorder%5B%5D=50&ColReorder%5B%5D=51&ColReorder%5B%5D=52&ColReorder%5B%5D=53&ColReorder%5B%5D=54&ColReorder%5B%5D=55&ColReorder%5B%5D=56&ColReorder%5B%5D=57&ColReorder%5B%5D=58&ColReorder%5B%5D=59&ColReorder%5B%5D=60&ColReorder%5B%5D=61&ColReorder%5B%5D=62&ColReorder%5B%5D=63&ColReorder%5B%5D=64&ColReorder%5B%5D=65&ColReorder%5B%5D=66&ColReorder%5B%5D=67&paramsExtra%5B0%5D%5Bnom%5D=idColegiat&paramsExtra%5B0%5D%5BisId%5D=true&paramsExtra%5B0%5D%5BsName%5D=Colegiat.idColegiat&paramsExtra%5B%5D=idModalitat&paramsExtra%5B%5D=numColegiat&paramsExtra%5B%5D=nomEstat&paramsExtra%5B%5D=cognoms&paramsExtra%5B%5D=nom&paramsExtra%5B%5D=nif&paramsExtra%5B%5D=residencia&paramsExtra%5B%5D=dataNaixement&searchURL%5B0%5D%5Bcamp%5D=Colegi.idColegi&searchURL%5B0%5D%5Bvalor%5D=1&cercaAvancada%5B0%5D%5Bcamp%5D=Colegiat.idColegiat&cercaAvancada%5B0%5D%5Btipus%5D=DT_CERCA_TIPUS_IGUAL&cercaAvancada%5B0%5D%5Bvalor%5D%5B%5D="
            + idColegiat
        )
        url = f"{self.url_api}/llistats/consulta"
        # url = f"http://localhost:8000/llistats/consulta"
        res = requests.post(url, data=data, headers=self.get_headers())
        return res.json().get("data")[0]


class Playoff:
    def __init__(self) -> None:
        self.api = PlayoffAPI()
        self.web = PlayoffWeb()
        self.api.client_web = self.web
        self.web.client_api = self.api
