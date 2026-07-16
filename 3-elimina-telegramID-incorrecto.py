#!/usr/bin/env python


import configparser
import os
import re

import common
import sync_store

# Pre-compile regex patterns (OPTIMIZATION - Phase 2D)
_DIGITS_ONLY_PATTERN = re.compile(r"\D+")
_DIGITS_ONLY_VALUE_PATTERN = re.compile(r"^[0-9]+$")
_MAX_TELEGRAM_ID = 2**63 - 1


def is_valid_telegram_id(value):
    """
    Check if a value is a valid Telegram user ID.

    Valid values are empty/None, or a strictly positive decimal integer that fits
    within Telegram's signed 64-bit range and contains no separators, signs, or
    scientific notation.
    """
    # Empty/None values are valid (user might not have provided telegram ID yet)
    if value is None:
        return True

    if isinstance(value, bool):
        return False

    value_str = str(value).strip()
    if not value_str:
        return True

    if not _DIGITS_ONLY_VALUE_PATTERN.fullmatch(value_str):
        return False

    if len(value_str) > 1 and value_str.startswith("0"):
        return False

    try:
        telegram_id = int(value_str, 10)
    except (ValueError, TypeError):
        return False

    return 2 <= telegram_id <= _MAX_TELEGRAM_ID


def _only_digits(value):
    """Remove all non-digit characters using pre-compiled pattern (OPTIMIZATION)"""
    return _DIGITS_ONLY_PATTERN.sub("", str(value or ""))


def _register_phone_variants(variants, phone_value, prefix_value=None):
    phone_digits = _only_digits(phone_value)
    if not phone_digits:
        return

    prefix_digits = _only_digits(prefix_value)

    variants.add(phone_digits)

    if prefix_digits:
        variants.add(prefix_digits + phone_digits)

    if prefix_digits and phone_digits.startswith(prefix_digits):
        local = phone_digits[len(prefix_digits) :]
        if local:
            variants.add(local)

    if len(phone_digits) > 9:
        variants.add(phone_digits[-9:])


def socio_phone_digit_variants(socio):
    """
    Build a set of digit-only variants for the socio phone numbers.

    We include forms with/without country prefix so we can detect when a telegram
    field incorrectly stores a phone number representation.
    """
    variants = set()

    persona = socio.get("persona") or {}

    # Direct phone fields on the persona object (common in some exports)
    for phone_key, prefix_key in (
        ("telefonPrincipal", "prefixTelefonPrincipal"),
        ("telefonSecundari", "prefixTelefonSecundari"),
        ("telefon", "prefixTelefon"),
        ("mobil", "prefixMobil"),
    ):
        _register_phone_variants(
            variants, persona.get(phone_key), persona.get(prefix_key)
        )

    adreces = persona.get("adreces") or []
    if not isinstance(adreces, list):
        return variants

    for addr in adreces:
        if not isinstance(addr, dict):
            continue

        for phone_key, prefix_key in (
            ("telefonPrincipal", "prefixTelefonPrincipal"),
            ("telefonSecundari", "prefixTelefonSecundari"),
            ("telefon", "prefixTelefon"),
            ("mobil", "prefixMobil"),
        ):
            _register_phone_variants(
                variants, addr.get(phone_key), addr.get(prefix_key)
            )

    return variants


