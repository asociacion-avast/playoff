#!/usr/bin/env python


import configparser
import os

import common

config = configparser.ConfigParser()
config.read(os.path.expanduser("~/.avast.ini"))


socios = common.readjson("socios")


token = common.gettoken(
    user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
)
headers = {"Authorization": f"Bearer {token}"}


def is_valid_telegram_id(value):
    """
    Check if a value is a valid telegram ID (positive integer) or empty/None (also valid)
    """
    # Empty/None values are valid (user might not have provided telegram ID yet)
    if not value:
        return True

    # Handle both string and integer inputs
    try:
        telegram_id = int(value)
        return telegram_id > 0
    except (ValueError, TypeError):
        return False


def validate_and_clean_telegram_fields(socio, token):
    """
    Validate and clean all telegram fields for a socio
    Returns number of fields that were cleaned
    """
    numcolegiat = socio["numColegiat"]
    idcolegiat = socio["idColegiat"]

    # Dictionary to map field IDs to readable names
    field_names = {
        common.tutor1: "TUTOR1",
        common.tutor2: "TUTOR2",
        common.socioid: "SOCIO_ID",
    }

    cleaned_count = 0

    # Check each telegram field that exists for this socio
    for field_id in common.telegramfields:
        if field_id in socio["campsDinamics"]:
            field_name = field_names.get(field_id, f"UNKNOWN_{field_id}")
            field_value = socio["campsDinamics"][field_id]

            # Skip empty/None values (they are valid)
            if not field_value:
                continue

            # Check if telegram ID equals member number (original logic)
            if str(numcolegiat) == str(field_value):
                print(
                    f"    {field_name}: Clearing field - telegram ID equals member number ({field_value})"
                )
                response = common.escribecampo(token, idcolegiat, field_id, "")
                print(f"    Response: {response}")
                cleaned_count += 1

            # Check if telegram ID is invalid (not a positive number)
            elif not is_valid_telegram_id(field_value):
                print(
                    f"    {field_name}: Clearing field - invalid telegram ID ({field_value})"
                )
                response = common.escribecampo(token, idcolegiat, field_id, "")
                print(f"    Response: {response}")
                cleaned_count += 1

    return cleaned_count


print("Procesando socios")


for socio in socios:
    if isinstance(socio["campsDinamics"], dict):
        # Check if any telegram fields exist for this socio
        telegram_fields_present = any(
            field in socio["campsDinamics"] for field in common.telegramfields
        )

        if telegram_fields_present:
            idcolegiat = socio["idColegiat"]

            cleaned_fields = validate_and_clean_telegram_fields(socio, token)

            if cleaned_fields != 0:
                print(f"{common.sociobase}{idcolegiat}")
