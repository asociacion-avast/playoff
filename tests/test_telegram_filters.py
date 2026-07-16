import importlib.util
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_common_module():
    with tempfile.TemporaryDirectory() as tmpdir:
        home_dir = Path(tmpdir)
        config_path = home_dir / ".avast.ini"
        config_path.write_text(
            "[auth]\n"
            "endpoint=asociacionavast\n"
            "username=testuser\n"
            "password=testpass\n"
            "RWusername=testuser\n"
            "RWpassword=testpass\n"
        )
        old_home = os.environ.get("HOME")
        os.environ["HOME"] = str(home_dir)
        try:
            spec = importlib.util.spec_from_file_location("common", ROOT / "common.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        finally:
            if old_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = old_home


common = load_common_module()


def load_telegram_script_module(common_module=None, sync_module=None):
    if common_module is None:
        common_module = load_common_module()
    if sync_module is None:
        sync_module = types.SimpleNamespace(read_outbox=lambda: [])

    with tempfile.TemporaryDirectory() as tmpdir:
        home_dir = Path(tmpdir)
        config_path = home_dir / ".avast.ini"
        config_path.write_text(
            "[auth]\n"
            "endpoint=asociacionavast\n"
            "username=testuser\n"
            "password=testpass\n"
            "RWusername=testuser\n"
            "RWpassword=testpass\n"
        )
        old_home = os.environ.get("HOME")
        os.environ["HOME"] = str(home_dir)

        original_modules = {}
        for name, module in {
            "common": common_module,
            "sync_store": sync_module,
        }.items():
            original_modules[name] = sys.modules.get(name)
            sys.modules[name] = module

        try:
            spec = importlib.util.spec_from_file_location(
                "telegram_script",
                ROOT / "3-elimina-telegramID-incorrecto.py",
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        finally:
            for name, previous in original_modules.items():
                if previous is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = previous
            if old_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = old_home


class TelegramFilterTests(unittest.TestCase):
    def test_es_socio_anual_activo_detects_active_annual_members(self):
        socio = {
            "idColegiat": 123,
            "colegiatHasModalitats": [
                {"idModalitat": str(common.categorias["socioactivo"])}
            ],
        }
        self.assertTrue(common.es_socio_anual_activo(socio))

    def test_es_socio_anual_activo_rejects_non_annual_members(self):
        socio = {
            "idColegiat": 456,
            "colegiatHasModalitats": [{"idModalitat": "1"}],
        }
        self.assertFalse(common.es_socio_anual_activo(socio))

    def test_socio_phone_digit_variants_detects_phone_number_variants(self):
        script = load_telegram_script_module()
        socio = {
            "persona": {
                "adreces": [
                    {
                        "telefonPrincipal": "612 345 678",
                        "prefixTelefonPrincipal": "+34",
                    }
                ]
            }
        }

        variants = script.socio_phone_digit_variants(socio)

        self.assertIn("612345678", variants)
        self.assertIn("34612345678", variants)

    def test_is_valid_telegram_id_rejects_malformed_and_overflow_values(self):
        script = load_telegram_script_module()

        self.assertTrue(script.is_valid_telegram_id("123456789"))
        self.assertFalse(script.is_valid_telegram_id("0"))
        self.assertFalse(script.is_valid_telegram_id("1"))
        self.assertFalse(script.is_valid_telegram_id("010"))
        self.assertFalse(script.is_valid_telegram_id("00123"))
        self.assertFalse(script.is_valid_telegram_id("+123"))
        self.assertFalse(script.is_valid_telegram_id("-123"))
        self.assertFalse(script.is_valid_telegram_id("123.45"))
        self.assertFalse(script.is_valid_telegram_id("1e10"))
        self.assertFalse(script.is_valid_telegram_id("123 456"))
        self.assertFalse(script.is_valid_telegram_id("abc"))
        self.assertFalse(script.is_valid_telegram_id("9223372036854775808"))

    def test_clean_single_telegram_field_clears_phone_number_values(self):
        calls = []

        def fake_escribecampo(token, idcolegiat, field_id, value):
            calls.append((idcolegiat, field_id, value))
            return {"ok": True}

        common_module = types.SimpleNamespace(
            readjson=lambda *_args, **_kwargs: [],
            gettoken=lambda **_kwargs: "token",
            read_entity_colegiat=lambda *_args, **_kwargs: None,
            escribecampo=fake_escribecampo,
            tutor1="0_13_20231012041710",
            tutor2="0_14_20231012045321",
            socioid="0_16_20241120130245",
            telegramfields=[
                "0_13_20231012041710",
                "0_14_20231012045321",
                "0_16_20241120130245",
            ],
            sociobase="SOCIO",
        )
        script = load_telegram_script_module(common_module=common_module)

        socio = {
            "idColegiat": 7,
            "numColegiat": 100,
            "campsDinamics": {},
            "persona": {
                "adreces": [
                    {
                        "telefonPrincipal": "612 345 678",
                        "prefixTelefonPrincipal": "+34",
                    }
                ]
            },
        }
        values = {"tutor1": "", "tutor2": "", "socioid": ""}
        cleared_field_ids = set()

        cleaned_count = script.clean_single_telegram_field(
            socio,
            "token",
            common_module.tutor1,
            "TUTOR1",
            "612345678",
            100,
            {"612345678"},
            values,
            cleared_field_ids,
        )

        self.assertEqual(cleaned_count, 1)
        self.assertEqual(calls, [(7, common_module.tutor1, "")])
        self.assertIn(common_module.tutor1, cleared_field_ids)


if __name__ == "__main__":
    unittest.main()