def clear_telegram_field(
    token,
    socio,
    field_id,
    field_name,
    field_value,
    reason,
    values,
    cleared_field_ids,
    outbox_entries=None,
):
    if field_id in cleared_field_ids:
        return 0

    idcolegiat = socio["idColegiat"]

    # Check if already cleared in cache
    cached_socio = common.read_entity_colegiat(idcolegiat)
    if cached_socio:
        cached_value = cached_socio.get("campsDinamics", {}).get(field_id)
        if not cached_value or cached_value == "":
            print(f"    {field_name}: Already cleared in cache (skipping)")
            cleared_field_ids.add(field_id)
            # Update local state to match cache
            socio["campsDinamics"][field_id] = ""
            if values:
                if field_id == common.tutor1:
                    values["tutor1"] = ""
                elif field_id == common.tutor2:
                    values["tutor2"] = ""
                elif field_id == common.socioid:
                    values["socioid"] = ""
            return 0

    # Check if already in outbox (use provided outbox entries or global state)
    outbox_entries = outbox_entries or []
    already_queued = any(
        e.get("op") == "escribecampo"
        and str(e.get("entity_id")) == str(idcolegiat)
        and e.get("payload", {}).get("campo") == field_id
        and e.get("payload", {}).get("valor", "X") == ""
        and e.get("status") in ["pending", "synced"]
        for e in outbox_entries
    )
    if already_queued:
        print(f"    {field_name}: Already queued for clearing (skipping)")
        cleared_field_ids.add(field_id)
        return 0

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
    outbox_entries=None,
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
            outbox_entries=outbox_entries,
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
            outbox_entries=outbox_entries,
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
            outbox_entries=outbox_entries,
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

    # Get current cached values to check if already cleared
    cached_socio = common.read_entity_colegiat(idcolegiat)
    cached_campos = cached_socio.get("campsDinamics", {}) if cached_socio else {}

    if values["tutor1"] == values["tutor2"] and values["tutor1"] != "":
        # Check cache first
        if cached_campos.get(common.tutor2, "X") == "":
            print("    TUTOR2 duplicate already cleared in cache (skipping)")
        else:
            common.escribecampo(token, idcolegiat, common.tutor2, "")
            cleaned_count += 1

    if (values["tutor1"] == values["socioid"] and values["tutor1"] != "") or (
        values["tutor2"] == values["socioid"] and values["tutor2"] != ""
    ):
        # Check cache first
        if cached_campos.get(common.socioid, "X") == "":
            print("    SOCIO_ID duplicate already cleared in cache (skipping)")
        else:
            common.escribecampo(token, idcolegiat, common.socioid, "")
            cleaned_count += 1

    return cleaned_count


def validate_and_clean_telegram_fields(socio, token, outbox_entries=None):
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
                outbox_entries=outbox_entries,
            )

    cleaned_count += dedupe_telegram_values(socio, token, values)

    return cleaned_count


def main():
    config = configparser.ConfigParser()
    config.read(os.path.expanduser("~/.avast.ini"))

    socios = common.readjson("socios")
    token = common.gettoken(
        user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
    )
    outbox_entries_global = sync_store.read_outbox()

    print("Procesando socios")

    # Progress tracking
    total_socios = len(socios)
    processed = 0
    cleaned_count = 0
    progress_interval = max(1, total_socios // 20)  # Show progress every 5%

    for socio in socios:
        processed += 1

        # Show progress every 5%
        if (
            processed == 1
            or processed % progress_interval == 0
            or processed == total_socios
        ):
            pct = int(100 * processed / total_socios)
            print(
                f"Procesando: {processed}/{total_socios} ({pct}%) - Limpiados: {cleaned_count}",
                flush=True,
            )

        idcolegiat = socio["idColegiat"]
        if isinstance(socio["campsDinamics"], dict):
            # Check if any telegram fields exist for this socio
            telegram_fields_present = any(
                field in socio["campsDinamics"] for field in common.telegramfields
            )

            if telegram_fields_present:
                cleaned_fields = validate_and_clean_telegram_fields(
                    socio, token, outbox_entries=outbox_entries_global
                )

                if cleaned_fields != 0:
                    cleaned_count += cleaned_fields
                    print(f"\n{common.sociobase}{idcolegiat}")
        # else:
        #     # No custom fields populated writing wrong ID.... then cleaning it up

        #     response = common.escribecampo(token, idcolegiat, common.socioid, "algo")
        #     response = common.escribecampo(token, idcolegiat, common.socioid, "")

    return cleaned_count


if __name__ == "__main__":
    main()
