import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

import audit_integridad


def socio(sid, categories=(), **extra):
    base = {
        "idColegiat": sid,
        "estat": "COLESTVAL",
        "estatColegiat": {"nom": "ESTALTA"},
        "numColegiat": str(sid),
        "persona": {
            "nom": "Nombre",
            "cognoms": "Apellidos",
            "nif": f"X{sid}0000A",
            "dataNaixement": "2010-01-01",
            "adreces": [
                {"email": f"{sid}@example.test", "telefonPrincipal": "600000000"}
            ],
        },
        "colegiatHasModalitats": [{"idModalitat": value} for value in categories],
    }
    base.update(extra)
    return base


class AuditIntegridadTests(unittest.TestCase):
    def test_detects_duplicate_inscription_and_category_conflict(self):
        members = [socio(1, (90, 91))]
        activities = [
            {
                "idActivitat": "10",
                "estat": "ACTIESTVIG",
                "maxPlaces": "1",
                "placesLliures": "0",
                "descripcio": "x",
            }
        ]
        rows = [
            {
                "idInscripcio": "a",
                "estat": "INSCRESTNOVA",
                "colegiat": {"idColegiat": "1"},
            },
            {
                "idInscripcio": "b",
                "estat": "INSCRESTNOVA",
                "colegiat": {"idColegiat": "1"},
            },
        ]
        findings = audit_integridad.audit_actividades(
            activities, {"10": rows}, {1: members[0]}, date(2026, 7, 17)
        )[0]
        codes = {item["code"] for item in findings}
        self.assertIn("INSCRIPCION_DUPLICADA", codes)
        self.assertIn("ACTIVIDAD_SOBRECUPO", codes)
        codes = {
            item["code"]
            for item in audit_integridad.audit_socios(members, date(2026, 7, 17))[0]
        }
        self.assertIn("SOCIO_CATEGORIAS_INCOMPATIBLES", codes)

    def test_run_reads_local_snapshot_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "socios.json").write_text(json.dumps([socio(1, (90,))]))
            (root / "actividades.json").write_text(
                json.dumps(
                    [
                        {
                            "idActivitat": "10",
                            "maxPlaces": "1",
                            "placesLliures": "0",
                            "estat": "ACTIESTVIG",
                            "descripcio": "x",
                        }
                    ]
                )
            )
            (root / "familias.json").write_text(
                json.dumps({"miembros": {"1": [999]}, "capfamilias": [1, 1]})
            )
            (root / "10.json").write_text(
                json.dumps(
                    [
                        {
                            "idInscripcio": "a",
                            "estat": "INSCRESTNOVA",
                            "colegiat": {"idColegiat": "1"},
                        }
                    ]
                )
            )
            findings = audit_integridad.run(root, today=date(2026, 7, 17))
        codes = {item["code"] for item in findings}
        self.assertIn("FAMILIA_MIEMBRO_INEXISTENTE", codes)
        self.assertIn("FAMILIA_CAP_DUPLICADO", codes)

    def test_shared_telegram_id_between_siblings_is_not_a_finding(self):
        telegram = {"0_16_20241120130245": "123456789"}
        first = socio(1, (90,), campsDinamics=telegram)
        second = socio(2, (90,), campsDinamics=telegram)
        findings, _ = audit_integridad.audit_socios([first, second], date(2026, 7, 17))
        self.assertNotIn(
            "SOCIO_TELEGRAM_DUPLICADO", {item["code"] for item in findings}
        )

    def test_shared_phone_is_allowed_but_invalid_phone_is_reported(self):
        first = socio(1, (90,))
        second = socio(2, (90,))
        second["persona"]["adreces"][0]["telefonPrincipal"] = "123"
        findings, _ = audit_integridad.audit_socios([first, second], date(2026, 7, 17))
        phone_findings = [
            item for item in findings if item["code"] == "SOCIO_TELEFONO_FORMATO"
        ]
        self.assertEqual(len(phone_findings), 1)
        self.assertEqual(phone_findings[0]["id"], "2")
        self.assertTrue(audit_integridad.valid_phone("612 345 678", "+34"))
        self.assertTrue(audit_integridad.valid_phone("2025550123", "+1"))

    def test_shared_iban_is_allowed_but_checksum_is_validated(self):
        first = socio(1, (90,), bancs=[{"iban": "ES9121000418450200051332"}])
        second = socio(2, (90,), bancs=[{"iban": "ES9121000418450200051332"}])
        invalid = socio(3, (90,), bancs=[{"iban": "ES9121000418450200051333"}])
        findings, _ = audit_integridad.audit_socios(
            [first, second, invalid], date(2026, 7, 17)
        )
        codes = [item["code"] for item in findings]
        self.assertNotIn("SOCIO_IBAN_DUPLICADO", codes)
        self.assertEqual(codes.count("SOCIO_IBAN_FORMATO"), 1)
        self.assertTrue(audit_integridad.valid_iban("ES9121000418450200051332"))

    def test_shared_email_is_allowed(self):
        first = socio(1, (90,))
        second = socio(2, (90,))
        second["persona"]["adreces"][0]["email"] = first["persona"]["adreces"][0][
            "email"
        ]
        findings, _ = audit_integridad.audit_socios([first, second], date(2026, 7, 17))
        self.assertNotIn("SOCIO_EMAIL_DUPLICADO", {item["code"] for item in findings})

    def test_family_finding_includes_clickable_profile_url(self):
        item = audit_integridad.finding("TEST", "warning", "familia", 5485, "Prueba")
        self.assertEqual(
            item["url"],
            "https://asociacionavast.playoffinformatica.com/FormAssociat.php?idColegiat=5485&eMenuLat=SECCIO_PERFIL",
        )

    def test_member_finding_includes_profile_url_but_grouped_one_does_not(self):
        member = audit_integridad.finding("TEST", "warning", "socio", 5485, "Prueba")
        grouped = audit_integridad.finding(
            "TEST", "warning", "socio", "12,34", "Prueba"
        )
        self.assertIn("idColegiat=5485", member["url"])
        self.assertNotIn("url", grouped)

    def test_age_category_is_tolerated_in_adjacent_birthday_months(self):
        near = socio(1, (66,))
        near["persona"]["dataNaixement"] = "2013-08-01"  # Cumple 13 el mes siguiente.
        far = socio(2, (66,))
        far["persona"]["dataNaixement"] = "2013-10-01"
        findings, _ = audit_integridad.audit_socios([near, far], date(2026, 7, 17))
        mismatches = {
            item["id"]
            for item in findings
            if item["code"] == "SOCIO_TRAMO_EDAD_INCORRECTO"
        }
        self.assertNotIn("1", mismatches)
        self.assertIn("2", mismatches)

    def test_age_category_is_tolerated_in_birthday_month(self):
        late = socio(1, (66,))
        late["persona"]["dataNaixement"] = (
            "2013-08-31"  # Cumple 13 a finales de agosto.
        )
        findings, _ = audit_integridad.audit_socios([late], date(2026, 8, 15))
        mismatches = {
            item["id"]
            for item in findings
            if item["code"] == "SOCIO_TRAMO_EDAD_INCORRECTO"
        }
        self.assertNotIn("1", mismatches)

    def test_post_crossing_family_does_not_trigger_false_multiple_relation(self):
        familias = {
            "miembros": {
                "1": [2, 3],
                "2": [1, 3],
                "3": [1, 2],
            },
            "capfamilias": [],
        }
        members = {
            1: socio(1, (12,)),
            2: socio(2, (13,)),
            3: socio(3, (90,)),
        }
        findings = audit_integridad.audit_familias(familias, members)
        codes = {item["code"] for item in findings}
        self.assertNotIn("FAMILIA_RELACION_MULTIPLE", codes)

    def test_post_crossing_family_reports_siblings_without_principal_once(self):
        familias = {
            "miembros": {
                "1": [2, 3],
                "2": [1, 3],
                "3": [1, 2],
            },
            "capfamilias": [],
        }
        members = {
            1: socio(1, (13,)),
            2: socio(2, (13,)),
            3: socio(3, (13,)),
        }
        findings = audit_integridad.audit_familias(familias, members)
        hermanos_findings = [
            item
            for item in findings
            if item["code"] == "FAMILIA_HERMANOS_SIN_PRINCIPAL"
        ]
        self.assertEqual(len(hermanos_findings), 1)
        self.assertEqual(hermanos_findings[0]["id"], "1")

    def test_post_crossing_family_reports_multiple_principals_once(self):
        familias = {
            "miembros": {
                "1": [2],
                "2": [1],
            },
            "capfamilias": [],
        }
        members = {
            1: socio(1, (12,)),
            2: socio(2, (12,)),
        }
        findings = audit_integridad.audit_familias(familias, members)
        principals_findings = [
            item for item in findings if item["code"] == "FAMILIA_PRINCIPALES_MULTIPLES"
        ]
        self.assertEqual(len(principals_findings), 1)
        self.assertEqual(principals_findings[0]["id"], "1")

    def test_malformed_family_keys_are_skipped(self):
        familias = {
            "miembros": {
                "1": [2],
                "not_a_number": [1],
                "2": [1],
            },
            "capfamilias": [],
        }
        members = {1: socio(1, (12,)), 2: socio(2, (13,))}
        findings = audit_integridad.audit_familias(familias, members)
        codes = {item["code"] for item in findings}
        self.assertNotIn("FAMILIA_CABEZA_INEXISTENTE", codes)
        self.assertNotIn("FAMILIA_RELACION_MULTIPLE", codes)


if __name__ == "__main__":
    unittest.main()
