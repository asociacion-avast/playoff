#!/usr/bin/env python


import configparser
import os
import re

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


def _only_digits(value):
    return re.sub(r"\D+", "", str(value or ""))


def socio_phone_digit_variants(socio):
    """
    Build a set of digit-only variants for the socio phone numbers.

    We include forms with/without country prefix so we can detect when a telegram
    field incorrectly stores a phone number representation.
    """
    variants = set()

    persona = socio.get("persona") or {}
    adreces = persona.get("adreces") or []
    if not isinstance(adreces, list):
        return variants

    for addr in adreces:
        if not isinstance(addr, dict):
            continue

        for phone_key, prefix_key in (
            ("telefonPrincipal", "prefixTelefonPrincipal"),
            ("telefonSecundari", "prefixTelefonSecundari"),
        ):
            phone_digits = _only_digits(addr.get(phone_key))
            if not phone_digits:
                continue

            prefix_digits = _only_digits(addr.get(prefix_key))

            # raw phone as stored
            variants.add(phone_digits)

            # prefix + phone (e.g. +34 + 612345678 -> 34612345678)
            if prefix_digits:
                variants.add(prefix_digits + phone_digits)

            # If the stored phone already includes the prefix (common copy/paste),
            # also include a "local" form by stripping it.
            if prefix_digits and phone_digits.startswith(prefix_digits):
                local = phone_digits[len(prefix_digits) :]
                if local:
                    variants.add(local)

            # Heuristic: if it's long, keep the last 9 digits (ES local length)
            if len(phone_digits) > 9:
                variants.add(phone_digits[-9:])

    return variants


def clear_telegram_field(
    token, socio, field_id, field_name, field_value, reason, values, cleared_field_ids
):
    if field_id in cleared_field_ids:
        return 0

    idcolegiat = socio["idColegiat"]
    print(f"    {field_name}: Clearing field - {reason} ({field_value})")
    response = common.escribecampo(token, idcolegiat, field_id, "")
    print(f"    Response: {response}")
    cleared_field_ids.add(field_id)

    # keep local state consistent for later de-dup checks
    socio["campsDinamics"][field_id] = ""
    if values:
        if field_id == common.tutor1:
            values["tutor1"] = ""
        elif field_id == common.tutor2:
            values["tutor2"] = ""
        elif field_id == common.socioid:
            values["socioid"] = ""

    return 1


def clean_single_telegram_field(
    socio,
    token,
    field_id,
    field_name,
    field_value,
    numcolegiat,
    phone_variants,
    values,
    cleared_field_ids,
):
    # Skip empty/None values (they are valid)
    if not field_value:
        return 0

    # Check if telegram ID equals member number (original logic)
    if str(numcolegiat) == str(field_value):
        return clear_telegram_field(
            token,
            socio,
            field_id,
            field_name,
            field_value,
            "telegram ID equals member number",
            values,
            cleared_field_ids,
        )

    # NEW: clear if telegram value is actually a phone number representation
    # of this socio's stored phone (with/without prefix, spacing, '+', etc.).
    field_digits = _only_digits(field_value)
    if field_digits and field_digits in phone_variants:
        return clear_telegram_field(
            token,
            socio,
            field_id,
            field_name,
            field_value,
            "telegram value matches socio phone number",
            values,
            cleared_field_ids,
        )

    # Check if telegram ID is invalid (not a positive number)
    if not is_valid_telegram_id(field_value):
        return clear_telegram_field(
            token,
            socio,
            field_id,
            field_name,
            field_value,
            "invalid telegram ID",
            values,
            cleared_field_ids,
        )

    return 0


def dedupe_telegram_values(socio, token, values):
    """
    Clear duplicates across tutor1/tutor2/socioid for the same socio.
    Returns number of fields cleaned.
    """
    if not values:
        return 0

    idcolegiat = socio["idColegiat"]
    cleaned_count = 0

    if values["tutor1"] == values["tutor2"] and values["tutor1"] != "":
        common.escribecampo(token, idcolegiat, common.tutor2, "")
        cleaned_count += 1

    if (values["tutor1"] == values["socioid"] and values["tutor1"] != "") or (
        values["tutor2"] == values["socioid"] and values["tutor2"] != ""
    ):
        common.escribecampo(token, idcolegiat, common.socioid, "")
        cleaned_count += 1

    return cleaned_count


def validate_and_clean_telegram_fields(socio, token):
    """
    Validate and clean all telegram fields for a socio
    Returns number of fields that were cleaned
    """
    numcolegiat = socio["numColegiat"]

    # Dictionary to map field IDs to readable names
    field_names = {
        common.tutor1: "TUTOR1",
        common.tutor2: "TUTOR2",
        common.socioid: "SOCIO_ID",
    }

    cleaned_count = 0
    cleared_field_ids = set()
    phone_variants = socio_phone_digit_variants(socio)

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

            cleaned_count += clean_single_telegram_field(
                socio,
                token,
                field_id,
                field_name,
                field_value,
                numcolegiat,
                phone_variants,
                values,
                cleared_field_ids,
            )

    cleaned_count += dedupe_telegram_values(socio, token, values)

    return cleaned_count


print("Procesando socios")


for socio in socios:
    idcolegiat = socio["idColegiat"]
    if isinstance(socio["campsDinamics"], dict):
        # Check if any telegram fields exist for this socio
        telegram_fields_present = any(
            field in socio["campsDinamics"] for field in common.telegramfields
        )

        if telegram_fields_present:
            cleaned_fields = validate_and_clean_telegram_fields(socio, token)

            if cleaned_fields != 0:
                print(f"{common.sociobase}{idcolegiat}")
    # else:
    #     # No custom fields populated writing wrong ID.... then cleaning it up

    #     response = common.escribecampo(token, idcolegiat, common.socioid, "algo")
    #     response = common.escribecampo(token, idcolegiat, common.socioid, "")
