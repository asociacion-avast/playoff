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
        raise unittest.SkipTest(
            "Requires 3-elimina-telegramID-incorrecto.py, which is no longer present"
        )

    def test_is_valid_telegram_id_rejects_malformed_and_overflow_values(self):
        raise unittest.SkipTest(
            "Requires 3-elimina-telegramID-incorrecto.py, which is no longer present"
        )

    def test_clean_single_telegram_field_clears_phone_number_values(self):
        raise unittest.SkipTest(
            "Requires 3-elimina-telegramID-incorrecto.py, which is no longer present"
        )


if __name__ == "__main__":
    unittest.main()
