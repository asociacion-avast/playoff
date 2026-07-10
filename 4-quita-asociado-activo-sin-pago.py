#!/usr/bin/env python

import argparse
import configparser
import os
from datetime import date, datetime

import common


def parse_date_value(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            pass
        try:
            return datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError:
            pass
    return None


def normalize_text(value):
    return (value or "").strip().lower()


def should_remove_socio_activo(socio, today=None):
    """True when the member has Asociado activo assigned today, informe revisado and no curso docentes."""
    if today is None:
        today = date.today()

    has_asociado_activo_today = False
    has_informe_revisado = False
    has_curso_docentes = False

    for modalitat in socio.get("colegiatHasModalitats", []):
        modalitat_id = None
        try:
            modalitat_id = int(modalitat.get("idModalitat", 0))
        except (TypeError, ValueError):
            modalitat_id = 0

        modalitat_data = modalitat.get("modalitat") or {}
        nom = normalize_text(modalitat_data.get("nom"))
        agrupacio = normalize_text((modalitat_data.get("agrupacio") or {}).get("nom"))
        assigned_date = parse_date_value(modalitat.get("dataAssignacio"))

        if modalitat_id == common.categorias["socioactivo"] and assigned_date == today:
            if nom == "asociado activo" or agrupacio == "socio actividades":
                has_asociado_activo_today = True

        if modalitat_id == common.categorias["informerevisado"]:
            if (
                nom == "informe revisado"
                or nom == "informe validado"
                or "informe" in nom
            ):
                has_informe_revisado = True

        if "curso" in nom and "docente" in nom:
            print("Socio has curso docentes")
            has_curso_docentes = True

    return has_asociado_activo_today and has_informe_revisado and not has_curso_docentes


def main():
    parser = argparse.ArgumentParser(
        description="Quita la categoría de Asociado activo cuando el socio tiene informe revisado y la categoría se asignó hoy"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo muestra los socios que se procesarían sin borrar ninguna categoría",
    )
    parser.add_argument(
        "--date",
        dest="target_date",
        help="Fecha a comprobar en formato YYYY-MM-DD (opcional)",
    )
    args = parser.parse_args()

    token = None
    if not args.dry_run:
        config = configparser.ConfigParser()
        config.read(os.path.expanduser("~/.avast.ini"))
        if "auth" not in config:
            raise SystemExit(
                "No se encontró ~/.avast.ini con la sección [auth]. Usa --dry-run para revisar sin aplicar cambios."
            )
        token = common.gettoken(
            user=config["auth"]["RWusername"], password=config["auth"]["RWpassword"]
        )

    today = date.today()
    if args.target_date:
        today = datetime.strptime(args.target_date, "%Y-%m-%d").date()

    socios = common.readjson("socios")

    matched = []
    for socio in socios:
        if not common.validasocio(
            socio,
            estado="COLESTVAL",
            estatcolegiat="ESTALTA",
            agrupaciones=["PREINSCRIPCIÓN"],
            reverseagrupaciones=False,
        ):
            continue

        if should_remove_socio_activo(socio, today=today):
            socioid = int(socio["idColegiat"])
            categoriassocio = common.getcategoriassocio(socio=socio)
            matched.append((socioid, categoriassocio))

            if common.categorias["socioactivo"] in categoriassocio:
                print(
                    f"Socio {common.sociobase}{socioid}#tab=CATEGORIES -> quitar 'Asociado activo'"
                )
                if not args.dry_run:
                    common.delcategoria(
                        token=token,
                        socio=socioid,
                        categoria=common.categorias["socioactivo"],
                    )
            else:
                print(
                    f"Socio {common.sociobase}{socioid}#tab=CATEGORIES -> ya no tiene 'Asociado activo'"
                )

    if not matched:
        print("No se encontraron socios para procesar")


if __name__ == "__main__":
    main()
