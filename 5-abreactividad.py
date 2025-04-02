#!/usr/bin/env python

import configparser
import datetime
import os
import pprint
import sys

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)


data = {"Authorization": f"Bearer {token}"}


idActivitat = False
if len(sys.argv) > 1:
    try:
        idActivitat = int(sys.argv[1])
    except Exception:
        idActivitat = False

if not idActivitat:
    print("Actividad no indicada")
    sys.exit(-1)


null = ""
false = False
true = True


# Get today date
today = datetime.datetime.now()
tomorrow = today + datetime.timedelta(minutes=15)

override = {
    "dataInici": "%s-%s-%s %s:%s"
    % (today.year, today.month, today.day, today.hour, today.minute),
    "dataLimit": "%s-%s-%s %s:%s"
    % (tomorrow.year, tomorrow.month, tomorrow.day, tomorrow.hour, tomorrow.minute),
}

print("Haciendo llamada API")
pprint.pprint(common.editaactividad(token, idActivitat, override))
