#!/usr/bin/env python

import configparser
import datetime
import json
import os

import dateutil.parser
import requests

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)

data = {"Authorization": f"Bearer {token}"}


print("Haciendo llamada API")
socioid = 2592
socioid = 3722

url = f"{common.apiurl}/colegiats/rebuts?idColegiat={socioid}&limit=1000"
response = json.loads(
    requests.get(
        url, headers=common.headers, auth=common.BearerAuth(token), timeout=15
    ).text
)

print(f"{common.sociobase}{socioid}#tab=CATEGORIES")

socio = common.get_colegiat_json(socioid)


socioname = socio["persona"]["nom"] + " " + socio["persona"]["cognoms"]
hoy = datetime.datetime.now()
year = hoy.year


texto = f"El socio <b>{socioname}</b>, ha pertenecido a la asociación con nº socio: <b>{socio['numColegiat']}</b>, durante el curso escolar <b>{year - 1}-{year}</b>. Asistiendo a los programas de ayudas para alumnos de altas capacidades intelectuales consistentes en enriquecimiento intelectual y terapias psicológicas de habilidades sociales, asertividad, autocontrol, etc. que el equipo técnico de la asociación considera adecuadas y que se realizan en horario extraescolar en el periodo mencionado."
texto += "<p>"
texto += "<table border='1' cellpadding='5' cellspacing='0'>"
# add table headers
texto += (
    "<tr><th>Base</th><th>Concepto</th><th>Fecha del recibo</th><th>Estado</th></tr>"
)


receiptfound = False
total = 0
for recibo in response:
    # Además, la fecha del recibo debe estar en el rango del año escolar en curso, es decir, desde el 1 de septiembre del año anterior al 30 de junio del año actual.
    # Año en curso (obtenido del sistema)

    # Convert datapagament to a date object using dateutil.parser
    try:
        datapagament = dateutil.parser.parse(recibo["dataPagament"])
    except:
        print("Error procesando %s" % recibo["dataPagament"])
        continue

    if datapagament >= datetime.datetime(
        year - 1, 9, 1
    ) and datapagament <= datetime.datetime(year, 6, 30):
        if "ACTIV" in recibo["concepte"]:
            estado = ""
            if recibo["estat"] == "REBESTRET":
                estado = "DEVUELTO"
            if recibo["estat"] == "REBESTEME":
                estado = "PAGADO"
                total = total + float(recibo["base"])
            print(recibo["base"], recibo["concepte"], recibo["dataPagament"], estado)
            receiptfound = True
            # Append to texto the line for the new receipt

            texto += f"<tr><td>{recibo['base']}</td><td>{recibo['concepte']}</td><td>{recibo['dataPagament']}</td><td>{estado}</td></tr>"

texto += "</table>"
texto += "<small>* Las actividades se han realizado los sábados alternos de cada mes en horario matinal durante el periodo escolar. Y para que conste y surta los efectos oportunos expido el presente documento.</small><p>"


texto += f"Siendo el importe total pagado a estos efectos de <b>{total}€</b>, distribuido como se detalla en la tabla anterior<p>"

texto += (
    f"<p><p>En Valencia a {hoy.day} de {common.nombremes[hoy.month]} de {hoy.year}.</p>"
)


texto += "<p><p><p><p><p>"

texto += "AVAST (Asociación Valenciana de Apoyo a las Altas Capacidades) Inscrita en la Sec. Primera del registro Nacional con el nº 97.619 y el de la C. Valenciana con el nº 4.397"

if receiptfound:
    print("Enviando comunicado")
    # 3290
    response = common.enviacomunicado(
        token=token, data=common.getcomunicado(3290, "Información de recibos", texto)
    )
    print(response)
    print(response.text)
