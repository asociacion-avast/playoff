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
    Check if a value is a valid telegram ID (positive integer without signs) or empty/None (also valid)
    """
    # Empty/None values are valid (user might not have provided telegram ID yet)
    if not value:
        return True

    # Convert to string to check for signs
    value_str = str(value).strip()

    # Reject if contains '+' or '-' signs
    if "+" in value_str or "-" in value_str:
        return False

    # Handle both string and integer inputs
    try:
        telegram_id = int(value_str)
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

    if isinstance(socio["campsDinamics"], dict):
        values = {"tutor1": "", "tutor2": "", "socioid": ""}
    else:
        values = False

    # Check each telegram field that exists for this socio
    for field_id in common.telegramfields:
        if field_id in socio["campsDinamics"]:
            field_name = field_names.get(field_id, f"UNKNOWN_{field_id}")
            field_value = socio["campsDinamics"][field_id]

            # Fill values on each field
            if field_id == common.tutor1:
                values["tutor1"] = field_value
            elif field_id == common.tutor2:
                values["tutor2"] = field_value
            elif field_id == common.socioid:
                values["socioid"] = field_value

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

    if values:
        # Chack that the same value is not stored in different fields
        if values["tutor1"] == values["tutor2"] and values["tutor1"] != "":
            response = common.escribecampo(token, idcolegiat, common.tutor2, "")
            cleaned_count += 1
        if (
            values["tutor1"] == values["socioid"]
            and values["tutor1"] != ""
            or values["tutor2"] == values["socioid"]
            and values["tutor2"] != ""
        ):
            response = common.escribecampo(token, idcolegiat, common.socioid, "")
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
