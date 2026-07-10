import importlib.util
import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script_module():
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
        old_sys_path = list(sys.path)
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        try:
            spec = importlib.util.spec_from_file_location(
                "quita_socio_activo",
                ROOT / "4-quita-asociado-activo-sin-pago.py",
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        finally:
            sys.path[:] = old_sys_path
            if old_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = old_home


class QuitaSocioActivoTests(unittest.TestCase):
    def test_should_remove_when_asociado_activo_assigned_today_and_informe_revisado(
        self,
    ):
        script = load_script_module()
        socio = {
            "idColegiat": 123,
            "colegiatHasModalitats": [
                {
                    "idModalitat": "82",
                    "dataAssignacio": "2026-07-10 10:15:00",
                    "modalitat": {
                        "nom": "Asociado activo",
                        "agrupacio": {"nom": "SOCIO ACTIVIDADES"},
                    },
                },
                {
                    "idModalitat": "94",
                    "dataAssignacio": "2026-07-09 09:00:00",
                    "modalitat": {
                        "nom": "Informe revisado",
                        "agrupacio": {"nom": "INFORME"},
                    },
                },
            ],
        }

        self.assertTrue(
            script.should_remove_socio_activo(socio, today=date(2026, 7, 10))
        )

    def test_should_not_remove_when_asociado_activo_not_assigned_today(self):
        script = load_script_module()
        socio = {
            "idColegiat": 456,
            "colegiatHasModalitats": [
                {
                    "idModalitat": "82",
                    "dataAssignacio": "2026-07-09 10:15:00",
                    "modalitat": {
                        "nom": "Asociado activo",
                        "agrupacio": {"nom": "SOCIO ACTIVIDADES"},
                    },
                },
                {
                    "idModalitat": "94",
                    "dataAssignacio": "2026-07-09 09:00:00",
                    "modalitat": {
                        "nom": "Informe revisado",
                        "agrupacio": {"nom": "INFORME"},
                    },
                },
            ],
        }

        self.assertFalse(
            script.should_remove_socio_activo(socio, today=date(2026, 7, 10))
        )

    def test_should_not_remove_when_socio_has_curso_docentes(self):
        script = load_script_module()
        socio = {
            "idColegiat": 789,
            "colegiatHasModalitats": [
                {
                    "idModalitat": "82",
                    "dataAssignacio": "2026-07-10 10:15:00",
                    "modalitat": {
                        "nom": "Asociado activo",
                        "agrupacio": {"nom": "SOCIO ACTIVIDADES"},
                    },
                },
                {
                    "idModalitat": "94",
                    "dataAssignacio": "2026-07-10 09:00:00",
                    "modalitat": {
                        "nom": "Informe revisado",
                        "agrupacio": {"nom": "INFORME"},
                    },
                },
                {
                    "idModalitat": "999",
                    "dataAssignacio": "2026-07-10 08:00:00",
                    "modalitat": {
                        "nom": "Curso docentes",
                        "agrupacio": {"nom": "CURSOS"},
                    },
                },
            ],
        }

        self.assertFalse(
            script.should_remove_socio_activo(socio, today=date(2026, 7, 10))
        )


if __name__ == "__main__":
    unittest.main()
