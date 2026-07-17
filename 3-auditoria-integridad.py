#!/usr/bin/env python3
"""Auditoría completa de datos locales de PlayOff; no realiza cambios."""

import argparse
import json
import signal
from collections import Counter
from datetime import datetime

import audit_integridad

signal.signal(signal.SIGPIPE, signal.SIG_DFL)


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--data-dir", default="data", help="Directorio de instantáneas (por defecto: data)"
)
parser.add_argument("--json", action="store_true", help="Emite los hallazgos en JSON")
parser.add_argument("--today", help="Fecha de referencia YYYY-MM-DD, útil para pruebas")
args = parser.parse_args()
today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else None
findings = audit_integridad.run(args.data_dir, today=today)

if args.json:
    print(json.dumps(findings, ensure_ascii=False, indent=2))
else:
    counts = Counter(item["severity"] for item in findings)
    try:
        print(
            f"Auditoría completada: {len(findings)} hallazgos "
            f"({counts['error']} errores, {counts['warning']} avisos)."
        )
        for item in findings:
            line = f"[{item['severity'].upper()}] {item['code']} {item['entity']} {item['id']}: {item['message']}"
            if item.get("url"):
                line = f"{line} {item['url']}"
            print(line)
    except BrokenPipeError:
        pass
